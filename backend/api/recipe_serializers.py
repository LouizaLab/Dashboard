"""
Serializers for recipe simulation models.
"""
from rest_framework import serializers
from .recipe_models import (
    RecipeVariant, ApprovalPersona, SimulationRun,
    SyntheticFocusGroup, SyntheticSurvey, LaunchReadinessReport
)


class RecipeVariantSerializer(serializers.ModelSerializer):
    """Serializer for RecipeVariant."""
    class Meta:
        model = RecipeVariant
        fields = [
            'id', 'name', 'base_product_id', 'base_product_name',
            'ingredient_changes_json', 'nutrition_delta_json',
            'sensory_delta_json', 'price_delta', 'positioning_tags_json',
            'description', 'created_at', 'created_by'
        ]


class ApprovalPersonaSerializer(serializers.ModelSerializer):
    """Serializer for ApprovalPersona."""
    class Meta:
        model = ApprovalPersona
        fields = [
            'id', 'persona_type', 'name',
            'taste_acceptance_threshold', 'price_sensitivity_threshold',
            'health_acceptance_threshold', 'cannibalization_risk_threshold',
            'demographic_coverage_threshold', 'substitution_risk_threshold',
            'risk_tolerance', 'factor_weights_json', 'description', 'created_at'
        ]


class SimulationRunSerializer(serializers.ModelSerializer):
    """Serializer for SimulationRun."""
    recipe_variant = RecipeVariantSerializer(read_only=True)
    recipe_variant_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = SimulationRun
        fields = [
            'id', 'recipe_variant', 'recipe_variant_id',
            'agent_count', 'time_horizon_weeks', 'segment_filters_json',
            'status', 'results_json', 'baseline_entropy', 'post_change_entropy',
            'entropy_delta', 'confidence_score', 'approval_assessment_json',
            'metadata_json', 'created_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'status', 'results_json', 'baseline_entropy', 'post_change_entropy',
            'entropy_delta', 'confidence_score', 'approval_assessment_json',
            'completed_at', 'error_message'
        ]


class SyntheticFocusGroupSerializer(serializers.ModelSerializer):
    """Serializer for SyntheticFocusGroup."""
    class Meta:
        model = SyntheticFocusGroup
        fields = [
            'id', 'simulation_run', 'segment_composition_json',
            'transcript_json', 'summary', 'key_themes_json',
            'overall_sentiment', 'created_at'
        ]


class SyntheticSurveySerializer(serializers.ModelSerializer):
    """Serializer for SyntheticSurvey."""
    class Meta:
        model = SyntheticSurvey
        fields = [
            'id', 'simulation_run', 'questions_json',
            'segment_breakdown_json', 'summary_stats_json', 'created_at'
        ]


class LaunchReadinessReportSerializer(serializers.ModelSerializer):
    """Serializer for LaunchReadinessReport."""
    simulation_run = SimulationRunSerializer(read_only=True)
    
    class Meta:
        model = LaunchReadinessReport
        fields = [
            'id', 'simulation_run', 'executive_summary', 'what_changed',
            'who_liked_json', 'who_disliked_json', 'risks_json',
            'confidence_score', 'recommendation', 'recommendation_reasoning',
            'charts_data_json', 'persona_assessments_json', 'created_at'
        ]

