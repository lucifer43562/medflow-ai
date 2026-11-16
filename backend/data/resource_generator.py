"""
Resource Generator: Synthesizes realistic hospital assets (Beds, Staff, Equipment).
"""

from typing import List, Dict
from ..models.resources import (
    Bed, BedType, BedStatus,
    Staff, StaffRole, StaffShift,
    Equipment, EquipmentType, EquipmentStatus,
    HospitalResources
)


def generate_default_resources(
    num_icu_beds: int = 4,
    num_emergency_beds: int = 8,
    num_general_beds: int = 12,
    num_isolation_beds: int = 2
) -> HospitalResources:
    """
    Creates a standard emergency department resource inventory.
    """
    beds: List[Bed] = []
    
    # 1. Beds Generation
    for i in range(1, num_icu_beds + 1):
        beds.append(Bed(
            bed_id=f"BED-ICU-{i:02d}",
            bed_type=BedType.ICU_BED,
            ward_name="Intensive Care Unit",
            status=BedStatus.AVAILABLE
        ))
    for i in range(1, num_emergency_beds + 1):
        beds.append(Bed(
            bed_id=f"BED-ER-{i:02d}",
            bed_type=BedType.EMERGENCY_BED,
            ward_name="Emergency Resuscitation Ward",
            status=BedStatus.AVAILABLE
        ))
    for i in range(1, num_general_beds + 1):
        beds.append(Bed(
            bed_id=f"BED-GEN-{i:02d}",
            bed_type=BedType.GENERAL_BED,
            ward_name="General Observation Ward",
            status=BedStatus.AVAILABLE
        ))
    for i in range(1, num_isolation_beds + 1):
        beds.append(Bed(
            bed_id=f"BED-ISO-{i:02d}",
            bed_type=BedType.ISOLATION_BED,
            ward_name="Negative Pressure Isolation",
            status=BedStatus.AVAILABLE
        ))
        
    # 2. Staff Generation
    staff: List[Staff] = [
        Staff(
            staff_id="DOC-ICU-01",
            name="Dr. Sarah Chen, MD",
            role=StaffRole.ICU_SPECIALIST,
            department="Intensive Care",
            shift=StaffShift.DAY,
            max_patient_capacity=2
        ),
        Staff(
            staff_id="DOC-ER-01",
            name="Dr. Marcus Vance, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=3
        ),
        Staff(
            staff_id="DOC-ER-02",
            name="Dr. Priya Patel, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=3
        ),
        Staff(
            staff_id="NURSE-CC-01",
            name="Nurse Liam O'Connor, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=1
        ),
        Staff(
            staff_id="NURSE-CC-02",
            name="Nurse Aisha Bello, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=1
        ),
        Staff(
            staff_id="NURSE-GEN-01",
            name="Nurse David Kim, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=4
        ),
        Staff(
            staff_id="NURSE-GEN-02",
            name="Nurse Elena Rossi, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=4
        ),
        Staff(
            staff_id="RT-01",
            name="Alex Taylor, RRT",
            role=StaffRole.RESPIRATORY_THERAPIST,
            department="Pulmonary & Critical Care",
            shift=StaffShift.DAY,
            max_patient_capacity=3
        ),
        Staff(
            staff_id="TRIAGE-01",
            name="Officer Jordan Reed, RN",
            role=StaffRole.TRIAGE_OFFICER,
            department="Triage Desk",
            shift=StaffShift.DAY,
            max_patient_capacity=10
        )
    ]
    
    # 3. Medical Equipment Generation
    equipment: List[Equipment] = [
        # Ventilators (Scarce Life Support)
        Equipment(
            equipment_id="EQ-VENT-01",
            equipment_type=EquipmentType.VENTILATOR,
            serial_number="VN-90812-A",
            location="ICU Bay 1"
        ),
        Equipment(
            equipment_id="EQ-VENT-02",
            equipment_type=EquipmentType.VENTILATOR,
            serial_number="VN-90812-B",
            location="ICU Bay 2"
        ),
        Equipment(
            equipment_id="EQ-VENT-03",
            equipment_type=EquipmentType.VENTILATOR,
            serial_number="VN-90812-C",
            location="Emergency Bay 1"
        ),
        
        # ECG Monitors
        Equipment(
            equipment_id="EQ-ECG-01",
            equipment_type=EquipmentType.ECG_MONITOR,
            serial_number="ECG-3310-A",
            location="Crash Cart 1"
        ),
        Equipment(
            equipment_id="EQ-ECG-02",
            equipment_type=EquipmentType.ECG_MONITOR,
            serial_number="ECG-3310-B",
            location="Crash Cart 2"
        ),
        Equipment(
            equipment_id="EQ-ECG-03",
            equipment_type=EquipmentType.ECG_MONITOR,
            serial_number="ECG-3310-C",
            location="Emergency Triage"
        ),
        
        # Oxygen Supplies
        Equipment(
            equipment_id="EQ-O2-01",
            equipment_type=EquipmentType.OXYGEN_SUPPLY,
            serial_number="O2-WALL-01",
            location="ER Bay 1"
        ),
        Equipment(
            equipment_id="EQ-O2-02",
            equipment_type=EquipmentType.OXYGEN_SUPPLY,
            serial_number="O2-WALL-02",
            location="ER Bay 2"
        ),
        Equipment(
            equipment_id="EQ-O2-03",
            equipment_type=EquipmentType.OXYGEN_SUPPLY,
            serial_number="O2-WALL-03",
            location="ER Bay 3"
        ),
        Equipment(
            equipment_id="EQ-O2-04",
            equipment_type=EquipmentType.OXYGEN_SUPPLY,
            serial_number="O2-WALL-04",
            location="General Ward 1"
        ),
        
        # Vital Signs Monitors
        Equipment(
            equipment_id="EQ-MON-01",
            equipment_type=EquipmentType.VITAL_SIGNS_MONITOR,
            serial_number="MON-8801",
            location="ER Bay 1"
        ),
        Equipment(
            equipment_id="EQ-MON-02",
            equipment_type=EquipmentType.VITAL_SIGNS_MONITOR,
            serial_number="MON-8802",
            location="ER Bay 2"
        ),
        Equipment(
            equipment_id="EQ-MON-03",
            equipment_type=EquipmentType.VITAL_SIGNS_MONITOR,
            serial_number="MON-8803",
            location="ICU Bay 1"
        ),
        Equipment(
            equipment_id="EQ-MON-04",
            equipment_type=EquipmentType.VITAL_SIGNS_MONITOR,
            serial_number="MON-8804",
            location="ICU Bay 2"
        ),
        
        # Infusion Pumps
        Equipment(
            equipment_id="EQ-PUMP-01",
            equipment_type=EquipmentType.INFUSION_PUMP,
            serial_number="INF-501",
            location="Pharmacy ER Cart"
        ),
        Equipment(
            equipment_id="EQ-PUMP-02",
            equipment_type=EquipmentType.INFUSION_PUMP,
            serial_number="INF-502",
            location="Pharmacy ER Cart"
        ),
        Equipment(
            equipment_id="EQ-PUMP-03",
            equipment_type=EquipmentType.INFUSION_PUMP,
            serial_number="INF-503",
            location="ICU Cart"
        )
    ]
    
    return HospitalResources(beds=beds, staff=staff, equipment=equipment)
