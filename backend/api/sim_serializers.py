"""
Serializers for simulation models.
"""
from rest_framework import serializers
from .sim_models import PersonaAgent, SurveyQuestion, HypothesisRun, EvidenceSurveyDatum


class PersonaAgentSerializer(serializers.ModelSerializer):
    """Serializer for PersonaAgent."""
    archetype_display = serializers.CharField(source='get_archetype_display', read_only=True)
    
    class Meta:
        model = PersonaAgent
        fields = [
            'id', 'display_name', 'age_bucket', 'gender', 'region', 'income',
            'archetype', 'archetype_display', 'taste_profile_json',
            'behavior_params_json', 'biography'
        ]


class SurveyQuestionSerializer(serializers.ModelSerializer):
    """Serializer for SurveyQuestion."""
    class Meta:
        model = SurveyQuestion
        fields = ['id', 'question_text', 'question_type', 'choices_json']


class HypothesisRunSerializer(serializers.ModelSerializer):
    """Serializer for HypothesisRun."""
    class Meta:
        model = HypothesisRun
        fields = ['id', 'created_at', 'input_text', 'filters_json', 'agent_count', 'mode', 'aggregated_result_json']


class EvidenceSurveyDatumSerializer(serializers.ModelSerializer):
    """Serializer for EvidenceSurveyDatum."""
    class Meta:
        model = EvidenceSurveyDatum
        fields = [
            'id', 'dataset_name', 'date', 'region', 'archetype',
            'question_text', 'distribution_json', 'snippet_text', 'metadata_json'
        ]

