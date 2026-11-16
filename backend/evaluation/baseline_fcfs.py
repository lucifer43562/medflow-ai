"""
First-Come, First-Served (FCFS) Manual / Greedy Baseline:
Mimics traditional emergency ward intake where patients are processed in order of arrival,
allocating the first available bed and staff greedily without global optimization.
"""

from typing import List, Dict, Tuple
from copy import deepcopy
from ..models.patient import PatientIntake
from ..models.resources import HospitalResources, BedStatus, EquipmentStatus
from ..models.decisions import ResourceAllocation, TriagePriority, TriageDecision


class FCFSBaselineEngine:
    """
    Greedy First-Come-First-Served allocation.
    Serves as the empirical benchmark to demonstrate the quantitative advantage of MedFlow AI.
    """
    
    @staticmethod
    def run_allocation(
        patients: List[PatientIntake],
        triage_decisions: Dict[str, TriageDecision],
        resources: HospitalResources
    ) -> Tuple[List[ResourceAllocation], HospitalResources]:
        """
        Processes patients chronologically by arrival time.
        Greedily seizes the first available matching bed, staff, and equipment.
        """
        res_copy = deepcopy(resources)
        # Sort strictly by arrival time
        sorted_patients = sorted(patients, key=lambda p: p.arrival_time)
        allocations: List[ResourceAllocation] = []
        
        for p in sorted_patients:
            pid = p.patient_id
            triage = triage_decisions.get(pid)
            
            # Find first available bed
            assigned_bed = None
            for b in res_copy.beds:
                if b.status == BedStatus.AVAILABLE:
                    # Greedy FCFS often places any patient in any available bed or loosely matches
                    if triage and b.bed_type == triage.required_bed_type:
                        assigned_bed = b
                        break
                    elif not triage:
                        assigned_bed = b
                        break
                        
            # If preferred bed not found, greedy FCFS grabs whatever bed is open
            if not assigned_bed:
                for b in res_copy.beds:
                    if b.status == BedStatus.AVAILABLE:
                        assigned_bed = b
                        break
                        
            # Find first available staff
            assigned_staff = []
            if assigned_bed:
                for s in res_copy.staff:
                    if s.is_on_duty and len(s.assigned_patient_ids) < s.max_patient_capacity:
                        assigned_staff.append(s.staff_id)
                        s.assigned_patient_ids.append(pid)
                        break
                        
            # Find first available equipment if required
            assigned_eq = []
            if assigned_bed and triage and triage.required_equipment:
                for req_eq_type in triage.required_equipment:
                    for eq in res_copy.equipment:
                        if eq.status == EquipmentStatus.AVAILABLE and eq.equipment_type == req_eq_type:
                            eq.status = EquipmentStatus.IN_USE
                            eq.current_patient_id = pid
                            assigned_eq.append(eq.equipment_id)
                            break
                            
            if assigned_bed and assigned_staff:
                assigned_bed.status = BedStatus.OCCUPIED
                assigned_bed.current_patient_id = pid
                allocations.append(ResourceAllocation(
                    patient_id=pid,
                    assigned_bed_id=assigned_bed.bed_id,
                    assigned_bed_type=assigned_bed.bed_type,
                    assigned_staff_ids=assigned_staff,
                    assigned_equipment_ids=assigned_eq,
                    is_allocated=True,
                    is_queued=False,
                    solver_status="GREEDY_FCFS",
                    notes="Assigned via First-Come-First-Served Greedy logic"
                ))
            else:
                # Patient starved of resources
                allocations.append(ResourceAllocation(
                    patient_id=pid,
                    is_allocated=False,
                    is_queued=True,
                    solver_status="GREEDY_FCFS_STARVED",
                    notes="Queued: Resources exhausted under FCFS"
                ))
                
        return allocations, res_copy
