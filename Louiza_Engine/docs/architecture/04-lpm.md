# Layer 4: Large Population Model (LPM)

## Purpose

The Large Population Model (LPM) is the **population-scale simulation runtime** of the Louiza Engine.

LPM is responsible for:
- instantiating large numbers of agents from personas
- executing the per-timestep simulation loop
- sampling actions from IBDE outputs
- updating the market environment
- aggregating micro-level behavior into macro-level metrics

LPM defines **scale, orchestration, and aggregation**, but does not define behavior.

---

## Non-Goals (Explicit)

LPM must **not**:

- implement behavioral logic (IBDE responsibility)
- modify persona definitions or parameters
- perform anchoring or calibration
- call PME during simulation
- query the Data Engine per timestep
- call LLMs during execution
- mutate agent state outside IBDE

Violations break determinism and reproducibility (see `99-invariants.md`).

---

## Inputs

LPM consumes **versioned, immutable inputs**:

### 1. PersonaSet
- Persona definitions and weights from PME
- Fixed for the duration of a simulation run

### 2. Scenario Configuration
Defines interventions and environment evolution:

```jsonc
{
  "scenario_id": "bk_new_chicken_2026q2",
  "time_horizon_weeks": 12,
  "interventions": [
    {
      "type": "price_change",
      "brand_id": "BK",
      "region_id": "US_South",
      "delta_pct": -0.05,
      "start_week": 3
    }
  ]
}


3. Environment Schedules

From the Data Engine (synthetic or real):

price schedules

promotion schedules

availability schedules

4. Simulation Controls

number of agents N

random seed(s)

timestep granularity

Outputs

LPM produces aggregated, replayable outputs:

1. Time-Series Metrics

transactions

revenue (proxy)

brand share

frequency

Keyed by:

week_id × brand_id × region_id

2. Persona Contribution Tables

how much each persona contributed to each metric

3. Diagnostics

constraint hit rates

action distribution entropy

effective price distributions

4. Run Metadata

persona version

IBDE version

scenario hash

random seeds

Core Data Structures
Agent Registry (Batched)

state_batch: agent latent states (owned by IBDE)

persona_idx: agent → persona mapping

static_features: region, channel, cohort

rng_state: per-agent RNG state (if needed)

Environment State

per-brand vectors:

prices

promotions

availability

context:

week

seasonality

intervention schedules

Aggregators

streaming counters and sums

keyed by brand / region / persona

Execution Model (Authoritative)
Logical Order (Per Timestep)

For timestep t = 1..T:

Build environment inputs for all agents

Call IBDE:

input: (state_t, env_t, persona_params)

output: (state_{t+1}, logits_t)

Sample actions from logits (LPM-owned randomness)

Update environment and schedules

Record events and update aggregates

This order must never be changed.

Parallelism Model

Execution is parallel across agents

IBDE runs as a vectorized kernel

Sampling runs as a vectorized kernel

Aggregation runs as streaming reductions

Logical sequencing does not imply serial execution.

Action Sampling

LPM owns all stochasticity.

Recommended sampling methods:

softmax with temperature

Gumbel-softmax (optional)

top-k filtering (optional, POC-safe)

Sampling must:

respect constraint masks

be reproducible from seeds

Environment Evolution

Environment state evolves via:

scenario interventions

scheduled changes

endogenous effects (optional, POC-light)

Environment updates must be:

deterministic

explicitly scheduled

versioned with scenario config

Aggregation Logic

Aggregation must:

occur every timestep

avoid storing per-agent logs at scale

produce time-series tables directly

Persona contribution must be computed by:

attributing each event to the agent’s persona

Determinism & Replay

A simulation run is replayable if:

persona version is fixed

IBDE version is fixed

scenario config is fixed

seeds are fixed

LPM must record all of the above.

Failure Modes & Guardrails

Reject missing persona mappings

Reject environment schema mismatches

Fail loudly on NaNs

Reject dynamic persona mutation

Reject mid-run data refresh

Integration With Other Layers
IBDE

Called every timestep

Returns updated state + logits

Data Engine

Supplies environment schedules

Not queried per timestep

Anchoring

Consumes LPM aggregates

Never called during execution

One-Line Canonical Summary

LPM is the scalable simulation runtime that instantiates agents from personas, executes the IBDE-driven timestep loop, samples actions, updates the environment, and aggregates outcomes into market-level metrics.


