"""
End-to-End Integration Tests for Coordinator and Comparative Benchmarking.
"""

import pytest
from backend.agents.coordinator import HospitalCoordinator
from backend.models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender
from backend.models.decisions import DoctorAction, TriagePriority
from backend.evaluation.evaluator import SystemEvaluator


def test_coordinator_intake_to_state_lifecycle():
    coordinator = HospitalCoordinator()
    
    # 1. Intake Patient
    patient = PatientIntake(
        patient_id="P-E2E-01",
        name="Elena Rostova",
        age=28,
        gender=Gender.FEMALE,
        chief_complaint="Superficial finger laceration",
        symptoms=["Minor cut"],
        vitals=VitalSigns(
            heart_rate=72, systolic_bp=118, diastolic_bp=75,
            oxygen_saturation=99.0, respiratory_rate=14,
            temperature_celsius=36.8, consciousness_level=ConsciousnessLevel.ALERT,
            pain_score=2
        )
    )
    
    result = coordinator.intake_patient(patient)
    assert result["patient_id"] == "P-E2E-01"
    assert result["triage"]["priority"] == "LOW"
    assert result["allocation"]["is_allocated"] is True
    
    # Check that hospital bed was marked OCCUPIED
    assigned_bed_id = result["allocation"]["assigned_bed_id"]
    assert assigned_bed_id in coordinator.state.beds
    assert coordinator.state.beds[assigned_bed_id].status.value == "OCCUPIED"
    
    # Discharge patient
    coordinator.discharge_patient("P-E2E-01")
    assert coordinator.state.beds[assigned_bed_id].status.value == "AVAILABLE"


def test_evaluator_medflow_vs_fcfs():
    evaluator = SystemEvaluator()
    benchmark = evaluator.run_benchmark(scenario_key="SCENARIO_1_NORMAL")
    assert "medflow_ai" in benchmark
    assert "fcfs_baseline" in benchmark
    assert benchmark["medflow_ai"]["allocation_rate_pct"] >= 0
    assert benchmark["fcfs_baseline"]["allocation_rate_pct"] >= 0
