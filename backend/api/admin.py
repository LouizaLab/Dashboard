"""
Admin configuration for API models.
"""
from django.contrib import admin
from .models import Company, CompanyMetricPoint, Edge
from .sim_models import PersonaAgent, SurveyQuestion, SurveyResponse, HypothesisRun, EvidenceSurveyDatum


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

