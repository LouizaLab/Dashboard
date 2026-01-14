"""
Django models for storing Agent-Tron requests/responses (optional)
"""

try:
    from django.db import models
    from django.utils import timezone
    
    # Handle JSONField for different Django versions
    try:
        from django.contrib.postgres.fields import JSONField
    except ImportError:
        # Django 3.1+ uses models.JSONField
        JSONField = models.JSONField
except ImportError:
    # Django not available
    models = None
    JSONField = None
    timezone = None


class PersonaDecision(models.Model):
    """
    Store Agent-Tron persona decision requests/responses
    """
    request_id = models.CharField(max_length=255, unique=True, db_index=True)
    agent_id = models.CharField(max_length=255, db_index=True)
    hypothesis = models.TextField()
    question_type = models.CharField(max_length=50)
    
    # Request data
    persona_data = JSONField(default=dict)
    context_data = JSONField(default=dict)
    seed = models.IntegerField(null=True, blank=True)
    num_samples = models.IntegerField(default=1)
    
    # Response data
    sampled_decision = JSONField(default=dict)
    sampled_responses = JSONField(default=list)
    population_prior = JSONField(default=dict)
    conditioned_distribution = JSONField(default=dict)
    uncertainty = JSONField(default=dict)
    ground_truth_evidence = JSONField(default=list)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent_id', 'created_at']),
            models.Index(fields=['question_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.request_id} - {self.agent_id}"


class AgentTronSession(models.Model):
    """
    Track Agent-Tron sessions for analytics
    """
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Session metadata
    total_requests = models.IntegerField(default=0)
    total_samples = models.IntegerField(default=0)
    
    # Aggregated metrics
    avg_confidence = models.FloatField(null=True, blank=True)
    avg_entropy = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Session {self.session_id}"

