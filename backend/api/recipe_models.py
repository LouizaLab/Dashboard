"""
Models for recipe simulation and regulatory readiness.
"""
import uuid
from django.db import models
from django.db.models import JSONField


class RecipeVariant(models.Model):
    """
    Represents a recipe change/variant to be simulated.
    Maps to Phase-1 embeddings for taste/preference prediction.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Human-readable name for this variant")
    base_product_id = models.CharField(max_length=100, help_text="ID of the base product being modified")
    base_product_name = models.CharField(max_length=200, blank=True)
    
    # Ingredient changes
    ingredient_changes_json = JSONField(
        default=dict,
        help_text="{'added': [list], 'removed': [list], 'substituted': {old: new}}"
    )
    
    # Nutrition changes (deltas from base)
    nutrition_delta_json = JSONField(
        default=dict,
        help_text="{'calories': delta, 'sugar': delta, 'fat': delta, 'sodium': delta, 'protein': delta}"
    )
    
    # Sensory delta vector (normalized 0-1)
    sensory_delta_json = JSONField(
        default=dict,
        help_text="{'sweetness': delta, 'saltiness': delta, 'texture': delta, 'heat': delta, 'aroma': delta}"
    )
    
    # Price change
    price_delta = models.FloatField(default=0.0, help_text="Price change in dollars")
    
    # Positioning tags
    positioning_tags_json = JSONField(
        default=list,
        help_text="Tags like 'healthy', 'indulgent', 'premium', 'value', 'spicy', etc."
    )
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (based on {self.base_product_name or self.base_product_id})"


class ApprovalPersona(models.Model):
    """
    Internal approval personas with acceptance thresholds.
    Represents decision-makers in CPG companies.
    """
    PERSONA_TYPES = [
        ('consumer_insights_head', 'Head of Consumer Insights'),
        ('regulatory_affairs', 'Regulatory Affairs Manager'),
        ('brand_manager', 'Brand Manager'),
        ('finance_forecasting', 'Finance / Forecasting'),
        ('r_d_director', 'R&D Director'),
        ('marketing_director', 'Marketing Director'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona_type = models.CharField(max_length=50, choices=PERSONA_TYPES)
    name = models.CharField(max_length=100, help_text="Custom name for this persona")
    
    # Acceptance thresholds (0-1 scale)
    taste_acceptance_threshold = models.FloatField(default=0.6, help_text="Minimum taste acceptance rate")
    price_sensitivity_threshold = models.FloatField(default=0.5, help_text="Max acceptable price sensitivity impact")
    health_acceptance_threshold = models.FloatField(default=0.5, help_text="Min health score acceptance")
    cannibalization_risk_threshold = models.FloatField(default=0.3, help_text="Max acceptable cannibalization")
    demographic_coverage_threshold = models.FloatField(default=0.5, help_text="Min demographic acceptance")
    substitution_risk_threshold = models.FloatField(default=0.4, help_text="Max acceptable substitution risk")
    
    # Risk tolerance (0-1, higher = more risk tolerant)
    risk_tolerance = models.FloatField(default=0.5)
    
    # Weightings for different factors
    factor_weights_json = JSONField(
        default=dict,
        help_text="Weights for different factors: {'taste': 0.3, 'price': 0.2, 'health': 0.25, ...}"
    )
    
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['persona_type', 'name']
    
    def __str__(self):
        return f"{self.get_persona_type_display()} - {self.name}"


class SimulationRun(models.Model):
    """
    A single simulation run for a recipe variant.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe_variant = models.ForeignKey(RecipeVariant, on_delete=models.CASCADE, related_name='simulation_runs')
    
    # Simulation parameters
    agent_count = models.IntegerField(default=1000, help_text="Number of agents in simulation")
    time_horizon_weeks = models.IntegerField(default=12, help_text="Simulation duration in weeks")
    segment_filters_json = JSONField(
        default=dict,
        help_text="Filters for agent segments: {'age_bucket': [...], 'region': [...], 'archetype': [...]}"
    )
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    results_json = JSONField(
        default=dict,
        help_text="Simulation results: acceptance rates, preference deltas, entropy metrics, etc."
    )
    
    # Metrics
    baseline_entropy = models.FloatField(null=True, blank=True)
    post_change_entropy = models.FloatField(null=True, blank=True)
    entropy_delta = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Approval assessment
    approval_assessment_json = JSONField(
        default=dict,
        help_text="Approval assessment by persona: {'persona_id': {'approved': bool, 'reason': str, ...}}"
    )
    
    # Metadata
    metadata_json = JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Additional metadata: simulator_type, simulator_message, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Simulation {self.id} - {self.recipe_variant.name} ({self.status})"


class SyntheticFocusGroup(models.Model):
    """
    Synthetic focus group transcript generated from simulation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation_run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='focus_groups')
    
    # Group composition
    segment_composition_json = JSONField(
        default=dict,
        help_text="Demographics of focus group participants"
    )
    
    # Transcript
    transcript_json = JSONField(
        default=list,
        help_text="List of {'speaker': str, 'archetype': str, 'text': str, 'sentiment': float}"
    )
    
    # Summary
    summary = models.TextField(blank=True)
    key_themes_json = JSONField(default=list)
    overall_sentiment = models.FloatField(default=0.5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Focus Group - {self.simulation_run.recipe_variant.name}"


class SyntheticSurvey(models.Model):
    """
    Synthetic survey results generated from simulation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation_run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='surveys')
    
    # Survey questions and responses
    questions_json = JSONField(
        default=list,
        help_text="List of questions and response distributions"
    )
    
    # Segment breakdowns
    segment_breakdown_json = JSONField(
        default=dict,
        help_text="Responses broken down by segment"
    )
    
    # Summary statistics
    summary_stats_json = JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Survey - {self.simulation_run.recipe_variant.name}"


class LaunchReadinessReport(models.Model):
    """
    Generated launch readiness report for a simulation run.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation_run = models.OneToOneField(SimulationRun, on_delete=models.CASCADE, related_name='readiness_report')
    
    # Report sections
    executive_summary = models.TextField()
    what_changed = models.TextField()
    who_liked_json = JSONField(default=dict, help_text="Segments that liked the change")
    who_disliked_json = JSONField(default=dict, help_text="Segments that disliked the change")
    risks_json = JSONField(default=list, help_text="List of identified risks")
    confidence_score = models.FloatField()
    recommendation = models.CharField(
        max_length=20,
        choices=[('proceed', 'Proceed'), ('iterate', 'Iterate'), ('kill', 'Kill')]
    )
    recommendation_reasoning = models.TextField()
    
    # Additional data
    charts_data_json = JSONField(default=dict, help_text="Chart data for visualization")
    persona_assessments_json = JSONField(default=dict, help_text="Assessments by approval personas")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Readiness Report - {self.simulation_run.recipe_variant.name} ({self.recommendation})"

