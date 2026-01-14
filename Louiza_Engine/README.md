# Louiza Engine

A ground-truth-anchored behavioral simulation system for modeling heterogeneous consumer behavior at scale.

## Architecture Overview

Louiza Engine is built as a layered system with strict separation of concerns:

- **Layer 1: Data Engine** - Data ingestion, normalization, and synthetic data generation
- **Layer 2: Persona Modeling Engine (PME)** - Define agent archetypes
- **Layer 3: Individual Behavioral Dynamics Engine (IBDE)** - Evolve single-agent state
- **Layer 4: Large Population Model (LPM)** - Scale agents & aggregate outcomes
- **Layer 5: Ground-Truth Anchoring Engine** - Calibrate to reality
- **Layer 6: Observability & Visualizations** - Make system behavior visible
- **Layer 7: Reasoning & Hypothesis Orchestration** - Prompt-to-simulation interface

See `docs/architecture/` for detailed specifications.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## POC Execution Flow

### Phase 1: Generate Synthetic Data
```bash
python scripts/generate_synthetic_data.py \
    --config configs/synthetic_config.json \
    --seed 42 \
    --output-dir data/synthetic/
```

### Phase 2: Initialize Personas
```bash
python scripts/initialize_personas.py \
    --data-version data_2026_01_08_run01 \
    --output PersonaSet_v1.json
```

### Phase 3: Run Baseline Simulation
```bash
python scripts/run_simulation.py \
    --persona-version PersonaSet_v1 \
    --scenario configs/baseline_scenario.json \
    --seed 123 \
    --num-agents 200000 \
    --output-dir runs/baseline_001/
```

### Phase 4: Run Counterfactual Scenario
```bash
python scripts/run_simulation.py \
    --persona-version PersonaSet_v1 \
    --scenario configs/counterfactual_scenario.json \
    --seed 123 \
    --num-agents 200000 \
    --output-dir runs/counterfactual_001/
```

### Phase 5: Anchor to Ground Truth
```bash
python scripts/run_anchoring.py \
    --observed-data data/synthetic/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_001/simulated_metrics.csv \
    --persona-version PersonaSet_v1 \
    --output-dir runs/anchored_001/
```

### Phase 6: Generate Visualizations
```bash
python scripts/generate_all_plots.py \
    --run-id baseline_001 \
    --artifacts-dir runs/baseline_001/ \
    --output-dir plots/baseline_001/
```

### Phase 7: Run from Natural Language Prompt
```bash
python scripts/run_from_prompt.py \
    "What happens if BK launches a chicken wrap with promo in US_South over 12 weeks?" \
    --data-version data_2026_01_08_run01 \
    --persona-version PersonaSet_v1.json \
    --enable-anchoring \
    --max-scenarios 3 \
    --max-runs 6 \
    --max-agents 10000
```

## Documentation

- **[Complete Workflow Guide](COMPLETE_WORKFLOW_GUIDE.md)** - End-to-end guide from persona creation to prompt testing with anchoring and hyperparameter tuning
- **[Interview Extraction Guide](INTERVIEW_EXTRACTION_GUIDE.md)** - Extract structured data from interview transcripts using LLM and web search
- **[Custom Data Integration Guide](CUSTOM_DATA_INTEGRATION_GUIDE.md)** - How to integrate your own datasets (revenue, preferences, etc.) into the pipeline
- **[Quick Reference](QUICK_REFERENCE.md)** - Quick command reference and common scenarios
- **[Prompt Workflow Guide](PROMPT_WORKFLOW_GUIDE.md)** - Detailed guide for prompt-based simulation

## Project Structure

```
Louiza_Engine/
├── data_engine/          # Layer 1: Data ingestion and synthetic generation
├── pme/                  # Layer 2: Persona Modeling Engine
├── ibde/                 # Layer 3: Individual Behavioral Dynamics Engine
├── lpm/                  # Layer 4: Large Population Model
├── anchoring/            # Layer 5: Ground-Truth Anchoring Engine
├── observability/        # Layer 6: Visualizations and observability
├── reasoning/            # Layer 7: Reasoning & Hypothesis Orchestration
├── common/               # Shared schemas, utilities, and constants
├── scripts/              # Execution scripts for POC
├── tests/                # Unit and integration tests
├── docs/                 # Architecture documentation
└── configs/              # Configuration files (to be created)
```

## Key Principles

1. **Layer Separation**: Each layer has exclusive responsibilities
2. **Determinism**: All randomness is seeded and reproducible
3. **Versioning**: Every artifact is versioned and traceable
4. **Ground Truth**: LLMs never generate numerical outputs; all numbers come from simulation
5. **Invariants**: See `docs/architecture/99-invariants.md` for non-negotiable constraints

## Development Status

This is a **Proof of Concept (POC)** implementation. The system is being built phase-by-phase:

- [x] Phase 0: Repo Scaffolding
- [x] Phase 1: Data Engine (POC Mode)
- [x] Phase 2: Persona Modeling Engine
- [x] Phase 3: IBDE
- [x] Phase 4: LPM
- [x] Phase 5: Ground-Truth Anchoring
- [x] Phase 6: Observability & Visualizations
- [x] Phase 7: Reasoning & Hypothesis Orchestration (LangGraph-compatible)

## License

MIT

