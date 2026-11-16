"""
Surge Simulation Engine:
Simulates high-velocity patient arrivals (e.g. mass casualties, seasonal outbreaks)
and runs the multi-agent pipeline with discrete temporal steps.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from ..models.patient import PatientIntake
from ..agents.coordinator import HospitalCoordinator
from ..data.scenarios import load_scenario

logger = logging.getLogger("medflow.simulation")


class SurgeSimulator:
    """
    Manages continuous and discrete surge scenarios.
    """
    
    def __init__(self, coordinator: HospitalCoordinator):
        self.coordinator = coordinator
        self.is_running = False
        self._current_task: Optional[asyncio.Task] = None

    async def run_scenario_stream(
        self,
        scenario_key: str,
        delay_seconds: float = 0.5,
        auto_approve_non_critical: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes a scenario stream sequentially, yielding state changes and WebSocket updates.
        """
        self.is_running = True
        logger.info(f"Starting surge simulation: {scenario_key}")
        
        patients, resources = load_scenario(scenario_key)
        self.coordinator.reset_hospital(resources)
        
        results = []
        for p in patients:
            if not self.is_running:
                logger.info("Simulation halted by user.")
                break
                
            res = self.coordinator.intake_patient(p)
            results.append(res)
            
            # If auto-approve is enabled for non-critical cases in simulation
            if auto_approve_non_critical and res.get("requires_doctor_review"):
                ticket_id = next(
                    (tid for tid, t in self.coordinator.state.pending_doctor_reviews.items() if t.patient_id == p.patient_id),
                    None
                )
                triage_prio = res["triage"]["priority"]
                if ticket_id and triage_prio != "CRITICAL":
                    # Simulate human doctor approving after a short review
                    self.coordinator.handle_doctor_action(
                        ticket_id=ticket_id,
                        action=self.coordinator.handle_doctor_action.__annotations__.get('action', 'APPROVE'),
                        doctor_id="SIMULATED-DOC",
                        doctor_notes="Simulated physician concurrence."
                    )
                    
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
                
        self.is_running = False
        logger.info(f"Surge simulation complete: {len(results)} patients processed.")
        return results

    def stop(self):
        """Halts the active simulation."""
        self.is_running = False
