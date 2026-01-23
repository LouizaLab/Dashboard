"""
Models for the network demo API.
"""
from django.db import models
import json


class Company(models.Model):
    """Fast-food company model."""
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CompanyMetricPoint(models.Model):
    """Time series metric point for a company."""
    METRIC_CHOICES = [
        ('foot_traffic', 'Foot Traffic'),
        ('revenue', 'Revenue'),
        ('intent_index', 'Intent Index'),
        ('taste_index', 'Taste Index'),
        ('sentiment_proxy', 'Sentiment Proxy'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    metric_name = models.CharField(max_length=50, choices=METRIC_CHOICES)
    value = models.FloatField()
    segment_json = models.JSONField(default=dict, help_text="Demographic segment data")
    
    class Meta:
        ordering = ['-date', 'metric_name']
        indexes = [
            models.Index(fields=['company', 'date', 'metric_name']),
        ]
        unique_together = [['company', 'date', 'metric_name']]
    
    def __str__(self):
        return f"{self.company.name} - {self.metric_name} - {self.date}"


class Edge(models.Model):
    """Edge representing relationship between two companies."""
    source_company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='outgoing_edges'
    )
    target_company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='incoming_edges'
    )
    weight = models.FloatField(help_text="Overall edge weight")
    factors_json = models.JSONField(
        default=dict,
        help_text="Breakdown of factors (intent, taste, context, etc.)"
    )
    matrix_json = models.JSONField(
        default=list,
        help_text="3x3 matrix representation of edge factors"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['source_company', 'target_company']]
        ordering = ['-weight']
    
    def __str__(self):
        return f"{self.source_company.name} -> {self.target_company.name} ({self.weight:.2f})"
    
    def get_top_factors(self, n=3):
        """Get top N factors by weight."""
        factors = self.factors_json or {}
        sorted_factors = sorted(
            factors.items(), 
            key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )
        return dict(sorted_factors[:n])
    
    def recalculate(self, lookback_days=90, min_data_points=10):
        """
        Recalculate edge weight and factors based on actual metrics.
        
        Args:
            lookback_days: Number of days to look back for calculations
            min_data_points: Minimum data points required
            
        Returns:
            Self (for chaining)
        """
        from api.edge_calculator import EdgeWeightCalculator
        
        calculator = EdgeWeightCalculator(
            lookback_days=lookback_days,
            min_data_points=min_data_points
        )
        
        calculator.recalculate_edge(self)
        return self

