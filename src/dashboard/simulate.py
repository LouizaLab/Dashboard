"""
Simulation wrapper for what-if scenarios
Wraps the Phase 3 engine for counterfactual simulations
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from models_phase3 import PopulationSimulator, Agent, Environment
    from models_phase2 import BehavioralDynamicEngine
    from train_phase2 import load_phase1_models
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False


def run_counterfactual_simulation(base_trajectories: pd.DataFrame,
                                 price_multiplier: float = 1.0,
                                 sugar_adjustment: float = 0.0,
                                 marketing_exposure: float = 1.0,
                                 n_agents: int = 10,
                                 n_days: int = 30) -> pd.DataFrame:
    """
    Run a counterfactual simulation with modified parameters
    
    Args:
        base_trajectories: Baseline simulation data
        price_multiplier: Price adjustment (1.0 = no change, 1.1 = +10%)
        sugar_adjustment: Sugar content adjustment (additive)
        marketing_exposure: Marketing exposure multiplier (1.0 = baseline)
        n_agents: Number of agents to simulate
        n_days: Number of days to simulate
    
    Returns:
        DataFrame with counterfactual trajectories
    """
    if not ENGINE_AVAILABLE:
        # Fallback: modify base trajectories
        return _modify_base_trajectories(
            base_trajectories, 
            price_multiplier, 
            sugar_adjustment, 
            marketing_exposure
        )
    
    # TODO: Full simulation would require loading models and running PopulationSimulator
    # For now, use simplified modification approach
    return _modify_base_trajectories(
        base_trajectories,
        price_multiplier,
        sugar_adjustment,
        marketing_exposure
    )


def _modify_base_trajectories(base_trajectories: pd.DataFrame,
                              price_multiplier: float,
                              sugar_adjustment: float,
                              marketing_exposure: float) -> pd.DataFrame:
    """
    Modify base trajectories to simulate counterfactual
    This is a simplified approach - full simulation would use the engine
    """
    cf_trajectories = base_trajectories.copy()
    
    # Price effect: higher price -> lower intent (price elasticity ~ -0.5)
    if 'price' in cf_trajectories.columns and 'intent_value' in cf_trajectories.columns:
        price_change_pct = (price_multiplier - 1.0) * 100
        # Apply price elasticity
        elasticity = -0.5  # Typical price elasticity
        intent_change = elasticity * price_change_pct / 100
        cf_trajectories['intent_value'] = cf_trajectories['intent_value'] * (1 + intent_change)
        cf_trajectories['price'] = cf_trajectories['price'] * price_multiplier
    
    # Sugar effect: adjust based on segment preferences
    # Higher sugar -> may increase intent for some segments
    if sugar_adjustment != 0 and 'intent_value' in cf_trajectories.columns:
        # Simple model: sugar adjustment affects intent
        sugar_effect = sugar_adjustment * 0.01  # Small effect
        cf_trajectories['intent_value'] = cf_trajectories['intent_value'] + sugar_effect
    
    # Marketing exposure: increases awareness -> increases intent
    if marketing_exposure != 1.0 and 'intent_value' in cf_trajectories.columns:
        exposure_effect = (marketing_exposure - 1.0) * 0.1  # 10% lift per 1x exposure
        cf_trajectories['intent_value'] = cf_trajectories['intent_value'] * (1 + exposure_effect)
    
    # Clamp intent values to [0, 1]
    if 'intent_value' in cf_trajectories.columns:
        cf_trajectories['intent_value'] = cf_trajectories['intent_value'].clip(0, 1)
    
    return cf_trajectories


def compare_baseline_vs_counterfactual(baseline: pd.DataFrame,
                                      counterfactual: pd.DataFrame) -> Dict:
    """
    Compare baseline vs counterfactual and compute deltas
    """
    if baseline.empty or counterfactual.empty:
        return {}
    
    baseline_metrics = {
        'avg_intent': baseline['intent_value'].mean() if 'intent_value' in baseline.columns else 0,
        'total_interactions': len(baseline)
    }
    
    cf_metrics = {
        'avg_intent': counterfactual['intent_value'].mean() if 'intent_value' in counterfactual.columns else 0,
        'total_interactions': len(counterfactual)
    }
    
    deltas = {
        'intent_delta': cf_metrics['avg_intent'] - baseline_metrics['avg_intent'],
        'intent_delta_pct': ((cf_metrics['avg_intent'] - baseline_metrics['avg_intent']) / baseline_metrics['avg_intent'] * 100) if baseline_metrics['avg_intent'] > 0 else 0,
        'interactions_delta': cf_metrics['total_interactions'] - baseline_metrics['total_interactions'],
        'interactions_delta_pct': ((cf_metrics['total_interactions'] - baseline_metrics['total_interactions']) / baseline_metrics['total_interactions'] * 100) if baseline_metrics['total_interactions'] > 0 else 0
    }
    
    return {
        'baseline': baseline_metrics,
        'counterfactual': cf_metrics,
        'deltas': deltas
    }

