"""
Hospital State and Resource Telemetry Endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from ..models.state import SharedHospitalState, HospitalMetrics
from ..agents.coordinator import HospitalCoordinator
from .deps import get_coordinator

router = APIRouter(prefix="/api/v1/hospital", tags=["Hospital State"])


@router.get("/state", response_model=SharedHospitalState)
def get_hospital_state(coordinator: HospitalCoordinator = Depends(get_coordinator)):
    """Returns the complete single-source-of-truth state object."""
    coordinator.recalculate_metrics()
    return coordinator.state


@router.get("/metrics", response_model=HospitalMetrics)
def get_metrics(coordinator: HospitalCoordinator = Depends(get_coordinator)):
    """Returns operational KPIs: bed occupancy, wait times, triage latency."""
    coordinator.recalculate_metrics()
    return coordinator.state.metrics


@router.post("/reset")
def reset_state(coordinator: HospitalCoordinator = Depends(get_coordinator)):
    """Resets the hospital environment to default clean slate."""
    coordinator.reset_hospital()
    return {"status": "SUCCESS", "message": "Hospital state reset to default."}
