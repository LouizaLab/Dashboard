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
import random
import math


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
                'value_seeker': '#10b981',  # green
                'health_optimizer': '#3b82f6',  # blue
                'convenience_loyalist': '#f59e0b',  # yellow
                'late_night_craver': '#8b5cf6',  # purple
                'trend_chaser': '#ec4899',  # pink
                'family_bundle_buyer': '#06b6d4',  # cyan
                'protein_maximizer': '#ef4444',  # red
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
        
        # Generate responses
        responses = []
        agents_info = []
        for agent in agents_list:
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode
            )
            responses.append({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            })
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
        
        # Update the run with new report
        if 'error' not in gpt_report:
            run.aggregated_result_json = gpt_report
            run.save()
        
        # Get evidence
        evidence = self._get_evidence(input_text, filters)
        
        # Generate segments breakdown
        segments = self._generate_segments(responses)
        
        return Response({
            'run_id': str(run.id),
            'aggregated_result': gpt_report if 'error' not in gpt_report else run.aggregated_result_json,
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
        
        # Generate responses
        responses = []
        agents_info = []
        for agent in agents_list:
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode
            )
            responses.append({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            })
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
        
        # If GPT report generation failed, fallback to basic aggregation
        if 'error' in gpt_report:
            aggregated = aggregate_agent_responses(responses, 'hypothesis')
            aggregated['error'] = gpt_report['error']
        else:
            aggregated = gpt_report
        
        # Get evidence
        evidence = self._get_evidence(input_text, filters)
        
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
        
        # Generate responses
        responses = []
        agents_info = []
        for agent in agents_list:
            response = generate_persona_response(
                agent,
                'hypothesis',
                {'input_text': input_text},
                mode
            )
            responses.append({
                'agent_id': str(agent.id),
                'agent_name': agent.display_name,
                'archetype': agent.archetype,
                **response
            })
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
        
        # If GPT report generation failed, fallback to basic aggregation
        if 'error' in gpt_report:
            aggregated = aggregate_agent_responses(responses, 'hypothesis')
            aggregated['error'] = gpt_report['error']
        else:
            # Use GPT-4 report as the aggregated result
            aggregated = gpt_report
            # Ensure required fields exist
            if 'overall_sentiment' not in aggregated:
                aggregated['overall_sentiment'] = aggregated.get('overall_sentiment', 0.5)
            if 'confidence' not in aggregated:
                aggregated['confidence'] = aggregated.get('confidence', 0.7)
            if 'top_themes' not in aggregated:
                aggregated['top_themes'] = {d['theme']: d['mentions'] for d in aggregated.get('top_drivers', [])}
        
        # Get evidence
        evidence = self._get_evidence(input_text, filters)
        
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
            'evidence': evidence,
            'segments': segments,
            'agent_count': len(agents_list),
            'agent_ids': [str(a.id) for a in agents_list],
            'gpt_report': gpt_report if 'error' not in gpt_report else None,  # Include full GPT report
        })
    
    def _get_evidence(self, input_text, filters):
        """Get relevant evidence survey data."""
        evidence_query = EvidenceSurveyDatum.objects.all()
        
        if filters.get('region'):
            evidence_query = evidence_query.filter(region=filters['region'])
        if filters.get('archetype'):
            evidence_query = evidence_query.filter(archetype=filters['archetype'])
        
        # Get 3-5 relevant snippets
        evidence_list = list(evidence_query.order_by('?')[:5])
        
        return [
            {
                'dataset_name': e.dataset_name,
                'question': e.question_text,
                'snippet': e.snippet_text,
                'distribution': e.distribution_json,
                'metadata': e.metadata_json,
                'date': e.date.isoformat(),
                'region': e.region,
            }
            for e in evidence_list
        ]
    
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
