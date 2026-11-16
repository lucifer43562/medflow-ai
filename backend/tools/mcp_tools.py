"""
Model Context Protocol (MCP) Tool Integration Subsystem:
Implements standardized MCP tool contracts and schemas for external clinical tool usage.
Includes:
1. ClinicalGuidelinesMCPTool: External clinical guideline & protocol knowledge base lookup.
2. MedicalCalculatorMCPTool: Validated physiological scoring calculators (NEWS2, GCS).
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ClinicalLookupInput(BaseModel):
    condition_or_symptom: str = Field(..., description="Target pathology, condition, or chief complaint to query")
    patient_age: Optional[int] = Field(default=None, description="Patient age for pediatric/geriatric protocol variations")


class MedicalCalculatorInput(BaseModel):
    calculator_type: str = Field(..., description="Calculator to run: 'NEWS2', 'GCS', or 'SHOCK_INDEX'")
    parameters: Dict[str, Any] = Field(..., description="Physiological parameters matching calculator requirements")


class ClinicalGuidelinesMCPTool:
    """
    MCP Tool 1: Clinical Protocol & Guideline Database Lookup.
    Adheres to the Model Context Protocol (MCP) specification.
    """
    
    CLINICAL_KB: Dict[str, Dict[str, Any]] = {
        "respiratory_distress": {
            "protocol_name": "Emergency Acute Dyspnea & Respiratory Failure Protocol",
            "immediate_actions": ["Supplemental High-Flow O2", "Arterial Blood Gas (ABG)", "Chest Radiograph"],
            "recommended_bed": "ICU_BED",
            "required_equipment": ["VENTILATOR", "OXYGEN_SUPPLY"],
            "staff_roles": ["ICU_SPECIALIST", "CRITICAL_CARE_NURSE", "RESPIRATORY_THERAPIST"],
            "contraindications": ["Do not administer sedatives without definitive airway protection."]
        },
        "cardiac_arrest": {
            "protocol_name": "Advanced Cardiac Life Support (ACLS) Resuscitation",
            "immediate_actions": ["Initiate CPR 30:2", "Attach Defibrillator/Monitor", "IV/IO Access"],
            "recommended_bed": "EMERGENCY_BED",
            "required_equipment": ["DEFIBRILLATOR", "ECG_MONITOR", "INFUSION_PUMP"],
            "staff_roles": ["EMERGENCY_DOCTOR", "CRITICAL_CARE_NURSE"],
            "contraindications": ["Do not interrupt chest compressions > 10 seconds."]
        },
        "stroke_fast": {
            "protocol_name": "Acute Ischemic Stroke Code Neuro",
            "immediate_actions": ["Non-contrast head CT within 20 mins", "Evaluate for IV Thrombolysis / tPA", "Blood Glucose Check"],
            "recommended_bed": "EMERGENCY_BED",
            "required_equipment": ["VITAL_SIGNS_MONITOR"],
            "staff_roles": ["EMERGENCY_DOCTOR"],
            "contraindications": ["Strict BP ceiling < 185/110 mmHg if considering thrombolysis."]
        },
        "sepsis": {
            "protocol_name": "Surviving Sepsis Campaign Hour-1 Bundle",
            "immediate_actions": ["Measure lactate level", "Obtain blood cultures before antibiotics", "Administer broad-spectrum antibiotics", "Rapid fluid resuscitation 30ml/kg"],
            "recommended_bed": "EMERGENCY_BED",
            "required_equipment": ["INFUSION_PUMP", "VITAL_SIGNS_MONITOR"],
            "staff_roles": ["EMERGENCY_DOCTOR", "WARD_NURSE"],
            "contraindications": ["Do not delay antibiotic administration > 1 hour."]
        }
    }

    @classmethod
    def get_mcp_schema(cls) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="clinical_guidelines_lookup",
            description="Queries validated hospital clinical guidelines, immediate resuscitation protocols, and drug/therapy contraindications via MCP.",
            inputSchema=ClinicalLookupInput.model_json_schema()
        )

    def execute(self, condition_or_symptom: str, patient_age: Optional[int] = None) -> Dict[str, Any]:
        """Executes MCP tool call."""
        query = condition_or_symptom.lower().replace(" ", "_")
        for key, protocol in self.CLINICAL_KB.items():
            if key in query or any(word in query for word in key.split("_")):
                res = dict(protocol)
                res["query"] = condition_or_symptom
                res["patient_age"] = patient_age
                res["matched_key"] = key
                return {"status": "SUCCESS", "protocol": res}
                
        # Default supportive care fallback
        return {
            "status": "GENERAL_PROTOCOL",
            "protocol": {
                "protocol_name": "Standard Emergency Supportive Care & Observation",
                "immediate_actions": ["Vital signs monitoring q15m", "Symptomatic relief"],
                "recommended_bed": "GENERAL_BED",
                "required_equipment": ["VITAL_SIGNS_MONITOR"],
                "staff_roles": ["WARD_NURSE"],
                "contraindications": []
            }
        }


class MedicalCalculatorMCPTool:
    """
    MCP Tool 2: Clinical Risk & Physiologic Scoring Calculator.
    Adheres to the Model Context Protocol (MCP) specification.
    """

    @classmethod
    def get_mcp_schema(cls) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="medical_calculator",
            description="Calculates deterministic physiologic risk scores (NEWS2, GCS, Shock Index) using standardized clinical formulas.",
            inputSchema=MedicalCalculatorInput.model_json_schema()
        )

    def execute(self, calculator_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        calc = calculator_type.upper().strip()
        
        if calc == "NEWS2":
            # National Early Warning Score
            hr = parameters.get("heart_rate", 75)
            sbp = parameters.get("systolic_bp", 120)
            spo2 = parameters.get("oxygen_saturation", 98.0)
            rr = parameters.get("respiratory_rate", 16)
            avpu = parameters.get("consciousness_level", "ALERT")
            temp = parameters.get("temperature_celsius", 37.0)
            
            score = 0
            if rr <= 8 or rr >= 25: score += 3
            elif 21 <= rr <= 24: score += 2
            elif 9 <= rr <= 11: score += 1
            
            if spo2 <= 91.0: score += 3
            elif 92.0 <= spo2 <= 93.0: score += 2
            elif 94.0 <= spo2 <= 95.0: score += 1
            
            if sbp <= 90 or sbp >= 220: score += 3
            elif 91 <= sbp <= 100: score += 2
            elif 101 <= sbp <= 110: score += 1
            
            if hr <= 40 or hr >= 131: score += 3
            elif 111 <= hr <= 130: score += 2
            elif 41 <= hr <= 50 or 91 <= hr <= 110: score += 1
            
            if str(avpu).upper() != "ALERT": score += 3
            
            if temp <= 35.0: score += 3
            elif temp >= 39.1: score += 2
            elif (35.1 <= temp <= 36.0) or (38.1 <= temp <= 39.0): score += 1
            
            risk_category = "HIGH_CRITICAL" if score >= 7 else ("MEDIUM_URGENT" if score >= 5 else "LOW_STABLE")
            return {
                "calculator": "NEWS2",
                "calculated_score": score,
                "clinical_risk_tier": risk_category,
                "urgency_action": "Immediate Attending Resuscitation" if score >= 7 else "Urgent Medical Review"
            }
            
        elif calc == "GCS":
            # Glasgow Coma Scale (Eye, Verbal, Motor: 3-15)
            eye = parameters.get("eye_response", 4)
            verbal = parameters.get("verbal_response", 5)
            motor = parameters.get("motor_response", 6)
            gcs_total = eye + verbal + motor
            severity = "SEVERE_COMA" if gcs_total <= 8 else ("MODERATE_DEFICIT" if gcs_total <= 12 else "MILD_NORMAL")
            return {
                "calculator": "GCS",
                "total_gcs": gcs_total,
                "components": {"eye": eye, "verbal": verbal, "motor": motor},
                "intubation_indicated": gcs_total <= 8,
                "clinical_severity": severity
            }
            
        elif calc == "SHOCK_INDEX":
            # Shock Index = Heart Rate / Systolic Blood Pressure (Normal ~0.5 - 0.7)
            hr = parameters.get("heart_rate", 80)
            sbp = max(1, parameters.get("systolic_bp", 120))
            si = round(hr / sbp, 2)
            is_shock = si >= 0.9
            return {
                "calculator": "SHOCK_INDEX",
                "shock_index": si,
                "occult_shock_suspected": is_shock,
                "interpretation": "Elevated Shock Index (>0.9) indicates critical hemodynamic instability." if is_shock else "Normal hemodynamic ratio."
            }
            
        else:
            return {"status": "ERROR", "message": f"Unsupported calculator type: {calculator_type}"}
