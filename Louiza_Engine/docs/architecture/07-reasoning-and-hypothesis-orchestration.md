# Layer 7: Reasoning & Hypothesis Orchestration (LangGraph)

## Purpose

This layer provides a **prompt-to-simulation** interface that lets internal users (consultants, researchers, engineers) describe a market question in natural language and reliably run:

- hypothesis formulation
- scenario construction
- evidence retrieval
- simulation execution (LPM + IBDE)
- ground-truth anchoring (outer loop)
- results synthesis with uncertainty and provenance

This layer is **orchestration + reasoning**, not modeling. It must never bypass simulation, anchoring, or data provenance.

---

## Non-Goals (Explicit)

This layer must **not**:

- generate numerical forecasts without running the simulation
- call IBDE per timestep (simulation is LPM-owned)
- modify personas mid-run
- run anchoring inside the timestep loop
- fabricate evidence or citations
- write back to the Data Engine as ground truth
- implement behavior logic (IBDE responsibility) or population scaling (LPM responsibility)

All quantitative outputs must originate from LPM outputs and (optionally) anchoring-calibrated runs.

---

## Inputs

### Primary Input
- `user_prompt` (string)

### Optional Inputs
- `constraints` (time window, regions, brands, channel scope)
- `persona_version` (pin PersonaSet version)
- `data_version` (pin Data Engine version)
- `simulation_budget` (max scenarios, max runs, max agents)

---

## Outputs

### Primary Outputs
- `hypotheses` (structured)
- `scenario_specs` (structured, executable by LPM)
- `run_artifacts` (IDs + file paths + metadata)
- `results_summary` (tables, deltas, bands)
- `observability_bundle` (links to plots, dashboards)
- `provenance` (data_version, persona_version, run IDs, seeds)

### Output Format (Recommended)
- JSON + markdown report
- Persisted artifacts on disk keyed by `run_id`

---

## Architecture Overview (LangGraph)

This layer is implemented as a **LangGraph workflow** with explicit state, nodes, and guardrails.

### Key Design Principle
> The graph produces **executable specs** and triggers downstream systems.  
> It does not “reason” numbers into existence.

---

## Global Graph State (Authoritative)

Define a single state object passed through the graph.

```jsonc
{
  "request": {
    "user_prompt": "string",
    "constraints": {
      "time_horizon_weeks": 12,
      "regions": ["US_South"],
      "brands": ["BK", "MCD"],
      "channels": ["drive_thru"]
    },
    "simulation_budget": {
      "max_scenarios": 5,
      "max_runs": 10,
      "max_agents": 200000
    }
  },

  "pins": {
    "data_version": "data_2026_01_08_run01",
    "persona_version": "PersonaSet_v1",
    "ibde_version": "ibde_git_sha",
    "lpm_version": "lpm_git_sha"
  },

  "hypotheses": [
    {
      "hypothesis_id": "H1",
      "statement": "Launching BK chicken wrap with promo will steal share from MCD in US_South over 12 weeks.",
      "metrics": ["transactions", "revenue"],
      "segments": ["persona_07_value_loyalist"],
      "acceptance_criteria": {
        "metric": "transactions",
        "delta_pct_min": 0.02,
        "confidence_min": 0.8
      }
    }
  ],

  "evidence": {
    "retrieved_docs": [],
    "retrieved_tables": [],
    "coverage": {},
    "data_trust_summary": {}
  },

  "scenario_specs": [
    {
      "scenario_id": "S0_baseline",
      "kind": "baseline",
      "time_horizon_weeks": 12,
      "interventions": []
    },
    {
      "scenario_id": "S1_bk_chicken_wrap_promo",
      "kind": "counterfactual",
      "time_horizon_weeks": 12,
      "interventions": [
        {"type": "menu_launch", "brand_id": "BK", "item_id": "chicken_wrap_x", "start_week": 3},
        {"type": "promo", "brand_id": "BK", "region_id": "US_South", "intensity": 0.7, "start_week": 3, "end_week": 6}
      ]
    }
  ],

  "runs": [
    {
      "run_id": "RUN_001",
      "scenario_id": "S0_baseline",
      "seed": 123,
      "num_agents": 200000,
      "status": "completed",
      "artifacts": {
        "simulated_metrics_path": "path/to/simulated_metrics.csv",
        "persona_contrib_path": "path/to/persona_contrib.csv",
        "plots_dir": "path/to/plots/"
      }
    }
  ],

  "anchoring": {
    "enabled": true,
    "anchoring_run_id": "ANCHOR_001",
    "status": "completed",
    "patch_path": "path/to/anchoring_patch.json",
    "fit_summary": {}
  },

  "analysis": {
    "scenario_comparisons": [],
    "uncertainty": {},
    "entropy": {}
  },

  "final_report": {
    "markdown_path": "path/to/report.md",
    "summary": "string"
  }
}
Graph Nodes (Required)
Node A: ParseRequest

Goal: Extract scope, entities, and intent from the prompt.

Output: structured request.constraints, candidate brands/regions/channels, candidate time horizon.

Guardrail: if scope is missing, choose safe defaults (POC defaults) and record assumptions.

Node B: GenerateHypotheses

Goal: Turn prompt into 1–3 testable hypotheses.

Output: hypotheses[] with metrics + acceptance criteria.

Constraint: acceptance criteria must be measurable from LPM outputs.

Node C: RetrieveEvidence

Goal: Query the Data Engine retrieval interfaces for:

relevant tables (observed metrics, schedules, survey summaries)

relevant documents (notes, surveys, assumptions)

trust/coverage metadata

Output: evidence.*

Guardrail: never cite or use evidence without provenance (dataset version + source).

Node D: CriticCheck

Goal: Validate hypothesis + evidence sufficiency.

Checks:

Are required metrics available at the chosen aggregation level?

Is coverage acceptable (confidence_weight present)?

Are assumptions too strong?

Output:

approved / needs narrowing / needs more evidence

If insufficient: loop back to RetrieveEvidence with refined queries.

Node E: ScenarioBuilder

Goal: Convert hypotheses into executable scenario specs for LPM.

Must produce:

baseline scenario S0

≥1 counterfactual scenario

Guardrail:

All interventions must be representable in LPM schema (04-lpm.md)

No free-form “magic” interventions; everything must map to environment schedules.

Node F: RunPlanner

Goal: Decide run plan given budget:

number of runs per scenario (for uncertainty bands)

seeds

agent counts

whether anchoring is needed

Output: runs[] (planned with status=pending)

Node G: SimulationRunner

Goal: Execute LPM runs (baseline + counterfactual).

Calls the simulation service/module with:

scenario_spec

pinned versions

seeds

Output: populated runs[].artifacts

Important: SimulationRunner is a single call per run.
It must not attempt per-timestep interventions.

Node H: AnchoringRunner (Optional but recommended)

Goal: Run anchoring between runs:

baseline run outputs + observed metrics

apply patch → rerun (or calibrate for reporting)

Output: anchoring.*

Node I: Comparator

Goal: Compute:

baseline vs scenario deltas

persona contribution deltas

uncertainty intervals (across seeds/runs)

Output: analysis.scenario_comparisons, analysis.uncertainty

Node J: InsightSynthesizer

Goal: Produce internal-ready explanations:

what moved, why, and which personas drove it

tie back to evidence retrieved

highlight uncertainty + entropy

Output: report sections + bullet insights

Node K: ReportWriter

Goal: Save a final markdown report and artifact index.

Output: final_report.*

LangGraph Topology (Recommended)
ParseRequest
   ↓
GenerateHypotheses
   ↓
RetrieveEvidence → CriticCheck ──┐
                 ↑              │ (loop until approved or budget exhausted)
                 └──────────────┘
   ↓
ScenarioBuilder
   ↓
RunPlanner
   ↓
SimulationRunner
   ↓
AnchoringRunner (optional)
   ↓
Comparator
   ↓
InsightSynthesizer
   ↓
ReportWriter

Tooling & Module Interfaces (POC)

This layer should call internal Python modules/services corresponding to Layers 1–6:

Data Engine

data_engine.get_table(table_name, data_version, filters)

data_engine.search_docs(query, data_version, top_k)

data_engine.get_trust_summary(data_version)

PME

Typically pinned persona version; optionally:

pme.load_personaset(persona_version)

LPM

lpm.run_simulation(scenario_spec, persona_version, data_version, seed, num_agents)

returns paths to:

simulated_metrics_brand_week_region.csv

persona_contributions.csv

run_metadata.json

Anchoring

anchoring.run(observed_metrics_table, simulated_metrics_table, persona_contributions, persona_version)

returns:

anchoring_patch.json

anchoring_report.json

Visualizations (Layer 6)

viz.generate_all(run_id, artifacts_dir)
Must generate before/after anchoring plots and save them.

Guardrails & Policy Checks (Hard Requirements)
GR-1: No “numbers without runs”

If any node tries to output a numeric forecast without a completed run artifact, the graph must:

stop and return an error with remediation steps

GR-2: Version pinning required

Every run must pin:

data_version

persona_version

ibde_version

lpm_version

scenario_hash

seed

GR-3: Evidence provenance

Every cited claim must reference:

table name + data_version OR document_id + data_version

GR-4: Budget enforcement

RunPlanner must not exceed:

max_scenarios

max_runs

max_agents

GR-5: Anchoring boundaries

Anchoring must:

operate only between runs

modify only adjustable_params declared by personas

Hypothesis DSL (Recommended Minimal Schema)

Hypotheses must be serializable and testable.

{
  "hypothesis_id": "H1",
  "statement": "string",
  "metrics": ["transactions", "revenue"],
  "slice": {"brand": ["BK"], "region": ["US_South"]},
  "baseline": "S0_baseline",
  "treatment": "S1_bk_chicken_wrap_promo",
  "acceptance_criteria": [
    {"metric": "transactions", "delta_pct_min": 0.02, "confidence_min": 0.8}
  ]
}

Scenario Spec DSL (Must Match LPM)

Scenario specs must map directly to LPM-supported interventions:

{
  "scenario_id": "S1",
  "time_horizon_weeks": 12,
  "scope": {"regions": ["US_South"], "channels": ["drive_thru"]},
  "interventions": [
    {"type": "price_change", "brand_id": "BK", "delta_pct": -0.05, "start_week": 3},
    {"type": "promo", "brand_id": "BK", "intensity": 0.7, "start_week": 3, "end_week": 6},
    {"type": "menu_launch", "brand_id": "BK", "item_id": "chicken_wrap_x", "start_week": 3}
  ]
}

Observables Produced by the Reasoning Layer

This layer must always produce:

Artifact index: where outputs live

Scenario diff report: baseline vs treatment

Uncertainty bands: across seeds

Evidence appendix: tables + docs used

Assumptions list: explicitly stated

Anchoring section (if enabled): before/after plots + error metrics

POC Implementation Notes (LangGraph)
Recommended Implementation Pattern

Each node is a pure function:

input: state

output: updated state

Side effects (running simulation, writing files) are isolated to:

SimulationRunner

AnchoringRunner

ReportWriter

Viz generation calls

Suggested LangGraph Files

louiza_reasoning/graph.py — graph definition

louiza_reasoning/nodes/*.py — node implementations

louiza_reasoning/schemas.py — pydantic models for state

louiza_reasoning/tools.py — wrappers for calling LPM/Anchoring/Data Engine

louiza_reasoning/prompts/*.md — prompt templates (optional)

One-Line Canonical Summary

The Reasoning & Hypothesis layer uses LangGraph to convert natural-language questions into evidence-backed, executable scenarios, runs simulations and anchoring under strict guardrails, and returns reproducible, uncertainty-aware insights with full provenance.