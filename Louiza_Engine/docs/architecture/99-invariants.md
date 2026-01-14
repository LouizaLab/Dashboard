# Louiza Engine — Architectural Invariants

## Purpose of This Document

This document defines the **non-negotiable invariants** of the Louiza Engine architecture.

These invariants are **hard constraints**, not guidelines.  
Any implementation that violates an invariant is considered **architecturally incorrect**, even if it appears to function.

When building with Cursor, this file acts as a **guardrail** against silent architectural drift.

---

## Invariant Categories

Invariants are grouped into five categories:

1. Layer Boundaries  
2. Time-Scale Separation  
3. Determinism & Reproducibility  
4. Parameter & State Safety  
5. LLM & Reasoning Constraints  

Each invariant is labeled with a unique ID for reference.

---

## 1. Layer Boundary Invariants

### INV-L1: No Layer May Assume Another Layer’s Responsibilities

Each layer has a single, exclusive responsibility:

- Data Engine → data ingestion and retrieval only  
- PME → persona definition only  
- IBDE → single-agent behavior only  
- LPM → population scaling and aggregation only  
- Anchoring → calibration only  

Violations include:
- IBDE performing aggregation
- LPM encoding behavioral rules
- Anchoring modifying agent state
- PME executing simulation logic

---

### INV-L2: No Upward Dependencies

Lower layers must never depend on higher layers.

Forbidden:
- IBDE calling Anchoring
- LPM querying PME mid-simulation
- Data Engine importing simulation logic

Allowed:
- Higher layers consuming outputs of lower layers

---

### INV-L3: Persona Logic Must Not Appear Outside PME

Personas:
- are defined only in PME
- are immutable once published
- are referenced only via parameters elsewhere

Forbidden:
- Persona creation in LPM
- Persona mutation in IBDE
- Hard-coded persona branching anywhere

---

## 2. Time-Scale Separation Invariants

### INV-T1: PME Must Never Run Inside the Simulation Loop

PME operates **episodically**.

Forbidden:
- Creating or modifying personas during a simulation run
- Triggering PME logic at a timestep boundary

---

### INV-T2: Anchoring Must Never Run Inside the Timestep Loop

Anchoring operates **between runs**, never per timestep.

Forbidden:
- Updating parameters at timestep `t`
- Using future data to correct past states
- Online calibration inside IBDE or LPM

---

### INV-T3: IBDE + LPM Form the Only Fast Inner Loop

Only IBDE and LPM are allowed to execute per timestep.

Forbidden:
- LLM calls per timestep
- Data Engine queries per timestep
- Persona logic per timestep

---

## 3. Determinism & Reproducibility Invariants

### INV-D1: IBDE Must Be Deterministic

IBDE outputs must be fully determined by:

(state_t, env_t, persona_params, seed)


Forbidden:
- Hidden global state
- External I/O
- Implicit randomness

---

### INV-D2: All Stochasticity Lives in LPM

Randomness:
- sampling actions
- tie-breaking
- event scheduling

Must exist **only** in LPM.

IBDE must not sample actions.

---

### INV-D3: Every Simulation Run Must Be Replayable

A run must be reproducible given:
- Persona version
- IBDE code version
- Scenario configuration
- Random seeds

If replay is impossible, the system is invalid.

---

## 4. Parameter & State Safety Invariants

### INV-P1: Agent State Must Never Be Modified by Anchoring

Anchoring may update:
- persona weights
- permitted persona parameters

Anchoring must never:
- modify agent latent state
- retroactively alter trajectories

---

### INV-P2: Anchoring May Modify Only Declared Parameters

Only parameters explicitly listed in: persona.calibration_hooks.adjustable_params


may be changed by anchoring.

All other parameters are frozen.

---

### INV-P3: Personas Must Be Immutable During Simulation

Once a simulation run starts:
- persona parameters are read-only
- persona weights are fixed
- persona membership is fixed

No mid-run mutation is allowed.

---

### INV-P4: IBDE Must Never Branch on Persona Identity

IBDE logic must depend only on:
- numerical parameters
- gated inputs

Forbidden:
- `if persona_id == ...`
- persona-specific code paths

This invariant enables vectorization and scalability.

---

## 5. LLM & Reasoning Invariants

### INV-R1: LLMs Must Never Generate Numerical Outputs

LLMs may:
- generate hypotheses
- synthesize explanations
- propose scenarios

LLMs must never:
- output forecasts
- invent numbers
- override simulation results

---

### INV-R2: All Quantitative Claims Must Flow Through Simulation

Any number shown to a user must originate from:
- LPM outputs
- Anchoring-calibrated results

No exceptions.

---

### INV-R3: LLMs Cannot Bypass Anchoring

LLMs cannot:
- declare results “confident” without uncertainty
- suppress entropy or error signals
- override calibration diagnostics

---

## 6. Data Integrity Invariants

### INV-I1: Data Engine Outputs Are Immutable Snapshots

Once consumed by a run:
- data version is frozen
- late-arriving data must trigger a new run

No hidden data refreshes.

---

### INV-I2: No Implicit Feature Leakage

Simulation must not access:
- future data
- holdout windows
- post-period ground truth

Violations invalidate all results.

---

## 7. Explicitly Forbidden Anti-Patterns

The following patterns are **architectural violations**:

- End-to-end black-box learning replacing IBDE + LPM
- Online persona creation
- Anchoring inside simulation
- Persona-conditioned branching logic
- Unversioned parameter updates
- Non-replayable stochasticity
- LLM-driven numeric prediction

---

## Enforcement Expectations

Implementations should:

- Encode these invariants as assertions where possible
- Add unit tests validating invariants
- Fail loudly when an invariant is violated
- Prefer stopping execution over silent fallback

Cursor should surface invariant violations explicitly rather than attempting to auto-fix them.

---

## One-Line Canonical Summary

> These invariants enforce separation of concerns, temporal isolation, determinism, and grounding, ensuring the Louiza Engine remains stable, interpretable, and reproducible as it evolves.

---


