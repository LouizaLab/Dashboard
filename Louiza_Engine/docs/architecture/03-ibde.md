# Layer 3: Individual Behavioral Dynamics Engine (IBDE)

## Purpose

The Individual Behavioral Dynamics Engine (IBDE) is the **single-agent behavioral execution core** of the Louiza Engine.

IBDE is responsible for:
- evolving an agent’s internal latent state over time
- computing decision utilities (logits) at each timestep

IBDE does **not** sample actions, manage populations, or aggregate outcomes.  
It operates as a **pure, deterministic state-transition and scoring function**.

---

## Non-Goals (Explicit)

IBDE must **not**:

- Sample actions or introduce randomness (except controlled noise via parameters)
- Aggregate across agents
- Modify personas
- Query the Data Engine
- Call LLMs
- Perform anchoring or calibration
- Branch logic on persona identity

Any violation breaks determinism and scalability (see `99-invariants.md`).

---

## Inputs

IBDE executes **per agent, per timestep**, but is implemented in **batched form**.

### 1. Agent State (`state_t`)

Mutable latent state owned by IBDE:

```jsonc
{
  "taste_embedding": [d],
  "brand_loyalty": [B],
  "habit_strength": [1],
  "reference_price": [1],
  "attention": [1],
  "fatigue": {
    "promo": [1],
    "novelty": [1]
  },
  "memory": {
    "ad_stock": [1],
    "last_choice": [1],
    "recency": [1]
  },
  "schedule": {
    "last_purchase_day": [1]
  }
}
State is updated only by IBDE.


2. Environment Inputs (env_t)

Read-only signals provided by LPM:

{
  "prices": [B],
  "availability": [B],
  "promotions": [B],
  "ads": [B],
  "context": {
    "week_id": [1],
    "season": [1],
    "daypart": [1]
  }
}


3. Persona Parameters (persona_params)

Immutable parameters provided by PME:

behavioral_params

feature_gates

interaction_effects

constraints

IBDE must treat these as read-only.

Outputs
1. Updated Agent State (state_{t+1})

Same schema as state_t, updated deterministically.

2. Decision Logits (logits_t)

Utilities over available actions (e.g., brands):

{
  "purchase_logits": [B],
  "no_purchase_logit": [1]
}


These logits are consumed by LPM for sampling.

3. Optional Diagnostics (Bounded)
{
  "price_term": [B],
  "promo_term": [B],
  "loyalty_term": [B],
  "constraint_mask": [B]
}


Diagnostics are optional, size-bounded, and used only for debugging or anchoring analysis.

Execution Model (Per Timestep)

IBDE executes the following four-stage pipeline at each timestep.

Stage 1: Input Processing & Gating

Raw environment inputs are transformed into persona-conditioned signals:

Normalize prices vs reference price

Apply feature gates

Construct derived signals

Example:

effective_price[b] = price[b] / reference_price
promo_signal[b] = promotions[b] * feature_gates.promo
ad_signal[b] = ads[b] * feature_gates.advertising


No state updates occur in this stage.

Stage 2: State Transition

Latent state variables evolve deterministically:

Taste drift (slow)

Loyalty reinforcement

Attention decay

Fatigue accumulation

Memory updates

Example:

attention_{t+1} = attention_t * exp(-attention_decay)
fatigue_{t+1} = fatigue_t + fatigue_rate * promo_signal


All coefficients come from behavioral_params.

Stage 3: Utility / Logit Computation

For each action (e.g., brand b):

U_b =
  + taste_similarity(taste_embedding, brand_embedding[b])
  - price_sensitivity * effective_price[b]
  + promo_responsiveness * promo_signal[b]
  + brand_loyalty_bias * brand_loyalty[b]
  - fatigue_penalty[b]
  + ε


Interaction effects are applied multiplicatively or additively:

price_penalty *= (1 - price_x_loyalty * brand_loyalty[b])


IBDE outputs logits only, never sampled actions.

Stage 4: Constraint Enforcement

Hard constraints are applied:

Mask actions exceeding price tolerance

Enforce minimum repeat intervals

Respect availability constraints

Masked logits are returned to LPM.

Determinism Guarantees

IBDE must be deterministic given:

(state_t, env_t, persona_params, seed)


Forbidden:

hidden randomness

external state

time-dependent side effects

Vectorization & Performance Requirements

IBDE must support batched execution

No persona-based branching

All operations must be tensorizable

No Python loops in inner kernels

Persona differences are expressed only via parameters.

Interface Contract (Conceptual)
def ibde_step(
    state_batch,
    env_batch,
    persona_params_batch,
    timestep,
    rng_seed=None
) -> (next_state_batch, logits_batch, diagnostics):
    ...

Integration With Other Layers
PME

Supplies persona parameters

Never invoked at runtime

LPM

Calls IBDE every timestep

Samples actions from logits

Owns stochasticity and aggregation

Anchoring

Never calls IBDE

May adjust allowed persona parameters between runs

Failure Modes & Guardrails

Reject missing or malformed state

Reject persona branching

Reject stochastic sampling

Fail loudly on NaNs or unstable updates

One-Line Canonical Summary

IBDE is a deterministic, persona-parameterized state machine that evolves individual agent state and computes choice utilities at each timestep, forming the behavioral core of the Louiza Engine.