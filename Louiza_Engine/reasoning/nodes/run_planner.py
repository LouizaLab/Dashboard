"""
Node F: RunPlanner

Decides run plan given budget constraints.
"""

import random
from reasoning.state import ReasoningState, Run


def run_planner(state: ReasoningState) -> ReasoningState:
    """
    Plan simulation runs given budget constraints.
    
    Creates run specifications for each scenario.
    """
    budget = state.request.simulation_budget
    
    # Limit scenarios to budget
    scenarios_to_run = state.scenario_specs[:budget.max_scenarios]
    
    runs = []
    run_counter = 1
    
    # Plan runs for each scenario
    for scenario in scenarios_to_run:
        # Number of runs per scenario (for uncertainty bands)
        num_runs_per_scenario = min(3, budget.max_runs // len(scenarios_to_run))
        
        for run_idx in range(num_runs_per_scenario):
            run_id = f"RUN_{run_counter:03d}"
            
            # Generate seed deterministically
            seed = hash((scenario.scenario_id, run_idx)) % (2**31)
            
            # Determine agent count (respect budget)
            num_agents = min(budget.max_agents, 10000)  # POC: use smaller number
            
            run = Run(
                run_id=run_id,
                scenario_id=scenario.scenario_id,
                seed=seed,
                num_agents=num_agents,
                status="pending"
            )
            runs.append(run)
            run_counter += 1
    
    state.runs = runs
    return state

