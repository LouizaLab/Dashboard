# Layer 1: Data Engine — Technical Design (POC + Synthetic Data)

## Purpose

The Data Engine is the **authoritative data substrate** of the Louiza Engine.  
It is responsible for ingesting, normalizing, versioning, and serving all data used by downstream layers while preserving **provenance, trust, and reproducibility**.

For the POC, the Data Engine must additionally support a **Synthetic Data Factory** that generates realistic mock datasets in the **same schemas** expected in production. This enables end-to-end system testing without dependence on external sources.

The Data Engine remains **model-agnostic** and must not implement behavioral logic, simulation logic, or anchoring logic.

---

## Non-Goals (Explicit)

The Data Engine must **not**:
- Implement IBDE behavioral dynamics
- Create personas (PME responsibility)
- Run simulations (LPM responsibility)
- Perform anchoring optimization (Anchoring responsibility)
- Call LLMs for prediction or reasoning inside core pipelines

The Data Engine **may** produce synthetic datasets in POC mode, but must treat them as **data artifacts**, not model outputs.

---

## POC Mode Overview

### POC Capability: Synthetic Data Factory
In POC mode, the Data Engine can generate:
- public-style datasets (menu, prices, store metadata)
- survey datasets (preferences, taste ratings, choice experiments)
- “partner-style” aggregates (transactions/revenue proxies)

These datasets must be:
- versioned
- reproducible (seeded)
- auditable (generation config stored)
- schema-compatible with production tables

**Key Principle:** POC synthetic generation is a *data source*, not a separate architecture.

---

## Inputs

### A) Production Sources (Optional in POC)
Same bucketed sources as production, but may be stubbed.

### B) Synthetic Data Factory Inputs (POC Required)
- `synthetic_config` (distribution parameters, sizes, date ranges)
- `random_seed`
- canonical entity lists (brands, regions, channels)
- optional scenario templates (promo schedules, price shocks)

---

## Outputs

The Data Engine exposes **read-only, versioned outputs** to downstream layers:

1. **Analytics Tables** (Observed Ground Truth Inputs)
   - `observed_metrics_brand_week_region`
   - `observed_metrics_brand_week_region_channel` (optional)

2. **Feature Views**
   - `features_brand_week_region`
   - `features_persona_discovery` (PME inputs)

3. **Environment Tables** (LPM Inputs)
   - `brand_price_schedule`
   - `brand_promo_schedule`
   - `brand_menu_availability`

4. **Survey Tables** (PME Inputs)
   - `survey_responses`
   - `taste_ratings`
   - `choice_experiments`

5. **Metadata**
   - dataset version IDs
   - trust/confidence weights
   - coverage diagnostics
   - lineage/generation configs

---

## Core Data Model

### Canonical Dimensions (Authoritative)
All tables must be keyed by a subset of:

- `week_id` (minimum resolution for POC)
- `brand_id`
- `region_id`
- `channel_id` (optional)
- `cohort_id` (optional)

No downstream layer may infer dimensions implicitly.

---

## Storage Architecture (POC-Compatible)

### Raw Lake (Immutable)
- Stores generated CSV/Parquet (or files) as immutable artifacts
- Original schema preserved

### Clean Warehouse (Normalized)
- Canonical tables with consistent keys
- Derived aggregates and joins materialized

### Feature Store
- Entity–time indexed features
- Deterministic recomputation from raw

### Metadata Catalog
- dataset version IDs
- ingestion timestamps (or synthetic generation timestamps)
- generation configs and random seeds
- lineage links across tables

---

## Synthetic Data Factory (POC Required)

### Responsibilities
The Synthetic Data Factory must:
- generate datasets that resemble real distributions
- enforce schema contracts
- support controlled “what-if” variations
- output consistent entity relationships across tables
- produce deterministic outputs given seed + config

### Output Dataset Families (Recommended for POC)

#### 1) Entities
- `brands.csv` (brand_id, name, category)
- `regions.csv` (region_id, name)
- `channels.csv` (channel_id, name)

#### 2) Environment Schedules (for LPM)
- `brand_price_schedule.csv`
  - week_id, brand_id, region_id, price_index
- `brand_promo_schedule.csv`
  - week_id, brand_id, region_id, promo_intensity
- `brand_menu_availability.csv`
  - week_id, brand_id, region_id, availability_score

#### 3) Survey / Preference Data (for PME)
- `survey_responses.csv`
  - respondent_id, week_id, region_id, brand_id, preference_score
- `taste_ratings.csv`
  - respondent_id, item_id, attributes..., rating
- `choice_experiments.csv`
  - respondent_id, week_id, option_set_id, chosen_brand_id, prices..., context...

#### 4) Observed Market Aggregates (for Anchoring)
- `observed_metrics_brand_week_region.csv`
  - week_id, brand_id, region_id, transactions_obs, revenue_obs, confidence_weight

### Synthetic Generation Requirements
- Must support:
  - seasonality patterns
  - region-level heterogeneity
  - brand differentiation
  - noise injection
  - controllable shocks (promo, price changes)
- Must produce `confidence_weight` to simulate real-world uncertainty.

### Deterministic Generation Contract
Synthetic generation must be reproducible from:
- `synthetic_config`
- `random_seed`
- `data_version`

---

## Trust & Quality Signals (POC)

In POC mode:
- all synthetic datasets must include a `confidence_weight`
- confidence may reflect:
  - simulated sample size
  - simulated measurement noise
  - missingness/coverage

Anchoring consumes these weights to demonstrate robustness.

---

## Versioning & Reproducibility

- Every synthetic generation run produces a new dataset version:
  - `data_YYYY_MM_DD_runNN`
- The generation config and seed must be stored alongside metadata
- Downstream layers must pin to specific versions for replay

---

## Execution Model

### POC Generation Flow
1. Generate entity tables (brands/regions/channels)
2. Generate environment schedules (prices/promos/availability)
3. Generate survey datasets
4. Generate “observed” aggregates from a hidden generative process
5. Publish versioned tables to warehouse + catalog

### Runtime Access
- Downstream layers must read only materialized outputs
- No per-timestep queries during simulation
- No silent refresh during a run

---

## Failure Modes & Guardrails

- Reject schema drift without explicit migration
- Reject missing canonical keys
- Fail loudly on inconsistent entity relationships (brand_ids not matching)
- Enforce strict dataset version pinning in simulations

---

## Integration With Other Layers

### PME
- Uses: survey tables + persona discovery features
- Does not consume raw events

### IBDE
- Does not query Data Engine directly in runtime loop
- Receives persona params produced by PME

### LPM
- Uses: environment schedules + scenario configs
- Does not query Data Engine per timestep

### Anchoring
- Uses: observed aggregates + confidence weights
- Produces parameter patches (not stored in Data Engine by default)

---

## One-Line Canonical Summary

> The Data Engine produces versioned, schema-compatible datasets (synthetic in POC mode) that feed PME, LPM, and Anchoring while maintaining strict reproducibility and separation from behavioral and calibration logic.

---
