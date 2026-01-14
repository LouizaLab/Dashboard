"""
Django admin for Agent-Tron models
"""

from django.contrib import admin
from .models import PersonaDecision, AgentTronSession


@admin.register(PersonaDecision)
class PersonaDecisionAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'agent_id', 'question_type', 'num_samples', 'created_at']
    list_filter = ['question_type', 'created_at']
    search_fields = ['request_id', 'agent_id', 'hypothesis']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'agent_id', 'hypothesis', 'question_type')
        }),
        ('Request Data', {
            'fields': ('persona_data', 'context_data', 'seed', 'num_samples')
        }),
        ('Response Data', {
            'fields': ('sampled_decision', 'sampled_responses', 'population_prior', 
                      'conditioned_distribution', 'uncertainty', 'ground_truth_evidence')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AgentTronSession)
class AgentTronSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user_id', 'total_requests', 'total_samples', 'last_activity']
    list_filter = ['last_activity', 'created_at']
    search_fields = ['session_id', 'user_id']
    readonly_fields = ['created_at', 'updated_at', 'last_activity']

