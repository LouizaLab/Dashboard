"""
Node G: SimulationRunner

Executes LPM runs for all scenarios.
"""

from pathlib import Path
from reasoning.state import ReasoningState
from reasoning.tools import run_simulation
from common.versioning import hash_scenario_config


def simulation_runner(state: ReasoningState) -> ReasoningState:
    """
    Execute simulation runs.
    
    Runs all pending simulations and updates run artifacts.
    """
    if not state.pins.data_version:
        state.pins.data_version = "data_2026_01_08_run01"
    
    if not state.pins.persona_version:
        state.pins.persona_version = "PersonaSet_v1.json"
    
    base_output_dir = Path("runs") / state.run_id
    
    for run in state.runs:
        if run.status != "pending":
            continue
        
        # Find scenario spec
        scenario_spec = next(
            (s for s in state.scenario_specs if s.scenario_id == run.scenario_id),
            None
        )
        
        if not scenario_spec:
            run.status = "failed"
            continue
        
        # Convert scenario spec to dict
        scenario_dict = {
            "scenario_id": scenario_spec.scenario_id,
            "time_horizon_weeks": scenario_spec.time_horizon_weeks,
            "interventions": [
                {
                    "type": interv.type,
                    "brand_id": interv.brand_id,
                    "region_id": interv.region_id,
                    "item_id": interv.item_id,
                    "delta_pct": interv.delta_pct,
                    "intensity": interv.intensity,
                    "start_week": interv.start_week,
                    "end_week": interv.end_week
                }
                for interv in scenario_spec.interventions
            ]
        }
        
        # Create output directory
        run_output_dir = base_output_dir / run.run_id
        run_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Run simulation
            artifacts = run_simulation(
                scenario_spec=scenario_dict,
                persona_version=state.pins.persona_version,
                data_version=state.pins.data_version,
                seed=run.seed,
                num_agents=run.num_agents,
                output_dir=str(run_output_dir)
            )
            
            # Update run artifacts
            run.artifacts.simulated_metrics_path = artifacts["simulated_metrics_path"]
            run.artifacts.persona_contrib_path = artifacts["persona_contrib_path"]
            run.status = "completed"
            
        except Exception as e:
            run.status = "failed"
            print(f"Warning: Simulation {run.run_id} failed: {e}")
    
    return state

