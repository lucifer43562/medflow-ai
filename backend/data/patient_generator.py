"""
Patient Synthetic Data Generator:
Produces clinically correlated synthetic patients across Critical, High, Moderate, and Low
severity classes, with controlled clinical noise and edge cases for safety stress testing.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from ..models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender


FIRST_NAMES = ["James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "Benjamin", "Isabella", 
               "Lucas", "Mia", "Henry", "Evelyn", "Alexander", "Harper", "Sebastian", "Camila", "Mateo", "Gianna"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

CLINICAL_PROFILES = {
    "CRITICAL": [
        {
            "complaint": "Acute Respiratory Distress and Cyanosis",
            "symptoms": ["Severe dyspnea", "Cyanotic lips", "Inability to speak in full sentences", "Stridor"],
            "hr_range": (125, 175), "sbp_range": (70, 95), "dbp_range": (40, 60),
            "spo2_range": (68.0, 84.0), "rr_range": (34, 52), "temp_range": (37.2, 39.8),
            "consciousness": [ConsciousnessLevel.VOICE, ConsciousnessLevel.PAIN, ConsciousnessLevel.UNRESPONSIVE],
            "pain_range": (6, 10),
            "history": ["Severe COPD", "Heart Failure NYHA IV", "Recent Pneumonia"]
        },
        {
            "complaint": "Sudden Collapse / Presumed Cardiac Arrest / Shock",
            "symptoms": ["Unresponsive", "Profound diaphoresis", "Pale/ashen skin", "Weak thready pulse"],
            "hr_range": (140, 190), "sbp_range": (55, 80), "dbp_range": (30, 50),
            "spo2_range": (72.0, 85.0), "rr_range": (28, 45), "temp_range": (35.5, 36.8),
            "consciousness": [ConsciousnessLevel.UNRESPONSIVE, ConsciousnessLevel.PAIN],
            "pain_range": (0, 0),
            "history": ["Coronary Artery Disease", "Previous Myocardial Infarction", "Hypertension"]
        },
        {
            "complaint": "Severe Multi-Trauma from High-Speed Collision",
            "symptoms": ["Flail chest", "Compound femur fracture", "Major hemorrhage", "Hypotension"],
            "hr_range": (130, 165), "sbp_range": (65, 85), "dbp_range": (35, 55),
            "spo2_range": (78.0, 88.0), "rr_range": (30, 48), "temp_range": (35.0, 36.5),
            "consciousness": [ConsciousnessLevel.PAIN, ConsciousnessLevel.VOICE],
            "pain_range": (8, 10),
            "history": ["No prior chronic conditions known"]
        }
    ],
    "HIGH": [
        {
            "complaint": "Crushing Retrosternal Chest Pain radiating to Jaw & Left Arm",
            "symptoms": ["Substernal pressure", "Diaphoresis", "Nausea", "Shortness of breath on exertion"],
            "hr_range": (98, 128), "sbp_range": (145, 185), "dbp_range": (90, 115),
            "spo2_range": (91.0, 95.0), "rr_range": (22, 28), "temp_range": (36.6, 37.4),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (7, 10),
            "history": ["Type 2 Diabetes Mellitus", "Hyperlipidemia", "Heavy Smoker"]
        },
        {
            "complaint": "Acute Onset Left-Sided Facial Droop and Hemiparesis (Suspected Stroke)",
            "symptoms": ["Slurred speech (dysarthria)", "Left arm drift", "Left facial numbness"],
            "hr_range": (85, 110), "sbp_range": (160, 210), "dbp_range": (95, 120),
            "spo2_range": (94.0, 98.0), "rr_range": (16, 22), "temp_range": (36.7, 37.6),
            "consciousness": [ConsciousnessLevel.ALERT, ConsciousnessLevel.VOICE],
            "pain_range": (0, 4),
            "history": ["Atrial Fibrillation", "Hypertension"]
        },
        {
            "complaint": "Acute Severe Asthma Exacerbation",
            "symptoms": ["Audible expiratory wheeze", "Accessory muscle use", "Tachypnea"],
            "hr_range": (110, 135), "sbp_range": (125, 145), "dbp_range": (75, 90),
            "spo2_range": (88.0, 92.0), "rr_range": (26, 34), "temp_range": (36.8, 37.5),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (3, 6),
            "history": ["Brittle Asthma", "Inhaled Steroid Reliance"]
        }
    ],
    "MODERATE": [
        {
            "complaint": "Severe Colicky Right Flank Pain (Suspected Nephrolithiasis)",
            "symptoms": ["Intermittent severe flank pain", "Microscopic hematuria", "Nausea", "Vomiting"],
            "hr_range": (85, 108), "sbp_range": (120, 145), "dbp_range": (75, 90),
            "spo2_range": (96.0, 99.0), "rr_range": (16, 20), "temp_range": (36.5, 37.3),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (6, 9),
            "history": ["Prior renal calculi", "Gout"]
        },
        {
            "complaint": "High Spiking Fever with Right Lower Quadrant Abdominal Pain",
            "symptoms": ["Abdominal guarding", "Anorexia", "Fever and chills", "Rebound tenderness"],
            "hr_range": (95, 115), "sbp_range": (110, 130), "dbp_range": (70, 85),
            "spo2_range": (96.0, 100.0), "rr_range": (18, 22), "temp_range": (38.3, 39.5),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (5, 8),
            "history": ["Appendicitis differential"]
        },
        {
            "complaint": "Dehydration secondary to 3-day Gastroenteritis",
            "symptoms": ["Profuse watery diarrhea", "Repeated emesis", "Dry mucous membranes", "Orthostasis"],
            "hr_range": (92, 112), "sbp_range": (100, 118), "dbp_range": (60, 75),
            "spo2_range": (97.0, 100.0), "rr_range": (16, 20), "temp_range": (37.5, 38.4),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (3, 6),
            "history": ["None significant"]
        }
    ],
    "LOW": [
        {
            "complaint": "Superficial Forearm Laceration with Controlled Hemostasis",
            "symptoms": ["Clean cut from kitchen knife", "Bleeding stopped with pressure", "No neurovascular deficit"],
            "hr_range": (65, 82), "sbp_range": (115, 128), "dbp_range": (70, 82),
            "spo2_range": (98.0, 100.0), "rr_range": (12, 16), "temp_range": (36.4, 37.0),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (2, 4),
            "history": ["Tetanus vaccine up-to-date"]
        },
        {
            "complaint": "Mild Lateral Ankle Inversion Sprain",
            "symptoms": ["Mild swelling", "Able to bear weight with discomfort", "Tenderness over ATFL"],
            "hr_range": (68, 85), "sbp_range": (118, 130), "dbp_range": (72, 84),
            "spo2_range": (98.0, 100.0), "rr_range": (12, 16), "temp_range": (36.5, 37.1),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (2, 4),
            "history": ["Recreational athlete"]
        },
        {
            "complaint": "Upper Respiratory Tract Infection / Common Cold",
            "symptoms": ["Nasal congestion", "Mild pharyngitis", "Dry non-productive cough", "Low-grade malaise"],
            "hr_range": (65, 80), "sbp_range": (112, 125), "dbp_range": (68, 80),
            "spo2_range": (98.0, 100.0), "rr_range": (12, 16), "temp_range": (37.0, 37.6),
            "consciousness": [ConsciousnessLevel.ALERT],
            "pain_range": (1, 2),
            "history": ["Seasonal allergies"]
        }
    ]
}


def generate_single_patient(
    patient_id: str,
    target_severity: Optional[str] = None,
    inject_ambiguity: bool = False,
    arrival_offset_minutes: int = 0
) -> PatientIntake:
    """
    Generates a single, clinically realistic patient with optional synthetic ambiguity.
    """
    if not target_severity:
        # Realistic emergency department distribution: 10% Critical, 25% High, 40% Moderate, 25% Low
        target_severity = random.choices(
            ["CRITICAL", "HIGH", "MODERATE", "LOW"],
            weights=[0.10, 0.25, 0.40, 0.25],
            k=1
        )[0]
        
    profile = random.choice(CLINICAL_PROFILES[target_severity])
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    gender = random.choice([Gender.MALE, Gender.FEMALE])
    
    # Age correlation with severity (higher probability of older age for critical/high)
    if target_severity == "CRITICAL":
        age = random.randint(48, 89)
    elif target_severity == "HIGH":
        age = random.randint(35, 82)
    elif target_severity == "MODERATE":
        age = random.randint(18, 70)
    else:
        age = random.randint(5, 65)
        
    arrival_time = datetime.now(timezone.utc) + timedelta(minutes=arrival_offset_minutes)
    
    hr = random.randint(*profile["hr_range"])
    sbp = random.randint(*profile["sbp_range"])
    dbp = random.randint(*profile["dbp_range"])
    spo2 = round(random.uniform(*profile["spo2_range"]), 1)
    rr = random.randint(*profile["rr_range"])
    temp = round(random.uniform(*profile["temp_range"]), 1)
    consciousness = random.choice(profile["consciousness"])
    pain = random.randint(*profile["pain_range"])
    
    complaint = profile["complaint"]
    symptoms = list(profile["symptoms"])
    history = list(profile["history"])
    
    # Synthetic Edge Case / Ambiguity Injection for Escalation Agent Validation:
    if inject_ambiguity:
        coin = random.random()
        if coin < 0.35:
            # Masked severity: Mild complaint text, but secretly crashing physiological vitals
            complaint = "Patient claims to feel mild fatigue and slight dizziness after walking"
            symptoms = ["Mild dizziness", "Feeling worn out"]
            spo2 = 81.0  # Life-threatening hypoxia
            sbp = 75     # Cardiogenic / Septic shock
            consciousness = ConsciousnessLevel.VOICE
        elif coin < 0.70:
            # Exaggerated complaint / Pain conflict: 10/10 pain with pristine normal vitals
            complaint = "States catastrophic 10/10 worst pain ever in papercut on right index finger"
            pain = 10
            hr = 70
            sbp = 120
            spo2 = 99.0
            rr = 14
        else:
            # Conflicting symptom signals (e.g., stroke symptoms with normal mental status and low pain)
            symptoms.append("Unusual sudden numbness but normal motor reflex reported")
            
    vitals = VitalSigns(
        heart_rate=hr,
        systolic_bp=sbp,
        diastolic_bp=dbp,
        oxygen_saturation=spo2,
        respiratory_rate=rr,
        temperature_celsius=temp,
        consciousness_level=consciousness,
        pain_score=pain
    )
    
    return PatientIntake(
        patient_id=patient_id,
        name=name,
        age=age,
        gender=gender,
        arrival_time=arrival_time,
        chief_complaint=complaint,
        symptoms=symptoms,
        vitals=vitals,
        medical_history=history,
        is_ambiguous=inject_ambiguity
    )


def generate_patient_batch(
    count: int = 20,
    ambiguity_ratio: float = 0.15,
    arrival_window_minutes: int = 30,
    forced_distribution: Optional[dict] = None
) -> List[PatientIntake]:
    """
    Generates a cohort of synthetic patients arriving across a time window.
    """
    patients: List[PatientIntake] = []
    
    if forced_distribution:
        # E.g. {"CRITICAL": 10, "HIGH": 15, "MODERATE": 15, "LOW": 10}
        p_id = 1
        for severity, num in forced_distribution.items():
            for _ in range(num):
                offset = random.randint(0, arrival_window_minutes)
                is_ambig = random.random() < ambiguity_ratio
                patients.append(
                    generate_single_patient(
                        patient_id=f"P-{p_id:04d}",
                        target_severity=severity,
                        inject_ambiguity=is_ambig,
                        arrival_offset_minutes=offset
                    )
                )
                p_id += 1
    else:
        for i in range(1, count + 1):
            offset = random.randint(0, arrival_window_minutes)
            is_ambig = random.random() < ambiguity_ratio
            patients.append(
                generate_single_patient(
                    patient_id=f"P-{i:04d}",
                    inject_ambiguity=is_ambig,
                    arrival_offset_minutes=offset
                )
            )
            
    # Sort chronologically by arrival time
    patients.sort(key=lambda p: p.arrival_time)
    return patients
