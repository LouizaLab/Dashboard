# Agent-Tron API

Agent-Tron is a clean API layer that sits on top of the grounded 4-phase LPM (Latent Preference Model). It exposes deterministic, JSON-based decision-making endpoints for persona agents without using LLMs for decisions.

## Overview

Agent-Tron orchestrates calls to the underlying LPM to provide:
- **Population priors**: Base preference distributions for archetypes
- **Conditioned distributions**: Persona-specific preferences conditioned on context
- **Sampled decisions**: Deterministic choices with probabilities
- **Uncertainty metrics**: Entropy and confidence measures
- **Phase 4 grounding**: Evidence references from ground-truth anchoring

## Architecture

```
agent_tron/
├── api/
│   └── server.py              # FastAPI server
├── core/
│   ├── handler.py             # Orchestration pipeline
│   ├── lpm_adapter.py         # Bridge to 4_phases/lpm_api.py
│   └── seeding.py             # Deterministic seeding
├── schemas/
│   ├── request.py             # Pydantic request models
│   └── response.py            # Pydantic response models
├── aggregation/
│   └── aggregate.py           # Executive summary aggregation
├── utils/
│   └── validation.py          # Distribution validation
└── tests/
    ├── test_contracts.py      # Response contract tests
    ├── test_determinism.py    # Determinism tests
    └── test_sums_to_one.py    # Distribution validation tests
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure 4_phases models are trained
cd 4_phases
python main.py --mode all_phases
```

## Quick Start

### Start the Server

```bash
# From project root
python agent_tron/run_server.py

# Or using uvicorn directly
uvicorn agent_tron.api.server:app --host 0.0.0.0 --port 8001

# Or set custom port via environment variable
AGENT_TRON_PORT=8002 python agent_tron/run_server.py
```

**Note:** Default port is 8001 to avoid conflicts with Django (port 8000).

### Example: Single Persona Decision

```bash
curl -X POST "http://localhost:8001/agent_tron/persona_decision" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "hypothesis": "Which product would this persona prefer?",
    "question_type": "preference",
    "persona": {
      "agent_id": "agent_001",
      "archetype": "health_conscious",
      "demographics": {
        "age_bucket": "26-35",
        "gender": "female",
        "region": "north",
        "income": "middle"
      },
      "psychographics": {
        "price_sensitivity": 0.3,
        "novelty_seeking": 0.4,
        "health_consciousness": 0.9,
        "brand_loyalty": 0.6
      }
    },
    "context": {
      "time_of_day": "morning",
      "location": "cafe",
      "region": "north"
    },
    "seed": 42
  }'
```

### Example: Multiple Samples

To get multiple sampled responses from the LPM:

```bash
curl -X POST "http://localhost:8001/agent_tron/persona_decision" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_002",
    "hypothesis": "What products would this persona choose?",
    "question_type": "preference",
    "num_samples": 10,
    "persona": {
      "agent_id": "agent_001",
      "archetype": "health_conscious",
      "demographics": {
        "age_bucket": "26-35",
        "gender": "female",
        "region": "north",
        "income": "middle"
      },
      "psychographics": {
        "price_sensitivity": 0.3,
        "novelty_seeking": 0.4,
        "health_consciousness": 0.9,
        "brand_loyalty": 0.6
      }
    },
    "context": {
      "time_of_day": "morning",
      "location": "cafe"
    }
  }'
```

This will return:
- `sampled_decision`: Primary sample (for backward compatibility)
- `sampled_responses`: List of additional samples (if `num_samples > 1`)

Test sampling with:
```bash
python agent_tron/test_sampling.py
```

### Example Response

```json
{
  "request_id": "req_001",
  "agent_id": "agent_001",
  "hypothesis": "Which product would this persona prefer?",
  "population_prior": {
    "product_1": 0.15,
    "product_2": 0.25,
    "product_3": 0.30,
    "product_4": 0.20,
    "product_5": 0.10
  },
  "conditioned_distribution": {
    "product_1": 0.10,
    "product_2": 0.20,
    "product_3": 0.45,
    "product_4": 0.15,
    "product_5": 0.10
  },
  "sampled_decision": {
    "choice": "product_3",
    "probability": 0.45,
    "alternatives": {
      "product_2": 0.20,
      "product_4": 0.15,
      "product_1": 0.10,
      "product_5": 0.10
    }
  },
  "dominant_drivers": [
    {"product_id": "product_3", "probability": 0.45},
    {"product_id": "product_2", "probability": 0.20},
    {"product_id": "product_4", "probability": 0.15}
  ],
  "uncertainty": {
    "entropy": 2.15,
    "confidence": 0.45
  },
  "ground_truth_evidence": [
    {
      "evidence_id": "intent_index_1",
      "source_type": "intent_index",
      "date": "2024-01-15",
      "excerpt": "Intent value: 0.723",
      "tags": ["intent", "time_series"],
      "weight": 0.8
    }
  ],
  "lpm_trace": {
    "phase4_output_dir": "phase4_output",
    "signals_dir": "phase4_output/signals",
    "model_version": "1.0",
    "run_id": "req_001"
  },
  "constraints_for_downstream_llm": {
    "decision_fixed": true,
    "no_new_evidence": true,
    "must_cite_evidence_ids": true,
    "max_confidence": 0.45,
    "entropy": 2.15
  }
}
```

### Example: Batch Decisions

```bash
curl -X POST "http://localhost:8001/agent_tron/batch_decisions" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "batch_001",
    "hypothesis": "Compare preferences across personas",
    "question_type": "comparison",
    "personas": [
      {
        "agent_id": "agent_001",
        "archetype": "health_conscious",
        "demographics": {
          "age_bucket": "26-35",
          "gender": "female",
          "region": "north",
          "income": "middle"
        },
        "psychographics": {
          "price_sensitivity": 0.3,
          "novelty_seeking": 0.4,
          "health_consciousness": 0.9,
          "brand_loyalty": 0.6
        }
      },
      {
        "agent_id": "agent_002",
        "archetype": "price_sensitive",
        "demographics": {
          "age_bucket": "18-25",
          "gender": "male",
          "region": "south",
          "income": "low"
        },
        "psychographics": {
          "price_sensitivity": 0.9,
          "novelty_seeking": 0.2,
          "health_consciousness": 0.3,
          "brand_loyalty": 0.4
        }
      }
    ],
    "context": {
      "time_of_day": "afternoon",
      "location": "store"
    }
  }'
```

### Example: Aggregate Responses

```bash
curl -X POST "http://localhost:8001/agent_tron/aggregate" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "request_id": "req_001",
      "agent_id": "agent_001",
      "hypothesis": "Test",
      "population_prior": {"p1": 0.5, "p2": 0.5},
      "conditioned_distribution": {"p1": 0.6, "p2": 0.4},
      "sampled_decision": {"choice": "p1", "probability": 0.6, "alternatives": {}},
      "dominant_drivers": [],
      "uncertainty": {"entropy": 1.0, "confidence": 0.6},
      "ground_truth_evidence": [],
      "lpm_trace": {},
      "constraints_for_downstream_llm": {}
    }
  ]'
```

## API Endpoints

### POST `/agent_tron/persona_decision`

Single agent decision endpoint.

**Request Body:**
- `request_id` (str): Unique request identifier
- `hypothesis` (str): Hypothesis/question to answer
- `question_type` (str): One of "comparison", "what_if", "forecast", "preference"
- `persona` (Persona): Persona object with agent_id, archetype, demographics, psychographics
- `context` (Context): Context object with time_of_day, location, region, etc.
- `seed` (int, optional): Random seed for determinism

**Response:**
- `PersonaDecisionResponse` with all decision components

### POST `/agent_tron/batch_decisions`

Batch decisions for multiple personas with shared hypothesis/context.

**Request Body:**
- `request_id` (str): Unique request identifier
- `hypothesis` (str): Hypothesis/question
- `question_type` (str): Question type
- `personas` (List[Persona]): List of personas
- `context` (Context): Shared context
- `seed` (int, optional): Random seed

**Response:**
- List of `PersonaDecisionResponse`

### POST `/agent_tron/aggregate`

Aggregate multiple responses into executive summary.

**Request Body:**
- List of `PersonaDecisionResponse`

**Response:**
- `AggregateResponse` with:
  - `agents_tested`: Number of agents
  - `preference_breakdown`: Weighted aggregate distribution
  - `segment_insights`: Insights grouped by archetype
  - `top_drivers`: Top preference drivers
  - `overall_entropy`: Aggregate entropy
  - `overall_confidence`: Weighted average confidence
  - `evidence_coverage`: Evidence statistics

## Determinism

Agent-Tron is fully deterministic:
- Same `request_id` + `agent_id` + `seed` → identical `sampled_decision`
- If `seed` not provided, derived deterministically from `request_id` + `agent_id`
- All distributions validated to sum to 1.0 within tolerance

## Integration with Dashboard

For dashboard integration:

1. **Call Agent-Tron** to get decision:
   ```python
   response = requests.post(
       "http://localhost:8000/agent_tron/persona_decision",
       json=request_data
   ).json()
   ```

2. **Pass to GPT-4** with strict instructions:
   ```
   Explain this decision. Do NOT change the decision.
   Cite evidence IDs from ground_truth_evidence.
   Decision: {response['sampled_decision']['choice']}
   Probability: {response['sampled_decision']['probability']}
   Evidence: {response['ground_truth_evidence']}
   ```

Agent-Tron makes the decision; GPT-4 narrates it.

## Testing

### Quick Test Script

Run the comprehensive test suite:

```bash
# Make sure server is running first
python agent_tron/run_server.py

# In another terminal, run tests
python agent_tron/test_agent_tron.py
```

This will test:
- Root endpoint
- Single persona decision
- Determinism (same inputs → same outputs)
- Batch decisions
- Aggregation
- Context sensitivity

### Example Usage

See how to use Agent-Tron programmatically:

```bash
python agent_tron/example_usage.py
```

### Unit Tests

```bash
# Run all unit tests
pytest agent_tron/tests/

# Run specific test file
pytest agent_tron/tests/test_contracts.py
pytest agent_tron/tests/test_determinism.py
pytest agent_tron/tests/test_sums_to_one.py
```

## Non-Negotiable Rules

1. **No LLM decisions**: Agent-Tron never uses GPT/LLM to make decisions
2. **No re-implementation**: Agent-Tron only orchestrates, never re-implements phase logic
3. **Strict JSON**: All outputs are JSON; no free-text decisions
4. **Fail fast**: Missing/invalid LPM outputs raise explicit errors
5. **Deterministic**: Same inputs → same outputs (via seed)

## Error Handling

Agent-Tron fails fast with explicit errors:
- Missing LPM models → 500 error with details
- Invalid distributions → 400 error with validation details
- Missing Phase 4 outputs → Warning, empty evidence list

## Configuration

Default paths (can be overridden in `DecisionHandler`):
- `phase1_checkpoint`: `4_phases/checkpoints/best_model.pt`
- `phase2_checkpoint`: `4_phases/checkpoints_phase2/best_model_phase2.pt`
- `data_dir`: `4_phases/data`

## License

[Your License Here]

