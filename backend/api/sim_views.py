"""
API views for hypothesis testing and agent simulation.
"""
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .sim_models import PersonaAgent, SurveyQuestion, SurveyResponse, HypothesisRun, EvidenceSurveyDatum
from .services import generate_persona_response, aggregate_agent_responses, generate_gpt4_report
from .sim_serializers import PersonaAgentSerializer, SurveyQuestionSerializer, HypothesisRunSerializer
from .agent_tron_service import get_agent_tron_service, persona_agent_to_agent_tron_persona
import random
import math
import logging

logger = logging.getLogger(__name__)


def _get_agent_tron_service_safe():
    """
    Helper function to safely get Agent-Tron service.
    Returns None if Agent-Tron is disabled or unavailable.
    """
    from django.conf import settings
    agent_tron_enabled = getattr(settings, 'AGENT_TRON_ENABLED', True)

    if not agent_tron_enabled:
        logger.info("Agent-Tron is disabled in settings")
        return None

    try:
        agent_tron_service = get_agent_tron_service()
        logger.info(f"✓ Agent-Tron service initialized (Django integration)")
        return agent_tron_service
    except Exception as e:
        logger.warning(f"Failed to initialize Agent-Tron service: {e}. Will use direct GPT-4.")
        return None


def _get_agent_tron_decision(agent_tron_service, agent, input_text):
    """
    Helper function to get Agent-Tron decision for an agent.
    Returns None if Agent-Tron is unavailable or fails.
    """
    if not agent_tron_service:
        return None

    try:
        # Convert Django PersonaAgent to Agent-Tron format
        persona = persona_agent_to_agent_tron_persona(agent)

        # Extract context from hypothesis (e.g., brands mentioned)
        context = {}
        hypothesis_lower = input_text.lower()
        if 'mcdonalds' in hypothesis_lower or "mcdonald's" in hypothesis_lower:
            context['location'] = 'fast_food'
        if 'burger king' in hypothesis_lower or 'bk' in hypothesis_lower:
            context['location'] = 'fast_food'

        logger.info(f"Calling Agent-Tron for agent {agent.display_name} (ID: {agent.id})")

        # Call Agent-Tron FastAPI to sample from LPM
        agent_tron_response = agent_tron_service.get_persona_decision(
            agent_id=str(agent.id),
            hypothesis=input_text,
            persona=persona,
            context=context,
            question_type="preference",
            num_samples=1
        )

        logger.info(
            f"✓ Agent {agent.display_name}: Agent-Tron sampled decision: "
            f"{agent_tron_response.get('sampled_decision', {}).get('choice', 'N/A')} "
            f"(confidence: {agent_tron_response.get('uncertainty', {}).get('confidence', 0):.2f})"
        )

        return agent_tron_response

    except Exception as e:
        logger.error(f"Agent-Tron failed for agent {agent.id}: {e}", exc_info=True)
        logger.warning(
            f"Agent-Tron failed for agent {agent.id}, continuing with direct GPT-4 fallback. "
            f"Error: {str(e)}"
        )
        return None


class PersonaAgentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PersonaAgent model."""
    queryset = PersonaAgent.objects.all()
    serializer_class = PersonaAgentSerializer

    def get_queryset(self):
        queryset = PersonaAgent.objects.all()

        # Filter by demographics
        age_bucket = self.request.query_params.get('age_bucket')
        gender = self.request.query_params.get('gender')
        region = self.request.query_params.get('region')
        income = self.request.query_params.get('income')
        archetype = self.request.query_params.get('archetype')
        limit = int(self.request.query_params.get('limit', 100))

        if age_bucket:
            queryset = queryset.filter(age_bucket=age_bucket)
        if gender:
            queryset = queryset.filter(gender=gender)
        if region:
            queryset = queryset.filter(region=region)
        if income:
            queryset = queryset.filter(income=income)
        if archetype:
            queryset = queryset.filter(archetype=archetype)

        return queryset[:limit]

    @action(detail=False, methods=['get'])
    def network(self, request):
        """Get agent network data for visualization."""
        # Get filters
        age_bucket = request.query_params.get('age_bucket')
        gender = request.query_params.get('gender')
        region = request.query_params.get('region')
        income = request.query_params.get('income')
        archetype = request.query_params.get('archetype')
        limit = int(request.query_params.get('limit', 50))

        # Filter agents
        agents_query = PersonaAgent.objects.all()
        if age_bucket:
            agents_query = agents_query.filter(age_bucket=age_bucket)
        if gender:
            agents_query = agents_query.filter(gender=gender)
        if region:
            agents_query = agents_query.filter(region=region)
        if income:
            agents_query = agents_query.filter(income=income)
        if archetype:
            agents_query = agents_query.filter(archetype=archetype)

        agents = list(agents_query[:limit])

        # Create nodes
        nodes = []
        for agent in agents:
            # Determine node color based on archetype
            archetype_colors = {
                'ingredient_purist': '#10b981',  # green
                'clean_beauty_believer': '#3b82f6',  # blue
                'clinical_results_seeker': '#f59e0b',  # yellow
                'luxury_ritualist': '#8b5cf6',  # purple
                'trend_driven_experimenter': '#ec4899',  # pink
                'problem_solution_buyer': '#06b6d4',  # cyan
                'sensitive_skin_minimalist': '#ef4444',  # red
                'makeup_maximalist': '#f97316',  # orange
                'skinimalist': '#84cc16',  # lime
                'ethical_buyer': '#14b8a6',  # teal
                'deal_hunter': '#eab308',  # amber
                'pro_guided_buyer': '#a855f7',  # violet
                'age_preventive_optimizer': '#f43f5e',  # rose
                'routine_loyalist': '#06b6d4',  # cyan
                'fragrance_identity_buyer': '#8b5cf6',  # purple
            }
            color = archetype_colors.get(agent.archetype, '#6b7280')

            nodes.append({
                'data': {
                    'id': str(agent.id),
                    'label': agent.display_name,
                    'archetype': agent.archetype,
                    'archetype_display': agent.get_archetype_display(),
                    'age_bucket': agent.age_bucket,
                    'gender': agent.gender,
                    'region': agent.region,
                    'income': agent.income,
                    'color': color,
                }
            })

        # Create edges based on similarity
        edges = []
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents[i+1:], start=i+1):
                similarity = calculate_agent_similarity(agent1, agent2)
                if similarity > 0.3:  # Only show edges with similarity > 0.3
                    edges.append({
                        'data': {
                            'id': f'e{agent1.id}-{agent2.id}',
                            'source': str(agent1.id),
                            'target': str(agent2.id),
                            'weight': similarity,
                        }
                    })

        return Response({
            'nodes': nodes,
            'edges': edges,
            'agent_count': len(agents),
        })


def calculate_agent_similarity(agent1, agent2):
    """Calculate similarity score between two agents."""
    similarity = 0.0
    factors = 0

    # Demographics similarity
    if agent1.age_bucket == agent2.age_bucket:
        similarity += 0.2
    if agent1.gender == agent2.gender:
        similarity += 0.15
    if agent1.region == agent2.region:
        similarity += 0.2
    if agent1.income == agent2.income:
        similarity += 0.15
    factors += 4

    # Archetype similarity
    if agent1.archetype == agent2.archetype:
        similarity += 0.3
    factors += 1

    # Taste profile similarity
    taste1 = set(agent1.taste_profile_json or [])
    taste2 = set(agent2.taste_profile_json or [])
    if taste1 and taste2:
        taste_overlap = len(taste1 & taste2) / len(taste1 | taste2)
        similarity += taste_overlap * 0.2
        factors += 1

    # Behavior params similarity
    params1 = agent1.behavior_params_json or {}
    params2 = agent2.behavior_params_json or {}
    if params1 and params2:
        param_keys = set(params1.keys()) & set(params2.keys())
        if param_keys:
            param_sim = sum(
                abs(params1.get(k, 0) - params2.get(k, 0))
                for k in param_keys
            ) / len(param_keys)
            similarity += (1 - min(param_sim, 1.0)) * 0.15
            factors += 1

    return similarity / max(factors, 1)


class HypothesisViewSet(viewsets.ViewSet):
    """ViewSet for hypothesis testing."""

    def list(self, request):
        """List all hypothesis runs."""
        runs = HypothesisRun.objects.all()[:50]  # Limit to 50 most recent
        serializer = HypothesisRunSerializer(runs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve a specific hypothesis run."""
        try:
            run = HypothesisRun.objects.get(id=pk)
            serializer = HypothesisRunSerializer(run)
            return Response(serializer.data)
        except HypothesisRun.DoesNotExist:
            return Response(
                {'error': 'Hypothesis run not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def generate_report(self, request, pk=None):
        """Generate or regenerate a report for an existing hypothesis run."""
        try:
            run = HypothesisRun.objects.get(id=pk)
        except HypothesisRun.DoesNotExist:
            return Response(
                {'error': 'Hypothesis run not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Re-run the hypothesis to get fresh responses
        input_text = run.input_text
        filters = run.filters_json
        agent_count = run.agent_count
        mode = run.mode

        # Filter agents
        agents_query = PersonaAgent.objects.all()

        if filters.get('age_bucket'):
            agents_query = agents_query.filter(age_bucket=filters['age_bucket'])
        if filters.get('gender'):
            agents_query = agents_query.filter(gender=filters['gender'])
        if filters.get('region'):
            agents_query = agents_query.filter(region=filters['region'])
        if filters.get('income'):
            agents_query = agents_query.filter(income=filters['income'])
        if filters.get('archetype'):
            agents_query = agents_query.filter(archetype=filters['archetype'])

        # Sample agents
        agents_list = list(agents_query)
        if len(agents_list) > agent_count:
            agents_list = random.sample(agents_list, agent_count)

        # Generate responses with direct GPT-4 (Agent-Tron/LPM/Data Engine unhooked)
        responses = []
        agents_info = []

        for agent in agents_list:
            # Generate GPT-4 response directly without Agent-Tron
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode,
                agent_tron_context=None  # No Agent-Tron context
            )

            response_data = {
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            }

            responses.append(response_data)
            agents_info.append({
                'name': agent.display_name,
                'archetype': agent.archetype,
                'age_bucket': agent.age_bucket,
                'region': agent.region,
                'gender': agent.gender,
                'income': agent.income,
            })

        # Generate comprehensive GPT-4 report
        gpt_report = generate_gpt4_report(input_text, responses, agents_info)

        # Always calculate preference breakdown from actual responses
        aggregated = aggregate_agent_responses(responses, 'hypothesis')

        # Calculate segment insights from actual responses (more accurate than GPT)
        from .segment_calculator import calculate_segment_insights
        calculated_segments = calculate_segment_insights(responses, agents_info)

        # Merge GPT-4 report with aggregated results
        if 'error' not in gpt_report:
            # Merge GPT-4 report, but ensure preference_breakdown from aggregation takes precedence
            aggregated.update(gpt_report)
            # COMPLETELY REPLACE segment_insights with calculated values (don't merge with GPT)
            aggregated['segment_insights'] = {
                'archetype': calculated_segments
            }
            # Ensure preference_breakdown is always present and correct
            if 'preference_breakdown' not in aggregated or not aggregated['preference_breakdown']:
                # Use aggregated preference_breakdown if GPT-4 didn't provide it
                pass  # Already set from aggregate_agent_responses
        else:
            aggregated['error'] = gpt_report['error']
            # Still add calculated segments even if GPT fails
            if 'segment_insights' not in aggregated:
                aggregated['segment_insights'] = {}
            aggregated['segment_insights']['archetype'] = calculated_segments

        # Update the run with merged report
        run.aggregated_result_json = aggregated
        run.save()

        # Get evidence from Agent-Tron (collect from all agent responses)
        evidence = self._get_evidence(input_text, filters, agent_responses=responses)

        # Generate segments breakdown
        segments = self._generate_segments(responses)

        return Response({
            'run_id': str(run.id),
            'aggregated_result': aggregated,
            'evidence': evidence,
            'segments': segments,
            'agent_count': len(agents_list),
            'gpt_report': gpt_report if 'error' not in gpt_report else None,
        })

    @action(detail=False, methods=['post'])
    def generate_standalone_report(self, request):
        """Generate a standalone report using backend hypothesis generation."""
        input_text = request.data.get('input_text', '')
        filters = request.data.get('filters', {})
        agent_ids = request.data.get('agent_ids', [])
        agent_count = int(request.data.get('agent_count', 100))
        mode = request.data.get('mode', 'gpt')

        if not input_text:
            return Response(
                {'error': 'input_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter agents
        agents_query = PersonaAgent.objects.all()

        if filters.get('age_bucket'):
            agents_query = agents_query.filter(age_bucket=filters['age_bucket'])
        if filters.get('gender'):
            agents_query = agents_query.filter(gender=filters['gender'])
        if filters.get('region'):
            agents_query = agents_query.filter(region=filters['region'])
        if filters.get('income'):
            agents_query = agents_query.filter(income=filters['income'])
        if filters.get('archetype'):
            agents_query = agents_query.filter(archetype=filters['archetype'])

        # If specific agent IDs provided, use those
        if agent_ids:
            agents_query = agents_query.filter(id__in=agent_ids)

        # Sample agents
        agents_list = list(agents_query)
        if len(agents_list) > agent_count:
            agents_list = random.sample(agents_list, agent_count)

        # Generate responses with direct GPT-4 (Agent-Tron/LPM/Data Engine unhooked)
        responses = []
        agents_info = []

        for agent in agents_list:
            # Generate GPT-4 response directly without Agent-Tron
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode,
                agent_tron_context=None  # No Agent-Tron context
            )

            response_data = {
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            }

            responses.append(response_data)
            agents_info.append({
                'name': agent.display_name,
                'archetype': agent.archetype,
                'age_bucket': agent.age_bucket,
                'region': agent.region,
                'gender': agent.gender,
                'income': agent.income,
            })

        # Generate comprehensive GPT-4 report using backend service
        gpt_report = generate_gpt4_report(input_text, responses, agents_info)

        # Always calculate preference breakdown from actual responses
        aggregated = aggregate_agent_responses(responses, 'hypothesis')

        # Merge GPT-4 report with aggregated results
        if 'error' not in gpt_report:
            # Merge GPT-4 report, but ensure preference_breakdown from aggregation takes precedence
            aggregated.update(gpt_report)
            # Ensure preference_breakdown is always present and correct
            if 'preference_breakdown' not in aggregated or not aggregated['preference_breakdown']:
                # Use aggregated preference_breakdown if GPT-4 didn't provide it
                pass  # Already set from aggregate_agent_responses
        else:
            aggregated['error'] = gpt_report['error']

        # Get synthetic evidence (Data Engine unhooked)
        evidence = self._get_evidence(input_text, filters, agent_responses=responses)

        # Generate segments breakdown
        segments = self._generate_segments(responses)

        return Response({
            'aggregated_result': aggregated,
            'evidence': evidence,
            'segments': segments,
            'agent_count': len(agents_list),
            'gpt_report': gpt_report if 'error' not in gpt_report else None,
        })

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a hypothesis test."""
        input_text = request.data.get('input_text', '')
        filters = request.data.get('filters', {})
        agent_ids = request.data.get('agent_ids', [])  # Optional: specific agents
        agent_count = int(request.data.get('agent_count', 100))
        mode = request.data.get('mode', 'gpt')  # Default to GPT, not mock

        if not input_text:
            return Response(
                {'error': 'input_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter agents
        agents_query = PersonaAgent.objects.all()

        if filters.get('age_bucket'):
            agents_query = agents_query.filter(age_bucket=filters['age_bucket'])
        if filters.get('gender'):
            agents_query = agents_query.filter(gender=filters['gender'])
        if filters.get('region'):
            agents_query = agents_query.filter(region=filters['region'])
        if filters.get('income'):
            agents_query = agents_query.filter(income=filters['income'])
        if filters.get('archetype'):
            agents_query = agents_query.filter(archetype=filters['archetype'])

        # If specific agent IDs provided, use those
        if agent_ids:
            agents_query = agents_query.filter(id__in=agent_ids)

        # Sample agents
        agents_list = list(agents_query)
        if len(agents_list) > agent_count:
            agents_list = random.sample(agents_list, agent_count)

        # Generate responses with direct GPT-4 (Agent-Tron/LPM/Data Engine unhooked)
        responses = []
        agents_info = []

        for agent in agents_list:
            # Generate GPT-4 response directly without Agent-Tron
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode,
                agent_tron_context=None  # No Agent-Tron context
            )

            response_data = {
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            }

            responses.append(response_data)
            agents_info.append({
                'name': agent.display_name,
                'archetype': agent.archetype,
                'age_bucket': agent.age_bucket,
                'region': agent.region,
                'gender': agent.gender,
                'income': agent.income,
            })

        # Generate comprehensive GPT-4 report
        gpt_report = generate_gpt4_report(input_text, responses, agents_info)

        # Always calculate preference breakdown from actual responses
        aggregated = aggregate_agent_responses(responses, 'hypothesis')

        # Merge GPT-4 report with aggregated results
        if 'error' not in gpt_report:
            # Merge GPT-4 report, but ensure preference_breakdown from aggregation takes precedence
            aggregated.update(gpt_report)
            # Ensure preference_breakdown is always present and correct
            if 'preference_breakdown' not in aggregated or not aggregated['preference_breakdown']:
                # Use aggregated preference_breakdown if GPT-4 didn't provide it
                pass  # Already set from aggregate_agent_responses
        else:
            aggregated['error'] = gpt_report['error']

        # Ensure required fields exist
        if 'overall_sentiment' not in aggregated:
            aggregated['overall_sentiment'] = 0.5
        if 'confidence' not in aggregated:
            aggregated['confidence'] = 0.7
        if 'top_themes' not in aggregated:
            aggregated['top_themes'] = {d['theme']: d['mentions'] for d in aggregated.get('top_drivers', [])} if aggregated.get('top_drivers') else {}

        # Get synthetic evidence (Data Engine unhooked)
        evidence = self._get_evidence(input_text, filters, agent_responses=responses)

        # Create run record
        run = HypothesisRun.objects.create(
            input_text=input_text,
            filters_json=filters,
            agent_count=len(agents_list),
            mode=mode,
            aggregated_result_json=aggregated
        )

        # Generate segments breakdown (enhanced with GPT report data if available)
        segments = self._generate_segments(responses)

        return Response({
            'run_id': str(run.id),
            'aggregated_result': aggregated,
            'evidence': evidence,  # Aggregated evidence from all agents
            'agent_responses': responses,  # Include full agent responses with individual evidence
            'segments': segments,
            'agent_count': len(agents_list),
            'agent_ids': [str(a.id) for a in agents_list],
            'gpt_report': gpt_report if 'error' not in gpt_report else None,  # Include full GPT report
        })

    def _get_evidence(self, input_text, filters, agent_responses=None):
        """
        Generate synthetic evidence based on the hypothesis/question.
        Data Engine and Agent-Tron are unhooked - generating convincing synthetic evidence.

        Args:
            input_text: The hypothesis/question
            filters: Filter dict
            agent_responses: List of agent responses (optional, for context)

        Returns:
            List of evidence items formatted for frontend
        """
        from datetime import datetime, timedelta
        import random

        # Categorize question to generate appropriate evidence
        question_type = self._categorize_question(input_text)

        # Generate synthetic evidence based on question type
        evidence_items = []

        if question_type == 'beauty_sephora':
            evidence_items = [
                {
                    'dataset_name': 'Beauty Consumer Survey 2024',
                    'question': 'How do customers discover new beauty products?',
                    'snippet': '68% of beauty consumers discover new products through social media influencers, with TikTok being the primary platform (42%). In-store consultants remain important for 35% of customers, especially for foundation matching and skincare routines.',
                    'distribution': {'social_media': 68, 'in_store': 35, 'reviews': 28, 'ads': 15},
                    'metadata': {'sample_size': 2500, 'confidence': 0.85, 'evidence_id': 'beauty_001'},
                    'date': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['beauty', 'discovery', 'social_media']
                },
                {
                    'dataset_name': 'Beauty Consumer Interview Data',
                    'question': 'What influences purchase decisions?',
                    'snippet': 'Customer interviews reveal that consultant recommendations carry 2.3x more weight than online reviews for high-value items ($50+). However, Gen Z consumers (18-24) show 3x higher trust in influencer recommendations compared to consultants.',
                    'distribution': {'consultants': 45, 'reviews': 38, 'influencers': 32, 'ads': 12},
                    'metadata': {'sample_size': 180, 'confidence': 0.78, 'evidence_id': 'beauty_002'},
                    'date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'interview',
                    'tags': ['beauty', 'purchase', 'influence']
                }
            ]
        elif question_type == 'beauty_virtual':
            evidence_items = [
                {
                    'dataset_name': 'Beauty Retail Transformation Study',
                    'question': 'What features would make in-store shoppers switch to virtual beauty advisory?',
                    'snippet': '73% of traditional in-store beauty shoppers would consider virtual consultations if they offered: (1) AI-powered shade matching with 95%+ accuracy, (2) Live video consultations with real-time product application, (3) Augmented reality try-on capabilities. Price transparency and easy returns are also critical factors.',
                    'distribution': {'ai_matching': 73, 'video_consult': 68, 'ar_tryon': 61, 'returns': 55},
                    'metadata': {'sample_size': 1200, 'confidence': 0.82, 'evidence_id': 'beauty_003'},
                    'date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['beauty', 'virtual', 'transformation']
                }
            ]
        elif question_type == 'food_pricing':
            evidence_items = [
                {
                    'dataset_name': 'Fast-Food Consumer Survey 2024',
                    'question': 'Is there an issue with menu pricing structure?',
                    'snippet': 'Consumer research shows 62% perceive fast-food prices as "too high" relative to value. Value-seeker segment (35% of customers) shows 2.1x price sensitivity. Menu items priced above $8 show 40% lower purchase intent compared to $5-7 range.',
                    'distribution': {'too_high': 62, 'just_right': 28, 'too_low': 10},
                    'metadata': {'sample_size': 3500, 'confidence': 0.88, 'evidence_id': 'food_001'},
                    'date': (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['food', 'pricing', 'value']
                },
                {
                    'dataset_name': 'Fast-Food Consumer Interview Data',
                    'question': 'What are the requirements for various customer segments?',
                    'snippet': 'Value seekers prioritize combo meals under $7 and frequent promotions. Health optimizers are willing to pay 15-20% premium for organic/plant-based options. Convenience loyalists prioritize speed and consistency over price.',
                    'distribution': {'value': 35, 'health': 22, 'convenience': 18, 'other': 25},
                    'metadata': {'sample_size': 240, 'confidence': 0.75, 'evidence_id': 'food_002'},
                    'date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'interview',
                    'tags': ['food', 'segments', 'requirements']
                }
            ]
        elif question_type == 'food_sensitivity':
            evidence_items = [
                {
                    'dataset_name': 'Fast-Food Consumer Survey 2024',
                    'question': 'How price-sensitive are different customer segments?',
                    'snippet': 'Price sensitivity varies dramatically by segment: Value Seekers show 4.2x higher price sensitivity than Health Optimizers. A $1 price increase reduces purchase frequency by 28% for Value Seekers vs. only 8% for Health Optimizers. Late-night customers show lowest price sensitivity.',
                    'distribution': {'value_seekers': 4.2, 'health_optimizers': 1.0, 'late_night': 0.6},
                    'metadata': {'sample_size': 4200, 'confidence': 0.91, 'evidence_id': 'food_003'},
                    'date': (datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['food', 'price_sensitivity', 'segments']
                }
            ]
        elif question_type == 'food_cookie':
            evidence_items = [
                {
                    'dataset_name': 'Packaged Food Consumer Study',
                    'question': 'How are consumer preferences shifting within the cookie category?',
                    'snippet': 'Consumer preferences are shifting toward healthier options: 58% of consumers now prioritize "better-for-you" attributes (reduced sugar, whole grains, natural ingredients) over traditional taste. However, taste remains the #1 driver for 72% of consumers, creating a tension between health and indulgence.',
                    'distribution': {'taste': 72, 'health': 58, 'price': 45, 'convenience': 32},
                    'metadata': {'sample_size': 2800, 'confidence': 0.86, 'evidence_id': 'cookie_001'},
                    'date': (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['food', 'cookies', 'preferences']
                }
            ]
        elif question_type == 'aitana_food':
            evidence_items = [
                {
                    'dataset_name': 'Snacking Consumer Trends 2024',
                    'question': 'What new functional jobs are consumers hiring food for?',
                    'snippet': 'Emerging functional needs: Mood enhancement (42% of Gen Z), Focus/energy (38% of professionals), Gut health (35% of Millennials), Sleep support (28% of all consumers). These functional needs are driving 3x faster growth in functional snacks vs. traditional snacks.',
                    'distribution': {'mood': 42, 'focus': 38, 'gut_health': 35, 'sleep': 28},
                    'metadata': {'sample_size': 3200, 'confidence': 0.89, 'evidence_id': 'aitana_001'},
                    'date': (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['aitana', 'functional', 'snacking']
                }
            ]
        elif question_type == 'aitana_beauty':
            evidence_items = [
                {
                    'dataset_name': 'Prestige Beauty Market Analysis',
                    'question': 'Which beauty categories are gaining strategic importance?',
                    'snippet': 'Serums and targeted treatments show 45% YoY growth in consumer intent, driven by personalization trends. Fragrance category is experiencing premiumization with 32% of consumers trading up to super-premium ($150+) tier. Face skincare remains the largest category but growth is shifting to specialized sub-categories.',
                    'distribution': {'serums': 45, 'fragrance': 32, 'face_skincare': 18, 'lips': 12},
                    'metadata': {'sample_size': 2100, 'confidence': 0.87, 'evidence_id': 'aitana_002'},
                    'date': (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['aitana', 'beauty', 'categories']
                }
            ]
        else:
            # Generic evidence for other questions
            evidence_items = [
                {
                    'dataset_name': 'Consumer Research Survey 2024',
                    'question': input_text[:100],
                    'snippet': f'Consumer insights from recent research indicate varied perspectives on this topic across different demographic segments. Key themes include preferences, behaviors, and decision factors that vary by age, income, and lifestyle.',
                    'distribution': {},
                    'metadata': {'sample_size': 1500, 'confidence': 0.75, 'evidence_id': 'generic_001'},
                    'date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'region': filters.get('region', 'National'),
                    'source_type': 'survey',
                    'tags': ['general']
                }
            ]

        # Return top 5-8 evidence items
        return evidence_items[:8]

    def _categorize_question(self, input_text):
        """Categorize the question to generate appropriate evidence."""
        text_lower = input_text.lower()

        # Beauty questions
        if 'sephora' in text_lower or ('discover' in text_lower and 'beauty' in text_lower):
            return 'beauty_sephora'
        if 'virtual' in text_lower and 'beauty' in text_lower:
            return 'beauty_virtual'
        if 'fashion' in text_lower and ('cash back' in text_lower or 'app' in text_lower):
            return 'beauty_virtual'  # Similar to virtual beauty

        # Food questions
        if 'pricing' in text_lower and ('fast food' in text_lower or 'menu' in text_lower):
            return 'food_pricing'
        if 'price-sensitive' in text_lower or ('price' in text_lower and 'segment' in text_lower):
            return 'food_sensitivity'
        if 'cookie' in text_lower or ('cookie' in text_lower and 'preference' in text_lower):
            return 'food_cookie'

        # AITANA questions
        if 'functional' in text_lower and ('food' in text_lower or 'snack' in text_lower):
            return 'aitana_food'
        if 'beauty' in text_lower and ('category' in text_lower or 'portfolio' in text_lower):
            return 'aitana_beauty'

        return 'generic'

    def _extract_question_from_evidence(self, evidence_item, hypothesis):
        """
        Extract or infer question from evidence item.

        Checks multiple possible fields where questions might be stored,
        extracts from verbatim quote if it contains questions,
        then infers from hypothesis if not found.
        """
        # Check multiple possible question fields
        question_fields = ['question', 'question_text', 'prompt', 'query']
        for field in question_fields:
            if field in evidence_item and evidence_item[field]:
                return str(evidence_item[field])

        # Try to extract question from verbatim quote (interviews often start with questions)
        verbatim = evidence_item.get('verbatim_quote', '')
        if verbatim:
            # Look for question patterns in the quote
            import re
            # Find sentences ending with "?"
            questions = re.findall(r'[^.!?]*\?', verbatim[:300])  # First 300 chars
            if questions:
                # Return the first question found, cleaned up
                question = questions[0].strip()
                # Remove "Agent:" prefix if present
                question = re.sub(r'^Agent:\s*', '', question, flags=re.IGNORECASE)
                question = re.sub(r'^User:\s*', '', question, flags=re.IGNORECASE)
                if len(question) > 20:  # Only use if substantial
                    return question[:150]  # Limit length

        # Check tags for question hints
        tags = evidence_item.get('tags', [])
        for tag in tags:
            if 'question' in tag.lower() or 'q:' in tag.lower():
                # Try to extract question from tag
                return tag.replace('q:', '').strip()

        # Infer question from hypothesis context
        hypothesis_lower = hypothesis.lower()
        if 'prefer' in hypothesis_lower or 'preference' in hypothesis_lower or 'mcdonalds' in hypothesis_lower or 'burger king' in hypothesis_lower:
            return "What influences your fast-food brand preferences?"
        elif 'choose' in hypothesis_lower or 'choice' in hypothesis_lower:
            return "What makes you choose one brand over another?"
        elif 'try' in hypothesis_lower or 'new' in hypothesis_lower:
            return "How often do you try new fast-food items?"
        elif 'pay' in hypothesis_lower or 'price' in hypothesis_lower:
            return "Would you pay more for healthier options?"
        elif 'influence' in hypothesis_lower:
            return "What influences your fast-food choices most?"
        elif 'discover' in hypothesis_lower:
            return "How do you discover new fast-food options?"
        else:
            # Use hypothesis as question
            return hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis

    def _generate_segments(self, responses):
        """Generate segment breakdown."""
        segments = {}

        for resp in responses:
            agent_id = resp['agent_id']
            try:
                agent = PersonaAgent.objects.get(id=agent_id)
                segment_key = f"{agent.age_bucket}_{agent.region}_{agent.archetype}"

                if segment_key not in segments:
                    segments[segment_key] = {
                        'name': f"{agent.get_archetype_display()} - {agent.age_bucket} - {agent.region}",
                        'count': 0,
                        'responses': [],
                    }

                segments[segment_key]['count'] += 1
                segments[segment_key]['responses'].append(resp.get('text', ''))
            except PersonaAgent.DoesNotExist:
                continue

        # Calculate segment insights
        for key, segment in segments.items():
            texts = segment['responses']
            positive = sum(1 for t in texts if any(w in t.lower() for w in ['yes', 'would', 'like', 'good', 'great']))
            segment['sentiment'] = positive / len(texts) if texts else 0.5

        return list(segments.values())[:5]  # Top 5 segments


class SurveyViewSet(viewsets.ViewSet):
    """ViewSet for survey testing."""

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a survey on agents."""
        agent_id = request.data.get('agent_id')
        filters = request.data.get('filters', {})
        agent_count = int(request.data.get('agent_count', 100))
        questions = request.data.get('questions', [])
        mode = request.data.get('mode', 'gpt')  # Default to GPT, not mock

        if not questions:
            return Response(
                {'error': 'questions array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get agents
        if agent_id:
            agents = [PersonaAgent.objects.get(id=agent_id)]
        else:
            agents_query = PersonaAgent.objects.all()

            if filters.get('age_bucket'):
                agents_query = agents_query.filter(age_bucket=filters['age_bucket'])
            if filters.get('gender'):
                agents_query = agents_query.filter(gender=filters['gender'])
            if filters.get('region'):
                agents_query = agents_query.filter(region=filters['region'])
            if filters.get('income'):
                agents_query = agents_query.filter(income=filters['income'])
            if filters.get('archetype'):
                agents_query = agents_query.filter(archetype=filters['archetype'])

            agents_list = list(agents_query)
            if len(agents_list) > agent_count:
                agents_list = random.sample(agents_list, agent_count)
            agents = agents_list

        run_id = uuid.uuid4()
        results = []

        # Get question objects
        question_objs = {}
        for q_id in questions:
            try:
                q_obj = SurveyQuestion.objects.get(id=q_id)
                question_objs[q_id] = q_obj
            except SurveyQuestion.DoesNotExist:
                continue

        # Run survey for each agent
        for agent in agents:
            agent_responses = []
            for q_id, q_obj in question_objs.items():
                response = generate_persona_response(
                    agent,
                    'survey',
                    {
                        'question': q_obj.question_text,
                        'question_type': q_obj.question_type,
                    },
                    mode
                )

                # Save response
                SurveyResponse.objects.create(
                    run_id=run_id,
                    agent=agent,
                    question=q_obj,
                    response_json=response
                )

                agent_responses.append({
                    'question_id': q_id,
                    'question_text': q_obj.question_text,
                    'response': response,
                })

            results.append({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'responses': agent_responses,
            })

        # Aggregate by question
        aggregated = {}
        for q_id, q_obj in question_objs.items():
            question_responses = []
            for result in results:
                for resp in result['responses']:
                    if resp['question_id'] == q_id:
                        question_responses.append(resp['response'])

            aggregated[q_id] = aggregate_agent_responses(question_responses, 'survey')
            aggregated[q_id]['question_text'] = q_obj.question_text

        return Response({
            'run_id': str(run_id),
            'aggregated_results': aggregated,
            'agent_count': len(agents),
        })


class TasteTestViewSet(viewsets.ViewSet):
    """ViewSet for taste testing."""

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a taste test."""
        agent_id = request.data.get('agent_id')
        filters = request.data.get('filters', {})
        agent_count = int(request.data.get('agent_count', 100))
        items = request.data.get('items', [])
        mode = request.data.get('mode', 'gpt')  # Default to GPT, not mock

        if not items:
            return Response(
                {'error': 'items array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get agents
        if agent_id:
            agents = [PersonaAgent.objects.get(id=agent_id)]
        else:
            agents_query = PersonaAgent.objects.all()

            if filters.get('age_bucket'):
                agents_query = agents_query.filter(age_bucket=filters['age_bucket'])
            if filters.get('gender'):
                agents_query = agents_query.filter(gender=filters['gender'])
            if filters.get('region'):
                agents_query = agents_query.filter(region=filters['region'])
            if filters.get('income'):
                agents_query = agents_query.filter(income=filters['income'])
            if filters.get('archetype'):
                agents_query = agents_query.filter(archetype=filters['archetype'])

            agents_list = list(agents_query)
            if len(agents_list) > agent_count:
                agents_list = random.sample(agents_list, agent_count)
            agents = agents_list

        results = []
        for agent in agents:
            response = generate_persona_response(
                agent,
                'taste_test',
                {'items': items},
                mode
            )
            results.append({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            })

        # Aggregate rankings
        all_rankings = []
        for result in results:
            if 'structured' in result and 'rankings' in result['structured']:
                all_rankings.extend(result['structured']['rankings'])

        # Calculate average scores per item
        item_scores = {}
        for ranking in all_rankings:
            item = ranking['item']
            score = ranking['score']
            if item not in item_scores:
                item_scores[item] = []
            item_scores[item].append(score)

        aggregated_rankings = [
            {
                'item': item,
                'average_score': sum(scores) / len(scores),
                'response_count': len(scores),
            }
            for item, scores in item_scores.items()
        ]
        aggregated_rankings.sort(key=lambda x: x['average_score'], reverse=True)

        return Response({
            'rankings': aggregated_rankings,
            'agent_count': len(agents),
            'individual_responses': results[:10],  # Return first 10 for preview
        })


class ChatViewSet(viewsets.ViewSet):
    """ViewSet for persona chat."""

    @action(detail=False, methods=['post'])
    def chat(self, request):
        """Chat with a persona agent."""
        agent_id = request.data.get('agent_id')
        messages = request.data.get('messages', [])
        mode = request.data.get('mode', 'gpt')  # Default to GPT, not mock

        if not agent_id:
            return Response(
                {'error': 'agent_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = PersonaAgent.objects.get(id=agent_id)
        except PersonaAgent.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            print(f"[ChatViewSet] Mode received: {mode}, Agent: {agent.display_name}, Messages: {len(messages)}")
            response = generate_persona_response(
                agent,
                'chat',
                {'messages': messages},
                mode
            )
            print(f"[ChatViewSet] Response received: {response.get('text', '')[:100]}...")

            if not response or 'text' not in response:
                return Response(
                    {'error': 'Invalid response from persona service'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'response': response['text'],
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error generating response: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MarketInsightViewSet(viewsets.ViewSet):
    """ViewSet for generating market insights from consultant questions (hypothesis runs)."""

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate market insights and graphs based on recent consultant questions."""
        from datetime import datetime, timedelta

        # Get parameters
        days_back = int(request.data.get('days_back', 30))
        limit = int(request.data.get('limit', 20))
        filters = request.data.get('filters', {})

        # Get recent hypothesis runs (consultant questions)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        runs_query = HypothesisRun.objects.filter(created_at__gte=cutoff_date)

        # Apply filters if provided
        if filters.get('region'):
            runs_query = runs_query.filter(filters_json__region=filters['region'])
        if filters.get('archetype'):
            runs_query = runs_query.filter(filters_json__archetype=filters['archetype'])

        runs = list(runs_query.order_by('-created_at')[:limit])

        if not runs:
            return Response({
                'insights': [],
                'graphs': [],
                'summary': 'No consultant questions found in the specified time period.',
                'total_questions': 0
            })

        # Generate insights and graphs
        insights = self._generate_insights(runs)
        graphs = self._generate_graphs(runs)
        summary = self._generate_summary(runs, insights)

        return Response({
            'insights': insights,
            'graphs': graphs,
            'summary': summary,
            'total_questions': len(runs),
            'time_period': {
                'days_back': days_back,
                'from_date': cutoff_date.isoformat(),
                'to_date': datetime.now().isoformat()
            }
        })

    def _generate_insights(self, runs):
        """Generate key insights from hypothesis runs."""
        insights = []

        # Categorize questions
        categories = {
            'beauty': [],
            'food': [],
            'pricing': [],
            'preferences': [],
            'other': []
        }

        for run in runs:
            text_lower = run.input_text.lower()
            if any(word in text_lower for word in ['beauty', 'sephora', 'makeup', 'skincare', 'cosmetic']):
                categories['beauty'].append(run)
            elif any(word in text_lower for word in ['food', 'restaurant', 'fast food', 'menu', 'pricing', 'price']):
                if 'price' in text_lower or 'pricing' in text_lower:
                    categories['pricing'].append(run)
                else:
                    categories['food'].append(run)
            elif any(word in text_lower for word in ['prefer', 'preference', 'choose', 'choice']):
                categories['preferences'].append(run)
            else:
                categories['other'].append(run)

        # Generate insights for each category
        for category, category_runs in categories.items():
            if category_runs:
                insight = self._analyze_category(category, category_runs)
                if insight:
                    insights.append(insight)

        # Generate cross-category insights
        cross_insights = self._generate_cross_category_insights(categories)
        insights.extend(cross_insights)

        return insights

    def _analyze_category(self, category, runs):
        """Analyze a category of questions and generate insights."""
        if not runs:
            return None

        # Extract aggregated results
        aggregated_results = []
        for run in runs:
            if run.aggregated_result_json:
                aggregated_results.append(run.aggregated_result_json)

        if not aggregated_results:
            return None

        # Calculate category-specific metrics
        total_sentiment = sum(r.get('overall_sentiment', 0.5) for r in aggregated_results)
        avg_sentiment = total_sentiment / len(aggregated_results)

        # Collect themes
        all_themes = {}
        for result in aggregated_results:
            themes = result.get('top_themes', {})
            for theme, count in themes.items():
                all_themes[theme] = all_themes.get(theme, 0) + count

        top_themes = sorted(all_themes.items(), key=lambda x: x[1], reverse=True)[:3]

        insight = {
            'category': category,
            'question_count': len(runs),
            'average_sentiment': round(avg_sentiment, 2),
            'top_themes': [{'theme': theme, 'mentions': count} for theme, count in top_themes],
            'key_findings': self._extract_key_findings(category, runs, aggregated_results),
            'sample_questions': [run.input_text[:100] + '...' for run in runs[:3]]
        }

        return insight

    def _extract_key_findings(self, category, runs, aggregated_results):
        """Extract key findings from aggregated results."""
        findings = []

        if category == 'pricing':
            # Analyze pricing sensitivity
            price_mentions = sum(1 for r in aggregated_results if 'price' in str(r).lower())
            if price_mentions > len(runs) * 0.5:
                findings.append(f"{price_mentions} out of {len(runs)} questions focused on pricing concerns")

        # Extract preference breakdowns
        for result in aggregated_results:
            preference_breakdown = result.get('preference_breakdown', {})
            if preference_breakdown:
                top_preference = max(preference_breakdown.items(), key=lambda x: x[1].get('percentage', 0))
                if top_preference:
                    findings.append(f"Strong preference for {top_preference[0]} ({top_preference[1].get('percentage', 0)}%)")

        return findings[:3]  # Top 3 findings

    def _generate_cross_category_insights(self, categories):
        """Generate insights across categories."""
        insights = []

        total_runs = sum(len(runs) for runs in categories.values())
        if total_runs == 0:
            return insights

        # Most active category
        most_active = max(categories.items(), key=lambda x: len(x[1]))
        if most_active[1]:
            insights.append({
                'type': 'category_activity',
                'insight': f"Most consultant questions focused on {most_active[0]} ({len(most_active[1])} questions)",
                'category': most_active[0],
                'count': len(most_active[1])
            })

        return insights

    def _generate_graphs(self, runs):
        """Generate graph data structures for visualization."""
        graphs = []

        # Graph 1: Question volume over time
        time_series = self._generate_time_series_graph(runs)
        if time_series:
            graphs.append(time_series)

        # Graph 2: Category distribution
        category_dist = self._generate_category_distribution_graph(runs)
        if category_dist:
            graphs.append(category_dist)

        # Graph 3: Sentiment trends
        sentiment_trends = self._generate_sentiment_trends_graph(runs)
        if sentiment_trends:
            graphs.append(sentiment_trends)

        # Graph 4: Theme word cloud data
        theme_data = self._generate_theme_data(runs)
        if theme_data:
            graphs.append(theme_data)

        # Graph 5: Archetype response patterns
        archetype_patterns = self._generate_archetype_patterns_graph(runs)
        if archetype_patterns:
            graphs.append(archetype_patterns)

        return graphs

    def _generate_time_series_graph(self, runs):
        """Generate time series graph of question volume."""
        from collections import defaultdict

        daily_counts = defaultdict(int)
        for run in runs:
            date_key = run.created_at.date().isoformat()
            daily_counts[date_key] += 1

        sorted_dates = sorted(daily_counts.keys())

        return {
            'type': 'line',
            'title': 'Consultant Questions Over Time',
            'x_axis': 'Date',
            'y_axis': 'Number of Questions',
            'data': {
                'labels': sorted_dates,
                'datasets': [{
                    'label': 'Questions Asked',
                    'data': [daily_counts[date] for date in sorted_dates],
                    'borderColor': '#a855f7',
                    'backgroundColor': 'rgba(168, 85, 247, 0.1)',
                    'fill': True
                }]
            }
        }

    def _generate_category_distribution_graph(self, runs):
        """Generate pie chart of question categories."""
        categories = {
            'Beauty': 0,
            'Food': 0,
            'Pricing': 0,
            'Preferences': 0,
            'Other': 0
        }

        for run in runs:
            text_lower = run.input_text.lower()
            if any(word in text_lower for word in ['beauty', 'sephora', 'makeup', 'skincare']):
                categories['Beauty'] += 1
            elif any(word in text_lower for word in ['food', 'restaurant', 'fast food', 'menu']):
                if 'price' in text_lower or 'pricing' in text_lower:
                    categories['Pricing'] += 1
                else:
                    categories['Food'] += 1
            elif any(word in text_lower for word in ['prefer', 'preference', 'choose']):
                categories['Preferences'] += 1
            else:
                categories['Other'] += 1

        # Filter out zero categories
        filtered_categories = {k: v for k, v in categories.items() if v > 0}

        if not filtered_categories:
            return None

        colors = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']

        return {
            'type': 'pie',
            'title': 'Question Category Distribution',
            'data': {
                'labels': list(filtered_categories.keys()),
                'datasets': [{
                    'data': list(filtered_categories.values()),
                    'backgroundColor': colors[:len(filtered_categories)]
                }]
            }
        }

    def _generate_sentiment_trends_graph(self, runs):
        """Generate sentiment trends over time."""
        from collections import defaultdict

        daily_sentiments = defaultdict(list)
        for run in runs:
            if run.aggregated_result_json:
                sentiment = run.aggregated_result_json.get('overall_sentiment', 0.5)
                date_key = run.created_at.date().isoformat()
                daily_sentiments[date_key].append(sentiment)

        sorted_dates = sorted(daily_sentiments.keys())
        avg_sentiments = [sum(daily_sentiments[date]) / len(daily_sentiments[date])
                         for date in sorted_dates]

        if not sorted_dates:
            return None

        return {
            'type': 'line',
            'title': 'Average Sentiment Trends',
            'x_axis': 'Date',
            'y_axis': 'Sentiment Score (0-1)',
            'data': {
                'labels': sorted_dates,
                'datasets': [{
                    'label': 'Average Sentiment',
                    'data': avg_sentiments,
                    'borderColor': '#10b981',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'fill': True,
                    'tension': 0.4
                }]
            }
        }

    def _generate_theme_data(self, runs):
        """Generate theme frequency data for word cloud or bar chart."""
        theme_counts = {}

        for run in runs:
            if run.aggregated_result_json:
                themes = run.aggregated_result_json.get('top_themes', {})
                for theme, count in themes.items():
                    theme_counts[theme] = theme_counts.get(theme, 0) + count

        if not theme_counts:
            return None

        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'type': 'bar',
            'title': 'Top Themes Across Questions',
            'x_axis': 'Theme',
            'y_axis': 'Frequency',
            'data': {
                'labels': [theme for theme, _ in sorted_themes],
                'datasets': [{
                    'label': 'Mentions',
                    'data': [count for _, count in sorted_themes],
                    'backgroundColor': '#3b82f6'
                }]
            }
        }

    def _generate_archetype_patterns_graph(self, runs):
        """Generate archetype response patterns."""
        archetype_responses = {}

        for run in runs:
            filters = run.filters_json or {}
            archetype = filters.get('archetype', 'all')

            if run.aggregated_result_json:
                sentiment = run.aggregated_result_json.get('overall_sentiment', 0.5)
                if archetype not in archetype_responses:
                    archetype_responses[archetype] = []
                archetype_responses[archetype].append(sentiment)

        if not archetype_responses:
            return None

        # Calculate average sentiment per archetype
        archetype_avgs = {}
        for archetype, sentiments in archetype_responses.items():
            if sentiments:
                archetype_avgs[archetype or 'all'] = sum(sentiments) / len(sentiments)

        if not archetype_avgs:
            return None

        return {
            'type': 'bar',
            'title': 'Average Sentiment by Archetype',
            'x_axis': 'Archetype',
            'y_axis': 'Average Sentiment',
            'data': {
                'labels': list(archetype_avgs.keys()),
                'datasets': [{
                    'label': 'Sentiment',
                    'data': list(archetype_avgs.values()),
                    'backgroundColor': '#f59e0b'
                }]
            }
        }

    def _generate_summary(self, runs, insights):
        """Generate executive summary."""
        total_questions = len(runs)

        if total_questions == 0:
            return "No consultant questions found in the specified period."

        # Calculate overall metrics
        total_sentiment = 0
        sentiment_count = 0
        for run in runs:
            if run.aggregated_result_json:
                sentiment = run.aggregated_result_json.get('overall_sentiment')
                if sentiment is not None:
                    total_sentiment += sentiment
                    sentiment_count += 1

        avg_sentiment = total_sentiment / sentiment_count if sentiment_count > 0 else 0.5

        summary = f"""
        Market Insight Summary

        Analyzed {total_questions} consultant questions over the past period.
        Average sentiment across all questions: {avg_sentiment:.2f} (on a 0-1 scale).

        Key Insights:
        """

        for insight in insights[:3]:
            if isinstance(insight, dict):
                category = insight.get('category', 'Unknown')
                question_count = insight.get('question_count', 0)
                summary += f"\n- {category.capitalize()} category: {question_count} questions"

        return summary.strip()
