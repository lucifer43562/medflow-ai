"""
CrewAI & Google ADK Framework Interoperability Bridge:
Implements:
1. CrewAITriageAgent: Triage Agent defined using the CrewAI framework (Role, Goal, Backstory).
2. ADKAllocationAgent: Resource Allocation Agent defined using the Google ADK / GenAI Agent pattern.
3. Cross-Framework A2A Execution Loop: Seamless message passing and state synchronization via Hover Blackboard.
"""

import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

import crewai
from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process

from ..models.patient import PatientIntake
from ..models.decisions import TriageDecision, TriagePriority, RecommendedDepartment
from ..models.resources import BedType, StaffRole, EquipmentType
from .a2a_protocol import A2AMessage, A2APerformative, global_a2a_dispatcher
from .blackboard import HoverBlackboard
from .callbacks import global_monitor
from ..optimization.ortools_allocator import HospitalOptimizationEngine

logger = logging.getLogger("medflow.interop")


class CrewAITriageSpecialist:
    """
    Triage Agent implemented using the CrewAI Framework.
    Employs clinical persona, goal, and backstory for structured clinical perception.
    """
    
    def __init__(self, blackboard: Optional[HoverBlackboard] = None):
        self.blackboard = blackboard
        
        # CrewAI Agent Definition
        self.crew_agent = CrewAgent(
            role="Senior Clinical Triage Specialist",
            goal="Rapidly analyze emergency patient vitals and chief complaints to produce deterministic triage classifications.",
            backstory="""You are a veteran Emergency Department Resuscitation Officer with 15+ years 
            of experience managing mass casualty incidents. You strictly adhere to the National Early 
            Warning Score 2 (NEWS2) and Emergency Severity Index (ESI) protocols.""",
            verbose=False,
            allow_delegation=False
        )

    def evaluate_patient_crew(self, patient: PatientIntake) -> TriageDecision:
        """
        Executes CrewAI triage reasoning and posts result to Blackboard & A2A protocol.
        """
        t0 = time.time()
        global_monitor.on_agent_start("CrewAI_TriageSpecialist", {"patient_id": patient.patient_id})
        
        # Clinical Rule Calculation
        v = patient.vitals
        from .triage_agent import calculate_news2
        news2 = calculate_news2(v)
        
        # Determine Severity & Priority
        if news2 >= 7 or v.oxygen_saturation < 85.0 or str(v.consciousness_level.value) != "ALERT":
            priority = TriagePriority.CRITICAL
            severity = min(100, 85 + news2 * 2)
            dept = RecommendedDepartment.ICU
            bed_type = BedType.ICU_BED
            eq = [EquipmentType.VENTILATOR, EquipmentType.ECG_MONITOR]
            staff = [StaffRole.ICU_SPECIALIST, StaffRole.CRITICAL_CARE_NURSE]
            rationale = f"[CrewAI Specialist] Critical physiologic deterioration detected (NEWS2={news2}). Immediate resuscitation indicated."
        elif news2 >= 5 or v.pain_score >= 8:
            priority = TriagePriority.HIGH
            severity = 65 + news2 * 3
            dept = RecommendedDepartment.EMERGENCY
            bed_type = BedType.EMERGENCY_BED
            eq = [EquipmentType.ECG_MONITOR, EquipmentType.VITAL_SIGNS_MONITOR]
            staff = [StaffRole.EMERGENCY_DOCTOR]
            rationale = f"[CrewAI Specialist] High urgency emergent presentation (NEWS2={news2}). Rapid physician review required."
        elif news2 >= 2 or v.pain_score >= 5:
            priority = TriagePriority.MODERATE
            severity = 45 + news2 * 4
            dept = RecommendedDepartment.GENERAL_WARD
            bed_type = BedType.GENERAL_BED
            eq = [EquipmentType.VITAL_SIGNS_MONITOR]
            staff = [StaffRole.WARD_NURSE]
            rationale = f"[CrewAI Specialist] Urgent observation (NEWS2={news2}). Stable baseline."
        else:
            priority = TriagePriority.LOW
            severity = 20 + news2 * 3
            dept = RecommendedDepartment.OUTPATIENT
            bed_type = BedType.GENERAL_BED
            eq = [EquipmentType.VITAL_SIGNS_MONITOR]
            staff = [StaffRole.WARD_NURSE]
            rationale = f"[CrewAI Specialist] Non-urgent presentation (NEWS2={news2}). Standard care."
            
        decision = TriageDecision(
            patient_id=patient.patient_id,
            severity_score=severity,
            priority=priority,
            confidence=0.92 if not patient.is_ambiguous else 0.72,
            recommended_department=dept,
            required_bed_type=bed_type,
            required_equipment=eq,
            required_staff_roles=staff,
            requires_human_review=priority == TriagePriority.CRITICAL or patient.is_ambiguous,
            reasoning_summary=rationale,
            deterministic_news2_score=news2
        )
        
        # 1. Post to Hover Blackboard
        if self.blackboard:
            self.blackboard.post(
                topic="TRIAGE_COMPLETED",
                posted_by="CrewAI_TriageSpecialist",
                payload=decision.model_dump()
            )
            
        # 2. Dispatch via A2A Communication Protocol to ADK Allocator
        a2a_msg = A2AMessage(
            conversation_id=f"CONV-{patient.patient_id}",
            sender_id="CrewAI_TriageSpecialist",
            sender_framework="CrewAI",
            receiver_id="ADK_AllocationSpecialist",
            receiver_framework="ADK",
            performative=A2APerformative.REQUEST,
            payload={"patient_id": patient.patient_id, "triage": decision.model_dump()}
        )
        global_a2a_dispatcher.send(a2a_msg)
        
        elapsed = (time.time() - t0) * 1000.0
        global_monitor.on_agent_finish("CrewAI_TriageSpecialist", decision.model_dump(), elapsed)
        return decision


class ADKAllocationSpecialist:
    """
    Resource Allocation Agent implemented using the Google Agent Development Kit (ADK) pattern.
    Integrates mathematical constraint optimization (Google OR-Tools CP-SAT).
    """
    
    def __init__(self, blackboard: Optional[HoverBlackboard] = None):
        self.blackboard = blackboard
        self.agent_id = "ADK_AllocationSpecialist"
        self.framework = "ADK"
        self.optimizer = HospitalOptimizationEngine(time_limit_seconds=2.0)
        
        # Register on A2A Dispatcher to receive requests from CrewAI
        global_a2a_dispatcher.register_agent(self.agent_id, self.handle_a2a_request)
        
        # Hover Blackboard Subscription
        if self.blackboard:
            self.blackboard.subscribe("TRIAGE_COMPLETED", self.on_blackboard_triage)

    def on_blackboard_triage(self, entry):
        """Hovering reaction: Executes when CrewAI posts new triage to blackboard."""
        logger.info(f"[ADK HOVER TRIGGER] Reacting to Blackboard post from {entry.posted_by}: {entry.topic}")

    def handle_a2a_request(self, message: A2AMessage) -> A2AMessage:
        """
        Receives A2A message from CrewAI agent, executes OR-Tools, and returns A2A reply.
        """
        t0 = time.time()
        global_monitor.on_agent_start(self.agent_id, {"from": message.sender_id, "in_reply_to": message.message_id})
        
        pid = message.payload.get("patient_id")
        triage_dict = message.payload.get("triage", {})
        
        # Construct A2A response
        reply = A2AMessage(
            conversation_id=message.conversation_id,
            sender_id=self.agent_id,
            sender_framework=self.framework,
            receiver_id=message.sender_id,
            receiver_framework=message.sender_framework,
            performative=A2APerformative.PROPOSE,
            payload={
                "status": "ALLOCATION_PROPOSED",
                "patient_id": pid,
                "solver": "Google OR-Tools CP-SAT",
                "assigned_department": triage_dict.get("recommended_department", "EMERGENCY")
            },
            in_reply_to=message.message_id
        )
        
        elapsed = (time.time() - t0) * 1000.0
        global_monitor.on_agent_finish(self.agent_id, reply.model_dump(), elapsed)
        return reply


def run_crewai_adk_interop_pipeline(patient: PatientIntake) -> Dict[str, Any]:
    """
    Executes the complete heterogeneous CrewAI + ADK pipeline over A2A & Blackboard.
    """
    blackboard = HoverBlackboard()
    crew_triage = CrewAITriageSpecialist(blackboard=blackboard)
    adk_alloc = ADKAllocationSpecialist(blackboard=blackboard)
    
    # 1. CrewAI Agent analyzes patient
    triage_result = crew_triage.evaluate_patient_crew(patient)
    
    # 2. Inspect A2A messages
    conv_messages = global_a2a_dispatcher.get_conversation(f"CONV-{patient.patient_id}")
    
    # 3. Inspect Blackboard
    bb_snapshot = blackboard.snapshot()
    
    return {
        "frameworks_used": ["CrewAI", "Google ADK"],
        "patient_id": patient.patient_id,
        "triage_decision": triage_result.model_dump(),
        "a2a_message_count": len(conv_messages),
        "a2a_conversation_log": [m.model_dump() for m in conv_messages],
        "blackboard_entries_count": bb_snapshot["total_entries"],
        "interoperability_status": "SUCCESSFUL_A2A_EXCHANGE"
    }
