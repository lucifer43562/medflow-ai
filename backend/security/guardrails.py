"""
Security & Guardrails Subsystem:
1. Input Sanitization & Prompt Injection Defense (Jailbreak / System Prompt Leakage prevention).
2. Toxicity & Malicious Content Filter.
3. Tool Return Type & Bounds Validation Guardrail.
4. Prompt Variance Engine (ReAct vs Few-Shot vs Persona Variance).
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("medflow.guardrails")


class GuardrailVerdict(BaseModel):
    is_safe: bool
    risk_score: float
    violations: list[str] = []
    sanitized_input: str


class SecurityGuardrailEngine:
    """
    Multi-layer Clinical & LLM Security Firewall.
    Protects MedFlow AI agents from adversarial inputs, prompt injection, and schema corruption.
    """
    
    # Prompt Injection / Jailbreak Attack Patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"bypass\s+(safety|clinical|triage)\s+rules",
        r"pretend\s+(you\s+are|to\s+be)\s+an\s+unregulated",
        r"system\s*prompt\s*override",
        r"developer\s+mode",
        r"you\s+are\s+now\s+dan",
        r"elevate\s+everyone\s+to\s+critical",
        r"<script.*?>",
        r"exec\(.*?\)",
        r"rm\s+-rf"
    ]
    
    # Toxicity & Profanity
    TOXIC_TERMS = [
        r"\b(hate|kill|murder|attack)\s+the\s+doctor\b",
        r"\bbomb\s+the\s+hospital\b"
    ]

    @classmethod
    def validate_input(cls, user_text: str) -> GuardrailVerdict:
        """
        Scans clinical inputs, chief complaints, and doctor override notes for adversarial jailbreaks.
        """
        violations = []
        risk_score = 0.0
        text_lower = user_text.lower()
        
        # 1. Prompt Injection Scanning
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(f"PROMPT_INJECTION_DETECTED: Matched pattern '{pattern}'")
                risk_score = max(risk_score, 0.95)
                
        # 2. Hostile / Threat Content Scanning
        for pattern in cls.TOXIC_TERMS:
            if re.search(pattern, text_lower):
                violations.append("HOSTILE_THREAT_DETECTED: Threatening hospital personnel or facility")
                risk_score = max(risk_score, 0.99)
                
        is_safe = len(violations) == 0
        if not is_safe:
            logger.warning(f"[SECURITY GUARDRAIL ALERT] Blocked malicious input: {violations}")
            
        return GuardrailVerdict(
            is_safe=is_safe,
            risk_score=risk_score,
            violations=violations,
            sanitized_input=user_text if is_safe else "[REDACTED BY MEDFLOW SECURITY GUARDRAIL]"
        )

    @classmethod
    def sanitize_prompt(cls, user_text: str) -> GuardrailVerdict:
        """Alias for validate_input for cross-runtime API compatibility."""
        return cls.validate_input(user_text)

    @classmethod
    def validate_tool_return(cls, tool_name: str, raw_output: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Type-checks and range-checks tool returns before handing them to downstream agents.
        Prevents corrupted tool outputs from skewing the OR-Tools optimizer.
        """
        if tool_name == "medical_calculator":
            if "calculated_score" in raw_output:
                score = raw_output["calculated_score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 50:
                    return False, f"Calculated score out of physiological bounds: {score}"
                    
            if "shock_index" in raw_output:
                si = raw_output["shock_index"]
                if not isinstance(si, (int, float)) or si < 0.1 or si > 5.0:
                    return False, f"Shock index out of bounds: {si}"
                    
        return True, None


class PromptVarianceEngine:
    """
    Generates and tests prompt architectural variances for Project Standardization:
    1. ReAct Pattern (Reasoning + Acting + Tool Observation loop)
    2. Few-Shot In-Context Learning Prompt
    3. Clinical Persona-Induced Variance (Resuscitation Fellow vs Senior Triage Nurse)
    """

    @staticmethod
    def get_react_prompt(patient_summary: str) -> str:
        return f"""
You are an Emergency Triage ReAct Agent. You must solve triage using Thought-Action-Observation:
Thought: I need to analyze the patient's vitals and determine their clinical deterioration risk.
Action: medical_calculator(NEWS2)
Observation: [Retrieve score]
Thought: Now I need to check relevant clinical protocols.
Action: clinical_guidelines_lookup(condition)
Observation: [Retrieve protocols]
Thought: Based on findings, formulate structured triage.
Final Answer: Produce structured JSON triage.

Patient Case:
{patient_summary}
"""

    @staticmethod
    def get_few_shot_prompt(patient_summary: str) -> str:
        return f"""
You are a Clinical Triage Specialist. Study these past verified emergency triage decisions:

EXAMPLE 1:
Vitals: HR 145, BP 75/40, SpO2 78%, RR 36, AVPU: Voice.
Diagnosis: Acute Respiratory Failure.
Output: Priority: CRITICAL, Severity: 94, Bed: ICU_BED, Equip: VENTILATOR.

EXAMPLE 2:
Vitals: HR 115, BP 160/95, SpO2 93%, RR 24, AVPU: Alert. Pain: 9/10 chest pain.
Diagnosis: Suspected Acute Coronary Syndrome (STEMI).
Output: Priority: HIGH, Severity: 78, Bed: EMERGENCY_BED, Equip: ECG_MONITOR.

EXAMPLE 3:
Vitals: HR 72, BP 120/80, SpO2 99%, RR 14, AVPU: Alert. Pain: 2/10 ankle.
Diagnosis: Mild Ankle Sprain.
Output: Priority: LOW, Severity: 20, Bed: GENERAL_BED, Equip: VITAL_SIGNS_MONITOR.

Now evaluate the new patient:
{patient_summary}
"""

    @staticmethod
    def get_persona_prompt(persona_role: str, patient_summary: str) -> str:
        if persona_role == "RESUSCITATION_FELLOW":
            persona_desc = "You are an aggressive, high-urgency Resuscitation ICU Fellow. You prioritize aggressive early life support and zero tolerance for missed shock."
        else:
            persona_desc = "You are a prudent, highly experienced Senior Triage Desk Nurse. You prioritize hospital bed conservation and accurate outpatient diversion."
            
        return f"""
{persona_desc}
Evaluate the following emergency presentation and provide your expert recommendation:
{patient_summary}
"""
