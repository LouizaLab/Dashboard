"""
Example Django views showing how to use Agent-Tron
"""

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from agent_tron.django_integration.client import get_client
import json


@method_decorator(csrf_exempt, name='dispatch')
class ProductRecommendationView(View):
    """
    Example: Get product recommendation for a user
    """
    
    def post(self, request):
        """Get product recommendation"""
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            # Get user profile (adjust based on your User model)
            # user = User.objects.get(id=user_id)
            # profile = user.profile
            
            # Build persona from user data
            persona = {
                "agent_id": str(user_id),
                "archetype": "health_conscious",  # or from user.profile
                "demographics": {
                    "age_bucket": "26-35",  # or from user.profile.age_bucket
                    "gender": "female",  # or from user.profile.gender
                    "region": "north",  # or from user.profile.region
                    "income": "middle"  # or from user.profile.income
                },
                "psychographics": {
                    "price_sensitivity": 0.3,  # or from user.profile
                    "novelty_seeking": 0.4,
                    "health_consciousness": 0.9,
                    "brand_loyalty": 0.6
                }
            }
            
            # Get context from request
            context = {
                "time_of_day": data.get('time_of_day', 'morning'),
                "location": data.get('location', 'cafe'),
                "region": data.get('region', 'north')
            }
            
            # Get decision from Agent-Tron
            client = get_client()
            response = client.get_persona_decision(
                request_id=f"req_{user_id}_{data.get('session_id', 'default')}",
                hypothesis="What product should we recommend to this user?",
                persona=persona,
                context=context,
                num_samples=5  # Get 5 samples to show variability
            )
            
            return JsonResponse({
                'success': True,
                'recommendation': response['sampled_decision']['choice'],
                'probability': response['sampled_decision']['probability'],
                'alternatives': response['sampled_decision']['alternatives'],
                'samples': [
                    {
                        'choice': s['choice'],
                        'probability': s['probability']
                    }
                    for s in response.get('sampled_responses', [])
                ],
                'confidence': response['uncertainty']['confidence'],
                'entropy': response['uncertainty']['entropy']
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class BatchComparisonView(View):
    """
    Example: Compare preferences across multiple users
    """
    
    def post(self, request):
        """Compare preferences for multiple users"""
        try:
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            
            # Build personas for each user
            personas = []
            for user_id in user_ids:
                # In real app, fetch user data
                personas.append({
                    "agent_id": str(user_id),
                    "archetype": "balanced",
                    "demographics": {
                        "age_bucket": "26-35",
                        "gender": "male",
                        "region": "south",
                        "income": "middle"
                    },
                    "psychographics": {
                        "price_sensitivity": 0.5,
                        "novelty_seeking": 0.5,
                        "health_consciousness": 0.5,
                        "brand_loyalty": 0.5
                    }
                })
            
            # Get batch decisions
            client = get_client()
            responses = client.get_batch_decisions(
                request_id=f"batch_{data.get('session_id', 'default')}",
                hypothesis="Compare preferences across users",
                personas=personas,
                context=data.get('context', {
                    "time_of_day": "afternoon",
                    "location": "store"
                })
            )
            
            # Aggregate results
            aggregated = client.aggregate_responses(responses)
            
            return JsonResponse({
                'success': True,
                'individual_results': [
                    {
                        'user_id': r['agent_id'],
                        'choice': r['sampled_decision']['choice'],
                        'probability': r['sampled_decision']['probability']
                    }
                    for r in responses
                ],
                'aggregate': {
                    'top_preferences': dict(list(aggregated['preference_breakdown'].items())[:10]),
                    'overall_confidence': aggregated['overall_confidence'],
                    'overall_entropy': aggregated['overall_entropy']
                }
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


# Add to your urls.py:
# urlpatterns = [
#     path('api/recommend/', ProductRecommendationView.as_view(), name='recommend'),
#     path('api/compare/', BatchComparisonView.as_view(), name='compare'),
# ]

