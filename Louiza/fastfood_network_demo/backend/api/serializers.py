"""
Serializers for the API.
"""
from rest_framework import serializers
from .models import Company, CompanyMetricPoint, Edge


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model."""
    class Meta:
        model = Company
        fields = ['id', 'name', 'symbol', 'description', 'logo_url']


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Company with KPIs."""
    kpis = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'symbol', 'description', 'logo_url', 'kpis']
    
    def get_kpis(self, obj):
        """Calculate KPIs from recent metrics."""
        recent_metrics = obj.metrics.order_by('-date')[:30]
        if not recent_metrics:
            return {}
        
        kpis = {}
        for metric_name in ['foot_traffic', 'revenue', 'intent_index', 'taste_index']:
            metric_points = recent_metrics.filter(metric_name=metric_name)
            if metric_points.exists():
                values = [m.value for m in metric_points]
                kpis[metric_name] = {
                    'current': values[0] if values else 0,
                    'avg': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                }
        return kpis


class MetricPointSerializer(serializers.ModelSerializer):
    """Serializer for metric points."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = CompanyMetricPoint
        fields = ['id', 'company', 'company_name', 'date', 'metric_name', 'value', 'segment_json']


class EdgeSerializer(serializers.ModelSerializer):
    """Serializer for Edge model."""
    source_name = serializers.CharField(source='source_company.name', read_only=True)
    target_name = serializers.CharField(source='target_company.name', read_only=True)
    top_factors = serializers.SerializerMethodField()
    
    class Meta:
        model = Edge
        fields = [
            'id', 'source_company', 'target_company', 
            'source_name', 'target_name', 'weight', 
            'factors_json', 'matrix_json', 'top_factors'
        ]
    
    def get_top_factors(self, obj):
        """Get top factors for the edge."""
        return obj.get_top_factors(n=3)


class NetworkNodeSerializer(serializers.Serializer):
    """Serializer for Cytoscape node format."""
    data = serializers.DictField()


class NetworkEdgeSerializer(serializers.Serializer):
    """Serializer for Cytoscape edge format."""
    data = serializers.DictField()


class NetworkSerializer(serializers.Serializer):
    """Serializer for network graph data."""
    nodes = NetworkNodeSerializer(many=True)
    edges = NetworkEdgeSerializer(many=True)

