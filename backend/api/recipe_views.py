"""
API views for recipe simulation and regulatory readiness.
"""
import uuid
import json
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .recipe_models import (
    RecipeVariant, ApprovalPersona, SimulationRun,
    SyntheticFocusGroup, SyntheticSurvey, LaunchReadinessReport
)
from .recipe_serializers import (
    RecipeVariantSerializer, ApprovalPersonaSerializer, SimulationRunSerializer,
    SyntheticFocusGroupSerializer, SyntheticSurveySerializer, LaunchReadinessReportSerializer
)
from .recipe_simulation_engine import (
    RecipeSimulationEngine, compute_entropy_metrics, assess_approval
)
from .lpm_adapter import LPMRecipeSimulator
from .sim_models import PersonaAgent
import random
import threading

# Try to import Phase 3-4 simulator, but don't fail if it's not available
try:
    from .phase34_simulator import Phase34RecipeSimulator
except (ImportError, ModuleNotFoundError, AttributeError) as e:
    print(f"Warning: Could not import Phase34RecipeSimulator: {e}")
    Phase34RecipeSimulator = None
except Exception as e:
    print(f"Warning: Unexpected error importing Phase34RecipeSimulator: {e}")
    import traceback
    traceback.print_exc()
    Phase34RecipeSimulator = None


class RecipeVariantViewSet(viewsets.ModelViewSet):
    """ViewSet for RecipeVariant."""
    queryset = RecipeVariant.objects.all()
    serializer_class = RecipeVariantSerializer
    
    def get_queryset(self):
        queryset = RecipeVariant.objects.all()
        base_product_id = self.request.query_params.get('base_product_id')
        if base_product_id:
            queryset = queryset.filter(base_product_id=base_product_id)
        return queryset.order_by('-created_at')


class ApprovalPersonaViewSet(viewsets.ModelViewSet):
    """ViewSet for ApprovalPersona."""
    queryset = ApprovalPersona.objects.all()
    serializer_class = ApprovalPersonaSerializer
    
    def get_queryset(self):
        queryset = ApprovalPersona.objects.all()
        persona_type = self.request.query_params.get('persona_type')
        if persona_type:
            queryset = queryset.filter(persona_type=persona_type)
        return queryset


class SimulationRunViewSet(viewsets.ModelViewSet):
    """ViewSet for SimulationRun."""
    queryset = SimulationRun.objects.all()
    serializer_class = SimulationRunSerializer
    
    def get_queryset(self):
        queryset = SimulationRun.objects.all()
        recipe_variant_id = self.request.query_params.get('recipe_variant_id')
        status_filter = self.request.query_params.get('status')
        if recipe_variant_id:
            queryset = queryset.filter(recipe_variant_id=recipe_variant_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def run_simulation(self, request):
        """
        Run a new simulation for a recipe variant.
        
        Expected payload:
        {
            "recipe_variant_id": "uuid",
            "agent_count": 1000,
            "time_horizon_weeks": 12,
            "segment_filters": {
                "age_bucket": ["18-24", "25-34"],
                "archetype": ["health_optimizer", "value_seeker"],
                ...
            }
        }
        """
        recipe_variant_id = request.data.get('recipe_variant_id')
        agent_count = int(request.data.get('agent_count', 1000))
        time_horizon_weeks = int(request.data.get('time_horizon_weeks', 12))
        segment_filters = request.data.get('segment_filters', {})
        
        if not recipe_variant_id:
            return Response(
                {'error': 'recipe_variant_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recipe_variant = RecipeVariant.objects.get(id=recipe_variant_id)
        except RecipeVariant.DoesNotExist:
            return Response(
                {'error': 'Recipe variant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create simulation run
        try:
            # Create with minimal fields first (in case metadata_json doesn't exist yet)
            simulation_run = SimulationRun(
                recipe_variant=recipe_variant,
                agent_count=agent_count,
                time_horizon_weeks=time_horizon_weeks,
                segment_filters_json=segment_filters,
                status='pending'
            )
            # Only set metadata_json if the field exists
            try:
                simulation_run.metadata_json = {}
            except AttributeError:
                pass  # Field doesn't exist yet, skip it
            simulation_run.save()
        except Exception as e:
            import traceback
            error_msg = str(e)
            # Check if it's a migration issue
            if 'metadata_json' in error_msg.lower() or 'no column' in error_msg.lower():
                error_msg = f"Database migration required. Please run: python manage.py makemigrations api && python manage.py migrate. Original error: {error_msg}"
            return Response(
                {
                    'error': f'Failed to create simulation run: {error_msg}',
                    'traceback': traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Run simulation in background thread
        def run_sim():
            try:
                simulation_run.status = 'running'
                simulation_run.save()
                
                # Get agents based on filters
                agents_query = PersonaAgent.objects.all()
                
                if segment_filters.get('age_bucket'):
                    agents_query = agents_query.filter(age_bucket__in=segment_filters['age_bucket'])
                if segment_filters.get('archetype'):
                    agents_query = agents_query.filter(archetype__in=segment_filters['archetype'])
                if segment_filters.get('region'):
                    agents_query = agents_query.filter(region__in=segment_filters['region'])
                if segment_filters.get('gender'):
                    agents_query = agents_query.filter(gender__in=segment_filters['gender'])
                if segment_filters.get('income'):
                    agents_query = agents_query.filter(income__in=segment_filters['income'])
                
                # Sample agents
                agents_list = list(agents_query)
                if len(agents_list) > agent_count:
                    agents_list = random.sample(agents_list, agent_count)
                
                # Convert to dict format
                agents_data = []
                for agent in agents_list:
                    agents_data.append({
                        'id': str(agent.id),
                        'segment_id': agent.archetype,  # Using archetype as segment
                        'archetype': agent.archetype,
                        'taste_profile_json': agent.taste_profile_json or [],
                        'behavior_params_json': agent.behavior_params_json or {},
                        'age_bucket': agent.age_bucket,
                        'region': agent.region,
                        'gender': agent.gender,
                        'income': agent.income,
                    })
                
                # Base product (simplified - in production would fetch from product catalog)
                base_product = {
                    'id': recipe_variant.base_product_id,
                    'name': recipe_variant.base_product_name or recipe_variant.base_product_id,
                }
                
                # Recipe variant data
                recipe_data = {
                    'nutrition_delta_json': recipe_variant.nutrition_delta_json or {},
                    'sensory_delta_json': recipe_variant.sensory_delta_json or {},
                    'price_delta': recipe_variant.price_delta,
                    'ingredient_changes_json': recipe_variant.ingredient_changes_json or {},
                }
                
                # Try to use Phase 3-4 simulator first, fallback to simplified
                simulator_type = 'phase34'  # Track which simulator was used
                try:
                    if Phase34RecipeSimulator is None:
                        raise RuntimeError("Phase34RecipeSimulator not available (import failed)")
                    print("=" * 60)
                    print("ATTEMPTING TO USE PHASE 3-4 SIMULATOR")
                    print("=" * 60)
                    print(f"Agents: {len(agents_data)}")
                    print(f"Time horizon: {time_horizon_weeks} weeks")
                    import traceback
                    phase34_simulator = Phase34RecipeSimulator(
                        agents_data, base_product, recipe_data, device='cpu'
                    )
                    print("Phase 3-4 simulator initialized successfully")
                    results = phase34_simulator.run_simulation(time_horizon_weeks)
                    results['simulator_type'] = 'phase34'
                    results['simulator_message'] = 'Using Phase 3-4 LPM (Real Models)'
                    print("=" * 60)
                    print("PHASE 3-4 SIMULATION COMPLETED SUCCESSFULLY!")
                    print(f"Acceptance rate: {results.get('overall_acceptance_rate', 0):.2%}")
                    print(f"Mean preference delta: {results.get('mean_preference_delta', 0):.3f}")
                    print("=" * 60)
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"Phase 3-4 simulator failed: {e}")
                    print(f"Error traceback:\n{error_trace}")
                    print("Falling back to simplified LPM simulator...")
                    simulator_type = 'simplified'
                    # Fallback to simplified simulator
                    lpm_simulator = LPMRecipeSimulator(agents_data, base_product, recipe_data)
                    results = lpm_simulator.run_simulation(time_horizon_weeks)
                    results['simulator_type'] = 'simplified'
                    results['simulator_message'] = 'Using Simplified Simulator (Phase 3-4 models unavailable)'
                
                # Convert to expected format (handle both Phase 3-4 and simplified results)
                if 'preference_deltas' not in results or not results.get('preference_deltas'):
                    # Convert simplified format to match Phase 3-4 format
                    results = {
                        'overall_acceptance_rate': results.get('overall_acceptance_rate', 0.0),
                        'overall_rejection_rate': results.get('overall_rejection_rate', 0.0),
                        'mean_preference_delta': results.get('mean_preference_delta', 0.0),
                        'segment_breakdown': results.get('segment_breakdown', {}),
                        'time_series': results.get('time_series', []),
                        'baseline_preferences': results.get('baseline_preferences', {}),
                        'preference_deltas': {
                            agent_id: results.get('final_preferences', {}).get(agent_id, 0.5) - 
                                     results.get('baseline_preferences', {}).get(agent_id, 0.5)
                            for agent_id in results.get('baseline_preferences', {}).keys()
                        },
                        'actions': results.get('agent_decisions', results.get('actions', {}))
                    }
                
                # Compute entropy metrics
                baseline_prefs = results.get('baseline_preferences', {})
                # Compute post-change preferences
                post_change_prefs = {}
                for agent_id, delta in results.get('preference_deltas', {}).items():
                    baseline = baseline_prefs.get(agent_id, 0.5)
                    post_change_prefs[agent_id] = baseline + delta
                
                entropy_metrics = compute_entropy_metrics(baseline_prefs, post_change_prefs)
                
                # Assess approval
                approval_personas = list(ApprovalPersona.objects.all().values())
                approval_assessment = assess_approval(results, approval_personas)
                
                # Update simulation run
                simulation_run.results_json = results
                simulation_run.baseline_entropy = entropy_metrics.get('baseline_entropy')
                simulation_run.post_change_entropy = entropy_metrics.get('post_change_entropy')
                simulation_run.entropy_delta = entropy_metrics.get('entropy_delta')
                simulation_run.confidence_score = entropy_metrics.get('confidence_score')
                simulation_run.approval_assessment_json = approval_assessment
                # Store simulator type in metadata (with safe fallback)
                try:
                    if not hasattr(simulation_run, 'metadata_json') or simulation_run.metadata_json is None:
                        simulation_run.metadata_json = {}
                    simulation_run.metadata_json['simulator_type'] = results.get('simulator_type', 'unknown')
                    simulation_run.metadata_json['simulator_message'] = results.get('simulator_message', '')
                except Exception as meta_error:
                    print(f"Warning: Could not set metadata_json: {meta_error}")
                    # Continue without metadata
                
                simulation_run.status = 'completed'
                simulation_run.completed_at = datetime.now()
                simulation_run.save()
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Simulation failed with error: {e}")
                print(f"Error traceback:\n{error_trace}")
                traceback.print_exc()
                simulation_run.status = 'failed'
                simulation_run.error_message = str(e)
                simulation_run.save()
        
        # Start simulation in background
        thread = threading.Thread(target=run_sim)
        thread.daemon = True
        thread.start()
        
        serializer = SimulationRunSerializer(simulation_run)
        return Response({
            'simulation_run_id': str(simulation_run.id),
            'id': str(simulation_run.id),
            'status': 'pending',
            'message': 'Simulation started. Check status endpoint for updates.'
        })
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get simulation results."""
        try:
            simulation_run = SimulationRun.objects.get(id=pk)
        except SimulationRun.DoesNotExist:
            return Response(
                {'error': 'Simulation run not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SimulationRunSerializer(simulation_run)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_focus_group(self, request, pk=None):
        """Generate synthetic focus group transcript."""
        try:
            simulation_run = SimulationRun.objects.get(id=pk)
        except SimulationRun.DoesNotExist:
            return Response(
                {'error': 'Simulation run not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if simulation_run.status != 'completed':
            return Response(
                {'error': 'Simulation must be completed before generating focus group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate synthetic focus group
        focus_group = self._generate_synthetic_focus_group(simulation_run)
        
        serializer = SyntheticFocusGroupSerializer(focus_group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_survey(self, request, pk=None):
        """Generate synthetic survey results."""
        try:
            simulation_run = SimulationRun.objects.get(id=pk)
        except SimulationRun.DoesNotExist:
            return Response(
                {'error': 'Simulation run not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if simulation_run.status != 'completed':
            return Response(
                {'error': 'Simulation must be completed before generating survey'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate synthetic survey
        survey = self._generate_synthetic_survey(simulation_run)
        
        serializer = SyntheticSurveySerializer(survey)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_readiness_report(self, request, pk=None):
        """Generate launch readiness report."""
        try:
            simulation_run = SimulationRun.objects.get(id=pk)
        except SimulationRun.DoesNotExist:
            return Response(
                {'error': 'Simulation run not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if simulation_run.status != 'completed':
            return Response(
                {'error': 'Simulation must be completed before generating report'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report
        report = self._generate_readiness_report(simulation_run)
        
        serializer = LaunchReadinessReportSerializer(report)
        return Response(serializer.data)
    
    def _generate_synthetic_focus_group(self, simulation_run: SimulationRun) -> SyntheticFocusGroup:
        """Generate synthetic focus group transcript."""
        results = simulation_run.results_json or {}
        segment_breakdown = results.get('segment_breakdown', {})
        
        # Select representative segments
        top_segments = sorted(
            segment_breakdown.items(),
            key=lambda x: x[1].get('count', 0),
            reverse=True
        )[:3]
        
        # Generate transcript
        transcript = []
        for segment_key, segment_data in top_segments:
            archetype = segment_data.get('demographics', {}).get('archetype', 'unknown')
            age = segment_data.get('demographics', {}).get('age_bucket', 'unknown')
            
            # Generate synthetic quotes based on actions
            actions = segment_data.get('actions', {})
            if actions.get('accept', 0) > 0.6:
                transcript.append({
                    'speaker': f"{archetype} participant",
                    'archetype': archetype,
                    'text': f"I really like this change. It aligns with what I'm looking for.",
                    'sentiment': 0.8
                })
            elif actions.get('reject', 0) > 0.4:
                transcript.append({
                    'speaker': f"{archetype} participant",
                    'archetype': archetype,
                    'text': f"I'm not sure about this. It doesn't match my preferences.",
                    'sentiment': 0.3
                })
        
        # Create focus group
        focus_group = SyntheticFocusGroup.objects.create(
            simulation_run=simulation_run,
            segment_composition_json={k: v.get('demographics', {}) for k, v in top_segments},
            transcript_json=transcript,
            summary=f"Focus group discussion about {simulation_run.recipe_variant.name}",
            key_themes_json=['taste', 'price', 'health'],
            overall_sentiment=results.get('overall_acceptance_rate', 0.5)
        )
        
        return focus_group
    
    def _generate_synthetic_survey(self, simulation_run: SimulationRun) -> SyntheticSurvey:
        """Generate synthetic survey results."""
        results = simulation_run.results_json or {}
        
        # Generate questions and responses
        questions = [
            {
                'question': 'How likely are you to purchase this product after the change?',
                'responses': {
                    'very_likely': results.get('overall_acceptance_rate', 0.0) * 0.4,
                    'likely': results.get('overall_acceptance_rate', 0.0) * 0.3,
                    'neutral': 0.2,
                    'unlikely': results.get('overall_rejection_rate', 0.0) * 0.3,
                    'very_unlikely': results.get('overall_rejection_rate', 0.0) * 0.4,
                }
            },
            {
                'question': 'How does the price change affect your purchase decision?',
                'responses': {
                    'positive_impact': 0.2,
                    'no_impact': 0.5,
                    'negative_impact': 0.3,
                }
            }
        ]
        
        # Segment breakdown
        segment_breakdown = results.get('segment_breakdown', {})
        
        survey = SyntheticSurvey.objects.create(
            simulation_run=simulation_run,
            questions_json=questions,
            segment_breakdown_json=segment_breakdown,
            summary_stats_json={
                'total_responses': simulation_run.agent_count,
                'overall_acceptance': results.get('overall_acceptance_rate', 0.0),
            }
        )
        
        return survey
    
    def _generate_readiness_report(self, simulation_run: SimulationRun) -> LaunchReadinessReport:
        """Generate launch readiness report."""
        results = simulation_run.results_json or {}
        recipe_variant = simulation_run.recipe_variant
        
        # Determine who liked/disliked
        segment_breakdown = results.get('segment_breakdown', {})
        who_liked = {}
        who_disliked = {}
        
        for segment_key, segment_data in segment_breakdown.items():
            delta = segment_data.get('mean_preference_delta', 0.0)
            if delta > 0.1:
                who_liked[segment_key] = {
                    'preference_delta': delta,
                    'acceptance_rate': segment_data.get('actions', {}).get('accept', 0.0),
                    'demographics': segment_data.get('demographics', {})
                }
            elif delta < -0.1:
                who_disliked[segment_key] = {
                    'preference_delta': delta,
                    'rejection_rate': segment_data.get('actions', {}).get('reject', 0.0),
                    'demographics': segment_data.get('demographics', {})
                }
        
        # Identify risks
        risks = []
        if results.get('overall_rejection_rate', 0.0) > 0.3:
            risks.append({
                'type': 'high_rejection',
                'severity': 'high',
                'description': f"High rejection rate ({results.get('overall_rejection_rate', 0.0):.1%}) indicates significant consumer resistance."
            })
        
        substitution_rate = sum(1 for a in results.get('actions', {}).values() if a == 'substitute') / len(results.get('actions', {})) if results.get('actions') else 0.0
        if substitution_rate > 0.3:
            risks.append({
                'type': 'substitution_risk',
                'severity': 'medium',
                'description': f"High substitution risk ({substitution_rate:.1%}) - consumers may switch to competitors."
            })
        
        # Determine recommendation
        overall_acceptance = results.get('overall_acceptance_rate', 0.0)
        confidence = simulation_run.confidence_score or 0.5
        
        if overall_acceptance >= 0.7 and confidence >= 0.7:
            recommendation = 'proceed'
            reasoning = "Strong acceptance rate and high confidence indicate readiness for launch."
        elif overall_acceptance >= 0.5 and confidence >= 0.6:
            recommendation = 'iterate'
            reasoning = "Moderate acceptance suggests need for refinement before launch."
        else:
            recommendation = 'kill'
            reasoning = "Low acceptance and/or confidence indicate this variant should not proceed."
        
        # Executive summary
        executive_summary = f"""
        This report evaluates the launch readiness of recipe variant "{recipe_variant.name}" 
        based on simulation of {simulation_run.agent_count} agents over {simulation_run.time_horizon_weeks} weeks.
        
        Overall acceptance rate: {overall_acceptance:.1%}
        Confidence score: {confidence:.1%}
        
        {"The variant shows strong potential for launch." if recommendation == 'proceed' else 
          "The variant requires further iteration before launch." if recommendation == 'iterate' else
          "The variant does not meet launch criteria."}
        """
        
        # What changed
        what_changed = f"""
        Recipe changes:
        - Nutrition: {recipe_variant.nutrition_delta_json}
        - Sensory: {recipe_variant.sensory_delta_json}
        - Price: ${recipe_variant.price_delta:+.2f}
        - Ingredients: {recipe_variant.ingredient_changes_json}
        """
        
        # Create report
        report = LaunchReadinessReport.objects.create(
            simulation_run=simulation_run,
            executive_summary=executive_summary.strip(),
            what_changed=what_changed.strip(),
            who_liked_json=who_liked,
            who_disliked_json=who_disliked,
            risks_json=risks,
            confidence_score=confidence,
            recommendation=recommendation,
            recommendation_reasoning=reasoning,
            charts_data_json={
                'time_series': results.get('time_series', []),
                'segment_breakdown': segment_breakdown,
            },
            persona_assessments_json=simulation_run.approval_assessment_json or {}
        )
        
        return report

