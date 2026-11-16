"""
Tests for Google OR-Tools CP-SAT Resource Optimization Allocator.
"""

import pytest
from datetime import datetime
from backend.optimization.ortools_allocator import HospitalOptimizationEngine
from backend.data.resource_generator import generate_default_resources
from backend.models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender
from backend.models.decisions import TriageDecision, TriagePriority, RecommendedDepartment
from backend.models.resources import BedType, StaffRole, EquipmentType, BedStatus


def test_ortools_single_patient_allocation():
    engine = HospitalOptimizationEngine(time_limit_seconds=1.0)
    resources = generate_default_resources()
    
    patient = PatientIntake(
        patient_id="P-OPT-1",
        name="Alice Smith",
        age=45,
        gender=Gender.FEMALE,
        chief_complaint="Severe dyspnea and cyanosis",
        symptoms=["Cyanosis"],
        vitals=VitalSigns(
            heart_rate=135,
            systolic_bp=85,
            diastolic_bp=55,
            oxygen_saturation=75.0,
            respiratory_rate=36,
            temperature_celsius=37.0,
            consciousness_level=ConsciousnessLevel.VOICE
        )
    )
    
    triage = TriageDecision(
        patient_id="P-OPT-1",
        severity_score=92,
        priority=TriagePriority.CRITICAL,
        confidence=0.95,
        recommended_department=RecommendedDepartment.ICU,
        required_bed_type=BedType.ICU_BED,
        required_equipment=[EquipmentType.VENTILATOR],
        required_staff_roles=[StaffRole.ICU_SPECIALIST],
        reasoning_summary="Critical respiratory failure.",
        deterministic_news2_score=12
    )
    
    allocations, metrics = engine.solve(
        patients=[patient],
        triage_decisions={"P-OPT-1": triage},
        available_beds=resources.beds,
        available_staff=resources.staff,
        available_equipment=resources.equipment
    )
    
    assert len(allocations) == 1
    alloc = allocations[0]
    assert alloc.is_allocated is True
    assert alloc.assigned_bed_type == BedType.ICU_BED
    assert len(alloc.assigned_equipment_ids) >= 1
    assert "EQ-VENT" in alloc.assigned_equipment_ids[0]


def test_ortools_resource_exhaustion_behavior():
    """When zero beds are available, engine should place patients in queue safely without crash."""
    engine = HospitalOptimizationEngine(time_limit_seconds=1.0)
    resources = generate_default_resources()
    
    # Mark all beds as occupied
    for b in resources.beds:
        b.status = BedStatus.OCCUPIED
        
    patient = PatientIntake(
        patient_id="P-OPT-2",
        name="Bob Jones",
        age=30,
        gender=Gender.MALE,
        chief_complaint="Laceration",
        symptoms=["Cut on leg"],
        vitals=VitalSigns(
            heart_rate=75,
            systolic_bp=120,
            diastolic_bp=80,
            oxygen_saturation=99.0,
            respiratory_rate=14,
            temperature_celsius=36.7,
            consciousness_level=ConsciousnessLevel.ALERT
        )
    )
    triage = TriageDecision(
        patient_id="P-OPT-2",
        severity_score=25,
        priority=TriagePriority.LOW,
        confidence=0.96,
        recommended_department=RecommendedDepartment.OUTPATIENT,
        required_bed_type=BedType.GENERAL_BED,
        required_equipment=[],
        required_staff_roles=[StaffRole.WARD_NURSE],
        reasoning_summary="Stable cut",
        deterministic_news2_score=0
    )
    
    allocations, metrics = engine.solve(
        patients=[patient],
        triage_decisions={"P-OPT-2": triage},
        available_beds=resources.beds,
        available_staff=resources.staff,
        available_equipment=resources.equipment
    )
    
    assert len(allocations) == 1
    assert allocations[0].is_allocated is False
    assert allocations[0].is_queued is True
