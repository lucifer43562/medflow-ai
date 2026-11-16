"""
Evaluation Metrics & Comparative Benchmarking:
Calculates statistical performance indicators for MedFlow AI vs. FCFS Baseline.
"""

from typing import List, Dict, Any
import numpy as np
from ..models.patient import PatientIntake
from ..models.decisions import ResourceAllocation, TriageDecision, TriagePriority


def calculate_scenario_metrics(
    patients: List[PatientIntake],
    triage_decisions: Dict[str, TriageDecision],
    allocations: List[ResourceAllocation],
    model_name: str
) -> Dict[str, Any]:
    """
    Computes comparative healthcare system metrics:
    - Allocation Success Rate
    - Critical Patient Allocation Rate
    - Resource Mismatch Rate
    - Average Simulated Wait Time (minutes)
    - Critical Patient Simulated Wait Time (minutes)
    """
    total = len(patients)
    allocated = [a for a in allocations if a.is_allocated]
    queued = [a for a in allocations if a.is_queued]
    
    crit_patients = [
        p for p in patients
        if triage_decisions.get(p.patient_id) and triage_decisions[p.patient_id].priority == TriagePriority.CRITICAL
    ]
    crit_pids = {p.patient_id for p in crit_patients}
    crit_allocated = [a for a in allocated if a.patient_id in crit_pids]
    
    # Calculate simulated wait times
    # In emergency triage, wait times correlate with queue position and lack of immediate allocation
    wait_times = []
    crit_wait_times = []
    
    for idx, p in enumerate(patients):
        alloc = next((a for a in allocations if a.patient_id == p.patient_id), None)
        triage = triage_decisions.get(p.patient_id)
        is_crit = p.patient_id in crit_pids
        
        if alloc and alloc.is_allocated:
            # Immediate or short wait based on processing order
            w = max(2.0, (idx % 4) * 3.5)
        else:
            # Starved / Queued: Heavy penalty wait time
            w = 45.0 + (idx * 4.0)
            
        wait_times.append(w)
        if is_crit:
            crit_wait_times.append(w)
            
    # Check for mismatches (e.g. non-ICU bed assigned to ICU patient)
    mismatches = 0
    for a in allocated:
        triage = triage_decisions.get(a.patient_id)
        if triage and a.assigned_bed_type:
            if triage.required_bed_type.value == "ICU_BED" and a.assigned_bed_type.value != "ICU_BED":
                mismatches += 1
                
    return {
        "model_name": model_name,
        "total_patients": total,
        "allocated_count": len(allocated),
        "queued_count": len(queued),
        "allocation_rate_pct": round((len(allocated) / max(1, total)) * 100, 1),
        "critical_count": len(crit_patients),
        "critical_allocated_count": len(crit_allocated),
        "critical_success_rate_pct": round((len(crit_allocated) / max(1, len(crit_patients))) * 100, 1),
        "average_wait_minutes": round(float(np.mean(wait_times)) if wait_times else 0.0, 1),
        "critical_wait_minutes": round(float(np.mean(crit_wait_times)) if crit_wait_times else 0.0, 1),
        "resource_mismatches": mismatches
    }
