# Django Integration Guide for Agent-Tron

Agent-Tron is built on **FastAPI** (not Django), but can be easily integrated into any Django application.

## Architecture

```
Django Application
    ↓ (HTTP requests)
Agent-Tron FastAPI Server (port 8001)
    ↓ (orchestrates)
4_phases LPM
```

## Installation

### Option 1: Add Agent-Tron as Django App (Recommended)

1. **Copy the integration package to your Django project:**

```bash
# From your Django project root
cp -r agent_tron/django_integration your_project/agent_tron
```

2. **Add to INSTALLED_APPS in settings.py:**

```python
INSTALLED_APPS = [
    # ... your other apps
    'agent_tron',
]
```

3. **Add Agent-Tron settings:**

```python
# settings.py
AGENT_TRON_URL = 'http://localhost:8001'  # Agent-Tron FastAPI server
AGENT_TRON_TIMEOUT = 30  # Request timeout in seconds
```

4. **Include URLs in your main urls.py:**

```python
# your_project/urls.py
from django.urls import path, include

urlpatterns = [
    # ... your other URLs
    path('api/agent_tron/', include('agent_tron.urls')),
]
```

5. **Run migrations (if using models):**

```bash
python manage.py makemigrations agent_tron
python manage.py migrate
```

### Option 2: Use as External Service (Simpler)

Keep Agent-Tron as a separate FastAPI service and call it from Django:

```python
# In your Django views/models
import requests

def get_agent_tron_decision(persona, context, hypothesis):
    response = requests.post(
        'http://localhost:8001/agent_tron/persona_decision',
        json={
            'request_id': f'req_{uuid.uuid4()}',
            'hypothesis': hypothesis,
            'question_type': 'preference',
            'persona': persona,
            'context': context
        }
    )
    return response.json()
```

## Usage Examples

### Example 1: Using the Django Client

```python
# views.py
from agent_tron.django_integration.client import AgentTronClient
from django.http import JsonResponse

def my_view(request):
    client = AgentTronClient()
    
    response = client.get_persona_decision(
        request_id=f"req_{request.user.id}",
        hypothesis="What product would this user prefer?",
        persona={
            "agent_id": str(request.user.id),
            "archetype": "health_conscious",
            "demographics": {
                "age_bucket": "26-35",
                "gender": request.user.profile.gender,
                "region": request.user.profile.region,
                "income": "middle"
            },
            "psychographics": {
                "price_sensitivity": 0.3,
                "novelty_seeking": 0.4,
                "health_consciousness": 0.9,
                "brand_loyalty": 0.6
            }
        },
        context={
            "time_of_day": "morning",
            "location": "cafe"
        },
        num_samples=5  # Get 5 samples
    )
    
    return JsonResponse(response)
```

### Example 2: Using Django Views (Proxy)

If you've added the URLs, you can proxy requests:

```python
# Your Django view
from django.shortcuts import render
import requests

def product_recommendation_view(request):
    # Your logic here
    persona = {...}
    context = {...}
    
    # Call Agent-Tron via Django proxy
    response = requests.post(
        f'{request.build_absolute_uri("/api/agent_tron/persona_decision/")}',
        json={
            'request_id': f'req_{request.user.id}',
            'hypothesis': 'What product should we recommend?',
            'question_type': 'preference',
            'persona': persona,
            'context': context,
            'num_samples': 10
        }
    )
    
    data = response.json()
    return render(request, 'recommendations.html', {
        'decision': data['sampled_decision'],
        'samples': data['sampled_responses']
    })
```

### Example 3: Storing Decisions in Database

```python
# views.py
from agent_tron.django_integration.client import get_client
from agent_tron.django_integration.models import PersonaDecision

def save_decision_view(request):
    client = get_client()
    
    # Get decision from Agent-Tron
    response = client.get_persona_decision(
        request_id=f"req_{request.user.id}_{timezone.now().timestamp()}",
        hypothesis="What product?",
        persona={...},
        context={...}
    )
    
    # Save to database
    PersonaDecision.objects.create(
        request_id=response['request_id'],
        agent_id=response['agent_id'],
        hypothesis=response['hypothesis'],
        question_type='preference',
        persona_data=response.get('persona', {}),
        context_data=response.get('context', {}),
        sampled_decision=response['sampled_decision'],
        sampled_responses=response.get('sampled_responses', []),
        population_prior=response['population_prior'],
        conditioned_distribution=response['conditioned_distribution'],
        uncertainty=response['uncertainty'],
        ground_truth_evidence=response.get('ground_truth_evidence', [])
    )
    
    return JsonResponse(response)
```

### Example 4: Batch Processing

```python
# views.py
from agent_tron.django_integration.client import get_client

def batch_recommendations_view(request):
    client = get_client()
    
    # Get decisions for multiple users
    personas = [
        {
            "agent_id": str(user.id),
            "archetype": user.profile.archetype,
            "demographics": {...},
            "psychographics": {...}
        }
        for user in User.objects.filter(is_active=True)[:10]
    ]
    
    responses = client.get_batch_decisions(
        request_id=f"batch_{timezone.now().timestamp()}",
        hypothesis="Compare preferences across users",
        personas=personas,
        context={"time_of_day": "afternoon", "location": "store"}
    )
    
    # Aggregate results
    aggregated = client.aggregate_responses(responses)
    
    return JsonResponse(aggregated)
```

## Starting Agent-Tron Server

**Important:** Agent-Tron runs as a separate FastAPI server. You need to start it:

```bash
# Terminal 1: Start Agent-Tron
python agent_tron/run_server.py

# Terminal 2: Start Django
python manage.py runserver
```

Or use a process manager like supervisor/systemd to keep it running.

## Configuration

### settings.py

```python
# Agent-Tron Configuration
AGENT_TRON_URL = 'http://localhost:8001'
AGENT_TRON_TIMEOUT = 30

# Optional: Enable request logging
AGENT_TRON_LOG_REQUESTS = True
```

### Environment Variables

```bash
# .env or environment
AGENT_TRON_URL=http://localhost:8001
AGENT_TRON_TIMEOUT=30
```

## Error Handling

```python
from agent_tron.django_integration.client import AgentTronClient
import requests

def safe_decision_view(request):
    client = AgentTronClient()
    
    try:
        response = client.get_persona_decision(...)
        return JsonResponse(response)
    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {'error': 'Agent-Tron server is not running'},
            status=503
        )
    except requests.exceptions.Timeout:
        return JsonResponse(
            {'error': 'Agent-Tron request timed out'},
            status=504
        )
    except requests.exceptions.HTTPError as e:
        return JsonResponse(
            {'error': f'Agent-Tron error: {e.response.text}'},
            status=e.response.status_code
        )
```

## Testing

```python
# tests.py
from django.test import TestCase
from agent_tron.django_integration.client import AgentTronClient
from unittest.mock import patch, Mock

class AgentTronTestCase(TestCase):
    
    @patch('agent_tron.django_integration.client.requests.post')
    def test_persona_decision(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'sampled_decision': {'choice': 'prod_001', 'probability': 0.5}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Test
        client = AgentTronClient()
        response = client.get_persona_decision(
            request_id='test',
            hypothesis='test',
            persona={},
            context={}
        )
        
        self.assertEqual(response['sampled_decision']['choice'], 'prod_001')
```

## Production Deployment

1. **Run Agent-Tron as a service:**
   - Use systemd, supervisor, or Docker
   - Configure reverse proxy (nginx) if needed

2. **Update Django settings:**
```python
AGENT_TRON_URL = 'http://agent-tron-service:8001'  # Internal service URL
```

3. **Add health checks:**
```python
# health_check.py
def check_agent_tron():
    try:
        response = requests.get(f'{settings.AGENT_TRON_URL}/', timeout=5)
        return response.status_code == 200
    except:
        return False
```

## Summary

- **Agent-Tron is FastAPI** (separate service)
- **Django integration** provides client and views
- **Two options**: Add as Django app OR call as external service
- **Always start Agent-Tron server** before using Django integration
- **Use `AgentTronClient`** for easy integration in Django views/models

