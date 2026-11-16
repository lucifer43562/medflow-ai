"""
Hospital Resource Models: Beds, Staff, and Medical Equipment entities.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class BedType(str, Enum):
    ICU_BED = "ICU_BED"
    EMERGENCY_BED = "EMERGENCY_BED"
    GENERAL_BED = "GENERAL_BED"
    ISOLATION_BED = "ISOLATION_BED"


class BedStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    RESERVED = "RESERVED"


class StaffRole(str, Enum):
    ICU_SPECIALIST = "ICU_SPECIALIST"
    EMERGENCY_DOCTOR = "EMERGENCY_DOCTOR"
    CRITICAL_CARE_NURSE = "CRITICAL_CARE_NURSE"
    WARD_NURSE = "WARD_NURSE"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST"
    TRIAGE_OFFICER = "TRIAGE_OFFICER"


class StaffShift(str, Enum):
    DAY = "DAY"
    EVENING = "EVENING"
    NIGHT = "NIGHT"


class EquipmentType(str, Enum):
    VENTILATOR = "VENTILATOR"
    ECG_MONITOR = "ECG_MONITOR"
    OXYGEN_SUPPLY = "OXYGEN_SUPPLY"
    VITAL_SIGNS_MONITOR = "VITAL_SIGNS_MONITOR"
    INFUSION_PUMP = "INFUSION_PUMP"
    DEFIBRILLATOR = "DEFIBRILLATOR"


class EquipmentStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"


class Bed(BaseModel):
    bed_id: str
    bed_type: BedType
    ward_name: str
    status: BedStatus = BedStatus.AVAILABLE
    current_patient_id: Optional[str] = None


class Staff(BaseModel):
    staff_id: str
    name: str
    role: StaffRole
    department: str
    shift: StaffShift
    is_on_duty: bool = True
    assigned_patient_ids: List[str] = Field(default_factory=list)
    max_patient_capacity: int = Field(default=2, ge=1)


class Equipment(BaseModel):
    equipment_id: str
    equipment_type: EquipmentType
    serial_number: str
    status: EquipmentStatus = EquipmentStatus.AVAILABLE
    current_patient_id: Optional[str] = None
    location: str


class HospitalResources(BaseModel):
    beds: List[Bed] = Field(default_factory=list)
    staff: List[Staff] = Field(default_factory=list)
    equipment: List[Equipment] = Field(default_factory=list)
