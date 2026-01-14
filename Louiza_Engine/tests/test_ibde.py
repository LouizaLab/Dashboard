"""
Tests for Individual Behavioral Dynamics Engine (Layer 3).

Tests enforce:
- Determinism (same inputs = same outputs)
- State transition correctness
- Logit computation
- Constraint enforcement
- No persona branching
"""

import pytest
import numpy as np

from ibde.state import AgentState, EnvironmentInputs, Logits
from ibde.ibde_step import ibde_step, ibde_step_batched
from pme.persona_schema import (
    Persona, PopulationWeight, BehavioralParams, StatePriors,
    TasteEmbedding, Lineage, Explainability, FeatureGates, Constraints
)


def create_test_persona(
    price_sensitivity=1.5,
    promo_responsiveness=1.2,
    habit_strength=1.0,
    brand_loyalty_bias=1.0,
    choice_noise=0.1,
    persona_id="test_persona"
) -> Persona:
    """Helper to create test persona."""
    return Persona(
        persona_id=persona_id,
        population_weight=PopulationWeight(global_weight=1.0),
        behavioral_params=BehavioralParams(
            price_sensitivity=price_sensitivity,
            promo_responsiveness=promo_responsiveness,
            habit_strength=habit_strength,
            brand_loyalty_bias=brand_loyalty_bias,
            choice_noise=choice_noise
        ),
        state_priors=StatePriors(
            taste_embedding=TasteEmbedding(
                mean=[0.1, 0.2, 0.3],
                cov=[[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]
            )
        ),
        lineage=Lineage(data_version="test"),
        explainability=Explainability(human_label="Test Persona")
    )


def test_determinism():
    """Test that IBDE is deterministic given same inputs."""
    # Use choice_noise=0 for true determinism
    persona = create_test_persona(choice_noise=0.0)
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.5, 0.3, 0.2]
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.1, 0.9],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.5, 0.0]
    )
    
    # Run twice with same inputs
    next_state1, logits1, _ = ibde_step(state, env, persona, timestep=1)
    next_state2, logits2, _ = ibde_step(state, env, persona, timestep=1)
    
    # Should be identical (within floating point precision)
    assert abs(next_state1.attention - next_state2.attention) < 1e-6
    assert np.allclose(logits1.purchase_logits, logits2.purchase_logits, atol=1e-6)


def test_state_transition():
    """Test that state transitions correctly."""
    persona = create_test_persona()
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.5, 0.3, 0.2],
        attention=1.0,
        reference_price=1.0
    )
    
    env = EnvironmentInputs(
        prices=[1.2, 1.3, 1.1],  # Different prices to trigger reference price update
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.5, 0.0]
    )
    
    next_state, _, _ = ibde_step(state, env, persona, timestep=1)
    
    # Attention should decay
    assert next_state.attention < state.attention
    
    # Reference price should update (toward mean of prices)
    assert abs(next_state.reference_price - state.reference_price) > 1e-6


def test_logit_computation():
    """Test that logits are computed correctly."""
    persona = create_test_persona(price_sensitivity=2.0, promo_responsiveness=1.5)
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.8, 0.1, 0.1]  # Strong loyalty to brand 0
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.2, 0.8],  # Brand 2 is cheaper
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.5]  # Brand 2 has promo
    )
    
    _, logits, diagnostics = ibde_step(state, env, persona, timestep=1, return_diagnostics=True)
    
    # Should have logits for all brands
    assert len(logits.purchase_logits) == 3
    
    # Check diagnostics
    assert diagnostics is not None
    assert len(diagnostics.price_term) == 3
    assert len(diagnostics.promo_term) == 3
    assert len(diagnostics.loyalty_term) == 3


def test_price_sensitivity():
    """Test that price sensitivity affects logits."""
    persona_low = create_test_persona(price_sensitivity=0.5)
    persona_high = create_test_persona(price_sensitivity=3.0)
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34]
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.5, 1.0],  # Brand 1 is more expensive
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.0]
    )
    
    _, logits_low, _ = ibde_step(state, env, persona_low, timestep=1)
    _, logits_high, _ = ibde_step(state, env, persona_high, timestep=1)
    
    # High price sensitivity should penalize expensive brand more
    # Brand 1 should have lower logit with high sensitivity
    assert logits_high.purchase_logits[1] < logits_low.purchase_logits[1]


def test_promo_responsiveness():
    """Test that promo responsiveness affects logits."""
    persona_low = create_test_persona(promo_responsiveness=0.5)
    persona_high = create_test_persona(promo_responsiveness=2.5)
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34]
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.0, 1.0],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.5, 0.0]  # Brand 1 has promo
    )
    
    _, logits_low, _ = ibde_step(state, env, persona_low, timestep=1)
    _, logits_high, _ = ibde_step(state, env, persona_high, timestep=1)
    
    # High promo responsiveness should boost brand 1 more
    assert logits_high.purchase_logits[1] > logits_low.purchase_logits[1]


def test_constraint_price_tolerance():
    """Test price tolerance constraint."""
    persona = create_test_persona()
    persona.constraints = Constraints(max_price_tolerance=1.2)
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34],
        reference_price=1.0
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.3, 0.9],  # Brand 1 exceeds tolerance (1.3 > 1.0 * 1.2)
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.0]
    )
    
    _, logits, diagnostics = ibde_step(state, env, persona, timestep=1, return_diagnostics=True)
    
    # Brand 1 should be masked
    assert diagnostics.constraint_mask[1] == False
    # Masked logit should be very negative
    assert logits.purchase_logits[1] < -1e5


def test_constraint_availability():
    """Test availability constraint."""
    persona = create_test_persona()
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34]
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.0, 1.0],
        availability=[1.0, 0.3, 1.0],  # Brand 1 has low availability
        promotions=[0.0, 0.0, 0.0]
    )
    
    _, logits, diagnostics = ibde_step(state, env, persona, timestep=1, return_diagnostics=True)
    
    # Brand 1 should be masked
    assert diagnostics.constraint_mask[1] == False


def test_batched_execution():
    """Test batched execution."""
    persona1 = create_test_persona(price_sensitivity=1.0)
    persona2 = create_test_persona(price_sensitivity=2.0)
    
    state1 = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.5, 0.3, 0.2]
    )
    state2 = AgentState(
        taste_embedding=[0.2, 0.1, 0.3],
        brand_loyalty=[0.4, 0.4, 0.2]
    )
    
    env1 = EnvironmentInputs(
        prices=[1.0, 1.1, 0.9],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.5, 0.0]
    )
    env2 = EnvironmentInputs(
        prices=[1.0, 1.1, 0.9],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.5, 0.0]
    )
    
    # Batched execution
    next_states, logits_list, _ = ibde_step_batched(
        [state1, state2],
        [env1, env2],
        [persona1, persona2],
        timestep=1
    )
    
    assert len(next_states) == 2
    assert len(logits_list) == 2
    
    # Compare with individual execution
    next_state1_ind, logits1_ind, _ = ibde_step(state1, env1, persona1, timestep=1)
    next_state2_ind, logits2_ind, _ = ibde_step(state2, env2, persona2, timestep=1)
    
    # Should match
    assert abs(next_states[0].attention - next_state1_ind.attention) < 1e-6
    assert abs(next_states[1].attention - next_state2_ind.attention) < 1e-6
    assert np.allclose(logits_list[0].purchase_logits, logits1_ind.purchase_logits, atol=1e-6)
    assert np.allclose(logits_list[1].purchase_logits, logits2_ind.purchase_logits, atol=1e-6)


def test_no_persona_branching():
    """Test that IBDE doesn't branch on persona identity."""
    # Create two different personas
    persona1 = create_test_persona(price_sensitivity=1.0, persona_id="persona_01")
    persona2 = create_test_persona(price_sensitivity=2.0, persona_id="persona_02")
    
    # Same state and environment
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34]
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.2, 1.0],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.0]
    )
    
    # Run with both personas
    _, logits1, _ = ibde_step(state, env, persona1, timestep=1)
    _, logits2, _ = ibde_step(state, env, persona2, timestep=1)
    
    # Differences should come only from parameters, not persona ID
    # Higher price sensitivity should penalize expensive brand more
    assert logits2.purchase_logits[1] < logits1.purchase_logits[1]


def test_loyalty_reinforcement():
    """Test that loyalty reinforces based on last choice."""
    from ibde.state import MemoryState
    
    persona = create_test_persona()
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.5, 0.3, 0.2],
        memory=MemoryState(last_choice=0)  # Last chose brand 0
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.0, 1.0],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.0]
    )
    
    next_state, _, _ = ibde_step(state, env, persona, timestep=1)
    
    # Brand 0 loyalty should increase
    assert next_state.brand_loyalty[0] > state.brand_loyalty[0]


def test_fatigue_accumulation():
    """Test that promo fatigue accumulates."""
    from ibde.state import FatigueState
    
    persona = create_test_persona()
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34],
        fatigue=FatigueState(promo=0.0)
    )
    
    env = EnvironmentInputs(
        prices=[1.0, 1.0, 1.0],
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.8, 0.0]  # Strong promo
    )
    
    next_state, _, _ = ibde_step(state, env, persona, timestep=1)
    
    # Fatigue should increase
    assert next_state.fatigue.promo > state.fatigue.promo


def test_reference_price_update():
    """Test that reference price updates."""
    persona = create_test_persona()
    
    state = AgentState(
        taste_embedding=[0.1, 0.2, 0.3],
        brand_loyalty=[0.33, 0.33, 0.34],
        reference_price=1.0
    )
    
    env = EnvironmentInputs(
        prices=[1.2, 1.2, 1.2],  # Higher prices
        availability=[1.0, 1.0, 1.0],
        promotions=[0.0, 0.0, 0.0]
    )
    
    next_state, _, _ = ibde_step(state, env, persona, timestep=1)
    
    # Reference price should move toward current price level
    assert next_state.reference_price > state.reference_price

