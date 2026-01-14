"""
Tests for Reasoning & Hypothesis Orchestration Layer (Layer 7).
"""

import pytest
import pandas as pd
from pathlib import Path
from reasoning.state import ReasoningState, Request, Pins, Hypothesis, ScenarioSpec
from reasoning.nodes.parse_request import parse_request
from reasoning.nodes.generate_hypotheses import generate_hypotheses
from reasoning.nodes.scenario_builder import scenario_builder
from reasoning.nodes.run_planner import run_planner


def test_parse_request():
    """Test ParseRequest node."""
    state = ReasoningState(
        request=Request(user_prompt="What happens if we launch a promo in US_South for 8 weeks?")
    )
    
    state = parse_request(state)
    
    assert state.request.constraints.time_horizon_weeks == 8
    assert len(state.request.constraints.regions) > 0


def test_generate_hypotheses():
    """Test GenerateHypotheses node."""
    state = ReasoningState(
        request=Request(user_prompt="What happens if we launch a promo?")
    )
    
    state = generate_hypotheses(state)
    
    assert len(state.hypotheses) > 0
    assert all(isinstance(h, Hypothesis) for h in state.hypotheses)
    assert all(h.acceptance_criteria for h in state.hypotheses)


def test_scenario_builder():
    """Test ScenarioBuilder node."""
    state = ReasoningState(
        request=Request(user_prompt="What happens if we launch a promo?")
    )
    state.request.constraints.time_horizon_weeks = 12
    
    state = scenario_builder(state)
    
    assert len(state.scenario_specs) >= 2  # Baseline + at least one counterfactual
    assert any(s.kind == "baseline" for s in state.scenario_specs)
    assert any(s.kind == "counterfactual" for s in state.scenario_specs)


def test_run_planner():
    """Test RunPlanner node."""
    state = ReasoningState(
        request=Request(
            user_prompt="What happens if we launch a promo?",
            simulation_budget={
                "max_scenarios": 3,
                "max_runs": 6,
                "max_agents": 5000
            }
        )
    )
    state.request.constraints.time_horizon_weeks = 12
    
    # Create scenarios first
    state = scenario_builder(state)
    state = run_planner(state)
    
    assert len(state.runs) > 0
    assert all(r.status == "pending" for r in state.runs)
    assert all(r.num_agents <= state.request.simulation_budget.max_agents for r in state.runs)


def test_reasoning_state_serialization():
    """Test that ReasoningState can be serialized."""
    state = ReasoningState(
        request=Request(user_prompt="Test prompt"),
        run_id="test_run_001"
    )
    
    # Should be able to convert to dict
    state_dict = state.model_dump()
    assert "request" in state_dict
    assert "run_id" in state_dict
    
    # Should be able to recreate from dict
    state_recreated = ReasoningState(**state_dict)
    assert state_recreated.run_id == "test_run_001"


def test_hypothesis_acceptance_criteria():
    """Test hypothesis acceptance criteria structure."""
    from reasoning.state import AcceptanceCriteria
    
    criteria = AcceptanceCriteria(
        metric="transactions",
        delta_pct_min=0.05,
        confidence_min=0.7
    )
    
    assert criteria.metric == "transactions"
    assert criteria.delta_pct_min == 0.05
    assert criteria.confidence_min == 0.7


def test_scenario_spec_interventions():
    """Test scenario spec intervention structure."""
    from reasoning.state import Intervention
    
    intervention = Intervention(
        type="promo",
        brand_id="BRAND_01",
        intensity=0.7,
        start_week=3,
        end_week=6
    )
    
    assert intervention.type == "promo"
    assert intervention.intensity == 0.7
    assert intervention.start_week == 3
    assert intervention.end_week == 6

