"""
Models for hypothesis testing and agent simulation.
"""

import uuid
from django.db import models
from django.db.models import JSONField


class PersonaAgent(models.Model):
    """Simulated persona agent for hypothesis testing."""

    ARCHETYPE_CHOICES = [
        ("ingredient_purist", "Ingredient Purist"),
        ("clean_beauty_believer", "Clean Beauty Believer"),
        ("clinical_results_seeker", "Clinical Results Seeker"),
        ("luxury_ritualist", "Luxury Ritualist"),
        ("trend_driven_experimenter", "Trend-Driven Experimenter"),
        ("problem_solution_buyer", "Problem-Solution Buyer"),
        ("sensitive_skin_minimalist", "Sensitive-Skin Minimalist"),
        ("makeup_maximalist", "Makeup Maximalist"),
        ("skinimalist", "Skinimalist"),
        ("ethical_buyer", "Ethical Buyer"),
        ("deal_hunter", "Deal Hunter"),
        ("pro_guided_buyer", "Pro-Guided Buyer"),
        ("age_preventive_optimizer", "Age-Preventive Optimizer"),
        ("routine_loyalist", "Routine Loyalist"),
        ("fragrance_identity_buyer", "Fragrance Identity Buyer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=100)
    age_bucket = models.CharField(max_length=20)
    gender = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    income = models.CharField(max_length=50)
    archetype = models.CharField(max_length=50, choices=ARCHETYPE_CHOICES)
    taste_profile_json = JSONField(default=list, help_text="Taste preferences as tags/vector")
    behavior_params_json = JSONField(
        default=dict,
        help_text="Behavioral parameters: price_sensitivity, health_bias, brand_loyalty, novelty_seeking",
    )
    system_prompt = models.TextField(help_text="GPT system prompt for this persona")
    biography = models.TextField(blank=True, help_text="Short persona biography")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["age_bucket", "gender", "region", "income", "archetype"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.get_archetype_display()})"


class SurveyQuestion(models.Model):
    """Survey question template."""

    QUESTION_TYPES = [
        ("likert", "Likert Scale"),
        ("multiple_choice", "Multiple Choice"),
        ("open", "Open Ended"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    choices_json = JSONField(default=list, help_text="Choices for multiple choice or Likert scale")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:50]


class HypothesisRun(models.Model):
    """A hypothesis test run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    input_text = models.TextField()
    filters_json = JSONField(default=dict)
    agent_count = models.IntegerField(default=100)
    mode = models.CharField(
        max_length=10, choices=[("gpt", "GPT"), ("mock", "Mock")], default="mock"
    )
    aggregated_result_json = JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Hypothesis Run {self.id} - {self.input_text[:50]}"


class SurveyResponse(models.Model):
    """Response from an agent to a survey question."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run_id = models.UUIDField()
    agent = models.ForeignKey(
        PersonaAgent, on_delete=models.CASCADE, related_name="survey_responses"
    )
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    response_json = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["run_id", "agent", "question"]),
        ]


class EvidenceSurveyDatum(models.Model):
    """Dummy "real survey" evidence data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_name = models.CharField(max_length=100, default="Fast-Food Consumer Survey 2024")
    date = models.DateField()
    region = models.CharField(max_length=50)
    archetype = models.CharField(max_length=50, blank=True)
    question_text = models.TextField()
    distribution_json = JSONField(default=dict, help_text="Response distribution")
    snippet_text = models.TextField(help_text="Short respondent quote")
    metadata_json = JSONField(default=dict, help_text="Sample size, confidence, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["region", "archetype"]),
        ]

    def __str__(self):
        return f"{self.dataset_name} - {self.question_text[:50]}"
