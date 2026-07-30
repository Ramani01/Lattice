"""
Lattice Deterministic Plan Validator
Decoupled validation logic for execution plans, dependency constraints, and service coverage.
"""

from typing import Dict, List, Tuple, Any

def validate_execution_plan(plan: Dict[str, Any], dependencies: List[Tuple[str, str]], inventory: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate execution plan containing both Transition and Target stages."""
    transition_phases = {}
    target_phases = {}
    
    for phase_name, stage_data in plan.items():
        try:
            phase_num = int(phase_name.replace("Phase", "").strip())
        except ValueError:
            phase_num = 999
            
        if isinstance(stage_data, dict):
            to_transition = stage_data.get("Upgrade to Transition State", [])
            to_target = stage_data.get("Enforce Target Configuration", [])
            
            for s in to_transition:
                transition_phases[s] = phase_num
            for s in to_target:
                target_phases[s] = phase_num
                
    conflicts = []
    expected_services = set([item["name"] if isinstance(item, dict) and "name" in item else item.get("service", "") for item in inventory])
    
    # Check if all services are scheduled for both states
    for s in expected_services:
        if not s:
            continue
        t_ph = transition_phases.get(s)
        tc_ph = target_phases.get(s)
        
        if t_ph is None:
            conflicts.append(f"Service '{s}' is missing an 'Upgrade to Transition State' phase.")
        if tc_ph is None:
            conflicts.append(f"Service '{s}' is missing an 'Enforce Target Configuration' phase.")
            
        # 1. Timeline Consistency: Transition must occur before or in the same phase as Target
        if t_ph is not None and tc_ph is not None:
            if t_ph > tc_ph:
                conflicts.append(
                    f"Timeline Conflict: '{s}' enforces Target Configuration in Phase {tc_ph}, "
                    f"but is upgraded to Transition State in later Phase {t_ph}."
                )
                
    # 2. Dependency Constraints
    for caller, callee in dependencies:
        t_caller = transition_phases.get(caller)
        t_callee = transition_phases.get(callee)
        tc_caller = target_phases.get(caller)
        tc_callee = target_phases.get(callee)
        
        # A. Callee B must become Transition before or in the same phase as caller A becomes Transition (T_B <= T_A)
        if t_caller is not None and t_callee is not None:
            if t_callee > t_caller:
                conflicts.append(
                    f"Dependency Conflict: Caller '{caller}' enters Transition State in Phase {t_caller}, "
                    f"but its dependency '{callee}' enters Transition State in later Phase {t_callee}."
                )
                
        # B. Callee B must become Target before or in the same phase caller A becomes Target (TC_B <= TC_A)
        if tc_caller is not None and tc_callee is not None:
            if tc_callee > tc_caller:
                conflicts.append(
                    f"Dependency Conflict: Caller '{caller}' enforces Target Configuration in Phase {tc_caller}, "
                    f"but its dependency '{callee}' enforces Target Configuration in later Phase {tc_callee}."
                )
                
        # C. Caller A must become Transition before or in the same phase callee B becomes Target (T_A <= TC_B)
        if t_caller is not None and tc_callee is not None:
            if t_caller > tc_callee:
                conflicts.append(
                    f"Deprecation Conflict: Dependency '{callee}' enforces Target Configuration in Phase {tc_callee}, "
                    f"but its caller '{caller}' is still Legacy and only enters Transition State in later Phase {t_caller}."
                )
                
    return len(conflicts) == 0, conflicts

def validate_plan(plan: Dict[str, Any], dependencies: List[Tuple[str, str]], inventory: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate plan for dependency violations, routing to binary or execution validations."""
    is_hybrid = False
    for val in plan.values():
        if isinstance(val, dict):
            is_hybrid = True
            break
            
    if is_hybrid:
        return validate_execution_plan(plan, dependencies, inventory)
        
    service_phases = {}
    for phase_name, services in plan.items():
        try:
            # Extract phase number from "Phase X"
            phase_num = int(phase_name.replace("Phase", "").strip())
        except ValueError:
            phase_num = 999
        for s in services:
            service_phases[s] = phase_num
            
    conflicts = []
    for caller, callee in dependencies:
        caller_phase = service_phases.get(caller)
        callee_phase = service_phases.get(callee)
        
        if caller_phase is None:
            conflicts.append(f"Missing caller '{caller}' from execution plan.")
        elif callee_phase is None:
            conflicts.append(f"Missing callee '{callee}' from execution plan.")
        elif caller_phase < callee_phase:
            conflicts.append(
                f"Dependency Conflict: Upstream '{caller}' scheduled in Phase {caller_phase}, "
                f"but callee dependency '{callee}' scheduled in later Phase {callee_phase}."
            )
            
    expected = set([item["name"] if isinstance(item, dict) and "name" in item else item.get("service", "") for item in inventory])
    planned = set(service_phases.keys())
    missing = expected - planned
    for m in missing:
        if m:
            conflicts.append(f"Missing service '{m}' entirely from plan.")
        
    return len(conflicts) == 0, conflicts
