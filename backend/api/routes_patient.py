"""
Patient Intake and Management Routes.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from ..models.patient import PatientIntake
from ..agents.coordinator import HospitalCoordinator
from .deps import get_coordinator

router = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


@router.post("/intake", response_model=Dict[str, Any])
def intake_single_patient(
    patient: PatientIntake,
    coordinator: HospitalCoordinator = Depends(get_coordinator)
):
    """
    Intakes a patient and executes the full agentic pipeline (Triage -> Allocation -> Escalation).
    """
    try:
        result = coordinator.intake_patient(patient)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[Dict[str, Any]])
def intake_patient_batch(
    patients: List[PatientIntake],
    coordinator: HospitalCoordinator = Depends(get_coordinator)
):
    """
    Intakes multiple patients sequentially.
    """
    results = []
    for p in patients:
        res = coordinator.intake_patient(p)
        results.append(res)
    return results


@router.get("/queue", response_model=List[str])
def get_waiting_queue(coordinator: HospitalCoordinator = Depends(get_coordinator)):
    """Returns patient IDs currently waiting in queue."""
    return coordinator.state.waiting_queue


@router.delete("/{patient_id}")
def discharge_patient(
    patient_id: str,
    coordinator: HospitalCoordinator = Depends(get_coordinator)
):
    """Discharges a patient and re-optimizes resources for the waiting queue."""
    if patient_id not in coordinator.state.patients:
        raise HTTPException(status_code=404, detail="Patient not found.")
    coordinator.discharge_patient(patient_id)
    return {"status": "SUCCESS", "message": f"Patient {patient_id} discharged."}
