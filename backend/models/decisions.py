"""
Decision Models: Triage, Allocation, Escalation, and Doctor Review Schemas.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from .resources import BedType, StaffRole, EquipmentType


class TriagePriority(str, Enum):
    CRITICAL = "CRITICAL"      # Immediate resuscitation required (Level 1)
    HIGH = "HIGH"              # Emergent, rapid intervention needed (Level 2)
    MODERATE = "MODERATE"      # Urgent, stable vitals but high risk (Level 3)
    LOW = "LOW"                # Non-urgent, semi-urgent (Level 4/5)


class RecommendedDepartment(str, Enum):
    ICU = "ICU"
    EMERGENCY = "EMERGENCY"
    GENERAL_WARD = "GENERAL_WARD"
    OUTPATIENT = "OUTPATIENT"
    ISOLATION = "ISOLATION"


class TriageDecision(BaseModel):
    """
    Structured outcome of the Triage Agent.
    Strictly constrained for downstream optimization consumption.
    """
    patient_id: str
    severity_score: int = Field(..., ge=0, le=100, description="Calibrated clinical severity [0-100]")
    priority: TriagePriority
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent epistemic confidence score")
    recommended_department: RecommendedDepartment
    required_bed_type: BedType
    required_equipment: List[EquipmentType] = Field(default_factory=list)
    required_staff_roles: List[StaffRole] = Field(default_factory=list)
    requires_human_review: bool = False
    reasoning_summary: str = Field(..., description="Explainable clinical justification")
    deterministic_news2_score: int = Field(default=0, description="Calculated National Early Warning Score")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResourceAllocation(BaseModel):
    """
    Outcome from the Google OR-Tools constraint optimization model.
    """
    patient_id: str
    assigned_bed_id: Optional[str] = None
    assigned_bed_type: Optional[BedType] = None
    assigned_staff_ids: List[str] = Field(default_factory=list)
    assigned_equipment_ids: List[str] = Field(default_factory=list)
    is_allocated: bool = False
    is_queued: bool = True
    queue_position: Optional[int] = None
    optimization_score: float = Field(default=0.0)
    solver_status: str = "OPTIMAL"
    allocation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


class EscalationReason(str, Enum):
    CONFIDENCE_BELOW_THRESHOLD = "CONFIDENCE_BELOW_THRESHOLD"
    CRITICAL_SEVERITY_OVERRIDE = "CRITICAL_SEVERITY_OVERRIDE"
    RULE_LLM_DISCREPANCY = "RULE_LLM_DISCREPANCY"
    RESOURCE_DEFICIT_UNALLOCATED = "RESOURCE_DEFICIT_UNALLOCATED"
    AMBIGUOUS_DATA_OR_CONFLICT = "AMBIGUOUS_DATA_OR_CONFLICT"
    EQUIPMENT_MISMATCH = "EQUIPMENT_MISMATCH"


class EscalationDecision(BaseModel):
    """
    Safety verification outcome evaluating whether case can proceed autonomously or requires human doctor sign-off.
    """
    patient_id: str
    is_escalated: bool
    reasons: List[EscalationReason] = Field(default_factory=list)
    risk_level: str = "LOW"
    action_required: str
    audit_notes: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DoctorReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


class DoctorAction(str, Enum):
    APPROVE = "APPROVE"
    OVERRIDE_PRIORITY = "OVERRIDE_PRIORITY"
    REASSIGN_RESOURCES = "REASSIGN_RESOURCES"
    DISCHARGE = "DISCHARGE"


class DoctorReviewTicket(BaseModel):
    ticket_id: str
    patient_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: DoctorReviewStatus = DoctorReviewStatus.PENDING
    escalation_decision: EscalationDecision
    triage_decision: TriageDecision
    candidate_allocation: Optional[ResourceAllocation] = None
    
    # Human Review Fields
    reviewer_doctor_id: Optional[str] = None
    action_taken: Optional[DoctorAction] = None
    override_priority: Optional[TriagePriority] = None
    override_bed_id: Optional[str] = None
    override_staff_id: Optional[str] = None
    override_equipment_ids: List[str] = Field(default_factory=list)
    doctor_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
