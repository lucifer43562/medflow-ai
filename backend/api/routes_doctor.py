"""
Human-In-The-Loop Doctor Review & Clinical Override Endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends

from ..models.decisions import DoctorReviewTicket, DoctorAction, TriagePriority
from ..agents.coordinator import HospitalCoordinator
from .deps import get_coordinator

router = APIRouter(prefix="/api/v1/doctor", tags=["Human-in-the-Loop"])


class DoctorReviewRequest(BaseModel):
    ticket_id: str
    action: DoctorAction
    doctor_id: str = "ATTENDING-DOC"
    override_priority: Optional[TriagePriority] = None
    override_bed_id: Optional[str] = None
    override_staff_id: Optional[str] = None
    doctor_notes: Optional[str] = None


@router.get("/tickets", response_model=List[DoctorReviewTicket])
def list_pending_tickets(coordinator: HospitalCoordinator = Depends(get_coordinator)):
    """Fetches all unresolved safety escalation tickets awaiting doctor review."""
    return list(coordinator.state.pending_doctor_reviews.values())


@router.post("/review", response_model=DoctorReviewTicket)
def submit_doctor_review(
    req: DoctorReviewRequest,
    coordinator: HospitalCoordinator = Depends(get_coordinator)
):
    """
    Submits doctor approval, override, or reassignment.
    Overrides AI triage and allocation decisions immediately.
    """
    try:
        ticket = coordinator.handle_doctor_action(
            ticket_id=req.ticket_id,
            action=req.action,
            doctor_id=req.doctor_id,
            override_priority=req.override_priority,
            override_bed_id=req.override_bed_id,
            override_staff_id=req.override_staff_id,
            doctor_notes=req.doctor_notes
        )
        return ticket
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
