"""
URL routing for API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, EdgeViewSet, NetworkView, CompareView
from .sim_views import PersonaAgentViewSet, HypothesisViewSet, SurveyViewSet, TasteTestViewSet, ChatViewSet, MarketInsightViewSet
from .survey_views import SurveyQuestionViewSet
from .agent_tron_views import AgentTronViewSet
from .recipe_views import (
    RecipeVariantViewSet, ApprovalPersonaViewSet, SimulationRunViewSet
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'edges', EdgeViewSet, basename='edge')
router.register(r'network', NetworkView, basename='network')
router.register(r'compare', CompareView, basename='compare')
router.register(r'agents', PersonaAgentViewSet, basename='agent')
router.register(r'hypothesis', HypothesisViewSet, basename='hypothesis')
router.register(r'survey', SurveyViewSet, basename='survey')
router.register(r'survey/questions', SurveyQuestionViewSet, basename='survey-question')
router.register(r'taste_test', TasteTestViewSet, basename='taste_test')
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'market-insight', MarketInsightViewSet, basename='market-insight')
router.register(r'recipe/variants', RecipeVariantViewSet, basename='recipe-variant')
router.register(r'recipe/personas', ApprovalPersonaViewSet, basename='approval-persona')
router.register(r'recipe/simulations', SimulationRunViewSet, basename='simulation-run')
router.register(r'agent_tron', AgentTronViewSet, basename='agent-tron')

urlpatterns = [
    path('', include(router.urls)),
]

