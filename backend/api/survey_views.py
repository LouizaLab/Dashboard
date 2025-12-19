"""
Additional views for survey questions.
"""
from rest_framework import viewsets
from .sim_models import SurveyQuestion
from .sim_serializers import SurveyQuestionSerializer


class SurveyQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SurveyQuestion."""
    queryset = SurveyQuestion.objects.all()
    serializer_class = SurveyQuestionSerializer

