"""
Patient Data Models: Clinical Vitals, Demographics, and Triage Ingestion Schema.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ConsciousnessLevel(str, Enum):
    ALERT = "ALERT"
    VOICE = "VOICE"
    PAIN = "PAIN"
    UNRESPONSIVE = "UNRESPONSIVE"


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "OTHER"


class VitalSigns(BaseModel):
    """
    Standard physiological telemetry for emergency triage.
    Used for clinical rule verification (NEWS2 score) and LLM reasoning.
    """
    heart_rate: int = Field(..., ge=30, le=240, description="Heart Rate in Beats Per Minute")
    systolic_bp: int = Field(..., ge=40, le=260, description="Systolic Blood Pressure in mmHg")
    diastolic_bp: int = Field(..., ge=20, le=160, description="Diastolic Blood Pressure in mmHg")
    oxygen_saturation: float = Field(..., ge=50.0, le=100.0, description="Pulse Oximetry SpO2 Percentage")
    respiratory_rate: int = Field(..., ge=5, le=60, description="Breaths per minute")
    temperature_celsius: float = Field(..., ge=30.0, le=44.0, description="Body Temperature in Celsius")
    consciousness_level: ConsciousnessLevel = Field(
        default=ConsciousnessLevel.ALERT,
        description="AVPU Scale: Alert, Voice, Pain, Unresponsive"
    )
    pain_score: int = Field(default=0, ge=0, le=10, description="Numeric Pain Scale 0-10")


class PatientIntake(BaseModel):
    """
    Comprehensive incoming patient admission profile.
    """
    patient_id: str = Field(..., description="Unique clinical patient identifier, e.g., P-1001")
    name: str = Field(..., description="Patient anonymized name or token")
    age: int = Field(..., ge=0, le=120)
    gender: Gender
    arrival_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chief_complaint: str = Field(..., description="Primary reason for presentation")
    symptoms: List[str] = Field(default_factory=list, description="Categorized clinical symptoms")
    vitals: VitalSigns
    medical_history: List[str] = Field(default_factory=list, description="Pre-existing conditions / comorbidities")
    is_ambiguous: bool = Field(default=False, description="Flag indicating synthetic noise/ambiguity for stress testing")
