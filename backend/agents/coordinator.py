"""
Central Hospital Coordinator:
Orchestrates the multi-agent life-cycle (Triage -> Allocation -> Escalation -> HITL -> Commit).
Maintains transactional consistency over the live SharedHospitalState.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable, Any

from ..models.patient import PatientIntake
from ..models.resources import BedStatus, EquipmentStatus, HospitalResources
from ..models.decisions import (
    TriageDecision, ResourceAllocation, EscalationDecision,
    DoctorReviewTicket, DoctorReviewStatus, DoctorAction, TriagePriority
)
from ..models.state import SharedHospitalState, WebSocketEvent, WebSocketEventType, HospitalMetrics
from ..data.resource_generator import generate_default_resources
from .triage_agent import TriageAgent
from .allocation_agent import AllocationAgent
from .escalation_agent import EscalationAgent
from .callbacks import global_monitor
import time

logger = logging.getLogger("medflow.coordinator")


class HospitalCoordinator:
    """
    Central Orchestrator for MedFlow AI.
    Controls state transitions, agent invocation, and human-in-the-loop workflows.
    """
    
    def __init__(
        self,
        triage_agent: Optional[TriageAgent] = None,
        allocation_agent: Optional[AllocationAgent] = None,
        escalation_agent: Optional[EscalationAgent] = None,
        initial_resources: Optional[HospitalResources] = None,
        event_callback: Optional[Callable[[WebSocketEvent], Any]] = None
    ):
        self.triage_agent = triage_agent or TriageAgent()
        self.allocation_agent = allocation_agent or AllocationAgent()
        self.escalation_agent = escalation_agent or EscalationAgent()
        self.event_callback = event_callback
        
        # Initialize Shared State
        self.state = SharedHospitalState()
        self._load_resources(initial_resources or generate_default_resources())
        
    def _load_resources(self, resources: HospitalResources):
        """Populates state with beds, staff, and equipment."""
        for b in resources.beds:
            self.state.beds[b.bed_id] = b
        for s in resources.staff:
            self.state.staff[s.staff_id] = s
        for e in resources.equipment:
            self.state.equipment[e.equipment_id] = e
        self.recalculate_metrics()

    def set_event_callback(self, callback: Callable[[WebSocketEvent], Any]):
        """Sets external WebSocket broadcaster callback."""
        self.event_callback = callback

    def _emit(self, event_type: WebSocketEventType, payload: dict):
        """Publishes an event to the audit trail and active WebSocket listeners."""
        evt = WebSocketEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload=payload
        )
        self.state.event_log.append(evt)
        # Keep last 200 events in memory
        if len(self.state.event_log) > 200:
            self.state.event_log = self.state.event_log[-200:]
            
        if self.event_callback:
            try:
                self.event_callback(evt)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    # -------------------------------------------------------------
    # PRIMARY END-TO-END INTAKE & ALLOCATION WORKFLOW
    # -------------------------------------------------------------
    def intake_patient(self, patient: PatientIntake) -> Dict[str, Any]:
        """
        Receives an incoming patient and executes the complete 4-stage agentic workflow:
        1. Perception & Registration
        2. Triage Reasoning
        3. Global CP-SAT Allocation
        4. Escalation & Safety Gate
        """
        pid = patient.patient_id
        self.state.patients[pid] = patient
        if pid not in self.state.waiting_queue:
            self.state.waiting_queue.append(pid)
            
        self._emit(WebSocketEventType.PATIENT_ARRIVED, {
            "patient_id": pid,
            "name": patient.name,
            "age": patient.age,
            "complaint": patient.chief_complaint
        })
        
        # Stage 1: Triage Agent
        t0 = time.time()
        global_monitor.on_agent_start("TriageAgent", {"patient_id": pid, "complaint": patient.chief_complaint})
        triage = self.triage_agent.evaluate(patient)
        global_monitor.on_agent_finish("TriageAgent", triage.model_dump(), execution_time_ms=(time.time() - t0) * 1000)
        self.state.triage_decisions[pid] = triage
        self.state.metrics.total_triaged += 1
        
        self._emit(WebSocketEventType.TRIAGE_COMPLETED, {
            "patient_id": pid,
            "severity_score": triage.severity_score,
            "priority": triage.priority.value,
            "confidence": triage.confidence,
            "department": triage.recommended_department.value,
            "news2": triage.deterministic_news2_score
        })
        
        # Stage 2: Global Optimization Batch
        # We re-optimize over all patients in the waiting queue
        queued_patients = [self.state.patients[p_idx] for p_idx in self.state.waiting_queue if p_idx in self.state.patients]
        
        # Calculate current wait times in minutes
        now = datetime.now(timezone.utc)
        wait_times = {
            p.patient_id: max(0.0, (now - p.arrival_time).total_seconds() / 60.0)
            for p in queued_patients
        }
        
        t1 = time.time()
        global_monitor.on_agent_start("AllocationAgent", {"queue_size": len(queued_patients)})
        allocations, opt_metrics = self.allocation_agent.allocate_batch(
            patients=queued_patients,
            triage_decisions=self.state.triage_decisions,
            beds=list(self.state.beds.values()),
            staff=list(self.state.staff.values()),
            equipment=list(self.state.equipment.values()),
            patient_wait_times=wait_times
        )
        status_val = opt_metrics.get("solver_status", "OPTIMAL") if isinstance(opt_metrics, dict) else getattr(opt_metrics, "status", "OPTIMAL")
        allocated_cnt = opt_metrics.get("allocated_count", len(allocations)) if isinstance(opt_metrics, dict) else getattr(opt_metrics, "allocated_count", len(allocations))
        global_monitor.on_agent_finish("AllocationAgent", {"status": str(status_val), "assigned_count": allocated_cnt}, execution_time_ms=(time.time() - t1) * 1000)
        
        # Match candidate allocation for this patient
        candidate_alloc = next((a for a in allocations if a.patient_id == pid), None)
        if candidate_alloc:
            self.state.allocations[pid] = candidate_alloc
            
        # Stage 3: Escalation Agent Gatekeeper
        t2 = time.time()
        global_monitor.on_agent_start("EscalationAgent", {"patient_id": pid})
        escalation = self.escalation_agent.evaluate(
            patient=patient,
            triage=triage,
            allocation=candidate_alloc
        )
        global_monitor.on_agent_finish("EscalationAgent", escalation.model_dump(), execution_time_ms=(time.time() - t2) * 1000)
        
        global_monitor.on_state_change(
            entity_id=pid,
            old_state="WAITING_QUEUE",
            new_state="ESCALATED_HITL" if escalation.is_escalated else ("ALLOCATED" if candidate_alloc and candidate_alloc.is_allocated else "WAITING"),
            reason=f"Priority: {triage.priority.value} | Escalated: {escalation.is_escalated}"
        )
        
        # Stage 4: Execution / Commitment or HITL Parking
        if escalation.is_escalated:
            self.state.metrics.total_escalated += 1
            ticket = self.escalation_agent.create_doctor_ticket(
                patient=patient,
                triage=triage,
                allocation=candidate_alloc,
                escalation=escalation
            )
            self.state.pending_doctor_reviews[ticket.ticket_id] = ticket
            
            self._emit(WebSocketEventType.ESCALATION_TRIGGERED, {
                "ticket_id": ticket.ticket_id,
                "patient_id": pid,
                "risk_level": escalation.risk_level,
                "reasons": [r.value for r in escalation.reasons],
                "action_required": escalation.action_required
            })
            
            # Immediately commit the bed allocation so the patient is actively admitted to ICU/Ward
            # and receiving resuscitation, while keeping the ticket active for physician review/override.
            if candidate_alloc and candidate_alloc.is_allocated:
                self._commit_allocation(candidate_alloc)
        else:
            # Safe to auto-commit
            if candidate_alloc and candidate_alloc.is_allocated:
                self._commit_allocation(candidate_alloc)
                
        self.recalculate_metrics()
        
        return {
            "patient_id": pid,
            "triage": triage.model_dump(),
            "allocation": candidate_alloc.model_dump() if candidate_alloc else None,
            "escalation": escalation.model_dump(),
            "requires_doctor_review": escalation.is_escalated
        }

    def _commit_allocation(self, alloc: ResourceAllocation):
        """Finalizes resource assignments into physical hospital records."""
        pid = alloc.patient_id
        
        # 1. Update Bed
        if alloc.assigned_bed_id and alloc.assigned_bed_id in self.state.beds:
            bed = self.state.beds[alloc.assigned_bed_id]
            bed.status = BedStatus.OCCUPIED
            bed.current_patient_id = pid
            
        # 2. Update Staff
        for sid in alloc.assigned_staff_ids:
            if sid in self.state.staff:
                st = self.state.staff[sid]
                if pid not in st.assigned_patient_ids:
                    st.assigned_patient_ids.append(pid)
                    
        # 3. Update Equipment
        for eid in alloc.assigned_equipment_ids:
            if eid in self.state.equipment:
                eq = self.state.equipment[eid]
                eq.status = EquipmentStatus.IN_USE
                eq.current_patient_id = pid
                
        # 4. Remove from waiting queue
        if pid in self.state.waiting_queue:
            self.state.waiting_queue.remove(pid)
            
        self.state.metrics.total_allocated += 1
        
        self._emit(WebSocketEventType.ALLOCATION_COMPLETED, {
            "patient_id": pid,
            "assigned_bed": alloc.assigned_bed_id,
            "assigned_staff": alloc.assigned_staff_ids,
            "assigned_equipment": alloc.assigned_equipment_ids
        })

    # -------------------------------------------------------------
    # HUMAN-IN-THE-LOOP (DOCTOR) ACTIONS
    # -------------------------------------------------------------
    def handle_doctor_action(
        self,
        ticket_id: str,
        action: DoctorAction,
        doctor_id: str = "DOC-ON-DUTY",
        override_priority: Optional[TriagePriority] = None,
        override_bed_id: Optional[str] = None,
        override_staff_id: Optional[str] = None,
        doctor_notes: Optional[str] = None
    ) -> DoctorReviewTicket:
        """
        Executes clinician override or approval. Guarantees that AI yields to human medical judgment.
        """
        if ticket_id not in self.state.pending_doctor_reviews:
            raise KeyError(f"Ticket {ticket_id} not found in pending review queue.")
            
        ticket = self.state.pending_doctor_reviews[ticket_id]
        pid = ticket.patient_id
        
        ticket.reviewer_doctor_id = doctor_id
        ticket.action_taken = action
        ticket.doctor_notes = doctor_notes
        ticket.resolved_at = datetime.now(timezone.utc)
        
        if action == DoctorAction.APPROVE:
            ticket.status = DoctorReviewStatus.APPROVED
            if ticket.candidate_allocation and ticket.candidate_allocation.is_allocated:
                self._commit_allocation(ticket.candidate_allocation)
            self._emit(WebSocketEventType.DOCTOR_APPROVED, {
                "ticket_id": ticket_id,
                "patient_id": pid,
                "doctor_id": doctor_id
            })
            
        elif action == DoctorAction.OVERRIDE_PRIORITY and override_priority:
            ticket.status = DoctorReviewStatus.OVERRIDDEN
            ticket.override_priority = override_priority
            # Mutate triage priority
            if pid in self.state.triage_decisions:
                self.state.triage_decisions[pid].priority = override_priority
            self.state.metrics.total_doctor_overrides += 1
            
            # Trigger re-optimization
            self._reoptimize_all()
            self._emit(WebSocketEventType.DOCTOR_OVERRIDE, {
                "ticket_id": ticket_id,
                "patient_id": pid,
                "type": "PRIORITY_OVERRIDE",
                "new_priority": override_priority.value
            })
            
        elif action == DoctorAction.REASSIGN_RESOURCES:
            ticket.status = DoctorReviewStatus.OVERRIDDEN
            ticket.override_bed_id = override_bed_id
            ticket.override_staff_id = override_staff_id
            self.state.metrics.total_doctor_overrides += 1
            
            # Manually assign bed if provided
            if override_bed_id and override_bed_id in self.state.beds:
                bed = self.state.beds[override_bed_id]
                bed.status = BedStatus.OCCUPIED
                bed.current_patient_id = pid
                if pid in self.state.waiting_queue:
                    self.state.waiting_queue.remove(pid)
                    
            if override_staff_id and override_staff_id in self.state.staff:
                st = self.state.staff[override_staff_id]
                if pid not in st.assigned_patient_ids:
                    st.assigned_patient_ids.append(pid)
                    
            self._emit(WebSocketEventType.DOCTOR_OVERRIDE, {
                "ticket_id": ticket_id,
                "patient_id": pid,
                "type": "RESOURCE_REASSIGNMENT",
                "bed": override_bed_id,
                "staff": override_staff_id
            })
            
        elif action == DoctorAction.DISCHARGE:
            ticket.status = DoctorReviewStatus.APPROVED
            self.discharge_patient(pid)
            
        # Remove from pending queue
        del self.state.pending_doctor_reviews[ticket_id]
        self.recalculate_metrics()
        return ticket

    def discharge_patient(self, patient_id: str):
        """
        Discharges a patient, freeing their assigned bed, equipment, and staff capacity,
        then automatically re-runs optimization for the waiting queue.
        """
        # Free Bed
        for bed in self.state.beds.values():
            if bed.current_patient_id == patient_id:
                bed.status = BedStatus.AVAILABLE
                bed.current_patient_id = None
                
        # Free Staff
        for staff in self.state.staff.values():
            if patient_id in staff.assigned_patient_ids:
                staff.assigned_patient_ids.remove(patient_id)
                
        # Free Equipment
        for eq in self.state.equipment.values():
            if eq.current_patient_id == patient_id:
                eq.status = EquipmentStatus.AVAILABLE
                eq.current_patient_id = None
                
        if patient_id in self.state.waiting_queue:
            self.state.waiting_queue.remove(patient_id)
            
        self.state.metrics.total_discharged += 1
        
        self._emit(WebSocketEventType.PATIENT_DISCHARGED, {
            "patient_id": patient_id
        })
        
        # Dynamic re-allocation of remaining queue
        self._reoptimize_all()
        self.recalculate_metrics()

    def _reoptimize_all(self):
        """Runs global optimization over any remaining unallocated patients in the queue."""
        if not self.state.waiting_queue:
            return
            
        queued_patients = [self.state.patients[pid] for pid in self.state.waiting_queue if pid in self.state.patients]
        now = datetime.now(timezone.utc)
        wait_times = {
            p.patient_id: max(0.0, (now - p.arrival_time).total_seconds() / 60.0)
            for p in queued_patients
        }
        
        allocations, _ = self.allocation_agent.allocate_batch(
            patients=queued_patients,
            triage_decisions=self.state.triage_decisions,
            beds=list(self.state.beds.values()),
            staff=list(self.state.staff.values()),
            equipment=list(self.state.equipment.values()),
            patient_wait_times=wait_times
        )
        
        for alloc in allocations:
            if alloc.is_allocated:
                self.state.allocations[alloc.patient_id] = alloc
                # If triage was not critical or already cleared, auto-commit
                triage = self.state.triage_decisions.get(alloc.patient_id)
                if triage and triage.priority != TriagePriority.CRITICAL:
                    self._commit_allocation(alloc)

    def recalculate_metrics(self):
        """Updates live hospital capacity, occupancy, and wait-time statistics."""
        m = self.state.metrics
        total_beds = len(self.state.beds)
        occupied_beds = sum(1 for b in self.state.beds.values() if b.status == BedStatus.OCCUPIED)
        m.bed_occupancy_rate = round(occupied_beds / max(1, total_beds), 3)
        
        icu_beds = [b for b in self.state.beds.values() if b.bed_type.value == "ICU_BED"]
        icu_occupied = sum(1 for b in icu_beds if b.status == BedStatus.OCCUPIED)
        m.icu_occupancy_rate = round(icu_occupied / max(1, len(icu_beds)), 3)
        
        total_staff_cap = sum(s.max_patient_capacity for s in self.state.staff.values() if s.is_on_duty)
        used_staff_cap = sum(len(s.assigned_patient_ids) for s in self.state.staff.values() if s.is_on_duty)
        m.staff_utilization_rate = round(used_staff_cap / max(1, total_staff_cap), 3)
        
        total_eq = len(self.state.equipment)
        used_eq = sum(1 for e in self.state.equipment.values() if e.status == EquipmentStatus.IN_USE)
        m.equipment_utilization_rate = round(used_eq / max(1, total_eq), 3)
        
        # Calculate Queue Wait Times
        now = datetime.now(timezone.utc)
        waits = []
        crit_waits = []
        for pid in self.state.waiting_queue:
            pt = self.state.patients.get(pid)
            triage = self.state.triage_decisions.get(pid)
            if pt:
                w = (now - pt.arrival_time).total_seconds() / 60.0
                waits.append(w)
                if triage and triage.priority == TriagePriority.CRITICAL:
                    crit_waits.append(w)
                    
        m.average_wait_time_minutes = round(sum(waits) / max(1, len(waits)), 1)
        m.critical_average_wait_time_minutes = round(sum(crit_waits) / max(1, len(crit_waits)), 1)
        self.state.last_updated = now

    def reset_hospital(self, initial_resources: Optional[HospitalResources] = None):
        """Cleans and re-initializes all hospital state."""
        self.state = SharedHospitalState()
        self._load_resources(initial_resources or generate_default_resources())
        self._emit(WebSocketEventType.SYSTEM_ALERT, {"message": "Hospital state reset to default."})
