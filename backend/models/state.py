"""
State Schema: Real-Time Shared Hospital State and Event Envelopes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .patient import PatientIntake
from .resources import Bed, Staff, Equipment
from .decisions import TriageDecision, ResourceAllocation, DoctorReviewTicket


class WebSocketEventType(str, Enum):
    PATIENT_ARRIVED = "PATIENT_ARRIVED"
    TRIAGE_COMPLETED = "TRIAGE_COMPLETED"
    ALLOCATION_COMPLETED = "ALLOCATION_COMPLETED"
    ESCALATION_TRIGGERED = "ESCALATION_TRIGGERED"
    DOCTOR_OVERRIDE = "DOCTOR_OVERRIDE"
    DOCTOR_APPROVED = "DOCTOR_APPROVED"
    RESOURCE_UPDATED = "RESOURCE_UPDATED"
    PATIENT_DISCHARGED = "PATIENT_DISCHARGED"
    SIMULATION_STEP = "SIMULATION_STEP"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class WebSocketEvent(BaseModel):
    event_id: str
    event_type: WebSocketEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]


class HospitalMetrics(BaseModel):
    total_admitted: int = 0
    total_triaged: int = 0
    total_allocated: int = 0
    total_escalated: int = 0
    total_doctor_overrides: int = 0
    total_discharged: int = 0
    
    # Capacity Gauges
    bed_occupancy_rate: float = 0.0
    icu_occupancy_rate: float = 0.0
    staff_utilization_rate: float = 0.0
    equipment_utilization_rate: float = 0.0
    
    # Performance & Wait Times
    average_wait_time_minutes: float = 0.0
    critical_average_wait_time_minutes: float = 0.0
    average_triage_latency_seconds: float = 0.0
    average_optimization_latency_seconds: float = 0.0


class SharedHospitalState(BaseModel):
    """
    Centralized Single Source of Truth for MedFlow AI operations.
    Thread-safe and JSON-serializable.
    """
    hospital_name: str = "MedFlow General Emergency Center"
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Active Entities (keyed by ID)
    patients: Dict[str, PatientIntake] = Field(default_factory=dict)
    triage_decisions: Dict[str, TriageDecision] = Field(default_factory=dict)
    allocations: Dict[str, ResourceAllocation] = Field(default_factory=dict)
    
    # Physical Resources
    beds: Dict[str, Bed] = Field(default_factory=dict)
    staff: Dict[str, Staff] = Field(default_factory=dict)
    equipment: Dict[str, Equipment] = Field(default_factory=dict)
    
    # Dynamic Queues
    waiting_queue: List[str] = Field(default_factory=list, description="Ordered list of unallocated patient IDs")
    pending_doctor_reviews: Dict[str, DoctorReviewTicket] = Field(default_factory=dict)
    
    # Audit Trail & System Metrics
    event_log: List[WebSocketEvent] = Field(default_factory=list)
    metrics: HospitalMetrics = Field(default_factory=HospitalMetrics)
