"""
Tests for Ground-Truth Anchoring Engine (Layer 5).

Tests enforce:
- Objective function computation
- Weight optimization
- Holdout validation
- Patch generation
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from anchoring.objective import AnchoringObjective
from anchoring.optimizer import AnchoringOptimizer
from anchoring.anchoring_runner import AnchoringRunner
from pme.pme_runner import PMERunner


def create_test_data():
    """Create test data for anchoring."""
    observed = pd.DataFrame({
        'week_id': [1, 1, 2, 2, 3, 3],
        'brand_id': ['B1', 'B2', 'B1', 'B2', 'B1', 'B2'],
        'region_id': ['R1', 'R1', 'R1', 'R1', 'R1', 'R1'],
        'transactions_obs': [100, 80, 110, 85, 105, 82],
        'revenue_obs': [100, 80, 110, 85, 105, 82],
        'confidence_weight': [0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
    })
    
    simulated = pd.DataFrame({
        'week_id': [1, 1, 2, 2, 3, 3],
        'brand_id': ['B1', 'B2', 'B1', 'B2', 'B1', 'B2'],
        'region_id': ['R1', 'R1', 'R1', 'R1', 'R1', 'R1'],
        'transactions_sim': [90, 90, 100, 90, 95, 88],
        'revenue_sim': [90, 90, 100, 90, 95, 88]
    })
    
    contributions = pd.DataFrame({
        'week_id': [1, 1, 1, 1, 2, 2, 2, 2],
        'brand_id': ['B1', 'B1', 'B2', 'B2', 'B1', 'B1', 'B2', 'B2'],
        'region_id': ['R1', 'R1', 'R1', 'R1', 'R1', 'R1', 'R1', 'R1'],
        'persona_id': ['P1', 'P2', 'P1', 'P2', 'P1', 'P2', 'P1', 'P2'],
        'transactions_sim': [50, 40, 45, 45, 55, 45, 50, 40],
        'revenue_sim': [50, 40, 45, 45, 55, 45, 50, 40]
    })
    
    return observed, simulated, contributions


def test_objective_function():
    """Test objective function computation."""
    observed, simulated, contributions = create_test_data()
    
    objective = AnchoringObjective(observed, simulated, contributions)
    
    baseline_loss = objective.compute_baseline_loss()
    assert baseline_loss > 0
    
    # Test scaling
    weights = {'P1': 0.6, 'P2': 0.4}
    scaled_metrics = objective.scale_simulated_by_weights(weights)
    assert len(scaled_metrics) > 0
    assert 'transactions_sim' in scaled_metrics.columns


def test_holdout_split():
    """Test holdout data splitting."""
    observed, simulated, contributions = create_test_data()
    
    objective = AnchoringObjective(observed, simulated, contributions)
    
    train_data, holdout_data = objective.get_holdout_split(
        train_weeks=[1, 2],
        holdout_weeks=[3]
    )
    
    assert len(train_data) > 0
    assert len(holdout_data) > 0
    assert set(train_data['week_id'].unique()) == {1, 2}
    assert set(holdout_data['week_id'].unique()) == {3}


def test_weight_optimization():
    """Test persona weight optimization."""
    observed, simulated, contributions = create_test_data()
    
    # Create a minimal PersonaSet
    pme_runner = PMERunner(data_version="test")
    personaset = pme_runner.initialize_seed_personas(num_personas=2)
    
    # Rename personas to match contributions
    personaset.personas[0].persona_id = "P1"
    personaset.personas[1].persona_id = "P2"
    
    objective = AnchoringObjective(observed, simulated, contributions)
    optimizer = AnchoringOptimizer(objective, personaset)
    
    # Optimize weights
    optimized_weights = optimizer.optimize_weights()
    
    assert len(optimized_weights) == 2
    assert "P1" in optimized_weights
    assert "P2" in optimized_weights
    
    # Weights should sum to 1.0
    total_weight = sum(optimized_weights.values())
    assert abs(total_weight - 1.0) < 1e-6


def test_anchoring_runner():
    """Test anchoring runner execution."""
    observed, simulated, contributions = create_test_data()
    
    # Create a minimal PersonaSet
    pme_runner = PMERunner(data_version="test")
    personaset = pme_runner.initialize_seed_personas(num_personas=2)
    
    # Rename personas to match contributions
    personaset.personas[0].persona_id = "P1"
    personaset.personas[1].persona_id = "P2"
    
    runner = AnchoringRunner(
        personaset=personaset,
        observed_metrics=observed,
        simulated_metrics=simulated,
        persona_contributions=contributions
    )
    
    # Run anchoring
    results = runner.run(
        train_weeks=[1, 2],
        holdout_weeks=[3]
    )
    
    assert "patch" in results
    assert "report" in results
    assert "diagnostics" in results
    
    # Check report structure
    report = results["report"]
    assert "baseline" in report
    assert "after_anchoring" in report
    assert "improvement" in report


def test_patch_generation():
    """Test patch generation."""
    observed, simulated, contributions = create_test_data()
    
    pme_runner = PMERunner(data_version="test")
    personaset = pme_runner.initialize_seed_personas(num_personas=2)
    personaset.personas[0].persona_id = "P1"
    personaset.personas[1].persona_id = "P2"
    
    runner = AnchoringRunner(
        personaset=personaset,
        observed_metrics=observed,
        simulated_metrics=simulated,
        persona_contributions=contributions
    )
    
    results = runner.run(train_weeks=[1, 2], holdout_weeks=[3])
    
    patch = results["patch"]
    assert "base_persona_version" in patch
    assert "updated_persona_version" in patch
    assert "parameter_updates" in patch


def test_save_results():
    """Test saving anchoring results."""
    observed, simulated, contributions = create_test_data()
    
    pme_runner = PMERunner(data_version="test")
    personaset = pme_runner.initialize_seed_personas(num_personas=2)
    personaset.personas[0].persona_id = "P1"
    personaset.personas[1].persona_id = "P2"
    
    runner = AnchoringRunner(
        personaset=personaset,
        observed_metrics=observed,
        simulated_metrics=simulated,
        persona_contributions=contributions
    )
    
    results = runner.run(train_weeks=[1, 2], holdout_weeks=[3])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner.save_results(results, tmpdir)
        
        assert Path(tmpdir) / "anchoring_patch.json"
        assert Path(tmpdir) / "anchoring_report.json"
        assert Path(tmpdir) / "anchoring_diagnostics.json"
        assert Path(tmpdir) / "anchored_metrics_brand_week_region.csv"

