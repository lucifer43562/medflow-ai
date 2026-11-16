"""
Escalation Agent:
Autonomous clinical safety supervisor and Human-In-The-Loop (HITL) gatekeeper.
Inspects confidence bounds, clinical criticalities, resource shortages, and data conflicts.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from ..config import settings
from ..models.patient import PatientIntake
from ..models.decisions import (
    TriageDecision, ResourceAllocation, EscalationDecision,
    EscalationReason, DoctorReviewTicket, DoctorReviewStatus,
    TriagePriority
)

logger = logging.getLogger("medflow.escalation")


class EscalationAgent:
    """
    Evaluates risk and determines whether an automated decision can safely auto-commit
    or must be halted for human doctor intervention.
    """
    
    def __init__(self, confidence_threshold: Optional[float] = None):
        self.confidence_threshold = confidence_threshold or settings.CONFIDENCE_THRESHOLD
        
    def evaluate(
        self,
        patient: PatientIntake,
        triage: TriageDecision,
        allocation: Optional[ResourceAllocation]
    ) -> EscalationDecision:
        """
        Runs comprehensive multi-dimensional safety auditing.
        """
        reasons: List[EscalationReason] = []
        
        # 1. Critical Severity Rule (Critical patients MUST be overseen by human clinician)
        if triage.priority == TriagePriority.CRITICAL or triage.severity_score >= settings.CRITICAL_SEVERITY_THRESHOLD:
            reasons.append(EscalationReason.CRITICAL_SEVERITY_OVERRIDE)
            
        # 2. Epistemic Confidence Check
        if triage.confidence < self.confidence_threshold:
            reasons.append(EscalationReason.CONFIDENCE_BELOW_THRESHOLD)
            
        # 3. Rule vs. LLM Discrepancy Signal
        # If NEWS2 is high (>=7) and original reasoning required safety override
        if triage.deterministic_news2_score >= 7 and "SAFETY OVERRIDE" in triage.reasoning_summary:
            reasons.append(EscalationReason.RULE_LLM_DISCREPANCY)
            
        # 4. Severe Resource Starvation (Critical/High patient cannot obtain a bed)
        if allocation and allocation.is_queued and triage.priority in [TriagePriority.CRITICAL, TriagePriority.HIGH]:
            reasons.append(EscalationReason.RESOURCE_DEFICIT_UNALLOCATED)
            
        # 5. Data Ambiguity / Conflict
        if patient.is_ambiguous:
            reasons.append(EscalationReason.AMBIGUOUS_DATA_OR_CONFLICT)
            
        is_escalated = len(reasons) > 0
        
        if is_escalated:
            if EscalationReason.CRITICAL_SEVERITY_OVERRIDE in reasons or EscalationReason.RESOURCE_DEFICIT_UNALLOCATED in reasons:
                risk_level = "CRITICAL"
                action_required = "Immediate Attending Physician Review & Bed Override Required"
            else:
                risk_level = "ELEVATED"
                action_required = "Secondary Clinical Review of Triage Assessment"
        else:
            risk_level = "LOW"
            action_required = "Autonomous Safe Commitment Authorized"
            
        audit_notes = (
            f"Evaluated {patient.patient_id}: Escalated={is_escalated}. "
            f"Triggers: {[r.value for r in reasons] if reasons else 'None'}. Confidence={triage.confidence}."
        )
        logger.info(audit_notes)
        
        return EscalationDecision(
            patient_id=patient.patient_id,
            is_escalated=is_escalated,
            reasons=reasons,
            risk_level=risk_level,
            action_required=action_required,
            audit_notes=audit_notes,
            evaluated_at=datetime.now(timezone.utc)
        )

    def create_doctor_ticket(
        self,
        patient: PatientIntake,
        triage: TriageDecision,
        allocation: Optional[ResourceAllocation],
        escalation: EscalationDecision
    ) -> DoctorReviewTicket:
        """
        Constructs an actionable pending review item for the human doctor dashboard.
        """
        ticket_id = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        return DoctorReviewTicket(
            ticket_id=ticket_id,
            patient_id=patient.patient_id,
            status=DoctorReviewStatus.PENDING,
            escalation_decision=escalation,
            triage_decision=triage,
            candidate_allocation=allocation
        )
