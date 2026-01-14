# Louiza Engine — Architecture Overview

## Purpose of This Document

This document provides the **authoritative architectural overview** of the Louiza Engine. It defines:

- The global execution model
- The separation of concerns across layers
- The time-scale semantics of the system
- The end-to-end data and control flow

All other layer-specific documents (`01–05`) must be interpreted as **refinements of this overview**, not overrides.

This document is written for **internal engineering use** and is intended to be **machine-actionable** by tools such as Cursor.

---

## System Objective (High-Level)

The Louiza Engine is a **ground-truth–anchored behavioral simulation system** designed to:

- Model heterogeneous consumer behavior at scale
- Simulate market scenarios via large populations of agents
- Generate calibrated, uncertainty-aware market insights
- Maintain auditability, reproducibility, and stability over time

The system explicitly separates:
- **Behavioral execution**
- **Population scaling**
- **Structural modeling**
- **Calibration**
- **Reasoning**

This separation is a core architectural invariant.

---

## Core Design Philosophy

### 1. Behavior Is Modeled, Not Memorized
Behavior is implemented as explicit state dynamics (IBDE), not learned end-to-end by an LLM or black-box predictor.

### 2. Heterogeneity via Parameterization
Diversity in behavior arises from **persona parameterization**, not duplicated logic.

### 3. Ground Truth Is an Outer Loop
Calibration happens **between simulation runs**, never inside the per-timestep loop.

### 4. Reasoning Is Constrained
LLMs may generate hypotheses and explanations, but **cannot invent numerical results** or bypass simulation.

---

## Layered Architecture (Authoritative)

The Louiza Engine is composed of **five core layers**, each operating at a distinct time scale:

| Layer | Name | Primary Role | Time Scale |
|-----|-----|-------------|-----------|
| 1 | Data Engine | Data ingestion, normalization, retrieval | Continuous / Batch |
| 2 | Persona Modeling Engine (PME) | Define agent archetypes | Episodic |
| 3 | Individual Behavioral Dynamics Engine (IBDE) | Evolve single-agent state | Per timestep |
| 4 | Large Population Model (LPM) | Scale agents & aggregate outcomes | Per timestep |
| 5 | Ground-Truth Anchoring Engine | Calibrate to reality | Between runs |

No layer may assume responsibilities of another.

---

## Time-Scale Semantics (Critical)

The system operates across **three nested time scales**:

### A. Episodic / Structural Time
- Persona creation and updates (PME)
- Schema and parameter versioning
- Happens infrequently

### B. Simulation Time (Fast Inner Loop)
- IBDE state updates
- LPM action sampling
- Environment evolution
- Happens every timestep

### C. Calibration Time (Outer Loop)
- Anchoring and parameter fitting
- Drift detection
- Happens between simulation runs

These time scales **must never be collapsed**.

---

## End-to-End Execution Flow (Canonical)

The system executes in the following sequence:

### Phase 1: Persona Definition (Offline)
1. Data Engine produces aggregated features and residuals
2. PME evaluates whether existing personas explain observed behavior
3. PME publishes a versioned `PersonaSet_vN`

### Phase 2: Simulation (Inner Loop)
4. LPM instantiates agents from personas
5. For each timestep:
   - IBDE updates agent state and computes logits
   - LPM samples actions and updates environment
   - Events are aggregated

### Phase 3: Anchoring (Outer Loop)
6. Anchoring compares simulated aggregates to observed data
7. Allowed parameters (e.g., persona weights) are adjusted
8. Diagnostics and uncertainty metrics are produced
9. If anchoring fails, PME may be triggered for reevaluation

This loop repeats, but layers remain isolated.

---

## Data Flow Summary

Observed Data
↓
Data Engine
↓
Persona Modeling Engine (PME)
↓
PersonaSet_vN
↓
Large Population Model (LPM)
↳ calls IBDE every timestep
↓
Simulated Aggregates
↓
Ground-Truth Anchoring
↓
Updated Persona Parameters / Diagnostics


---

## Determinism & Reproducibility Guarantees

The architecture enforces the following guarantees:

- IBDE is deterministic given inputs, parameters, and seed
- All stochasticity lives in LPM sampling
- Persona definitions are immutable once published
- Anchoring updates are versioned and replayable
- Every simulation run is reproducible from:
  - Persona version
  - IBDE code version
  - Scenario config
  - Random seeds

---

## What This Architecture Explicitly Avoids

- End-to-end black-box learning
- Online parameter updates during simulation
- Persona mutation mid-run
- LLM-driven numerical prediction
- Implicit state or hidden coupling between layers

These are considered architectural violations.

---

## Intended Usage With Cursor

This architecture is designed to be **built directly from specification**.

When used with Cursor:
- Treat each layer `.md` file as a **non-negotiable contract**
- Implement layers sequentially (1 → 5)
- Stop and surface ambiguities rather than guessing
- Prefer simple, explicit implementations over clever abstractions

---

## One-Line Canonical Summary

> The Louiza Engine is a layered, ground-truth–anchored behavioral simulation system where personas define heterogeneity, IBDE defines behavior, LPM defines scale, and anchoring ensures alignment with reality—each operating at a distinct and enforced time scale.

---
