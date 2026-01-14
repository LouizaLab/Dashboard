"""
Django views for Agent-Tron integration
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .client import get_client


@csrf_exempt
@require_http_methods(["POST"])
def persona_decision_view(request):
    """
    Django view wrapper for Agent-Tron persona decision endpoint
    
    Usage:
        POST /agent_tron/persona_decision/
        Body: JSON with request_id, hypothesis, persona, context, etc.
    """
    try:
        data = json.loads(request.body)
        client = get_client()
        
        response = client.get_persona_decision(
            request_id=data.get('request_id'),
            hypothesis=data.get('hypothesis'),
            persona=data.get('persona'),
            context=data.get('context', {}),
            question_type=data.get('question_type', 'preference'),
            num_samples=data.get('num_samples', 1),
            seed=data.get('seed')
        )
        
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=400
        )


@csrf_exempt
@require_http_methods(["POST"])
def batch_decisions_view(request):
    """
    Django view wrapper for Agent-Tron batch decisions endpoint
    """
    try:
        data = json.loads(request.body)
        client = get_client()
        
        response = client.get_batch_decisions(
            request_id=data.get('request_id'),
            hypothesis=data.get('hypothesis'),
            personas=data.get('personas'),
            context=data.get('context', {}),
            question_type=data.get('question_type', 'comparison'),
            seed=data.get('seed')
        )
        
        return JsonResponse({'results': response}, safe=False)
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=400
        )


@method_decorator(csrf_exempt, name='dispatch')
class AgentTronView(View):
    """
    Class-based view for Agent-Tron endpoints
    """
    
    def post(self, request, endpoint):
        """Handle POST requests to Agent-Tron endpoints"""
        try:
            data = json.loads(request.body)
            client = get_client()
            
            if endpoint == 'persona_decision':
                response = client.get_persona_decision(
                    request_id=data.get('request_id'),
                    hypothesis=data.get('hypothesis'),
                    persona=data.get('persona'),
                    context=data.get('context', {}),
                    question_type=data.get('question_type', 'preference'),
                    num_samples=data.get('num_samples', 1),
                    seed=data.get('seed')
                )
                return JsonResponse(response)
            
            elif endpoint == 'batch_decisions':
                response = client.get_batch_decisions(
                    request_id=data.get('request_id'),
                    hypothesis=data.get('hypothesis'),
                    personas=data.get('personas'),
                    context=data.get('context', {}),
                    question_type=data.get('question_type', 'comparison'),
                    seed=data.get('seed')
                )
                return JsonResponse({'results': response}, safe=False)
            
            elif endpoint == 'aggregate':
                response = client.aggregate_responses(data.get('responses', []))
                return JsonResponse(response)
            
            else:
                return JsonResponse(
                    {'error': f'Unknown endpoint: {endpoint}'},
                    status=404
                )
        
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=400
            )

