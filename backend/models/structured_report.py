"""
Structured Output using Pydantic (Standardization Requirement 3):
Ensures all agentic system outputs are deterministically validated via Pydantic
and can be rendered in structured JSON, Markdown, and Tabular formats.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .patient import PatientIntake
from .decisions import TriageDecision, ResourceAllocation, EscalationDecision


class StructuredClinicalReport(BaseModel):
    """
    Unified Structured Output Model representing the finalized clinical synthesis
    of patient triage, constraint-optimized resource allocation, and escalation decisions.
    """
    report_id: str = Field(..., description="Unique clinical report identifier")
    patient_id: str
    patient_name: str
    age: int
    chief_complaint: str
    vitals_summary: Dict[str, Any]
    
    # Triage decision fields
    triage_priority: str
    severity_score: int
    epistemic_confidence: float
    recommended_department: str
    news2_score: int
    reasoning_summary: str
    
    # Allocation fields
    assigned_bed_id: Optional[str] = None
    assigned_bed_type: Optional[str] = None
    assigned_staff_ids: List[str] = Field(default_factory=list)
    assigned_equipment_ids: List[str] = Field(default_factory=list)
    allocation_status: str
    queue_position: Optional[int] = None
    
    # Escalation fields
    requires_human_review: bool
    escalation_reasons: List[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_workflow(
        cls,
        patient: PatientIntake,
        triage: TriageDecision,
        allocation: Optional[ResourceAllocation] = None,
        escalation: Optional[EscalationDecision] = None
    ) -> "StructuredClinicalReport":
        """Constructs a validated StructuredClinicalReport from pipeline intermediate objects."""
        vitals_dict = {
            "heart_rate": patient.vitals.heart_rate,
            "blood_pressure": f"{patient.vitals.systolic_bp}/{patient.vitals.diastolic_bp}",
            "oxygen_saturation": f"{patient.vitals.oxygen_saturation}%",
            "respiratory_rate": patient.vitals.respiratory_rate,
            "temperature_celsius": f"{patient.vitals.temperature_celsius} °C",
            "consciousness": patient.vitals.consciousness_level.value
        }
        
        alloc_status = "UNALLOCATED"
        bed_id, bed_type = None, None
        staff_ids, equip_ids = [], []
        queue_pos = None
        
        if allocation:
            if allocation.is_allocated:
                alloc_status = "ALLOCATED"
                bed_id = allocation.assigned_bed_id
                bed_type = allocation.assigned_bed_type.value if allocation.assigned_bed_type else None
                staff_ids = allocation.assigned_staff_ids
                equip_ids = allocation.assigned_equipment_ids
            elif allocation.is_queued:
                alloc_status = f"QUEUED (Position #{allocation.queue_position})"
                queue_pos = allocation.queue_position

        req_review = triage.requires_human_review
        reasons = []
        if escalation:
            req_review = escalation.is_escalated
            reasons = [r.value for r in escalation.reasons]

        return cls(
            report_id=f"RPT-{patient.patient_id}-{int(datetime.now(timezone.utc).timestamp())}",
            patient_id=patient.patient_id,
            patient_name=patient.name,
            age=patient.age,
            chief_complaint=patient.chief_complaint,
            vitals_summary=vitals_dict,
            triage_priority=triage.priority.value,
            severity_score=triage.severity_score,
            epistemic_confidence=triage.confidence,
            recommended_department=triage.recommended_department.value,
            news2_score=triage.deterministic_news2_score,
            reasoning_summary=triage.reasoning_summary,
            assigned_bed_id=bed_id,
            assigned_bed_type=bed_type,
            assigned_staff_ids=staff_ids,
            assigned_equipment_ids=equip_ids,
            allocation_status=alloc_status,
            queue_position=queue_pos,
            requires_human_review=req_review,
            escalation_reasons=reasons
        )

    def to_structured_markdown(self) -> str:
        """Renders the structured Pydantic report into formatted GitHub-flavored Markdown."""
        alert_type = "CAUTION" if self.triage_priority == "CRITICAL" else ("WARNING" if self.triage_priority == "HIGH" else "NOTE")
        esc_badge = "🔴 YES (Physician Sign-Off Required)" if self.requires_human_review else "🟢 NO (Autonomous Path Validated)"
        
        staff_str = ", ".join(self.assigned_staff_ids) if self.assigned_staff_ids else "None"
        equip_str = ", ".join(self.assigned_equipment_ids) if self.assigned_equipment_ids else "None"
        
        return f"""### 📋 Clinical Summary Report: `{self.patient_name}` ({self.patient_id})
> [!{alert_type}]
> **Priority**: `{self.triage_priority}` | **Severity Score**: `{self.severity_score}/100` | **NEWS2**: `{self.news2_score}`
> **Escalation Gate**: {esc_badge}

#### 1. Patient Demographics & Presenting Vitals
- **Age**: {self.age} years | **Chief Complaint**: *"{self.chief_complaint}"*
- **Vitals**: HR `{self.vitals_summary.get('heart_rate')} bpm` | BP `{self.vitals_summary.get('blood_pressure')}` | SpO2 `{self.vitals_summary.get('oxygen_saturation')}` | RR `{self.vitals_summary.get('respiratory_rate')}` | Temp `{self.vitals_summary.get('temperature_celsius')}` | Consciousness `{self.vitals_summary.get('consciousness')}`

#### 2. Agentic Clinical Decision & Justification
- **Department**: `{self.recommended_department}`
- **Epistemic Confidence**: `{self.epistemic_confidence * 100:.1f}%`
- **Clinical Rationale**: {self.reasoning_summary}

#### 3. Resource Allocation (Google OR-Tools)
- **Status**: `{self.allocation_status}`
- **Assigned Bed**: `{self.assigned_bed_id or 'Pending'}` ({self.assigned_bed_type or 'None'})
- **Assigned Medical Staff**: `{staff_str}`
- **Assigned Equipment**: `{equip_str}`
"""

    def to_structured_table_row(self) -> Dict[str, Any]:
        """Renders a flat tabular dictionary representation suitable for dataframes and tables."""
        return {
            "Patient ID": self.patient_id,
            "Name": self.patient_name,
            "Age": self.age,
            "Priority": self.triage_priority,
            "Severity": self.severity_score,
            "NEWS2": self.news2_score,
            "Confidence": f"{self.epistemic_confidence*100:.1f}%",
            "Department": self.recommended_department,
            "Allocation Status": self.allocation_status,
            "Assigned Bed": self.assigned_bed_id or "Unassigned",
            "Doctor Review": "REQUIRED" if self.requires_human_review else "AUTONOMOUS",
            "Generated At": self.generated_at.strftime("%H:%M:%S")
        }
