"""
Allocation Agent:
Autonomous resource manager responsible for orchestrating the CP-SAT optimization engine,
evaluating hospital resource state, and preparing candidate allocations.
"""

import logging
from typing import List, Dict, Tuple, Optional
from ..optimization.ortools_allocator import HospitalOptimizationEngine
from ..models.patient import PatientIntake
from ..models.decisions import TriageDecision, ResourceAllocation
from ..models.resources import Bed, Staff, Equipment
from ..config import settings

logger = logging.getLogger("medflow.allocation_agent")


class AllocationAgent:
    """
    Coordinates global constraint solving for emergency department resources.
    """
    
    def __init__(self, time_limit_seconds: Optional[float] = None):
        self.optimizer = HospitalOptimizationEngine(
            time_limit_seconds=time_limit_seconds or settings.MAX_ORTOOLS_SOLVER_TIME_SECONDS
        )
        
    def allocate_batch(
        self,
        patients: List[PatientIntake],
        triage_decisions: Dict[str, TriageDecision],
        beds: List[Bed],
        staff: List[Staff],
        equipment: List[Equipment],
        patient_wait_times: Optional[Dict[str, float]] = None
    ) -> Tuple[List[ResourceAllocation], Dict[str, any]]:
        """
        Executes optimal resource matching for a cohort of patients.
        """
        logger.info(f"AllocationAgent initiating CP-SAT solve for {len(patients)} patients.")
        allocations, metrics = self.optimizer.solve(
            patients=patients,
            triage_decisions=triage_decisions,
            available_beds=beds,
            available_staff=staff,
            available_equipment=equipment,
            patient_wait_times=patient_wait_times
        )
        return allocations, metrics
