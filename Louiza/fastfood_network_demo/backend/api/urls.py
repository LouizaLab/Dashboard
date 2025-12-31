"""
URL routing for API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, EdgeViewSet, NetworkView, CompareView
from .sim_views import PersonaAgentViewSet, HypothesisViewSet, SurveyViewSet, TasteTestViewSet, ChatViewSet
from .survey_views import SurveyQuestionViewSet

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

urlpatterns = [
    path('', include(router.urls)),
]

