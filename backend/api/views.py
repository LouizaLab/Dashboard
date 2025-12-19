"""
API views for the network demo.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Company, CompanyMetricPoint, Edge
from .serializers import (
    CompanySerializer, CompanyDetailSerializer, MetricPointSerializer,
    EdgeSerializer, NetworkSerializer
)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Company model."""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer
    
    @action(detail=True, methods=['get'])
    def timeseries(self, request, pk=None):
        """Get time series data for a company."""
        company = self.get_object()
        metric = request.query_params.get('metric', 'foot_traffic')
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        queryset = company.metrics.filter(metric_name=metric)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        queryset = queryset.order_by('date')
        serializer = MetricPointSerializer(queryset, many=True)
        return Response(serializer.data)


class EdgeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Edge model."""
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer


class NetworkView(viewsets.ViewSet):
    """View for network graph data."""
    
    def list(self, request):
        """Get network graph data formatted for Cytoscape."""
        view_type = request.query_params.get('view', 'Market Insight')
        
        # Get all companies
        companies = Company.objects.all()
        
        # Build nodes
        nodes = []
        for company in companies:
            # Get recent KPIs
            kpis = {}
            for metric_name in ['foot_traffic', 'revenue', 'intent_index', 'taste_index']:
                # Filter first, then slice
                metric_points = company.metrics.filter(metric_name=metric_name).order_by('-date')[:30]
                if metric_points.exists():
                    values = [m.value for m in metric_points]
                    kpis[metric_name] = {
                        'current': values[0] if values else 0,
                        'avg': sum(values) / len(values) if values else 0,
                    }
            
            node_data = {
                'id': str(company.id),
                'label': company.name,
                'name': company.name,
                'kpis': kpis,
            }
            nodes.append({'data': node_data})
        
        # Build edges
        edges = []
        edge_queryset = Edge.objects.select_related('source_company', 'target_company').all()
        
        # Apply view-based filtering/weighting
        for edge in edge_queryset:
            weight = edge.weight
            
            # Adjust weight based on view type
            if view_type == 'Foot Traffic':
                weight = edge.factors_json.get('foot_traffic_correlation', weight)
            elif view_type == 'Revenue':
                weight = edge.factors_json.get('revenue_correlation', weight)
            elif view_type == 'Intent':
                weight = edge.factors_json.get('intent_overlap', weight)
            elif view_type == 'Taste Dynamics':
                weight = edge.factors_json.get('taste_similarity', weight)
            
            edge_data = {
                'id': f"e{edge.id}",
                'source': str(edge.source_company.id),
                'target': str(edge.target_company.id),
                'weight': weight,
                'edge_weight': edge.weight,
                'edge_weight_matrix': edge.matrix_json,
                'edge_factors': edge.factors_json,
                'top_factors': edge.get_top_factors(3),
            }
            edges.append({'data': edge_data})
        
        return Response({
            'nodes': nodes,
            'edges': edges,
        })


class CompareView(viewsets.ViewSet):
    """View for comparing two companies."""
    
    def list(self, request):
        """Compare two companies' time series."""
        company_a_id = request.query_params.get('a')
        company_b_id = request.query_params.get('b')
        metric = request.query_params.get('metric', 'foot_traffic')
        
        if not company_a_id or not company_b_id:
            return Response(
                {'error': 'Both company IDs (a and b) are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company_a = Company.objects.get(id=company_a_id)
            company_b = Company.objects.get(id=company_b_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'One or both companies not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get time series for both companies
        metrics_a = company_a.metrics.filter(metric_name=metric).order_by('date')
        metrics_b = company_b.metrics.filter(metric_name=metric).order_by('date')
        
        # Align dates
        dates = set()
        dates.update([m.date for m in metrics_a])
        dates.update([m.date for m in metrics_b])
        dates = sorted(list(dates))
        
        series_a = {m.date: m.value for m in metrics_a}
        series_b = {m.date: m.value for m in metrics_b}
        
        aligned_data = []
        for date in dates:
            aligned_data.append({
                'date': date.isoformat(),
                'company_a': series_a.get(date),
                'company_b': series_b.get(date),
            })
        
        # Get edge between companies if exists
        edge = None
        try:
            edge = Edge.objects.get(
                source_company=company_a,
                target_company=company_b
            )
        except Edge.DoesNotExist:
            try:
                edge = Edge.objects.get(
                    source_company=company_b,
                    target_company=company_a
                )
            except Edge.DoesNotExist:
                pass
        
        edge_metric = None
        if edge:
            # Derive edge metric from factors
            factors = edge.factors_json or {}
            edge_metric = factors.get('intent_overlap', edge.weight)
        
        return Response({
            'company_a': {
                'id': company_a.id,
                'name': company_a.name,
            },
            'company_b': {
                'id': company_b.id,
                'name': company_b.name,
            },
            'metric': metric,
            'data': aligned_data,
            'edge_metric': edge_metric,
            'edge': EdgeSerializer(edge).data if edge else None,
        })

