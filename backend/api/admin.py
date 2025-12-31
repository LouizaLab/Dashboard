"""
Admin configuration for API models.
"""
from django.contrib import admin
from .models import Company, CompanyMetricPoint, Edge
from .sim_models import PersonaAgent, SurveyQuestion, SurveyResponse, HypothesisRun, EvidenceSurveyDatum
from .recipe_models import (
    RecipeVariant, ApprovalPersona, SimulationRun,
    SyntheticFocusGroup, SyntheticSurvey, LaunchReadinessReport
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'created_at']
    search_fields = ['name', 'symbol']


@admin.register(CompanyMetricPoint)
class CompanyMetricPointAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'metric_name', 'value']
    list_filter = ['metric_name', 'date']
    search_fields = ['company__name']


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ['source_company', 'target_company', 'weight']
    search_fields = ['source_company__name', 'target_company__name']


@admin.register(PersonaAgent)
class PersonaAgentAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'archetype', 'age_bucket', 'region', 'gender']
    list_filter = ['archetype', 'age_bucket', 'region', 'gender']
    search_fields = ['display_name']


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'question_type']
    list_filter = ['question_type']


@admin.register(HypothesisRun)
class HypothesisRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'input_text', 'mode', 'agent_count', 'created_at']
    list_filter = ['mode', 'created_at']
    search_fields = ['input_text']


@admin.register(EvidenceSurveyDatum)
class EvidenceSurveyDatumAdmin(admin.ModelAdmin):
    list_display = ['dataset_name', 'question_text', 'region', 'date']
    list_filter = ['region', 'archetype', 'date']
    search_fields = ['question_text', 'snippet_text']


@admin.register(RecipeVariant)
class RecipeVariantAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_product_name', 'price_delta', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'base_product_name', 'base_product_id']


@admin.register(ApprovalPersona)
class ApprovalPersonaAdmin(admin.ModelAdmin):
    list_display = ['name', 'persona_type', 'risk_tolerance', 'created_at']
    list_filter = ['persona_type', 'created_at']
    search_fields = ['name']


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipe_variant', 'status', 'agent_count', 'confidence_score', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipe_variant__name']
    readonly_fields = ['results_json', 'baseline_entropy', 'post_change_entropy', 'entropy_delta', 'confidence_score']


@admin.register(SyntheticFocusGroup)
class SyntheticFocusGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'simulation_run', 'overall_sentiment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['simulation_run__recipe_variant__name']


@admin.register(SyntheticSurvey)
class SyntheticSurveyAdmin(admin.ModelAdmin):
    list_display = ['id', 'simulation_run', 'created_at']
    list_filter = ['created_at']
    search_fields = ['simulation_run__recipe_variant__name']


@admin.register(LaunchReadinessReport)
class LaunchReadinessReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'simulation_run', 'recommendation', 'confidence_score', 'created_at']
    list_filter = ['recommendation', 'created_at']
    search_fields = ['simulation_run__recipe_variant__name']
    readonly_fields = ['executive_summary', 'what_changed', 'who_liked_json', 'who_disliked_json', 'risks_json']

