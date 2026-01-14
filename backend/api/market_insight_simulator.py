"""
Market Simulation Engine - Deterministic synthetic market impact simulation.
Simulates market perturbations and their impact on the 3D manifold.
"""
import numpy as np
import hashlib
from typing import Dict, List, Tuple, Optional
from django.db.models import Q
from .market_insight_models import (
    MarketDefinition, Brand, Product, MarketSignal, InnovationEvent,
    ManifoldPoint, MarketSimRun, MarketSimResult
)


class MarketSimulator:
    """Deterministic synthetic market simulation engine."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
    
    def simulate_market_impact(
        self,
        question: str,
        vertical: str,
        region: str,
        pinned_nodes: List[str],
        filters: Dict,
        scenario_params: Dict
    ) -> Dict:
        """
        Simulate market impact from a question/scenario.
        
        Returns SimulationResult dict with:
        - impacted_clusters
        - impacted_points (with reactivity scores)
        - category_tier_shifts
        - competitor_positioning
        - innovation_patterns
        - confidence_score
        - entropy_score
        """
        # Get all manifold points for the vertical/region
        points = ManifoldPoint.objects.filter(vertical=vertical, region=region)
        
        # Determine perturbation type from question/scenario
        perturbation_type = self._detect_perturbation_type(question, scenario_params)
        
        # Calculate impact propagation
        impacted_clusters = self._calculate_cluster_impact(
            points, pinned_nodes, perturbation_type, scenario_params
        )
        
        # Calculate point-level reactivity
        impacted_points = self._calculate_point_reactivity(
            points, pinned_nodes, impacted_clusters, perturbation_type
        )
        
        # Generate category/tier shifts
        category_tier_shifts = self._generate_category_tier_shifts(
            vertical, impacted_clusters, scenario_params
        )
        
        # Generate competitor positioning
        competitor_positioning = self._generate_competitor_positioning(
            vertical, impacted_clusters
        )
        
        # Generate innovation patterns
        innovation_patterns = self._generate_innovation_patterns(
            vertical, scenario_params, impacted_clusters
        )
        
        # Calculate confidence and entropy
        confidence_score, entropy_score = self._calculate_confidence_entropy(
            impacted_clusters, impacted_points, len(pinned_nodes)
        )
        
        return {
            'impacted_clusters': impacted_clusters,
            'impacted_points': impacted_points,
            'category_tier_shifts': category_tier_shifts,
            'competitor_positioning': competitor_positioning,
            'innovation_patterns': innovation_patterns,
            'confidence_score': confidence_score,
            'entropy_score': entropy_score,
        }
    
    def _detect_perturbation_type(self, question: str, scenario_params: Dict) -> str:
        """Detect what type of market perturbation this is."""
        question_lower = question.lower()
        
        if scenario_params.get('price_tier_shift'):
            return 'price_tier_shift'
        elif scenario_params.get('channel_shift'):
            return 'channel_shift'
        elif scenario_params.get('claim_emphasis'):
            return 'claim_shift'
        elif 'whitespace' in question_lower or 'opportunity' in question_lower:
            return 'whitespace_discovery'
        elif 'portfolio' in question_lower or 'strategy' in question_lower:
            return 'portfolio_strategy'
        elif 'category' in question_lower:
            return 'category_shift'
        else:
            return 'general_analysis'
    
    def _calculate_cluster_impact(
        self,
        points,
        pinned_nodes: List[str],
        perturbation_type: str,
        scenario_params: Dict
    ) -> List[Dict]:
        """Calculate which clusters are impacted and by how much."""
        # Get clusters
        clusters = {}
        for point in points:
            if point.cluster_id is not None:
                cluster_id = point.cluster_id
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        'cluster_id': cluster_id,
                        'cluster_label': point.cluster_label,
                        'points': [],
                        'pinned_count': 0,
                    }
                clusters[cluster_id]['points'].append(point)
                
                # Check if pinned
                if str(point.node_id) in pinned_nodes:
                    clusters[cluster_id]['pinned_count'] += 1
        
        # Calculate impact scores
        impacted_clusters = []
        for cluster_id, cluster_data in clusters.items():
            # Base impact from pinned nodes
            pinned_impact = min(1.0, cluster_data['pinned_count'] / max(1, len(cluster_data['points']) / 10))
            
            # Perturbation-specific impact
            if perturbation_type == 'price_tier_shift':
                tier = scenario_params.get('price_tier_shift', '')
                # Check if cluster matches tier
                label_lower = cluster_data['cluster_label'].lower()
                if tier and tier.replace('_', ' ') in label_lower:
                    perturbation_impact = 0.8
                else:
                    perturbation_impact = 0.2
            elif perturbation_type == 'channel_shift':
                channel = scenario_params.get('channel_shift', '')
                # Clusters with matching channel emphasis
                perturbation_impact = 0.6 if channel else 0.3
            elif perturbation_type == 'claim_shift':
                claim = scenario_params.get('claim_emphasis', '')
                label_lower = cluster_data['cluster_label'].lower()
                if claim and claim.replace('_', ' ') in label_lower:
                    perturbation_impact = 0.7
                else:
                    perturbation_impact = 0.2
            else:
                perturbation_impact = 0.4
            
            # Combine impacts
            impact_score = (pinned_impact * 0.4 + perturbation_impact * 0.6)
            
            # Drivers
            drivers = []
            if cluster_data['pinned_count'] > 0:
                drivers.append(f"{cluster_data['pinned_count']} pinned nodes")
            if perturbation_type != 'general_analysis':
                drivers.append(perturbation_type.replace('_', ' ').title())
            
            impacted_clusters.append({
                'cluster_id': cluster_id,
                'cluster_label': cluster_data['cluster_label'],
                'impact_score': round(impact_score, 3),
                'drivers': drivers,
                'point_count': len(cluster_data['points']),
            })
        
        # Sort by impact score
        impacted_clusters.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return impacted_clusters[:10]  # Top 10 impacted clusters
    
    def _calculate_point_reactivity(
        self,
        points,
        pinned_nodes: List[str],
        impacted_clusters: List[Dict],
        perturbation_type: str
    ) -> List[Dict]:
        """Calculate reactivity score (0-1) for each point."""
        cluster_impact_map = {c['cluster_id']: c['impact_score'] for c in impacted_clusters}
        pinned_set = set(pinned_nodes)
        
        impacted_points = []
        for point in points:
            reactivity = 0.0
            
            # Base reactivity from cluster impact
            if point.cluster_id in cluster_impact_map:
                reactivity += cluster_impact_map[point.cluster_id] * 0.6
            
            # Boost if pinned
            if str(point.node_id) in pinned_set:
                reactivity += 0.4
            
            # Distance-based decay for non-pinned points
            if str(point.node_id) not in pinned_set and point.cluster_id in cluster_impact_map:
                reactivity *= 0.7
            
            reactivity = min(1.0, reactivity)
            
            if reactivity > 0.1:  # Only include points with meaningful reactivity
                impacted_points.append({
                    'node_id': str(point.node_id),
                    'node_type': point.node_type,
                    'reactivity_score': round(reactivity, 3),
                    'cluster_id': point.cluster_id,
                })
        
        return impacted_points
    
    def _generate_category_tier_shifts(
        self,
        vertical: str,
        impacted_clusters: List[Dict],
        scenario_params: Dict
    ) -> Dict:
        """Generate category × tier impact table."""
        shifts = {}
        
        # Extract categories and tiers from impacted clusters
        for cluster in impacted_clusters[:5]:
            label = cluster['cluster_label']
            impact = cluster['impact_score']
            
            # Parse category and tier from label
            category = 'Unknown'
            tier = 'Unknown'
            
            if 'Skincare' in label:
                category = 'Skincare'
            elif 'Makeup' in label:
                category = 'Makeup'
            elif 'Fragrance' in label:
                category = 'Fragrance'
            
            if 'Premium' in label:
                tier = 'Premium'
            elif 'Super-Premium' in label or 'Super Premium' in label:
                tier = 'Super-Premium'
            elif 'Ultra-Luxury' in label or 'Ultra Luxury' in label:
                tier = 'Ultra-Luxury'
            
            key = f"{category}_{tier}"
            if key not in shifts:
                shifts[key] = {
                    'category': category,
                    'tier': tier,
                    'impact': 0.0,
                    'trend': 'neutral',
                }
            
            shifts[key]['impact'] = max(shifts[key]['impact'], impact)
        
        # Apply scenario params
        if scenario_params.get('price_tier_shift'):
            tier_shift = scenario_params['price_tier_shift']
            for key, shift_data in shifts.items():
                if shift_data['tier'] == tier_shift.replace('_', ' ').title():
                    shift_data['impact'] += 0.2
                    shift_data['trend'] = 'growing'
        
        return shifts
    
    def _generate_competitor_positioning(
        self,
        vertical: str,
        impacted_clusters: List[Dict]
    ) -> Dict:
        """Generate competitor positioning grid."""
        # Get brands from impacted clusters
        cluster_ids = [c['cluster_id'] for c in impacted_clusters[:5]]
        
        # Get markets in these clusters
        points = ManifoldPoint.objects.filter(
            cluster_id__in=cluster_ids,
            node_type='market'
        )
        
        market_ids = [p.node_id for p in points]
        markets = MarketDefinition.objects.filter(id__in=market_ids)
        
        # Build positioning grid
        positioning = {}
        categories = set()
        tiers = set()
        
        for market in markets:
            categories.add(market.category)
            if market.price_tier:
                tiers.add(market.price_tier)
            
            # Get competitor brands
            if market.competitor_set:
                for brand_id in market.competitor_set[:5]:  # Limit to 5 competitors
                    try:
                        brand = Brand.objects.get(id=brand_id)
                        key = f"{market.category}_{market.price_tier or 'unknown'}"
                        if key not in positioning:
                            positioning[key] = []
                        
                        positioning[key].append({
                            'brand_name': brand.name,
                            'brand_type': brand.brand_type,
                            'positioning_tags': brand.positioning_tags[:3],
                        })
                    except Brand.DoesNotExist:
                        continue
        
        return {
            'grid': positioning,
            'categories': list(categories),
            'tiers': list(tiers),
        }
    
    def _generate_innovation_patterns(
        self,
        vertical: str,
        scenario_params: Dict,
        impacted_clusters: List[Dict]
    ) -> Dict:
        """Generate innovation patterns."""
        patterns = {
            'indie': {'launches': 0, 'claims': [], 'formats': []},
            'luxury': {'launches': 0, 'claims': [], 'formats': []},
            'heritage': {'launches': 0, 'claims': [], 'formats': []},
        }
        
        # Get innovation events for impacted clusters
        cluster_ids = [c['cluster_id'] for c in impacted_clusters[:5]]
        points = ManifoldPoint.objects.filter(cluster_id__in=cluster_ids, node_type='market')
        market_ids = [p.node_id for p in points]
        
        events = InnovationEvent.objects.filter(market_id__in=market_ids).order_by('-date')[:20]
        
        for event in events:
            if event.brand:
                brand_type = event.brand.brand_type
                if brand_type in ['indie', 'luxury', 'heritage']:
                    patterns[brand_type]['launches'] += 1
                    if event.innovation_tags:
                        patterns[brand_type]['claims'].extend(event.innovation_tags[:2])
                    if event.product:
                        patterns[brand_type]['formats'].append(event.product.format)
        
        # Apply scenario params
        if scenario_params.get('claim_emphasis'):
            claim = scenario_params['claim_emphasis']
            # Boost matching claim patterns
            for brand_type in patterns:
                if claim in patterns[brand_type]['claims']:
                    patterns[brand_type]['launches'] += 2
        
        return patterns
    
    def _calculate_confidence_entropy(
        self,
        impacted_clusters: List[Dict],
        impacted_points: List[Dict],
        pinned_count: int
    ) -> Tuple[int, float]:
        """Calculate confidence (1-5) and entropy (0-1) scores."""
        # Confidence based on evidence
        evidence_count = len(impacted_clusters) + len(impacted_points)
        base_confidence = min(5, max(1, 1 + evidence_count // 10))
        
        # Boost if pinned nodes
        if pinned_count > 0:
            base_confidence = min(5, base_confidence + 1)
        
        # Entropy based on impact dispersion
        if impacted_clusters:
            impact_scores = [c['impact_score'] for c in impacted_clusters]
            impact_std = np.std(impact_scores) if len(impact_scores) > 1 else 0.0
            entropy = min(1.0, impact_std / 0.5)  # Normalize
        else:
            entropy = 0.5
        
        return base_confidence, round(entropy, 3)
