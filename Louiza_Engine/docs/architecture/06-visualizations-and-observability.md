# Layer 6: Visualizations & Observability (POC)

## Purpose

This document defines the **observability layer** for the Louiza Engine POC.

Its purpose is to:
- make the system’s behavior visible
- validate architectural correctness
- demonstrate grounding and calibration
- provide confidence to engineers, stakeholders, and investors

Visualizations are treated as **first-class architectural outputs**, not cosmetic UI.

---

## Design Principles

1. **Every visualization must correspond to a system invariant**
2. **No visualization may invent numbers**
3. **All plots must be derivable from logged outputs**
4. **Before/After anchoring comparisons are mandatory**
5. **Uncertainty must be visible, not hidden**

---

## Observability Layers

Observability is organized by architectural layer:

| Layer | Observable Type |
|-----|----------------|
| Data Engine | Data coverage & distributions |
| PME | Persona structure & stability |
| IBDE | Single-agent dynamics |
| LPM | Population-level behavior |
| Anchoring | Calibration & error reduction |

---

## 1. Data Engine Visualizations (POC)

### 1.1 Synthetic Data Sanity Checks

**Plots**
- Transactions over time (by brand, region)
- Revenue over time
- Price & promo schedules

**Purpose**
- Prove synthetic data is non-degenerate
- Validate seasonality and shocks exist

**Observable Questions**
- Do trends look realistic?
- Are shocks visible where expected?

---

### 1.2 Data Coverage Dashboard

**Plots**
- Heatmap: week × region data availability
- Confidence weight distribution

**Purpose**
- Show anchoring knows what data to trust
- Validate missingness handling

---

## 2. PME Visualizations

### 2.1 Persona Overview Panel

**Plots**
- Persona population weights (bar chart)
- Persona distribution by region (stacked bar)

**Purpose**
- Show heterogeneity exists
- Validate persona weights sum to 1

---

### 2.2 Persona Separation Diagnostics

**Plots**
- 2D projection (PCA / UMAP) of survey features
- Color-coded by persona assignment

**Purpose**
- Demonstrate personas are distinct
- Detect persona collapse or redundancy

---

### 2.3 Persona Stability Over Time

**Plots**
- Persona weight drift across anchoring runs
- Stability score over time

**Purpose**
- Prove personas evolve slowly
- Validate invariant: no rapid oscillation

---

## 3. IBDE Visualizations (Critical for Trust)

### 3.1 Single-Agent Trajectory Viewer

**Plots**
- Taste embedding drift (line plot)
- Loyalty score over time
- Fatigue & attention decay

**Purpose**
- Make IBDE dynamics interpretable
- Prove behavior is stateful, not random

---

### 3.2 Utility Decomposition Plot

**Plots**
- Stacked bar per timestep:
  - price term
  - promo term
  - loyalty term
  - noise

**Purpose**
- Prove choices are explainable
- Debug incorrect parameterization

---

### 3.3 Constraint Activation Monitor

**Plots**
- % of actions masked by constraints
- Max price tolerance hit rate

**Purpose**
- Validate constraints are active but not dominant

---

## 4. LPM Visualizations (Core Demo Layer)

### 4.1 Population Outcome Dashboard

**Plots**
- Transactions by brand over time
- Revenue by brand over time
- Market share evolution

**Purpose**
- Demonstrate emergent macro behavior
- Show competition dynamics

---

### 4.2 Persona Contribution Breakdown

**Plots**
- Stacked area:
  - persona contribution to transactions
- Persona × brand heatmap

**Purpose**
- Show *why* outcomes happen
- Validate persona attribution pipeline

---

### 4.3 Scenario Comparison View

**Plots**
- Baseline vs scenario deltas
- % lift / decline by brand

**Purpose**
- Enable “what-if” analysis
- Support consultant use cases

---

## 5. Anchoring Visualizations (Most Important for Credibility)

### 5.1 Before vs After Anchoring

**Plots**
- Observed vs simulated (before)
- Observed vs simulated (after)

Overlay with:
- confidence bands
- residuals

**Purpose**
- Prove anchoring works
- Make improvement obvious

---

### 5.2 Error Reduction Metrics

**Plots**
- MSE / MAE before vs after
- Holdout error comparison

**Purpose**
- Prevent overfitting
- Enforce anchoring discipline

---

### 5.3 Persona Weight Adjustments

**Plots**
- Delta bars for persona weights
- Regional persona shifts

**Purpose**
- Explain *how* anchoring corrected the model
- Support narrative explanations

---

## 6. Entropy & Uncertainty Visualizations

### 6.1 Predictive Uncertainty Bands

**Plots**
- Mean ± confidence interval for transactions
- Fan charts for future weeks

**Purpose**
- Make uncertainty explicit
- Avoid false precision

---

### 6.2 Entropy Attribution

**Plots**
- Entropy contribution by persona
- Entropy by region / brand

**Purpose**
- Identify weak signals
- Drive data acquisition decisions

---

## 7. POC Dashboard Layout (Recommended)

### Tab 1: Data & Assumptions
- Synthetic data plots
- Scenario config

### Tab 2: Personas
- Persona weights
- Persona separation

### Tab 3: Individual Behavior
- Single-agent trajectories
- Utility decomposition

### Tab 4: Market Simulation
- LPM outputs
- Scenario comparisons

### Tab 5: Anchoring & Ground Truth
- Before/after plots
- Error reduction
- Uncertainty

---

## 8. POC Success Criteria (Observable)

The POC is successful if:

- Personas are visually distinct
- IBDE shows smooth, interpretable state evolution
- LPM produces realistic macro trends
- Anchoring reduces error without instability
- Uncertainty is visible and non-zero
- All plots are reproducible from logged artifacts

---

## 9. Explicit Anti-Patterns (Forbidden)

- Visuals without source tables
- Smoothed curves hiding noise
- Single-point forecasts without bands
- LLM-generated numbers
- Post-hoc manual adjustments

---

## 10. Implementation Notes for Cursor

- Prefer Python + matplotlib / plotly
- All plots must load from saved artifacts
- Save figures alongside run metadata
- Name plots deterministically by run ID

---

## One-Line Canonical Summary

> The visualization and observability layer makes every architectural assumption, behavioral mechanism, and calibration step explicit, inspectable, and defensible.

---
