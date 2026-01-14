# Quick Start: Django Integration

## Step 1: Start Agent-Tron Server

```bash
# Terminal 1
python agent_tron/run_server.py
```

## Step 2: Add to Your Django Project

### Option A: Copy Integration Package

```bash
# From your Django project root
cp -r agent_tron/django_integration your_project/agent_tron
```

### Option B: Use as External Service (No Copy Needed)

Just use the client directly:

```python
# In your Django views
import sys
sys.path.insert(0, '/path/to/agent_tron')

from django_integration.client import AgentTronClient

client = AgentTronClient()
response = client.get_persona_decision(...)
```

## Step 3: Configure Django Settings

```python
# settings.py
AGENT_TRON_URL = 'http://localhost:8001'
AGENT_TRON_TIMEOUT = 30
```

## Step 4: Use in Your Views

```python
# views.py
from agent_tron.django_integration.client import get_client

def recommend_product(request):
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
        context={
            "time_of_day": "morning",
            "location": "cafe"
        },
        num_samples=5  # Get 5 samples!
    )
    
    return JsonResponse({
        'recommendation': response['sampled_decision']['choice'],
        'samples': response['sampled_responses']
    })
```

## That's It!

Your Django app can now talk to Agent-Tron. See `DJANGO_INTEGRATION.md` for more examples.

