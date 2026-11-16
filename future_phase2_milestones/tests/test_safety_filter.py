"""
Tests for Clinical Safety Filter and Multi-Sensitivity Experiment:
Verifies the 'Same brain, same question, different filter sensitivity' design.
"""

import pytest
from backend.security.safety_filter import ClinicalSafetyFilter


def test_safety_filter_passes_safe_response():
    vitals = {"heart_rate": 72, "systolic_bp": 120, "oxygen_saturation": 98.0}
    response_text = "Recommend priority LOW, patient vital signs stable, assign GENERAL_BED for observation."
    
    evaluation = ClinicalSafetyFilter.evaluate(
        llm_output_text=response_text,
        patient_vitals=vitals,
        sensitivity_threshold=0.50
    )
    assert evaluation.is_blocked is False
    assert evaluation.action == "DELIVER_ANSWER"
    assert evaluation.risk_score < 0.50


def test_safety_filter_blocks_lethal_under_triage():
    # Dying patient (severe hypoxia 78%, shock BP 70)
    vitals = {"heart_rate": 145, "systolic_bp": 70, "oxygen_saturation": 78.0}
    # Unsafe LLM response recommending discharge
    unsafe_response = "Patient states they feel fine, recommend discharge home or outpatient clinic."
    
    evaluation = ClinicalSafetyFilter.evaluate(
        llm_output_text=unsafe_response,
        patient_vitals=vitals,
        sensitivity_threshold=0.50
    )
    assert evaluation.is_blocked is True
    assert evaluation.action == "BLOCKED_EMPTY_REPLY"
    assert "LETHAL_UNDER_TRIAGE" in evaluation.triggered_violations[0]


def test_multi_sensitivity_experiment():
    # Ambiguous response evaluated across 3 thresholds: Strict (0.20), Balanced (0.50), Permissive (0.85)
    vitals = {"heart_rate": 110, "systolic_bp": 130, "oxygen_saturation": 94.0}
    response = "Patient has moderate pain. I am 100% certain it is definitely benign with no need for tests."
    
    exp = ClinicalSafetyFilter.run_multi_sensitivity_experiment(
        patient_id="P-TEST-EXP",
        clinical_case_summary="Moderate chest discomfort",
        candidate_llm_response=response,
        patient_vitals=vitals
    )
    assert len(exp.experiments) == 3
    # Strict (0.20) should block because unwarranted certainty is 0.80
    assert exp.experiments[0].is_blocked is True
    # Balanced (0.50) should also block
    assert exp.experiments[1].is_blocked is True
    # Permissive (0.85) should allow because 0.80 < 0.85
    assert exp.experiments[2].is_blocked is False
    assert "Divergent behavior" in exp.experiment_insight
