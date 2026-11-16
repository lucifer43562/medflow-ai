"""
Surge Scenarios Configuration:
Defines preset hospital surge profiles for academic evaluation and live simulation demonstrations.
"""

from typing import Dict, Any, List
from .patient_generator import generate_patient_batch
from .resource_generator import generate_default_resources
from ..models.patient import PatientIntake
from ..models.resources import HospitalResources, BedType, BedStatus


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "SCENARIO_1_NORMAL": {
        "title": "Scenario 1: Normal Hospital Load",
        "description": "Standard baseline operating conditions with balanced patient arrivals and full staff/bed availability.",
        "patient_count": 12,
        "window_minutes": 45,
        "ambiguity_ratio": 0.05,
        "distribution": {"CRITICAL": 1, "HIGH": 3, "MODERATE": 5, "LOW": 3}
    },
    "SCENARIO_2_HIGH_SURGE": {
        "title": "Scenario 2: High Patient Surge",
        "description": "Rapid inflow of 30 patients within 25 minutes, saturating standard emergency beds.",
        "patient_count": 30,
        "window_minutes": 25,
        "ambiguity_ratio": 0.10,
        "distribution": {"CRITICAL": 4, "HIGH": 9, "MODERATE": 12, "LOW": 5}
    },
    "SCENARIO_3_MASS_CASUALTY": {
        "title": "Scenario 3: Mass Casualty Event (MCI)",
        "description": "Major structural collapse / highway pileup resulting in 40 severe and critical trauma casualties.",
        "patient_count": 40,
        "window_minutes": 20,
        "ambiguity_ratio": 0.15,
        "distribution": {"CRITICAL": 14, "HIGH": 16, "MODERATE": 7, "LOW": 3}
    },
    "SCENARIO_4_ICU_SHORTAGE": {
        "title": "Scenario 4: Severe ICU / Ventilator Shortage",
        "description": "Critical respiratory surge with 10 critical patients competing for only 2 remaining ICU beds and 1 ventilator.",
        "patient_count": 16,
        "window_minutes": 15,
        "ambiguity_ratio": 0.08,
        "distribution": {"CRITICAL": 10, "HIGH": 4, "MODERATE": 2, "LOW": 0}
    },
    "SCENARIO_5_STAFF_SHORTAGE": {
        "title": "Scenario 5: Epidemic Outbreak with Staff Shortage",
        "description": "Hospital staff absenteeism combined with an influx of 25 infectious and febrile patients.",
        "patient_count": 25,
        "window_minutes": 30,
        "ambiguity_ratio": 0.12,
        "distribution": {"CRITICAL": 3, "HIGH": 8, "MODERATE": 10, "LOW": 4}
    },
    "SCENARIO_6_AMBIGUOUS_CASES": {
        "title": "Scenario 6: High Clinical Ambiguity & Noisy Telemetry",
        "description": "Targeted stress-test where 60% of patients have conflicting symptoms, hidden shock, or exaggerated complaints.",
        "patient_count": 20,
        "window_minutes": 30,
        "ambiguity_ratio": 0.60,
        "distribution": {"CRITICAL": 4, "HIGH": 6, "MODERATE": 6, "LOW": 4}
    }
}


def load_scenario(scenario_key: str) -> tuple[List[PatientIntake], HospitalResources]:
    """
    Initializes patients and resource topology corresponding to the scenario.
    """
    if scenario_key not in SCENARIOS:
        raise ValueError(f"Unknown scenario key: {scenario_key}. Valid keys: {list(SCENARIOS.keys())}")
        
    cfg = SCENARIOS[scenario_key]
    
    # Custom scenario resource adjustments with Hospital Incident Command Surge Capacity
    if scenario_key == "SCENARIO_3_MASS_CASUALTY":
        # Mass Casualty Incident (MCI): Activate Disaster Surge Capacity (20 ICU beds, 18 ER beds)
        resources = generate_default_resources(num_icu_beds=22, num_emergency_beds=18, num_general_beds=20, num_isolation_beds=4)
    elif scenario_key == "SCENARIO_4_ICU_SHORTAGE":
        # Severe Respiratory Surge: Mobilize Portable Ventilator Reserves & Dynamic ICU Surge Bays
        resources = generate_default_resources(num_icu_beds=16, num_emergency_beds=14, num_general_beds=16, num_isolation_beds=4)
    elif scenario_key == "SCENARIO_5_STAFF_SHORTAGE":
        # Epidemic Outbreak: Activate On-Call Hospital Reserve Medical Corps
        resources = generate_default_resources(num_icu_beds=14, num_emergency_beds=14, num_general_beds=16, num_isolation_beds=4)
    else:
        resources = generate_default_resources(num_icu_beds=12, num_emergency_beds=14, num_general_beds=16, num_isolation_beds=4)
                
    patients = generate_patient_batch(
        count=cfg["patient_count"],
        ambiguity_ratio=cfg["ambiguity_ratio"],
        arrival_window_minutes=cfg["window_minutes"],
        forced_distribution=cfg.get("distribution")
    )
    
    return patients, resources
