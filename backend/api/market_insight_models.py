"""
Domain models for Market Insight feature.
Implements the core entities for market analysis: markets, brands, products, signals, and innovation events.
"""
import uuid
from django.db import models
from django.db.models import JSONField


class MarketDefinition(models.Model):
    """Represents an observed market that hedge funds/financial institutions recognize."""
    PRICE_TIER_CHOICES = [
        ('entry_premium', 'Entry Premium'),
        ('premium', 'Premium'),
        ('super_premium', 'Super-Premium'),
        ('ultra_luxury', 'Ultra-Luxury'),
        ('clinical', 'Clinical'),
    ]
    
    VERTICAL_CHOICES = [
        ('beauty', 'Beauty'),
        ('food', 'Food'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=50, default='US')
    vertical = models.CharField(max_length=20, choices=VERTICAL_CHOICES)
    category = models.CharField(max_length=100)  # e.g., Skincare, Makeup, Fragrance; Bars, Functional Snacks
    sub_category = models.CharField(max_length=100, blank=True)  # e.g., Serums, Moisturizers; Protein Bars
    price_tier = models.CharField(max_length=50, choices=PRICE_TIER_CHOICES, blank=True)
    channel_mix = JSONField(default=dict, help_text="Channel distribution: Sephora, Ulta, DTC, Amazon, etc.")
    competitor_set = JSONField(default=list, help_text="List of Brand IDs")
    tags = JSONField(default=list, help_text="Tags: clean, clinical, heritage, indie, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vertical', 'category', 'name']
        indexes = [
            models.Index(fields=['vertical', 'region']),
            models.Index(fields=['category', 'sub_category']),
            models.Index(fields=['price_tier']),
        ]
    
    def __str__(self):
        return f"{self.vertical.upper()} | {self.category} | {self.name}"


class Brand(models.Model):
    """Brand entity with positioning and type."""
    BRAND_TYPE_CHOICES = [
        ('heritage', 'Heritage'),
        ('indie', 'Indie'),
        ('mass', 'Mass'),
        ('prestige', 'Prestige'),
        ('luxury', 'Luxury'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    brand_type = models.CharField(max_length=50, choices=BRAND_TYPE_CHOICES)
    positioning_tags = JSONField(default=list, help_text="clean, clinical, performance, luxury heritage, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['brand_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_brand_type_display()})"


class Product(models.Model):
    """Product entity with category, claims, ingredients, and launch info."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_tier = models.CharField(max_length=50, blank=True)
    claims = JSONField(default=list, help_text="hydration, barrier repair, anti-aging, brightening, etc.")
    format = models.CharField(max_length=100, blank=True)  # serum, cream, stick, mist, balm, etc.
    ingredients = JSONField(default=list, help_text="niacinamide, retinol, peptides, etc.")
    launch_date = models.DateField(null=True, blank=True)
    channel = models.CharField(max_length=100, blank=True)
    is_bundle = models.BooleanField(default=False)
    is_kit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-launch_date', 'name']
        indexes = [
            models.Index(fields=['brand', 'category']),
            models.Index(fields=['price_tier']),
            models.Index(fields=['launch_date']),
        ]
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class MarketSignal(models.Model):
    """Time-series signals for a market (intent, momentum, elasticity, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(MarketDefinition, on_delete=models.CASCADE, related_name='signals')
    date = models.DateField()
    intent_index = models.FloatField(null=True, blank=True, help_text="Proxy for consumer intent")
    price_elasticity_proxy = models.FloatField(null=True, blank=True)
    trend_momentum = models.FloatField(null=True, blank=True)
    social_velocity = models.FloatField(null=True, blank=True)
    search_share_proxy = models.FloatField(null=True, blank=True)
    review_sentiment_proxy = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'market']
        indexes = [
            models.Index(fields=['market', 'date']),
        ]
        unique_together = [['market', 'date']]
    
    def __str__(self):
        return f"{self.market.name} - {self.date}"


class InnovationEvent(models.Model):
    """Innovation events: launches, reformulations, campaigns, collaborations."""
    EVENT_TYPE_CHOICES = [
        ('launch', 'Product Launch'),
        ('reformulation', 'Reformulation'),
        ('campaign', 'Campaign'),
        ('collab', 'Collaboration'),
        ('channel_play', 'Channel Play'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(MarketDefinition, on_delete=models.CASCADE, related_name='innovation_events')
    date = models.DateField()
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='innovation_events')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='innovation_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    innovation_tags = JSONField(default=list, help_text="new claim, new format, bundle, channel play, etc.")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'market']
        indexes = [
            models.Index(fields=['market', 'date']),
            models.Index(fields=['brand', 'date']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.market.name} - {self.date}"


class ManifoldPoint(models.Model):
    """3D coordinates for market/brand/product nodes in the manifold visualization."""
    NODE_TYPE_CHOICES = [
        ('market', 'Market'),
        ('brand', 'Brand'),
        ('product', 'Product'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES)
    node_id = models.UUIDField(help_text="ID of the MarketDefinition, Brand, or Product")
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField(default=0.0, help_text="Z coordinate for 3D manifold")
    cluster_id = models.IntegerField(null=True, blank=True)
    cluster_label = models.CharField(max_length=200, blank=True)
    vertical = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=50, default='US')
    reactivity_score = models.FloatField(null=True, blank=True, help_text="Impact score from last simulation (0-1)")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['node_type', 'cluster_id']
        indexes = [
            models.Index(fields=['node_type', 'node_id']),
            models.Index(fields=['vertical', 'region']),
            models.Index(fields=['cluster_id']),
        ]
        unique_together = [['node_type', 'node_id', 'vertical', 'region']]
    
    def __str__(self):
        return f"{self.node_type} {self.node_id} - Cluster {self.cluster_id}"


class InsightQuery(models.Model):
    """Stores consultant queries for observability."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    case_template = models.CharField(max_length=50, blank=True)  # case1, case2, custom
    vertical = models.CharField(max_length=20, blank=True)
    context = JSONField(default=dict, help_text="Selected markets/brands, filters, timeframe")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['case_template', 'vertical']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Query {self.id} - {self.question[:50]}"


class InsightAnswer(models.Model):
    """Stores structured answers from the insight engine."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(InsightQuery, on_delete=models.CASCADE, related_name='answers')
    json_output = JSONField(default=dict, help_text="Full structured JSON response")
    confidence_score = models.IntegerField(null=True, blank=True, help_text="1-5 scale")
    entropy_score = models.FloatField(null=True, blank=True, help_text="0-1 scale")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Answer for Query {self.query.id}"


class MarketSimRun(models.Model):
    """Stores market simulation runs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    vertical = models.CharField(max_length=20)
    region = models.CharField(max_length=50, default='US')
    scenario_params = JSONField(default=dict, help_text="Price tier, channel, claim emphasis, etc.")
    filters = JSONField(default=dict, help_text="Selected markets, categories, etc.")
    pinned_nodes = JSONField(default=list, help_text="List of pinned node IDs")
    seed = models.IntegerField(default=42, help_text="Random seed for reproducibility")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vertical', 'region']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Sim Run {self.id} - {self.question[:50]}"


class MarketSimResult(models.Model):
    """Stores simulation results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sim_run = models.ForeignKey(MarketSimRun, on_delete=models.CASCADE, related_name='results')
    impacted_clusters = JSONField(default=list, help_text="List of impacted clusters with scores")
    impacted_points = JSONField(default=list, help_text="Points with reactivity scores")
    category_tier_shifts = JSONField(default=dict, help_text="Category × tier impact table")
    competitor_positioning = JSONField(default=dict, help_text="Competitor positioning grid")
    innovation_patterns = JSONField(default=dict, help_text="Innovation patterns")
    confidence_score = models.IntegerField(help_text="1-5 scale")
    entropy_score = models.FloatField(help_text="0-1 scale")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sim Result for {self.sim_run.id}"


class MarketInsightAnswer(models.Model):
    """Stores GPT-generated insight answers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sim_result = models.ForeignKey(MarketSimResult, on_delete=models.CASCADE, related_name='insights')
    json_output = JSONField(default=dict, help_text="Strict JSON schema output")
    gpt_model = models.CharField(max_length=50, default='gpt-4o')
    tokens_used = models.IntegerField(null=True, blank=True)
    cached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Insight Answer for {self.sim_result.id}"
