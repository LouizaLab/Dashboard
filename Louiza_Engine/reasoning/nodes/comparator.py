"""
Node I: Comparator

Computes scenario comparisons and uncertainty metrics.
"""

import pandas as pd
import numpy as np
from reasoning.state import ReasoningState


def comparator(state: ReasoningState) -> ReasoningState:
    """
    Compare scenarios and compute uncertainty.
    
    Computes:
    - Baseline vs scenario deltas
    - Persona contribution deltas
    - Uncertainty intervals
    """
    comparisons = []
    
    # Find baseline run
    baseline_run = next(
        (r for r in state.runs if r.scenario_id == "S0_baseline" and r.status == "completed"),
        None
    )
    
    if not baseline_run or not baseline_run.artifacts.simulated_metrics_path:
        return state
    
    # Load baseline metrics
    baseline_metrics = pd.read_csv(baseline_run.artifacts.simulated_metrics_path)
    
    # Compare each counterfactual scenario
    for scenario in state.scenario_specs:
        if scenario.kind != "counterfactual":
            continue
        
        # Find runs for this scenario
        scenario_runs = [r for r in state.runs if r.scenario_id == scenario.scenario_id and r.status == "completed"]
        
        if not scenario_runs:
            continue
        
        # Aggregate across runs for uncertainty
        all_metrics = []
        for run in scenario_runs:
            if run.artifacts.simulated_metrics_path:
                metrics = pd.read_csv(run.artifacts.simulated_metrics_path)
                all_metrics.append(metrics)
        
        if not all_metrics:
            continue
        
        # Compute mean and std across runs
        scenario_metrics = pd.concat(all_metrics)
        scenario_agg = scenario_metrics.groupby(['week_id', 'brand_id', 'region_id']).agg({
            'transactions_sim': ['mean', 'std'],
            'revenue_sim': ['mean', 'std']
        }).reset_index()
        
        # Flatten column names
        scenario_agg.columns = ['week_id', 'brand_id', 'region_id', 'transactions_mean', 'transactions_std', 'revenue_mean', 'revenue_std']
        
        # Merge with baseline
        baseline_agg = baseline_metrics.groupby(['week_id', 'brand_id', 'region_id']).agg({
            'transactions_sim': 'mean',
            'revenue_sim': 'mean'
        }).reset_index()
        
        merged = pd.merge(
            baseline_agg,
            scenario_agg,
            on=['week_id', 'brand_id', 'region_id'],
            how='inner'
        )
        
        # Compute deltas
        merged['transactions_delta_pct'] = ((merged['transactions_mean'] - merged['transactions_sim']) / merged['transactions_sim']) * 100
        merged['revenue_delta_pct'] = ((merged['revenue_mean'] - merged['revenue_sim']) / merged['revenue_sim']) * 100
        
        comparison = {
            "scenario_id": scenario.scenario_id,
            "baseline_id": "S0_baseline",
            "mean_transactions_delta_pct": float(merged['transactions_delta_pct'].mean()),
            "mean_revenue_delta_pct": float(merged['revenue_delta_pct'].mean()),
            "transactions_uncertainty_std": float(merged['transactions_std'].mean()),
            "revenue_uncertainty_std": float(merged['revenue_std'].mean())
        }
        
        comparisons.append(comparison)
    
    state.analysis.scenario_comparisons = comparisons
    
    # Compute overall uncertainty
    if comparisons:
        state.analysis.uncertainty = {
            "mean_transactions_std": np.mean([c["transactions_uncertainty_std"] for c in comparisons]),
            "mean_revenue_std": np.mean([c["revenue_uncertainty_std"] for c in comparisons])
        }
    
    return state

