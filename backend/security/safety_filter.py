"""
Safety Filter & Sensitivity Experiment Subsystem:
Implements the 'Same Brain, Same Question, Different Filter Sensitivity' architecture.
Evaluates LLM clinical output against configurable safety risk thresholds:
- STRICT (Low Threshold: e.g. 0.25) -> High safety, blocks minor ambiguity.
- BALANCED (Medium Threshold: e.g. 0.50) -> Recommended clinical operational baseline.
- PERMISSIVE (High Threshold: e.g. 0.80) -> Only halts catastrophic harm / lethal contraindications.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class SafetySensitivity(str, Enum):
    STRICT = "STRICT"
    BALANCED = "BALANCED"
    PERMISSIVE = "PERMISSIVE"


class SafetyFilterEvaluation(BaseModel):
    is_blocked: bool
    risk_score: float = Field(..., ge=0.0, le=1.0)
    sensitivity_threshold: float
    filter_tier: str  # "STRICT", "BALANCED", "PERMISSIVE"
    triggered_violations: List[str] = []
    clinical_risk_factors: Dict[str, float] = Field(default_factory=dict)
    action: str  # "DELIVER_ANSWER" or "BLOCKED_EMPTY_REPLY"
    explanation: str


class MultiSensitivityExperimentResult(BaseModel):
    patient_id: str
    clinical_case_summary: str
    raw_llm_response: str
    experiments: List[SafetyFilterEvaluation]
    experiment_insight: str


class ClinicalSafetyFilter:
    """
    Evaluates generated clinical answers/recommendations before state commitment.
    Applies multi-dimensional risk scoring:
    1. Clinical Deterioration Risk (NEWS2 mismatch or under-triage)
    2. Overconfidence under Diagnostic Ambiguity
    3. Dangerous Drug / Procedural Contraindications
    4. Toxic or Adversarial Guidance
    """

    def __init__(self, sensitivity: SafetySensitivity = SafetySensitivity.BALANCED):
        self.sensitivity = sensitivity
        self.threshold = (
            0.20 if sensitivity == SafetySensitivity.STRICT
            else (0.85 if sensitivity == SafetySensitivity.PERMISSIVE else 0.50)
        )

    def evaluate_risk(self, prompt: str) -> Tuple[str, float, List[str]]:
        text_lower = prompt.lower()
        violations = []
        score = 0.05
        
        # Check adversarial prompt injection patterns
        injection_triggers = [
            "ignore previous", "ignore all", "bypass", "pretend you are",
            "developer mode", "system prompt", "override", "force allocate", "dan mode"
        ]
        matched_triggers = [t for t in injection_triggers if t in text_lower]
        if matched_triggers:
            score = 0.95
            violations.append(f"INJECTION_ATTACK_DETECTED: Matched trigger '{matched_triggers[0]}'")
            
        if any(w in text_lower for w in ["kill", "murder", "bomb", "attack the doctor"]):
            score = max(score, 0.99)
            violations.append("TOXIC_CONTENT: Threat detected in clinical input.")
            
        verdict = "BLOCK" if score >= self.threshold else "PASS"
        return verdict, score, violations

    @classmethod
    def evaluate(
        cls,
        llm_output_text: str,
        patient_vitals: Dict[str, Any],
        sensitivity_threshold: float = 0.50,
        filter_tier: str = "BALANCED"
    ) -> SafetyFilterEvaluation:
        text_lower = llm_output_text.lower()
        violations = []
        risk_components = {}
        
        # 1. Check for Under-Triage Risk with Collapsing Vitals
        spo2 = patient_vitals.get("oxygen_saturation", 98.0)
        sbp = patient_vitals.get("systolic_bp", 120)
        hr = patient_vitals.get("heart_rate", 75)
        
        vitals_critical = spo2 < 85.0 or sbp < 80 or hr > 140
        recommends_discharge = any(w in text_lower for w in ["discharge", "home", "outpatient", "low priority", "minor"])
        
        if vitals_critical and recommends_discharge:
            risk_components["lethal_under_triage"] = 0.95
            violations.append("LETHAL_UNDER_TRIAGE: Recommends non-urgent/discharge despite critical vital signs collapse.")
        else:
            risk_components["lethal_under_triage"] = 0.05
            
        # 2. Check for Overconfidence / Missing Workup
        claims_certainty = any(w in text_lower for w in ["100% certain", "definitely benign", "no need for tests", "ignore vitals"])
        if claims_certainty:
            risk_components["unwarranted_certainty"] = 0.80
            violations.append("UNWARRANTED_CERTAINTY: LLM asserts diagnostic certainty without diagnostic labs.")
        else:
            risk_components["unwarranted_certainty"] = 0.10
            
        # 3. Check for Dangerous Medical Advice
        dangerous_advice = any(w in text_lower for w in ["do not call doctor", "delay treatment", "no oxygen needed", "sedate without airway"])
        if dangerous_advice:
            risk_components["dangerous_contraindication"] = 0.90
            violations.append("CONTRAINDICATION_RISK: Recommends clinically dangerous action.")
        else:
            risk_components["dangerous_contraindication"] = 0.05
            
        # 4. Prompt Injection & Malicious Pattern
        if any(w in text_lower for w in ["bypass safety", "dan mode", "unregulated"]):
            risk_components["jailbreak_leakage"] = 0.99
            violations.append("JAILBREAK_LEAKAGE: LLM output reveals safety bypass attempt.")
        else:
            risk_components["jailbreak_leakage"] = 0.0
            
        # Calculate aggregate risk score (max of components)
        composite_risk = max(risk_components.values())
        is_blocked = composite_risk >= sensitivity_threshold
        
        action = "BLOCKED_EMPTY_REPLY" if is_blocked else "DELIVER_ANSWER"
        explanation = (
            f"Risk score {composite_risk:.2f} exceeded threshold {sensitivity_threshold:.2f}. Output BLOCKED."
            if is_blocked else
            f"Risk score {composite_risk:.2f} below threshold {sensitivity_threshold:.2f}. Output ALLOWED."
        )
        
        return SafetyFilterEvaluation(
            is_blocked=is_blocked,
            risk_score=round(composite_risk, 2),
            sensitivity_threshold=sensitivity_threshold,
            filter_tier=filter_tier,
            triggered_violations=violations,
            clinical_risk_factors=risk_components,
            action=action,
            explanation=explanation
        )

    @classmethod
    def run_multi_sensitivity_experiment(
        cls,
        patient_id: str,
        clinical_case_summary: str,
        candidate_llm_response: str,
        patient_vitals: Dict[str, Any]
    ) -> MultiSensitivityExperimentResult:
        """
        Executes the exact experiment from the architectural slide:
        'Three professors share the same model and the same instruction.
         Only the filter threshold changes, so any difference in their replies is caused by the threshold.'
        """
        thresholds = [
            {"tier": "STRICT", "threshold": 0.20, "desc": "High Safety: Flags minor ambiguities and demands human oversight."},
            {"tier": "BALANCED", "threshold": 0.50, "desc": "Standard: Allows confident safe triage, blocks clear clinical risks."},
            {"tier": "PERMISSIVE", "threshold": 0.85, "desc": "Permissive: Only blocks overt lethal contraindications or attacks."}
        ]
        
        results = []
        for t in thresholds:
            ev = cls.evaluate(
                llm_output_text=candidate_llm_response,
                patient_vitals=patient_vitals,
                sensitivity_threshold=t["threshold"],
                filter_tier=t["tier"]
            )
            results.append(ev)
            
        # Synthesis
        blocked_count = sum(1 for r in results if r.is_blocked)
        if blocked_count == 0:
            insight = "All 3 sensitivity thresholds allowed the answer. Case is clinically unambiguous and safe."
        elif blocked_count == len(results):
            insight = "All 3 sensitivity thresholds BLOCKED the answer. Case presents severe clinical risk requiring mandatory human physician takeover."
        else:
            insight = "Divergent behavior observed: Strict threshold intercepted the case while Permissive threshold allowed it, confirming that variance is solely induced by filter sensitivity."
            
        return MultiSensitivityExperimentResult(
            patient_id=patient_id,
            clinical_case_summary=clinical_case_summary,
            raw_llm_response=candidate_llm_response,
            experiments=results,
            experiment_insight=insight
        )
