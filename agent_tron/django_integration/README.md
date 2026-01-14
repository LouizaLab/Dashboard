# Agent-Tron Django Integration

**Agent-Tron is FastAPI, not Django** - but this package makes it easy to use from Django!

## Quick Answer

**Q: Is Agent-Tron built on Django?**  
A: No, Agent-Tron is **FastAPI**. It runs as a separate service.

**Q: How do I integrate it?**  
A: Two options:
1. **Add as Django app** (full integration with models/admin)
2. **Use as external service** (just import the client)

## Architecture

```
┌─────────────────┐
│  Django App     │
│  (Your Code)    │
└────────┬────────┘
         │ HTTP requests
         ↓
┌─────────────────┐
│ Agent-Tron      │
│ FastAPI Server  │  ← Runs on port 8001
│ (port 8001)     │
└────────┬────────┘
         │ orchestrates
         ↓
┌─────────────────┐
│  4_phases LPM   │
│  (ML Models)    │
└─────────────────┘
```

## Installation

### 1. Start Agent-Tron Server

```bash
python agent_tron/run_server.py
```

### 2. Add to Django Project

**Option A: Copy Integration Package**

```bash
# Copy to your Django project
cp -r agent_tron/django_integration your_project/agent_tron

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'agent_tron',
]

# Add settings
AGENT_TRON_URL = 'http://localhost:8001'
```

**Option B: Use Client Directly (No Copy)**

```python
# In your Django views
import sys
sys.path.insert(0, '/path/to/agent_tron')

from django_integration.client import AgentTronClient

client = AgentTronClient()
```

## Usage Examples

### Basic Usage

```python
from agent_tron.django_integration.client import get_client

def my_view(request):
    client = get_client()
    
    response = client.get_persona_decision(
        request_id=f"req_{request.user.id}",
        hypothesis="What product should we recommend?",
        persona={
            "agent_id": str(request.user.id),
            "archetype": "health_conscious",
            "demographics": {...},
            "psychographics": {...}
        },
        context={"time_of_day": "morning"}
    )
    
    return JsonResponse(response)
```

### Multiple Samples

```python
response = client.get_persona_decision(
    ...,
    num_samples=10  # Get 10 samples!
)

# Access samples
primary = response['sampled_decision']
samples = response['sampled_responses']  # 9 additional samples
```

### Batch Processing

```python
responses = client.get_batch_decisions(
    request_id="batch_001",
    hypothesis="Compare preferences",
    personas=[persona1, persona2, persona3],
    context={...}
)

# Aggregate
aggregated = client.aggregate_responses(responses)
```

## Files Included

- `client.py` - Django-friendly client
- `views.py` - Django view wrappers (optional)
- `urls.py` - URL configuration (optional)
- `models.py` - Database models for storing decisions (optional)
- `admin.py` - Django admin interface (optional)
- `example_django_view.py` - Complete examples

## See Also

- `DJANGO_INTEGRATION.md` - Full integration guide
- `QUICK_START.md` - Quick start guide
- `../README.md` - Agent-Tron API documentation

