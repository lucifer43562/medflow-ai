"""
Tests for Triage Agent and NEWS2 Calculation.
"""

import pytest
from backend.models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender
from backend.agents.triage_agent import calculate_news2, TriageAgent
from backend.models.decisions import TriagePriority


def test_news2_normal_vitals():
    """Completely normal physiology should yield NEWS2 = 0."""
    vitals = VitalSigns(
        heart_rate=72,
        systolic_bp=120,
        diastolic_bp=80,
        oxygen_saturation=98.0,
        respiratory_rate=14,
        temperature_celsius=36.8,
        consciousness_level=ConsciousnessLevel.ALERT,
        pain_score=0
    )
    score = calculate_news2(vitals)
    assert score == 0


def test_news2_critical_vitals():
    """Severe hypoxia, hypotension, tachycardia, and altered consciousness must yield high NEWS2 (>=7)."""
    vitals = VitalSigns(
        heart_rate=145,         # +3
        systolic_bp=75,         # +3
        diastolic_bp=45,
        oxygen_saturation=80.0, # +3
        respiratory_rate=36,    # +3
        temperature_celsius=39.5, # +2
        consciousness_level=ConsciousnessLevel.UNRESPONSIVE, # +3
        pain_score=0
    )
    score = calculate_news2(vitals)
    assert score >= 14
    assert score >= 7  # Level 1 emergency threshold


def test_triage_under_triage_safety_ceiling():
    """
    Under-triage prevention: If vital signs indicate physiological collapse (NEWS2 >= 7),
    the agent must override any lenient assessment to CRITICAL.
    """
    agent = TriageAgent()
    patient = PatientIntake(
        patient_id="TEST-001",
        name="John Doe",
        age=55,
        gender=Gender.MALE,
        chief_complaint="Felt a little dizzy after watching TV",
        symptoms=["Mild dizziness"],
        vitals=VitalSigns(
            heart_rate=142,
            systolic_bp=68,
            diastolic_bp=40,
            oxygen_saturation=79.0,
            respiratory_rate=38,
            temperature_celsius=36.5,
            consciousness_level=ConsciousnessLevel.VOICE,
            pain_score=1
        ),
        is_ambiguous=True
    )
    decision = agent.evaluate(patient)
    assert decision.priority == TriagePriority.CRITICAL
    assert decision.severity_score >= 85
    assert decision.requires_human_review is True
