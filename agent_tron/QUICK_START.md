# Agent-Tron Quick Start

## Start the Server

```bash
# From project root
python agent_tron/run_server.py
```

Server will start on **port 8001** (to avoid conflicts with Django on port 8000).

## Test the API

```bash
# Test root endpoint
curl http://localhost:8001/

# Test persona decision endpoint
curl -X POST "http://localhost:8001/agent_tron/persona_decision" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_001",
    "hypothesis": "Test hypothesis",
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
      "location": "cafe"
    }
  }'
```

## Troubleshooting

### Port Already in Use

If port 8001 is also in use:

```bash
AGENT_TRON_PORT=8002 python agent_tron/run_server.py
```

### Models Not Found

Ensure LPM models are trained:

```bash
cd 4_phases
python main.py --mode all_phases
```

This creates:
- `checkpoints/best_model.pt`
- `checkpoints_phase2/best_model_phase2.pt`

### Import Errors

Run from project root:

```bash
cd /Users/rohitganti/Desktop/Louiza
python agent_tron/run_server.py
```

## API Documentation

Once server is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

