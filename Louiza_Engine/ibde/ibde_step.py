"""
IBDE step function - Deterministic state transition and logit computation.

Implements the four-stage pipeline:
1. Input Processing & Gating
2. State Transition
3. Utility / Logit Computation
4. Constraint Enforcement
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import warnings

from ibde.state import AgentState, EnvironmentInputs, Logits, Diagnostics
from pme.persona_schema import Persona


def ibde_step(
    state: AgentState,
    env: EnvironmentInputs,
    persona: Persona,
    timestep: int,
    brand_embeddings: Optional[np.ndarray] = None,
    return_diagnostics: bool = False
) -> Tuple[AgentState, Logits, Optional[Diagnostics]]:
    """
    Execute one IBDE step: state transition + logit computation.
    
    This is a deterministic, pure function. No randomness except via parameters.
    
    Args:
        state: Current agent state
        env: Environment inputs
        persona: Persona parameters (read-only)
        timestep: Current timestep
        brand_embeddings: Optional brand embedding matrix [B, d] for taste similarity
        return_diagnostics: Whether to return diagnostics
        
    Returns:
        Tuple of (next_state, logits, diagnostics)
    """
    # Convert to numpy for processing
    state_np = state.to_numpy()
    env_np = env.to_numpy()
    
    num_brands = len(env.prices)
    
    # Stage 1: Input Processing & Gating
    effective_prices, promo_signals, ad_signals = _process_inputs(
        state_np, env_np, persona
    )
    
    # Stage 2: State Transition
    next_state_np = _transition_state(
        state_np, effective_prices, promo_signals, ad_signals,
        env_np, persona, timestep
    )
    
    # Stage 3: Utility / Logit Computation
    purchase_logits, no_purchase_logit, diagnostics_dict = _compute_logits(
        next_state_np, effective_prices, promo_signals, ad_signals,
        env_np, persona, brand_embeddings, timestep, return_diagnostics
    )
    
    # Stage 4: Constraint Enforcement
    purchase_logits, constraint_mask = _apply_constraints(
        purchase_logits, next_state_np, env_np, persona, timestep
    )
    
    # Convert back to Pydantic models
    next_state = AgentState.from_numpy(next_state_np)
    logits = Logits(
        purchase_logits=purchase_logits.tolist(),
        no_purchase_logit=float(no_purchase_logit)
    )
    
    diagnostics = None
    if return_diagnostics:
        diagnostics_dict["constraint_mask"] = constraint_mask.tolist()
        diagnostics = Diagnostics(**diagnostics_dict)
    
    return next_state, logits, diagnostics


def _process_inputs(
    state_np: Dict[str, np.ndarray],
    env_np: Dict[str, np.ndarray],
    persona: Persona
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Stage 1: Input Processing & Gating.
    
    Normalize prices, apply feature gates, construct derived signals.
    """
    prices = env_np["prices"]
    promotions = env_np["promotions"]
    ads = env_np["ads"]
    
    # Normalize prices vs reference price
    reference_price = state_np["reference_price"][0]
    effective_prices = prices / (reference_price + 1e-8)  # Avoid division by zero
    
    # Apply feature gates
    promo_signal_gate = persona.feature_gates.promo_signal if hasattr(persona.feature_gates, 'promo_signal') else 1.0
    ad_signal_gate = persona.feature_gates.advertising_signal if hasattr(persona.feature_gates, 'advertising_signal') else 0.5
    
    promo_signals = promotions * promo_signal_gate
    ad_signals = ads * ad_signal_gate
    
    return effective_prices, promo_signals, ad_signals


def _transition_state(
    state_np: Dict[str, np.ndarray],
    effective_prices: np.ndarray,
    promo_signals: np.ndarray,
    ad_signals: np.ndarray,
    env_np: Dict[str, np.ndarray],
    persona: Persona,
    timestep: int
) -> Dict[str, np.ndarray]:
    """
    Stage 2: State Transition.
    
    Evolve latent state deterministically.
    """
    next_state = state_np.copy()
    
    # Taste drift (slow)
    taste_embedding = state_np["taste_embedding"]
    taste_drift_rate = 0.01  # Small drift
    taste_noise = np.random.RandomState(seed=timestep).normal(0, taste_drift_rate, size=taste_embedding.shape)
    next_state["taste_embedding"] = taste_embedding + taste_noise
    # Normalize to prevent explosion
    taste_norm = np.linalg.norm(next_state["taste_embedding"])
    if taste_norm > 0:
        next_state["taste_embedding"] = next_state["taste_embedding"] / (taste_norm + 1e-8)
    
    # Loyalty reinforcement (based on last choice)
    brand_loyalty = state_np["brand_loyalty"].copy()
    last_choice = state_np["last_choice"][0]
    if last_choice >= 0 and last_choice < len(brand_loyalty):
        loyalty_reinforcement = 0.05
        brand_loyalty[last_choice] = np.clip(brand_loyalty[last_choice] + loyalty_reinforcement, 0.0, 1.0)
        # Decay other brands slightly
        decay_rate = 0.01
        brand_loyalty = brand_loyalty * (1 - decay_rate)
        brand_loyalty[last_choice] = np.clip(brand_loyalty[last_choice], 0.0, 1.0)
    next_state["brand_loyalty"] = brand_loyalty
    
    # Attention decay
    attention_decay = 0.02
    attention = state_np["attention"][0]
    next_state["attention"][0] = attention * np.exp(-attention_decay)
    
    # Fatigue accumulation
    fatigue_promo = state_np["fatigue_promo"][0]
    fatigue_novelty = state_np["fatigue_novelty"][0]
    
    # Promo fatigue increases with promo exposure, decays over time
    promo_fatigue_rate = 0.1
    promo_fatigue_decay = 0.05
    next_state["fatigue_promo"][0] = fatigue_promo * (1 - promo_fatigue_decay) + np.sum(promo_signals) * promo_fatigue_rate
    next_state["fatigue_promo"][0] = np.clip(next_state["fatigue_promo"][0], 0.0, 1.0)
    
    # Novelty fatigue (simplified)
    novelty_fatigue_decay = 0.03
    next_state["fatigue_novelty"][0] = fatigue_novelty * (1 - novelty_fatigue_decay)
    
    # Memory updates
    # Ad stock decay
    ad_stock_decay = 0.1
    ad_stock = state_np["ad_stock"][0]
    ad_stock = ad_stock * (1 - ad_stock_decay) + np.sum(ad_signals) * 0.2
    next_state["ad_stock"][0] = np.clip(ad_stock, 0.0, 1.0)
    
    # Recency decay
    recency_decay = 0.1
    recency = state_np["recency"][0]
    next_state["recency"][0] = recency * (1 - recency_decay)
    
    # Reference price update (exponential moving average)
    if len(effective_prices) > 0:
        current_price_level = np.mean(effective_prices)
        reference_price = state_np["reference_price"][0]
        alpha = 0.1  # Smoothing factor
        next_state["reference_price"][0] = alpha * current_price_level + (1 - alpha) * reference_price
    
    return next_state


def _compute_logits(
    state_np: Dict[str, np.ndarray],
    effective_prices: np.ndarray,
    promo_signals: np.ndarray,
    ad_signals: np.ndarray,
    env_np: Dict[str, np.ndarray],
    persona: Persona,
    brand_embeddings: Optional[np.ndarray],
    timestep: int,
    return_diagnostics: bool
) -> Tuple[np.ndarray, float, Dict[str, List[float]]]:
    """
    Stage 3: Utility / Logit Computation.
    
    Compute utilities for each brand.
    """
    num_brands = len(effective_prices)
    brand_loyalty = state_np["brand_loyalty"]
    taste_embedding = state_np["taste_embedding"]
    attention = state_np["attention"][0]
    fatigue_promo = state_np["fatigue_promo"][0]
    ad_stock = state_np["ad_stock"][0]
    
    # Initialize logits
    purchase_logits = np.zeros(num_brands, dtype=np.float32)
    
    # Price term (negative)
    price_sensitivity = persona.behavioral_params.price_sensitivity
    price_term = -price_sensitivity * effective_prices
    
    # Promo term (positive, but reduced by fatigue)
    promo_responsiveness = persona.behavioral_params.promo_responsiveness
    promo_term = promo_responsiveness * promo_signals * (1 - fatigue_promo)
    
    # Loyalty term (positive)
    brand_loyalty_bias = persona.behavioral_params.brand_loyalty_bias
    loyalty_term = brand_loyalty_bias * brand_loyalty
    
    # Taste similarity term (if brand embeddings provided)
    taste_term = np.zeros(num_brands, dtype=np.float32)
    if brand_embeddings is not None and len(brand_embeddings) == num_brands:
        for b in range(num_brands):
            brand_emb = brand_embeddings[b]
            if len(brand_emb) == len(taste_embedding):
                similarity = np.dot(taste_embedding, brand_emb)
                taste_term[b] = similarity * attention
    
    # Ad term
    ad_term = ad_stock * 0.3 * np.ones(num_brands, dtype=np.float32)
    
    # Interaction effects
    # Price × loyalty interaction
    price_x_loyalty = persona.interaction_effects.price_x_loyalty if hasattr(persona.interaction_effects, 'price_x_loyalty') else 0.0
    price_penalty_modifier = 1.0 - price_x_loyalty * brand_loyalty
    price_term = price_term * price_penalty_modifier
    
    # Combine terms
    purchase_logits = (
        taste_term +
        price_term +
        promo_term +
        loyalty_term +
        ad_term
    )
    
    # Add controlled noise (from persona parameter)
    choice_noise = persona.behavioral_params.choice_noise
    if choice_noise > 0:
        # Use deterministic seed based on timestep for reproducibility
        rng = np.random.RandomState(seed=hash((id(state_np), timestep)) % (2**31))
        noise = rng.normal(0, choice_noise, size=num_brands)
        purchase_logits = purchase_logits + noise
    
    # No-purchase logit (baseline)
    no_purchase_logit = 0.0
    
    # Diagnostics
    diagnostics_dict = {}
    if return_diagnostics:
        diagnostics_dict = {
            "price_term": price_term.tolist(),
            "promo_term": promo_term.tolist(),
            "loyalty_term": loyalty_term.tolist()
        }
    
    return purchase_logits, no_purchase_logit, diagnostics_dict


def _apply_constraints(
    purchase_logits: np.ndarray,
    state_np: Dict[str, np.ndarray],
    env_np: Dict[str, np.ndarray],
    persona: Persona,
    timestep: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stage 4: Constraint Enforcement.
    
    Apply hard constraints: price tolerance, repeat intervals, availability.
    """
    num_brands = len(purchase_logits)
    constraint_mask = np.ones(num_brands, dtype=bool)
    
    # Price tolerance constraint
    max_price_tolerance = persona.constraints.max_price_tolerance if hasattr(persona.constraints, 'max_price_tolerance') else 2.0
    reference_price = state_np["reference_price"][0]
    prices = env_np["prices"]
    
    for b in range(num_brands):
        if prices[b] > reference_price * max_price_tolerance:
            constraint_mask[b] = False
    
    # Availability constraint
    availability = env_np["availability"]
    for b in range(num_brands):
        if availability[b] < 0.5:  # Threshold for availability
            constraint_mask[b] = False
    
    # Minimum repeat interval constraint
    min_repeat_interval = persona.constraints.min_repeat_interval_days if hasattr(persona.constraints, 'min_repeat_interval_days') else 1
    last_purchase_day = state_np["last_purchase_day"][0]
    if last_purchase_day >= 0 and min_repeat_interval > 0:
        days_since_purchase = timestep - last_purchase_day
        if days_since_purchase < min_repeat_interval:
            # Mask all brands (can't purchase yet)
            constraint_mask[:] = False
    
    # Apply mask: set masked logits to very negative value
    masked_logits = purchase_logits.copy()
    masked_logits[~constraint_mask] = -1e6
    
    return masked_logits, constraint_mask


def ibde_step_batched(
    state_batch: List[AgentState],
    env_batch: List[EnvironmentInputs],
    persona_batch: List[Persona],
    timestep: int,
    brand_embeddings: Optional[np.ndarray] = None,
    return_diagnostics: bool = False
) -> Tuple[List[AgentState], List[Logits], Optional[List[Diagnostics]]]:
    """
    Batched version of ibde_step.
    
    Processes multiple agents in parallel (vectorized where possible).
    
    Args:
        state_batch: List of agent states
        env_batch: List of environment inputs
        persona_batch: List of personas (one per agent)
        timestep: Current timestep
        brand_embeddings: Optional brand embedding matrix
        return_diagnostics: Whether to return diagnostics
        
    Returns:
        Tuple of (next_state_batch, logits_batch, diagnostics_batch)
    """
    if len(state_batch) != len(env_batch) or len(state_batch) != len(persona_batch):
        raise ValueError("Batch sizes must match")
    
    next_states = []
    logits_list = []
    diagnostics_list = []
    
    for i in range(len(state_batch)):
        next_state, logits, diagnostics = ibde_step(
            state_batch[i],
            env_batch[i],
            persona_batch[i],
            timestep,
            brand_embeddings,
            return_diagnostics
        )
        next_states.append(next_state)
        logits_list.append(logits)
        if diagnostics is not None:
            diagnostics_list.append(diagnostics)
    
    diagnostics_batch = diagnostics_list if return_diagnostics else None
    
    return next_states, logits_list, diagnostics_batch

