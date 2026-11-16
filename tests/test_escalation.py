"""
Tests for Escalation Agent and Human-In-The-Loop Safety Gating.
"""

import pytest
from backend.agents.escalation_agent import EscalationAgent
from backend.models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender
from backend.models.decisions import (
    TriageDecision, TriagePriority, RecommendedDepartment,
    ResourceAllocation, EscalationReason
)
from backend.models.resources import BedType, StaffRole


def test_escalation_triggers_on_low_confidence():
    agent = EscalationAgent(confidence_threshold=0.85)
    patient = PatientIntake(
        patient_id="P-ESC-1",
        name="Charlie Brown",
        age=60,
        gender=Gender.MALE,
        chief_complaint="Unspecified discomfort",
        symptoms=["Fatigue"],
        vitals=VitalSigns(
            heart_rate=80, systolic_bp=125, diastolic_bp=82,
            oxygen_saturation=97.0, respiratory_rate=16,
            temperature_celsius=37.0, consciousness_level=ConsciousnessLevel.ALERT
        )
    )
    triage = TriageDecision(
        patient_id="P-ESC-1",
        severity_score=45,
        priority=TriagePriority.MODERATE,
        confidence=0.72,  # Below threshold
        recommended_department=RecommendedDepartment.GENERAL_WARD,
        required_bed_type=BedType.GENERAL_BED,
        required_equipment=[],
        required_staff_roles=[StaffRole.WARD_NURSE],
        reasoning_summary="Uncertain presentation",
        deterministic_news2_score=0
    )
    decision = agent.evaluate(patient, triage, allocation=None)
    assert decision.is_escalated is True
    assert EscalationReason.CONFIDENCE_BELOW_THRESHOLD in decision.reasons


def test_escalation_triggers_on_critical_severity():
    agent = EscalationAgent()
    patient = PatientIntake(
        patient_id="P-ESC-2",
        name="Diana Prince",
        age=52,
        gender=Gender.FEMALE,
        chief_complaint="Severe shock",
        symptoms=["Collapse"],
        vitals=VitalSigns(
            heart_rate=140, systolic_bp=70, diastolic_bp=40,
            oxygen_saturation=78.0, respiratory_rate=32,
            temperature_celsius=36.0, consciousness_level=ConsciousnessLevel.PAIN
        )
    )
    triage = TriageDecision(
        patient_id="P-ESC-2",
        severity_score=94,
        priority=TriagePriority.CRITICAL,
        confidence=0.95,
        recommended_department=RecommendedDepartment.ICU,
        required_bed_type=BedType.ICU_BED,
        required_equipment=[],
        required_staff_roles=[],
        reasoning_summary="Critical shock",
        deterministic_news2_score=13
    )
    decision = agent.evaluate(patient, triage, allocation=None)
    assert decision.is_escalated is True
    assert EscalationReason.CRITICAL_SEVERITY_OVERRIDE in decision.reasons
