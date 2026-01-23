"""
Edge Weight Calculator for Network Graph
Calculates accurate edge weights and factors based on actual company metrics.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from django.db.models import Q
from datetime import date, timedelta
from .models import Company, CompanyMetricPoint, Edge


class EdgeWeightCalculator:
    """
    Calculates edge weights and factors between companies based on actual metrics.
    
    Methods:
    - intent_overlap: Calculates overlap in intent_index between two companies
    - taste_similarity: Calculates similarity in taste_index between two companies
    - correlation: Calculates Pearson correlation between two time series
    - compute_edge_weight: Computes overall edge weight from multiple factors
    """
    
    def __init__(self, lookback_days: int = 90, min_data_points: int = 10):
        """
        Args:
            lookback_days: Number of days to look back for calculations
            min_data_points: Minimum data points required for valid calculation
        """
        self.lookback_days = lookback_days
        self.min_data_points = min_data_points
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=lookback_days)
    
    def get_metric_series(self, company: Company, metric_name: str) -> Dict[date, float]:
        """
        Get time series of a metric for a company as a date-value dictionary.
        
        Args:
            company: Company instance
            metric_name: Name of the metric
            
        Returns:
            Dictionary mapping date to metric value
        """
        metrics = company.metrics.filter(
            metric_name=metric_name,
            date__gte=self.start_date,
            date__lte=self.end_date
        ).order_by('date')
        
        return {m.date: m.value for m in metrics}
    
    def align_series(self, series_a: Dict[date, float], series_b: Dict[date, float]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Align two time series by date.
        Returns aligned arrays with NaN handling for missing dates.
        
        Args:
            series_a: First time series (date -> value dict)
            series_b: Second time series (date -> value dict)
            
        Returns:
            Tuple of aligned numpy arrays
        """
        # Get common dates
        dates_a = set(series_a.keys())
        dates_b = set(series_b.keys())
        common_dates = sorted(list(dates_a & dates_b))
        
        if len(common_dates) < self.min_data_points:
            return np.array([]), np.array([])
        
        # Build aligned arrays
        aligned_a = np.array([series_a.get(d, np.nan) for d in common_dates])
        aligned_b = np.array([series_b.get(d, np.nan) for d in common_dates])
        
        return aligned_a, aligned_b
    
    def calculate_pearson_correlation(self, series_a: np.ndarray, series_b: np.ndarray) -> float:
        """
        Calculate Pearson correlation coefficient between two series.
        
        Args:
            series_a: First time series
            series_b: Second time series
            
        Returns:
            Correlation coefficient between -1 and 1, normalized to 0-1
        """
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        # Remove NaN values
        mask = ~(np.isnan(series_a) | np.isnan(series_b))
        if mask.sum() < self.min_data_points:
            return 0.0
        
        clean_a = series_a[mask]
        clean_b = series_b[mask]
        
        if len(clean_a) < self.min_data_points:
            return 0.0
        
        # Calculate correlation
        correlation = np.corrcoef(clean_a, clean_b)[0, 1]
        
        # Handle NaN correlation
        if np.isnan(correlation):
            return 0.0
        
        # Normalize to 0-1 range (correlation is -1 to 1)
        # Use absolute value and scale: (corr + 1) / 2
        normalized = (abs(correlation) + 1) / 2
        
        return float(normalized)
    
    def calculate_overlap(self, series_a: np.ndarray, series_b: np.ndarray) -> float:
        """
        Calculate overlap/similarity between two series using cosine similarity.
        
        Args:
            series_a: First time series
            series_b: Second time series
            
        Returns:
            Overlap score between 0 and 1
        """
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        # Remove NaN values
        mask = ~(np.isnan(series_a) | np.isnan(series_b))
        if mask.sum() < self.min_data_points:
            return 0.0
        
        clean_a = series_a[mask]
        clean_b = series_b[mask]
        
        if len(clean_a) < self.min_data_points:
            return 0.0
        
        # Normalize series
        norm_a = np.linalg.norm(clean_a)
        norm_b = np.linalg.norm(clean_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        # Cosine similarity
        cosine_sim = np.dot(clean_a, clean_b) / (norm_a * norm_b)
        
        # Normalize to 0-1 (cosine similarity is -1 to 1)
        normalized = (cosine_sim + 1) / 2
        
        return float(normalized)
    
    def calculate_jaccard_similarity(self, series_a: np.ndarray, series_b: np.ndarray) -> float:
        """
        Calculate Jaccard-like similarity for continuous values.
        Measures intersection over union of value ranges.
        
        Args:
            series_a: First time series
            series_b: Second time series
            
        Returns:
            Similarity score between 0 and 1
        """
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        # Remove NaN values
        mask = ~(np.isnan(series_a) | np.isnan(series_b))
        if mask.sum() < self.min_data_points:
            return 0.0
        
        clean_a = series_a[mask]
        clean_b = series_b[mask]
        
        if len(clean_a) < self.min_data_points:
            return 0.0
        
        # Calculate ranges
        min_a, max_a = clean_a.min(), clean_a.max()
        min_b, max_b = clean_b.min(), clean_b.max()
        
        # Intersection
        intersection_min = max(min_a, min_b)
        intersection_max = min(max_a, max_b)
        
        if intersection_min > intersection_max:
            return 0.0
        
        intersection = intersection_max - intersection_min
        
        # Union
        union_min = min(min_a, min_b)
        union_max = max(max_a, max_b)
        union = union_max - union_min
        
        if union == 0:
            return 1.0 if intersection == 0 else 0.0
        
        return float(intersection / union)
    
    def intent_overlap(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate intent overlap between two companies.
        Uses cosine similarity of intent_index time series.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Intent overlap score between 0 and 1
        """
        series_a = self.get_metric_series(company_a, 'intent_index')
        series_b = self.get_metric_series(company_b, 'intent_index')
        
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        aligned_a, aligned_b = self.align_series(series_a, series_b)
        
        if len(aligned_a) < self.min_data_points:
            return 0.0
        
        return self.calculate_overlap(aligned_a, aligned_b)
    
    def get_latest_metric_value(self, company: Company, metric_name: str, default: float = 0.5) -> float:
        """
        Get the latest value for a metric.
        
        Args:
            company: Company instance
            metric_name: Name of the metric
            default: Default value if no data exists
            
        Returns:
            Latest metric value or default
        """
        latest = company.metrics.filter(
            metric_name=metric_name
        ).order_by('-date').first()
        
        return latest.value if latest else default
    
    def taste_similarity(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate taste similarity between two companies.
        Uses cosine similarity of taste_index time series.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Taste similarity score between 0 and 1
        """
        series_a = self.get_metric_series(company_a, 'taste_index')
        series_b = self.get_metric_series(company_b, 'taste_index')
        
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        aligned_a, aligned_b = self.align_series(series_a, series_b)
        
        if len(aligned_a) < self.min_data_points:
            return 0.0
        
        return self.calculate_overlap(aligned_a, aligned_b)
    
    def foot_traffic_correlation(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate foot traffic correlation between two companies.
        Uses Pearson correlation of foot_traffic time series.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Correlation score between 0 and 1
        """
        series_a = self.get_metric_series(company_a, 'foot_traffic')
        series_b = self.get_metric_series(company_b, 'foot_traffic')
        
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        aligned_a, aligned_b = self.align_series(series_a, series_b)
        
        if len(aligned_a) < self.min_data_points:
            return 0.0
        
        return self.calculate_pearson_correlation(aligned_a, aligned_b)
    
    def revenue_correlation(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate revenue correlation between two companies.
        Uses Pearson correlation of revenue time series.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Correlation score between 0 and 1
        """
        series_a = self.get_metric_series(company_a, 'revenue')
        series_b = self.get_metric_series(company_b, 'revenue')
        
        if len(series_a) < self.min_data_points or len(series_b) < self.min_data_points:
            return 0.0
        
        aligned_a, aligned_b = self.align_series(series_a, series_b)
        
        if len(aligned_a) < self.min_data_points:
            return 0.0
        
        return self.calculate_pearson_correlation(aligned_a, aligned_b)
    
    def compute_substitution_likelihood(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate substitution likelihood based on multiple factors.
        Higher when companies are similar in taste/intent but compete.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Substitution likelihood between 0 and 1
        """
        intent_overlap = self.intent_overlap(company_a, company_b)
        taste_sim = self.taste_similarity(company_a, company_b)
        
        # Substitution is higher when both intent and taste are similar
        # Weighted average with slight preference for intent
        substitution = (0.6 * intent_overlap + 0.4 * taste_sim)
        
        return substitution
    
    def compute_co_visit_probability(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate co-visit probability based on foot traffic correlation.
        Higher correlation suggests customers visit both.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Co-visit probability between 0 and 1
        """
        foot_traffic_corr = self.foot_traffic_correlation(company_a, company_b)
        
        # Co-visit is directly related to foot traffic correlation
        return foot_traffic_corr
    
    def compute_brand_adjacency(self, company_a: Company, company_b: Company) -> float:
        """
        Calculate brand adjacency based on overall similarity.
        Combines multiple factors for brand positioning similarity.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Brand adjacency score between 0 and 1
        """
        intent_overlap = self.intent_overlap(company_a, company_b)
        taste_sim = self.taste_similarity(company_a, company_b)
        revenue_corr = self.revenue_correlation(company_a, company_b)
        
        # Weighted combination
        adjacency = (0.4 * intent_overlap + 0.3 * taste_sim + 0.3 * revenue_corr)
        
        return adjacency
    
    def compute_edge_weight(self, company_a: Company, company_b: Company) -> Tuple[float, Dict]:
        """
        Compute overall edge weight and all factors between two companies.
        
        Args:
            company_a: Source company
            company_b: Target company
            
        Returns:
            Tuple of (overall_weight, factors_dict)
        """
        # Calculate all factors
        factors = {
            'intent_overlap': self.intent_overlap(company_a, company_b),
            'taste_similarity': self.taste_similarity(company_a, company_b),
            'foot_traffic_correlation': self.foot_traffic_correlation(company_a, company_b),
            'revenue_correlation': self.revenue_correlation(company_a, company_b),
            'substitution_likelihood': self.compute_substitution_likelihood(company_a, company_b),
            'co_visit_probability': self.compute_co_visit_probability(company_a, company_b),
            'brand_adjacency': self.compute_brand_adjacency(company_a, company_b),
        }
        
        # Compute overall weight as weighted average of key factors
        # Intent and taste are most important
        weights = {
            'intent_overlap': 0.30,
            'taste_similarity': 0.25,
            'foot_traffic_correlation': 0.15,
            'revenue_correlation': 0.15,
            'brand_adjacency': 0.15,
        }
        
        overall_weight = sum(
            factors[key] * weights[key]
            for key in weights.keys()
        )
        
        # Ensure weight is in valid range [0, 1]
        overall_weight = max(0.0, min(1.0, overall_weight))
        
        # Validate and normalize all factors to [0, 1]
        for key in factors:
            factors[key] = max(0.0, min(1.0, factors[key]))
        
        # Generate 3x3 matrix representation
        # Matrix represents: [Intent, Taste, Revenue] x [Source, Target, Combined]
        # Row 0: Combined metrics (overlaps/correlations)
        # Row 1: Source company metrics (normalized)
        # Row 2: Target company metrics (normalized)
        
        # Normalize revenue values (assuming typical range 0-10000)
        revenue_a = self.get_latest_metric_value(company_a, 'revenue', 5000)
        revenue_b = self.get_latest_metric_value(company_b, 'revenue', 5000)
        revenue_norm_a = min(1.0, revenue_a / 10000)
        revenue_norm_b = min(1.0, revenue_b / 10000)
        
        matrix = [
            [
                factors['intent_overlap'],
                factors['taste_similarity'],
                factors['revenue_correlation']
            ],
            [
                self.get_latest_metric_value(company_a, 'intent_index', 0.5),
                self.get_latest_metric_value(company_a, 'taste_index', 0.5),
                revenue_norm_a
            ],
            [
                self.get_latest_metric_value(company_b, 'intent_index', 0.5),
                self.get_latest_metric_value(company_b, 'taste_index', 0.5),
                revenue_norm_b
            ],
        ]
        
        return overall_weight, factors, matrix
    
    def validate_data_quality(self, company_a: Company, company_b: Company) -> Dict[str, bool]:
        """
        Validate data quality for edge calculation.
        
        Args:
            company_a: First company
            company_b: Second company
            
        Returns:
            Dictionary with validation results for each metric
        """
        validation = {}
        
        for metric_name in ['intent_index', 'taste_index', 'foot_traffic', 'revenue']:
            series_a = self.get_metric_series(company_a, metric_name)
            series_b = self.get_metric_series(company_b, metric_name)
            
            has_enough_data = (
                len(series_a) >= self.min_data_points and
                len(series_b) >= self.min_data_points
            )
            
            validation[metric_name] = has_enough_data
        
        return validation
    
    def recalculate_edge(self, edge: Edge) -> Edge:
        """
        Recalculate edge weight and factors for an existing edge.
        
        Args:
            edge: Edge instance to recalculate
            
        Returns:
            Updated edge instance
        """
        weight, factors, matrix = self.compute_edge_weight(
            edge.source_company,
            edge.target_company
        )
        
        edge.weight = weight
        edge.factors_json = factors
        edge.matrix_json = matrix
        edge.save()
        
        return edge
