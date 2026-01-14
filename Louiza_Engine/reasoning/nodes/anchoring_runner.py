"""
Node H: AnchoringRunner

Runs anchoring calibration (optional).
"""

from pathlib import Path
from reasoning.state import ReasoningState
from reasoning.tools import run_anchoring


def anchoring_runner(state: ReasoningState) -> ReasoningState:
    """
    Run anchoring calibration.
    
    Anchors baseline run to observed data.
    """
    if not state.anchoring.enabled:
        return state
    
    # Find baseline run
    baseline_run = next(
        (r for r in state.runs if r.scenario_id == "S0_baseline" and r.status == "completed"),
        None
    )
    
    if not baseline_run or not baseline_run.artifacts.simulated_metrics_path:
        state.anchoring.status = "failed"
        return state
    
    # Prepare paths
    observed_metrics_path = f"data/synthetic/{state.pins.data_version}/observed_metrics_brand_week_region.csv"
    
    if not Path(observed_metrics_path).exists():
        state.anchoring.status = "failed"
        return state
    
    anchoring_output_dir = Path("runs") / state.run_id / "anchoring"
    anchoring_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Determine available weeks from observed data
        import pandas as pd
        obs_data = pd.read_csv(observed_metrics_path)
        available_weeks = sorted(obs_data['week_id'].unique())
        
        # Use 80/20 split if we have enough weeks, otherwise use all for training
        if len(available_weeks) >= 5:
            split_idx = int(len(available_weeks) * 0.8)
            train_weeks = available_weeks[:split_idx]
            holdout_weeks = available_weeks[split_idx:]
        else:
            # If too few weeks, use all for training and skip holdout
            train_weeks = available_weeks
            holdout_weeks = []
        
        # Run anchoring
        artifacts = run_anchoring(
            observed_metrics_path=observed_metrics_path,
            simulated_metrics_path=baseline_run.artifacts.simulated_metrics_path,
            persona_contributions_path=baseline_run.artifacts.persona_contrib_path,
            persona_version=state.pins.persona_version,
            output_dir=str(anchoring_output_dir),
            train_weeks=train_weeks,
            holdout_weeks=holdout_weeks if holdout_weeks else None
        )
        
        state.anchoring.anchoring_run_id = f"ANCHOR_{state.run_id}"
        state.anchoring.patch_path = artifacts["patch_path"]
        state.anchoring.status = "completed"
        
        # Load fit summary
        import json
        with open(artifacts["report_path"], 'r') as f:
            report = json.load(f)
            state.anchoring.fit_summary = {
                "baseline_loss": report["baseline"]["train_loss"],
                "final_loss": report["after_anchoring"]["train_loss"],
                "improvement_pct": report["improvement"]["train_loss_reduction"]
            }
        
    except Exception as e:
        state.anchoring.status = "failed"
        print(f"Warning: Anchoring failed: {e}")
    
    return state

