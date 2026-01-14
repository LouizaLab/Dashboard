"""
Django app configuration for Agent-Tron integration
"""

from django.apps import AppConfig


class AgentTronConfig(AppConfig):
    name = 'agent_tron.django_integration'
    verbose_name = 'Agent-Tron Integration'
    
    def ready(self):
        """Initialize Agent-Tron client when Django starts"""
        pass

