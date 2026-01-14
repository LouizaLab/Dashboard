# Agent-Tron Integration Guide

## Overview

Agent-Tron is a deterministic API layer that sits on top of the 4-phase LPM. It provides clean JSON endpoints for persona decision-making without using LLMs for decisions.

## Quick Start

### 1. Ensure LPM Models are Trained

```bash
cd 4_phases
python main.py --mode all_phases
```

This creates:
- `checkpoints/best_model.pt` (Phase 1)
- `checkpoints_phase2/best_model_phase2.pt` (Phase 2)
- `phase4_output/` (Phase 4 signals and evidence)

### 2. Start Agent-Tron Server

```bash
# From project root
python agent_tron/run_server.py

# Or using uvicorn directly
uvicorn agent_tron.api.server:app --host 0.0.0.0 --port 8001

# Custom port
AGENT_TRON_PORT=8002 python agent_tron/run_server.py
```

**Note:** Default port is 8001 to avoid conflicts with Django (port 8000).

### 3. Make API Calls

See `agent_tron/README.md` for detailed examples.

## Architecture

```
Dashboard/LLM System
    ↓ (HTTP POST)
Agent-Tron API
    ↓ (orchestrates)
4_phases/lpm_api.py
    ↓ (calls)
Phase 1/2/3/4 Models
```

## Key Principles

1. **Agent-Tron makes decisions** - No LLM calls inside Agent-Tron
2. **Deterministic** - Same inputs → same outputs (via seed)
3. **Strict JSON** - All outputs are structured JSON
4. **Fail fast** - Explicit errors for missing/invalid data
5. **Orchestration only** - Never re-implements LPM logic

## Integration Pattern

### For Dashboard Systems

```python
import requests

# 1. Call Agent-Tron for decision
response = requests.post(
    "http://localhost:8001/agent_tron/persona_decision",
    json={
        "request_id": "dashboard_req_001",
        "hypothesis": "What product would this user prefer?",
        "question_type": "preference",
        "persona": {
            "agent_id": "user_123",
            "archetype": "health_conscious",
            "demographics": {...},
            "psychographics": {...}
        },
        "context": {...}
    }
).json()

# 2. Extract decision
decision = response['sampled_decision']['choice']
probability = response['sampled_decision']['probability']
evidence = response['ground_truth_evidence']

# 3. Pass to GPT-4 for narration (NOT decision-making)
gpt_prompt = f"""
Explain this decision. Do NOT change the decision.
Decision: {decision}
Probability: {probability}
Evidence IDs: {[e['evidence_id'] for e in evidence]}

Constraints:
- Decision is fixed: {response['constraints_for_downstream_llm']['decision_fixed']}
- Must cite evidence IDs: {response['constraints_for_downstream_llm']['must_cite_evidence_ids']}
- Max confidence: {response['constraints_for_downstream_llm']['max_confidence']}
"""
```

## API Endpoints Summary

- `POST /agent_tron/persona_decision` - Single agent decision
- `POST /agent_tron/batch_decisions` - Multiple agents with shared context
- `POST /agent_tron/aggregate` - Aggregate responses into executive summary

## Response Structure

Every response includes:
- `population_prior`: Base distribution for archetype
- `conditioned_distribution`: Persona-specific distribution
- `sampled_decision`: Chosen product with probability
- `dominant_drivers`: Top preference drivers
- `uncertainty`: Entropy and confidence metrics
- `ground_truth_evidence`: Phase 4 evidence references
- `constraints_for_downstream_llm`: Instructions for LLM narration

## Testing

```bash
# Run tests
pytest agent_tron/tests/

# Test determinism
pytest agent_tron/tests/test_determinism.py

# Test contracts
pytest agent_tron/tests/test_contracts.py
```

## Troubleshooting

### Models Not Found

If you see errors about missing models:
1. Ensure `4_phases/checkpoints/best_model.pt` exists
2. Ensure `4_phases/checkpoints_phase2/best_model_phase2.pt` exists
3. Run training: `cd 4_phases && python main.py --mode all_phases`

### Import Errors

If you see import errors:
1. Ensure you're running from project root
2. Check that `4_phases/lpm_api.py` exists
3. Verify Python path includes project root

### Distribution Validation Errors

If distributions don't sum to 1.0:
- This indicates an LPM issue, not Agent-Tron
- Check LPM model outputs
- Verify data files are correct

## Next Steps

1. Train LPM models if not already done
2. Start Agent-Tron server
3. Test with example requests
4. Integrate with your dashboard/LLM system
5. Use GPT-4 for narration only, not decisions

