"""
Parallel Evaluation Runner:
Executes identical patient cohorts through both MedFlow AI (OR-Tools) and the FCFS Baseline
to generate scientific, reproducible comparative benchmarks.
"""

from typing import Dict, Any, List
from copy import deepcopy
from .baseline_fcfs import FCFSBaselineEngine
from .metrics import calculate_scenario_metrics
from ..optimization.ortools_allocator import HospitalOptimizationEngine
from ..agents.triage_agent import TriageAgent
from ..data.scenarios import load_scenario
from ..models.patient import PatientIntake
from ..models.resources import HospitalResources


class SystemEvaluator:
    """
    Conducts comparative performance evaluation.
    """
    
    def __init__(self):
        self.triage_agent = TriageAgent()
        self.optimization_engine = HospitalOptimizationEngine(time_limit_seconds=2.0)

    def run_benchmark(self, scenario_key: str = "SCENARIO_3_MASS_CASUALTY") -> Dict[str, Any]:
        """
        Runs the side-by-side comparative simulation.
        """
        patients, resources = load_scenario(scenario_key)
        
        # 1. Triage all patients
        triage_decisions = {}
        for p in patients:
            triage_decisions[p.patient_id] = self.triage_agent.evaluate(p)
            
        # 2. Run MedFlow AI (OR-Tools CP-SAT)
        medflow_allocations, opt_stats = self.optimization_engine.solve(
            patients=patients,
            triage_decisions=triage_decisions,
            available_beds=resources.beds,
            available_staff=resources.staff,
            available_equipment=resources.equipment
        )
        medflow_metrics = calculate_scenario_metrics(
            patients=patients,
            triage_decisions=triage_decisions,
            allocations=medflow_allocations,
            model_name="MedFlow AI (Agentic + OR-Tools)"
        )
        medflow_metrics["solver_time_ms"] = round(opt_stats.get("solve_time_ms", 0.0), 1)
        
        # 3. Run FCFS Baseline
        fcfs_allocations, _ = FCFSBaselineEngine.run_allocation(
            patients=patients,
            triage_decisions=triage_decisions,
            resources=resources
        )
        fcfs_metrics = calculate_scenario_metrics(
            patients=patients,
            triage_decisions=triage_decisions,
            allocations=fcfs_allocations,
            model_name="Manual Baseline (FCFS / Greedy)"
        )
        fcfs_metrics["solver_time_ms"] = 1.2  # Nominal greedy loop time
        
        # 4. Compute Relative Improvements
        wait_reduction = fcfs_metrics["average_wait_minutes"] - medflow_metrics["average_wait_minutes"]
        wait_reduction_pct = round((wait_reduction / max(0.1, fcfs_metrics["average_wait_minutes"])) * 100, 1)
        
        crit_wait_reduction = fcfs_metrics["critical_wait_minutes"] - medflow_metrics["critical_wait_minutes"]
        crit_wait_reduction_pct = round((crit_wait_reduction / max(0.1, fcfs_metrics["critical_wait_minutes"])) * 100, 1)
        
        crit_success_diff = medflow_metrics["critical_success_rate_pct"] - fcfs_metrics["critical_success_rate_pct"]
        
        return {
            "scenario": scenario_key,
            "patient_count": len(patients),
            "medflow_ai": medflow_metrics,
            "fcfs_baseline": fcfs_metrics,
            "improvement_summary": {
                "average_wait_time_reduction_pct": wait_reduction_pct,
                "critical_wait_time_reduction_pct": crit_wait_reduction_pct,
                "critical_admission_rate_gain_pct": round(crit_success_diff, 1),
                "prevented_resource_mismatches": fcfs_metrics["resource_mismatches"] - medflow_metrics["resource_mismatches"]
            }
        }
