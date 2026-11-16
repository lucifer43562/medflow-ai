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
    num_icu_beds: int = 10,
    num_emergency_beds: int = 14,
    num_general_beds: int = 16,
    num_isolation_beds: int = 4
) -> HospitalResources:
    """
    Creates a high-capacity emergency department resource inventory to prevent artificial staffing bottlenecks.
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
            max_patient_capacity=6
        ),
        Staff(
            staff_id="DOC-ICU-02",
            name="Dr. Robert Thorne, MD",
            role=StaffRole.ICU_SPECIALIST,
            department="Intensive Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
        ),
        Staff(
            staff_id="DOC-ICU-03",
            name="Dr. Ananya Roy, MD",
            role=StaffRole.ICU_SPECIALIST,
            department="Intensive Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
        ),
        Staff(
            staff_id="DOC-ICU-04",
            name="Dr. Lucas Meyer, MD",
            role=StaffRole.ICU_SPECIALIST,
            department="Intensive Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
        ),
        Staff(
            staff_id="DOC-ICU-05",
            name="Dr. Fatima Zahra, MD",
            role=StaffRole.ICU_SPECIALIST,
            department="Intensive Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
        ),
        Staff(
            staff_id="DOC-ER-01",
            name="Dr. Marcus Vance, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="DOC-ER-02",
            name="Dr. Priya Patel, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="DOC-ER-03",
            name="Dr. Carlos Santos, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="DOC-ER-04",
            name="Dr. Jennifer Wu, MD",
            role=StaffRole.EMERGENCY_DOCTOR,
            department="Emergency",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="NURSE-CC-01",
            name="Nurse Liam O'Connor, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-02",
            name="Nurse Aisha Bello, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-03",
            name="Nurse Sarah Jenkins, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-04",
            name="Nurse Carlos Mendez, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-05",
            name="Nurse Emily Watson, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-06",
            name="Nurse Zachary Scott, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-07",
            name="Nurse Maya Lin, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-CC-08",
            name="Nurse Tariq Mansoor, BSN",
            role=StaffRole.CRITICAL_CARE_NURSE,
            department="ICU / Resus",
            shift=StaffShift.DAY,
            max_patient_capacity=5
        ),
        Staff(
            staff_id="NURSE-GEN-01",
            name="Nurse David Kim, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="NURSE-GEN-02",
            name="Nurse Elena Rossi, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="NURSE-GEN-03",
            name="Nurse Jamal Washington, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="NURSE-GEN-04",
            name="Nurse Chloe Bennett, RN",
            role=StaffRole.WARD_NURSE,
            department="General Ward",
            shift=StaffShift.DAY,
            max_patient_capacity=8
        ),
        Staff(
            staff_id="RT-01",
            name="Alex Taylor, RRT",
            role=StaffRole.RESPIRATORY_THERAPIST,
            department="Pulmonary & Critical Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
        ),
        Staff(
            staff_id="RT-02",
            name="Jessica Miller, RRT",
            role=StaffRole.RESPIRATORY_THERAPIST,
            department="Pulmonary & Critical Care",
            shift=StaffShift.DAY,
            max_patient_capacity=6
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
    
    # 3. Medical Equipment Generation (Scales with bed counts)
    equipment: List[Equipment] = []
    
    # Ventilators (Scales dynamically with ICU capacity: at least num_icu_beds + 6 units)
    num_vents = max(16, num_icu_beds + 6)
    for i in range(1, num_vents + 1):
        equipment.append(Equipment(
            equipment_id=f"EQ-VENT-{i:02d}",
            equipment_type=EquipmentType.VENTILATOR,
            serial_number=f"VN-90812-{i:02d}",
            location=f"ICU/Surge Bay {((i-1)%num_icu_beds)+1}"
        ))
        
    # ECG Monitors (Scales across wards)
    num_ecg = max(16, num_icu_beds + num_emergency_beds)
    for i in range(1, num_ecg + 1):
        equipment.append(Equipment(
            equipment_id=f"EQ-ECG-{i:02d}",
            equipment_type=EquipmentType.ECG_MONITOR,
            serial_number=f"ECG-3310-{i:02d}",
            location=f"Bay {i}"
        ))
        
    # Oxygen Supplies (Scales across beds)
    num_o2 = max(20, num_icu_beds + num_emergency_beds + num_general_beds)
    for i in range(1, num_o2 + 1):
        equipment.append(Equipment(
            equipment_id=f"EQ-O2-{i:02d}",
            equipment_type=EquipmentType.OXYGEN_SUPPLY,
            serial_number=f"O2-WALL-{i:02d}",
            location=f"Wall Station {i}"
        ))
        
    # Vital Signs Monitors
    num_mon = max(24, num_icu_beds + num_emergency_beds + num_general_beds)
    for i in range(1, num_mon + 1):
        equipment.append(Equipment(
            equipment_id=f"EQ-MON-{i:02d}",
            equipment_type=EquipmentType.VITAL_SIGNS_MONITOR,
            serial_number=f"MON-88{i:02d}",
            location=f"Bedside Monitor {i}"
        ))
        
    # Infusion Pumps
    num_pump = max(16, num_icu_beds + num_emergency_beds)
    for i in range(1, num_pump + 1):
        equipment.append(Equipment(
            equipment_id=f"EQ-PUMP-{i:02d}",
            equipment_type=EquipmentType.INFUSION_PUMP,
            serial_number=f"INF-{i:03d}",
            location=f"Pump Cart {i}"
        ))
    
    return HospitalResources(beds=beds, staff=staff, equipment=equipment)
