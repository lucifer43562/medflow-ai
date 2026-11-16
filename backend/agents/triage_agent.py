"""
Triage Agent:
Combines deterministic clinical safety rule scoring (NEWS2 - National Early Warning Score)
with LLM semantic symptom analysis to produce safe, explainable, structured triage evaluations.
"""

import json
import logging
from typing import Optional
from ..config import settings
from ..models.patient import PatientIntake, VitalSigns, ConsciousnessLevel
from ..models.decisions import TriageDecision, TriagePriority, RecommendedDepartment
from ..models.resources import BedType, StaffRole, EquipmentType

logger = logging.getLogger("medflow.triage")


def calculate_news2(vitals: VitalSigns) -> int:
    """
    Computes the standardized National Early Warning Score 2 (NEWS2).
    A validated clinical aggregate score used internationally to detect clinical deterioration.
    """
    score = 0
    
    # 1. Respiration Rate
    rr = vitals.respiratory_rate
    if rr <= 8 or rr >= 25:
        score += 3
    elif 21 <= rr <= 24:
        score += 2
    elif 9 <= rr <= 11:
        score += 1
        
    # 2. Oxygen Saturation (SpO2)
    spo2 = vitals.oxygen_saturation
    if spo2 <= 91.0:
        score += 3
    elif 92.0 <= spo2 <= 93.0:
        score += 2
    elif 94.0 <= spo2 <= 95.0:
        score += 1
        
    # 3. Systolic Blood Pressure
    sbp = vitals.systolic_bp
    if sbp <= 90 or sbp >= 220:
        score += 3
    elif 91 <= sbp <= 100:
        score += 2
    elif 101 <= sbp <= 110:
        score += 1
        
    # 4. Pulse / Heart Rate
    hr = vitals.heart_rate
    if hr <= 40 or hr >= 131:
        score += 3
    elif 111 <= hr <= 130:
        score += 2
    elif 41 <= hr <= 50 or 91 <= hr <= 110:
        score += 1
        
    # 5. Consciousness (AVPU scale)
    if vitals.consciousness_level != ConsciousnessLevel.ALERT:
        score += 3
        
    # 6. Temperature
    temp = vitals.temperature_celsius
    if temp <= 35.0:
        score += 3
    elif temp >= 39.1:
        score += 2
    elif (35.1 <= temp <= 36.0) or (38.1 <= temp <= 39.0):
        score += 1
        
    return score


class TriageAgent:
    """
    Autonomous Triage Agent.
    Executes multi-step clinical reasoning, cross-checks against deterministic safety baselines,
    and returns a structured TriageDecision.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("TriageAgent initialized with Gemini API Client.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}. Falling back to Rule-Based Clinical Engine.")
                self.client = None
                
    def evaluate(self, patient: PatientIntake) -> TriageDecision:
        """
        Executes the full triage pipeline for an incoming patient.
        """
        news2 = calculate_news2(patient.vitals)
        
        # 1. Attempt LLM-Based Reasoning if client is available
        llm_decision = None
        if self.client:
            try:
                llm_decision = self._call_llm_triage(patient, news2)
            except Exception as e:
                logger.error(f"LLM Triage failed ({e}). Employing deterministic fail-safe.")
                llm_decision = None
                
        # 2. Deterministic / Fallback Clinical Triage
        if not llm_decision:
            llm_decision = self._deterministic_clinical_triage(patient, news2)
            
        # 3. Deterministic Safety Ceiling & Discrepancy Check (Safety Arbitration)
        final_decision = self._apply_safety_guardrails(patient, llm_decision, news2)
        return final_decision

    def _call_llm_triage(self, patient: PatientIntake, news2: int) -> Optional[dict]:
        """
        Queries Gemini with strict JSON schema instructions.
        """
        prompt = f"""
You are the Lead Clinical Triage AI in a major emergency hospital.
Analyze the following incoming patient record and calculate an urgent triage recommendation.

Patient ID: {patient.patient_id}
Age: {patient.age}, Gender: {patient.gender}
Chief Complaint: {patient.chief_complaint}
Reported Symptoms: {', '.join(patient.symptoms)}
Medical History: {', '.join(patient.medical_history) if patient.medical_history else 'None'}

Vital Signs:
- Heart Rate: {patient.vitals.heart_rate} bpm
- Blood Pressure: {patient.vitals.systolic_bp}/{patient.vitals.diastolic_bp} mmHg
- SpO2 (Oxygen): {patient.vitals.oxygen_saturation}%
- Respiratory Rate: {patient.vitals.respiratory_rate} /min
- Temperature: {patient.vitals.temperature_celsius} C
- Consciousness: {patient.vitals.consciousness_level.value}
- Pain Score: {patient.vitals.pain_score}/10
- Pre-calculated NEWS2: {news2}

Respond with ONLY a raw JSON object with this exact structure:
{{
  "severity_score": <integer 0 to 100>,
  "priority": "<CRITICAL | HIGH | MODERATE | LOW>",
  "confidence": <float 0.0 to 1.0>,
  "recommended_department": "<ICU | EMERGENCY | GENERAL_WARD | OUTPATIENT | ISOLATION>",
  "required_bed_type": "<ICU_BED | EMERGENCY_BED | GENERAL_BED | ISOLATION_BED>",
  "required_equipment": ["<VENTILATOR | ECG_MONITOR | OXYGEN_SUPPLY | VITAL_SIGNS_MONITOR | INFUSION_PUMP>"],
  "required_staff_roles": ["<ICU_SPECIALIST | EMERGENCY_DOCTOR | CRITICAL_CARE_NURSE | WARD_NURSE | RESPIRATORY_THERAPIST>"],
  "reasoning_summary": "<concise clinical explanation>"
}}
"""
        response = self.client.models.generate_content(
            model=settings.LLM_MODEL_NAME,
            contents=prompt,
        )
        text = response.text.strip()
        # Clean potential markdown wrapping
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    def _deterministic_clinical_triage(self, patient: PatientIntake, news2: int) -> dict:
        """
        High-fidelity clinical rule-based engine mirroring Emergency Severity Index (ESI) v4.
        """
        v = patient.vitals
        symptoms_str = " ".join(patient.symptoms).lower() + " " + patient.chief_complaint.lower()
        
        # Level 1: Immediate Resuscitation / Critical (NEWS2 >= 7 or overt collapse)
        is_critical = (
            news2 >= 7 or
            v.consciousness_level in [ConsciousnessLevel.UNRESPONSIVE, ConsciousnessLevel.PAIN] or
            v.oxygen_saturation < 85.0 or
            v.systolic_bp < 80 or
            v.heart_rate > 150 or
            "cardiac arrest" in symptoms_str or
            "flail chest" in symptoms_str or
            "cyanosis" in symptoms_str
        )
        
        if is_critical:
            severity = min(100, 85 + news2 * 2)
            dept = "ICU" if (v.oxygen_saturation < 86 or v.consciousness_level == ConsciousnessLevel.UNRESPONSIVE or news2 >= 9) else "EMERGENCY"
            bed_type = "ICU_BED" if dept == "ICU" else "EMERGENCY_BED"
            eq = ["VENTILATOR", "ECG_MONITOR", "VITAL_SIGNS_MONITOR"] if v.oxygen_saturation < 86 else ["ECG_MONITOR", "OXYGEN_SUPPLY", "VITAL_SIGNS_MONITOR"]
            staff = ["ICU_SPECIALIST", "CRITICAL_CARE_NURSE"] if dept == "ICU" else ["EMERGENCY_DOCTOR", "CRITICAL_CARE_NURSE"]
            
            alarming_vitals = []
            if v.oxygen_saturation < 90: alarming_vitals.append(f"Severe Hypoxemia (SpO2: {v.oxygen_saturation}%)")
            if v.systolic_bp < 90: alarming_vitals.append(f"Circulatory Shock / Hypotension (BP: {v.systolic_bp}/{v.diastolic_bp} mmHg)")
            if v.heart_rate > 130 or v.heart_rate < 50: alarming_vitals.append(f"Severe Arrhythmia / Tachycardia (HR: {v.heart_rate} bpm)")
            if v.respiratory_rate > 28: alarming_vitals.append(f"Tachypnea (RR: {v.respiratory_rate}/min)")
            if v.consciousness_level != ConsciousnessLevel.ALERT: alarming_vitals.append(f"Altered Sensorium ({v.consciousness_level.value})")
            
            clinical_rationale = (
                f"CRITICAL ESI-1 PROTOCOL ACTIVATED: Patient {patient.name} ({patient.age}y {patient.gender.value}) "
                f"presents with '{patient.chief_complaint}'. Standardized NEWS2 score of {news2} confirms imminent "
                f"physiological collapse. Primary clinical triggers: {'; '.join(alarming_vitals) if alarming_vitals else 'Severe hemodynamic instability'}. "
                f"Suspected Differential: Acute Cardiogenic Shock / Severe Respiratory Failure / Septic Organ Hypoperfusion. "
                f"Mandatory Action: Immediate transfer to {dept} ({bed_type}), invasive airway protection/ventilation, continuous 12-lead ECG telemetry, and urgent attending intensivist review."
            )
            return {
                "severity_score": severity,
                "priority": "CRITICAL",
                "confidence": 0.96 if not patient.is_ambiguous else 0.74,
                "recommended_department": dept,
                "required_bed_type": bed_type,
                "required_equipment": eq,
                "required_staff_roles": staff,
                "reasoning_summary": clinical_rationale
            }
            
        # Level 2: High Risk / Emergent (NEWS2 5-6, or severe pain with acute presentation)
        is_high = (
            news2 >= 5 or
            "chest pain" in symptoms_str or
            "stroke" in symptoms_str or
            "hemiparesis" in symptoms_str or
            "severe dyspnea" in symptoms_str or
            (v.pain_score >= 8 and not patient.is_ambiguous)
        )
        
        if is_high:
            severity = 65 + news2 * 3
            clinical_rationale = (
                f"EMERGENT ESI-2 PROTOCOL: Patient {patient.name} ({patient.age}y) presents with '{patient.chief_complaint}' "
                f"(Symptoms: {', '.join(patient.symptoms)}). Elevated NEWS2 of {news2} combined with acute distress indicates "
                f"high risk of rapid physiological decompensation. Vitals: HR {v.heart_rate} bpm, BP {v.systolic_bp}/{v.diastolic_bp} mmHg, SpO2 {v.oxygen_saturation}%, Pain {v.pain_score}/10. "
                f"Suspected Differential: Acute Coronary Syndrome (ACS), Acute Pulmonary Embolism, or Cerebrovascular Event. "
                f"Action Required: Emergency Department bed, immediate 12-lead ECG, cardiac biomarkers/troponin stat draw, and Emergency Physician evaluation within 10 minutes."
            )
            return {
                "severity_score": severity,
                "priority": "HIGH",
                "confidence": 0.92 if not patient.is_ambiguous else 0.70,
                "recommended_department": "EMERGENCY",
                "required_bed_type": "EMERGENCY_BED",
                "required_equipment": ["ECG_MONITOR", "VITAL_SIGNS_MONITOR"],
                "required_staff_roles": ["EMERGENCY_DOCTOR", "CRITICAL_CARE_NURSE"],
                "reasoning_summary": clinical_rationale
            }
            
        # Level 3: Moderate (NEWS2 3-4, or significant symptoms requiring multiple hospital resources)
        is_moderate = (
            news2 >= 2 or
            "abdominal" in symptoms_str or
            "vomiting" in symptoms_str or
            "fracture" in symptoms_str or
            "fever" in symptoms_str or
            v.pain_score >= 5
        )
        
        if is_moderate:
            clinical_rationale = (
                f"URGENT ESI-3 PROTOCOL: Patient {patient.name} ({patient.age}y) presents with '{patient.chief_complaint}'. "
                f"Moderate physiological deviation with NEWS2={news2}. Vitals show stable hemodynamics (HR {v.heart_rate} bpm, BP {v.systolic_bp}/{v.diastolic_bp} mmHg, SpO2 {v.oxygen_saturation}%), "
                f"but symptoms require dedicated diagnostic workup (laboratory chemistry, imaging, IV hydration). "
                f"Plan: General observation bed placement, IV access, symptomatic analgesic relief, and serial vital checks."
            )
            return {
                "severity_score": 45 + news2 * 4,
                "priority": "MODERATE",
                "confidence": 0.90,
                "recommended_department": "GENERAL_WARD",
                "required_bed_type": "GENERAL_BED",
                "required_equipment": ["VITAL_SIGNS_MONITOR", "INFUSION_PUMP"],
                "required_staff_roles": ["EMERGENCY_DOCTOR", "WARD_NURSE"],
                "reasoning_summary": clinical_rationale
            }
            
        # Level 4/5: Low / Non-urgent
        clinical_rationale = (
            f"NON-URGENT ESI-4/5 PROTOCOL: Patient {patient.name} ({patient.age}y) presents with stable complaint '{patient.chief_complaint}'. "
            f"Normal physiological parameters with NEWS2={news2} (HR {v.heart_rate} bpm, BP {v.systolic_bp}/{v.diastolic_bp} mmHg, SpO2 {v.oxygen_saturation}%). "
            f"No acute life-threatening red flags detected. "
            f"Recommendation: Outpatient triage or ambulatory general observation, routine nursing evaluation, and standard medical counseling."
        )
        return {
            "severity_score": 20 + news2 * 3,
            "priority": "LOW",
            "confidence": 0.95,
            "recommended_department": "OUTPATIENT",
            "required_bed_type": "GENERAL_BED",
            "required_equipment": ["VITAL_SIGNS_MONITOR"],
            "required_staff_roles": ["WARD_NURSE"],
            "reasoning_summary": clinical_rationale
        }

    def _apply_safety_guardrails(
        self,
        patient: PatientIntake,
        raw_decision: dict,
        news2: int
    ) -> TriageDecision:
        """
        Deterministic safety arbitration:
        Under-triage prevention rule: If deterministic NEWS2 >= 7 (life-threatening),
        neither the LLM nor human prompt can classify the patient below HIGH/CRITICAL.
        """
        severity = int(raw_decision.get("severity_score", 50))
        priority_str = raw_decision.get("priority", "MODERATE").upper()
        confidence = float(raw_decision.get("confidence", 0.85))
        reasoning = raw_decision.get("reasoning_summary", "Standard clinical evaluation.")
        
        # Enforce NEWS2 Criticality Floor
        if settings.ENABLE_DETERMINISTIC_NEWS2_OVERRIDE and news2 >= 7:
            if priority_str not in ["CRITICAL", "HIGH"]:
                logger.warning(
                    f"Safety Violation Detected for {patient.patient_id}: Raw priority was {priority_str} "
                    f"despite critical NEWS2 of {news2}. Overriding to CRITICAL."
                )
                priority_str = "CRITICAL"
                severity = max(severity, 88)
                confidence = min(confidence, 0.75)  # Signal discrepancy to Escalation Agent
                reasoning = f"[SAFETY OVERRIDE: NEWS2={news2} indicates physiological collapse] " + reasoning
            elif priority_str == "CRITICAL" and severity < 85:
                severity = 88
                
        # Ambiguity Penalty on Confidence
        if patient.is_ambiguous:
            confidence = round(confidence * 0.75, 2)
            
        # Map Enums safely
        try:
            priority = TriagePriority(priority_str)
        except ValueError:
            priority = TriagePriority.MODERATE
            
        try:
            dept = RecommendedDepartment(raw_decision.get("recommended_department", "EMERGENCY"))
        except ValueError:
            dept = RecommendedDepartment.EMERGENCY
            
        try:
            bed_type = BedType(raw_decision.get("required_bed_type", "GENERAL_BED"))
        except ValueError:
            bed_type = BedType.GENERAL_BED
            
        eq_list = []
        for eq in raw_decision.get("required_equipment", []):
            try:
                eq_list.append(EquipmentType(eq))
            except ValueError:
                pass
                
        staff_list = []
        for st in raw_decision.get("required_staff_roles", []):
            try:
                staff_list.append(StaffRole(st))
            except ValueError:
                pass
                
        requires_review = (
            confidence < settings.CONFIDENCE_THRESHOLD or
            priority == TriagePriority.CRITICAL or
            patient.is_ambiguous
        )
        
        return TriageDecision(
            patient_id=patient.patient_id,
            severity_score=severity,
            priority=priority,
            confidence=confidence,
            recommended_department=dept,
            required_bed_type=bed_type,
            required_equipment=eq_list,
            required_staff_roles=staff_list,
            requires_human_review=requires_review,
            reasoning_summary=reasoning,
            deterministic_news2_score=news2
        )
