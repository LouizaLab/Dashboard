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
from .market_insight_models import (
    MarketDefinition, Brand, Product, MarketSignal, InnovationEvent,
    ManifoldPoint, InsightQuery, InsightAnswer,
    MarketSimRun, MarketSimResult, MarketInsightAnswer
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


@admin.register(MarketDefinition)
class MarketDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'vertical', 'category', 'price_tier', 'region', 'created_at']
    list_filter = ['vertical', 'category', 'price_tier', 'region']
    search_fields = ['name', 'category', 'sub_category']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand_type', 'created_at']
    list_filter = ['brand_type']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'price_tier', 'launch_date']
    list_filter = ['category', 'price_tier', 'launch_date']
    search_fields = ['name', 'brand__name']


@admin.register(MarketSignal)
class MarketSignalAdmin(admin.ModelAdmin):
    list_display = ['market', 'date', 'trend_momentum', 'intent_index']
    list_filter = ['date', 'market__vertical']
    search_fields = ['market__name']


@admin.register(InnovationEvent)
class InnovationEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'market', 'brand', 'date']
    list_filter = ['event_type', 'date', 'market__vertical']
    search_fields = ['market__name', 'brand__name']


@admin.register(ManifoldPoint)
class ManifoldPointAdmin(admin.ModelAdmin):
    list_display = ['node_type', 'cluster_label', 'vertical', 'region', 'updated_at']
    list_filter = ['node_type', 'vertical', 'region', 'cluster_id']
    search_fields = ['cluster_label']


@admin.register(InsightQuery)
class InsightQueryAdmin(admin.ModelAdmin):
    list_display = ['question', 'case_template', 'vertical', 'timestamp']
    list_filter = ['case_template', 'vertical', 'timestamp']
    search_fields = ['question']


@admin.register(InsightAnswer)
class InsightAnswerAdmin(admin.ModelAdmin):
    list_display = ['query', 'confidence_score', 'entropy_score', 'created_at']
    list_filter = ['confidence_score', 'created_at']
    search_fields = ['query__question']


@admin.register(MarketSimRun)
class MarketSimRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'vertical', 'region', 'created_at']
    list_filter = ['vertical', 'region', 'created_at']
    search_fields = ['question']


@admin.register(MarketSimResult)
class MarketSimResultAdmin(admin.ModelAdmin):
    list_display = ['sim_run', 'confidence_score', 'entropy_score', 'created_at']
    list_filter = ['confidence_score', 'created_at']
    search_fields = ['sim_run__question']


@admin.register(MarketInsightAnswer)
class MarketInsightAnswerModelAdmin(admin.ModelAdmin):
    list_display = ['sim_result', 'gpt_model', 'cached', 'tokens_used', 'created_at']
    list_filter = ['gpt_model', 'cached', 'created_at']
    search_fields = ['sim_result__sim_run__question']

