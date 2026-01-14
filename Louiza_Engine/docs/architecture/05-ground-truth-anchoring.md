# Layer 5: Ground-Truth Anchoring Engine

## Purpose

The Ground-Truth Anchoring Engine (Anchoring) is the **outer-loop calibration layer** of the Louiza Engine.

Its responsibility is to align simulated outputs from the Large Population Model (LPM) with observed market data provided by the Data Engine, while preserving:

- behavioral stability
- interpretability
- reproducibility
- uncertainty awareness

Anchoring operates **between simulation runs**, never inside the per-timestep loop.

---

## Non-Goals (Explicit)

Anchoring must **not**:

- run inside the IBDE–LPM timestep loop
- modify agent latent state
- introduce new personas
- override behavioral dynamics
- generate forecasts independently
- call LLMs for numerical estimation
- backfill or revise past simulation trajectories

Violations constitute architectural failure (see `99-invariants.md`).

---

## Anchoring Scope (POC)

For the POC, anchoring focuses on **aggregate alignment**, not micro-level fitting.

### Anchoring Targets (MVP)

Anchoring is performed on the following metrics:

- `transactions`
- `revenue` (or revenue proxy)

### Aggregation Level (Authoritative)

week_id × brand_id × region_id



Anchoring at finer granularity is explicitly out of scope for the POC.

---

## Inputs

Anchoring consumes **versioned outputs** from upstream layers.

### 1. Observed Metrics (Data Engine)

```text
observed_metrics_brand_week_region
----------------------------------
week_id
brand_id
region_id
transactions_obs
revenue_obs
confidence_weight


confidence_weight encodes trust, sample size, or noise

Missing rows are allowed and must be masked

2. Simulated Metrics (LPM)
simulated_metrics_brand_week_region
-----------------------------------
week_id
brand_id
region_id
transactions_sim
revenue_sim

3. Persona Contribution Table (Required)
persona_contributions
---------------------
week_id
brand_id
region_id
persona_id
transactions_sim
revenue_sim


This table enables persona-level calibration and diagnostics.

4. Persona Calibration Hooks (PME Output)

From each persona definition:

anchor_targets

adjustable_params

regularization_strength

Anchoring may only modify parameters explicitly declared here.

Outputs

Anchoring produces versioned calibration artifacts:

1. Persona Parameter Patch
{
  "base_persona_version": "PersonaSet_v1",
  "updated_persona_version": "PersonaSet_v2",
  "parameter_updates": {
    "persona_07_value_loyalist": {
      "population_weight.global": 0.16
    }
  }
}


No other parameters may be changed.

2. Anchoring Report

Must include:

loss before vs after

parameter deltas

stability assessment

holdout performance

drift flags (if any)

3. Uncertainty & Diagnostics

residual distributions

persona-level contribution error

entropy / identifiability metrics

Calibration Parameters (POC Rules)
Primary Adjustable Parameters (Required)

population_weight.global

population_weight.by_region

These are the safest and highest-leverage parameters.

Secondary Adjustable Parameter (Optional)

Allow at most one behavioral parameter globally or per persona:

price_sensitivity or

promo_responsiveness

Never both in the POC.

Objective Function (POC)

Anchoring minimizes a regularized error objective:

𝐿
=
∑
𝑤
,
𝑏
,
𝑟
[
𝛼
(
𝑇
𝑤
,
𝑏
,
𝑟
𝑜
𝑏
𝑠
−
𝑇
𝑤
,
𝑏
,
𝑟
𝑠
𝑖
𝑚
)
2
+
𝛽
(
𝑅
𝑤
,
𝑏
,
𝑟
𝑜
𝑏
𝑠
−
𝑅
𝑤
,
𝑏
,
𝑟
𝑠
𝑖
𝑚
)
2
]
+
𝜆
∥
𝜃
−
𝜃
0
∥
2
L=
w,b,r
∑
	​

[α(T
w,b,r
obs
	​

−T
w,b,r
sim
	​

)
2
+β(R
w,b,r
obs
	​

−R
w,b,r
sim
	​

)
2
]+λ∥θ−θ
0
	​

∥
2

Where:

𝑇
T = transactions

𝑅
R = revenue

𝜃
θ = adjustable parameters

𝜆
λ = persona-specific regularization strength

Recommended POC values:

α = 1.0

β = 0.5

λ = 0.1

Optimization Strategy (POC)
Step 1: Persona Weight Calibration (Required)

Constrained optimization:

weights ≥ 0

weights sum to 1 (globally and per region)

Methods:

projected gradient descent

quadratic programming

This step alone should show visible improvement.

Step 2: Optional Behavioral Parameter Calibration

Adjust one parameter only

Strong regularization

Abort if holdout performance degrades

Validation & Safety Checks
Holdout Validation (Required)

Fit on early window (e.g., weeks 1–8)

Validate on later window (e.g., weeks 9–10)

Anchoring must fail if:

training loss improves but holdout worsens materially

Stability Checks

Fail anchoring if:

persona weights oscillate across runs

parameters hit hard bounds

identifiability collapses (many params explain same error)

Drift Detection & PME Triggering

Anchoring must flag drift when:

residuals remain large after allowed calibration

residuals cluster coherently across time/region

repeated anchoring attempts fail to converge

In such cases:

no further calibration is applied

PME reevaluation is recommended

Anchoring must never force-fit by expanding parameter freedom.

Execution Model

Anchoring executes as a batch process:

Align observed and simulated tables

Mask missing or low-confidence data

Optimize permitted parameters

Validate on holdout

Emit versioned patch + report

Optionally trigger PME review

Anchoring is never invoked automatically inside simulation.

Determinism & Reproducibility

Anchoring runs must be reproducible from:

observed data version

simulated data version

persona base version

optimization config

All runs must record these identifiers.

Integration With Other Layers
LPM

Provides simulated aggregates

Not modified by anchoring

Data Engine

Provides observed aggregates + confidence

Not mutated by anchoring

PME

Receives drift signals

Owns persona creation decisions

Failure Modes & Guardrails

Reject unauthorized parameter updates

Reject mid-run calibration

Reject missing persona contribution tables

Fail loudly on schema mismatch

One-Line Canonical Summary

Anchoring is the outer-loop calibration layer that aligns simulated market aggregates to observed data by safely adjusting permitted persona parameters, quantifying uncertainty, and detecting when structural model changes are required.


