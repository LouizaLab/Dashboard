"""
URL configuration for Agent-Tron Django integration
"""

from django.urls import path
from . import views

app_name = 'agent_tron'

urlpatterns = [
    # Function-based views
    path('persona_decision/', views.persona_decision_view, name='persona_decision'),
    path('batch_decisions/', views.batch_decisions_view, name='batch_decisions'),
    
    # Class-based view (more flexible)
    path('<str:endpoint>/', views.AgentTronView.as_view(), name='agent_tron_endpoint'),
]

