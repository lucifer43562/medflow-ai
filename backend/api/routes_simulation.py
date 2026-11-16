"""
Simulation and Evaluation Benchmarking Routes.
"""

from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from ..data.scenarios import SCENARIOS
from ..simulation.surge_engine import SurgeSimulator
from ..evaluation.evaluator import SystemEvaluator
from ..agents.coordinator import HospitalCoordinator
from .deps import get_coordinator

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation & Evaluation"])


class RunScenarioRequest(BaseModel):
    scenario_key: str
    delay_seconds: float = 0.2
    auto_approve_non_critical: bool = True


@router.get("/scenarios")
def list_available_scenarios():
    """Returns metadata for all 6 surge scenarios."""
    return SCENARIOS


@router.post("/run")
async def run_scenario(
    req: RunScenarioRequest,
    coordinator: HospitalCoordinator = Depends(get_coordinator)
):
    """
    Executes a surge scenario and returns the outcomes.
    """
    if req.scenario_key not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario key: {req.scenario_key}")
        
    sim = SurgeSimulator(coordinator)
    results = await sim.run_scenario_stream(
        scenario_key=req.scenario_key,
        delay_seconds=req.delay_seconds,
        auto_approve_non_critical=req.auto_approve_non_critical
    )
    return {
        "status": "COMPLETED",
        "scenario": req.scenario_key,
        "patients_processed": len(results),
        "results": results
    }


@router.get("/benchmark")
def run_comparative_benchmark(scenario_key: str = "SCENARIO_3_MASS_CASUALTY"):
    """
    Runs MedFlow AI vs. FCFS Baseline comparison and returns statistical metrics.
    """
    if scenario_key not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario key: {scenario_key}")
        
    evaluator = SystemEvaluator()
    comparison = evaluator.run_benchmark(scenario_key)
    return comparison
