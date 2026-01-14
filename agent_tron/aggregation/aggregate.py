"""
Aggregation module for executive summaries
"""

from typing import List, Dict
import numpy as np
from collections import defaultdict

from ..schemas.response import PersonaDecisionResponse, AggregateResponse
from ..utils.validation import compute_entropy


def aggregate_responses(responses: List[PersonaDecisionResponse]) -> AggregateResponse:
    """
    Aggregate multiple persona decision responses into executive summary
    """
    if not responses:
        raise ValueError("Cannot aggregate empty list of responses")
    
    n_agents = len(responses)
    
    # Weighted aggregation: each agent contributes weight = confidence
    weights = [r.uncertainty.confidence for r in responses]
    total_weight = sum(weights)
    
    if total_weight == 0:
        # Fallback to uniform weights
        weights = [1.0] * n_agents
        total_weight = n_agents
    
    # Aggregate preference distribution (weighted average)
    preference_breakdown = defaultdict(float)
    for response, weight in zip(responses, weights):
        normalized_weight = weight / total_weight
        for product_id, prob in response.conditioned_distribution.items():
            preference_breakdown[product_id] += prob * normalized_weight
    
    # Normalize
    total = sum(preference_breakdown.values())
    if total > 0:
        preference_breakdown = {k: v / total for k, v in preference_breakdown.items()}
    
    # Segment insights: group by archetype
    # Extract archetype from agent_id or use a default
    segment_insights = defaultdict(lambda: {'count': 0, 'preferences': defaultdict(float)})
    
    for response, weight in zip(responses, weights):
        # Try to extract archetype from agent_id, fallback to 'unknown'
        archetype = 'unknown'
        if '_' in response.agent_id:
            archetype = response.agent_id.split('_')[0]
        # Or try to get from lpm_trace if available
        # For now, use a simple heuristic
        segment_insights[archetype]['count'] += 1
        
        normalized_weight = weight / total_weight
        for product_id, prob in response.conditioned_distribution.items():
            segment_insights[archetype]['preferences'][product_id] += prob * normalized_weight
    
    # Normalize segment preferences
    segment_summary = {}
    for archetype, data in segment_insights.items():
        total_seg = sum(data['preferences'].values())
        if total_seg > 0:
            normalized_prefs = {k: v / total_seg for k, v in data['preferences'].items()}
        else:
            normalized_prefs = {}
        
        segment_summary[archetype] = {
            'count': data['count'],
            'mean_preferences': normalized_prefs
        }
    
    # Top drivers: count occurrences weighted by confidence
    driver_counts = defaultdict(float)
    for response, weight in zip(responses, weights):
        normalized_weight = weight / total_weight
        for driver in response.dominant_drivers:
            product_id = driver.get('product_id', '')
            prob = driver.get('probability', 0.0)
            driver_counts[product_id] += prob * normalized_weight
    
    # Sort and get top drivers
    sorted_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)
    top_drivers = [
        {'product_id': product_id, 'weight': float(weight)}
        for product_id, weight in sorted_drivers[:10]
    ]
    
    # Overall entropy: entropy of aggregated distribution
    overall_entropy = compute_entropy(preference_breakdown)
    
    # Overall confidence: weighted average of individual confidences
    overall_confidence = sum(
        r.uncertainty.confidence * w for r, w in zip(responses, weights)
    ) / total_weight
    
    # Evidence coverage stats
    evidence_coverage = defaultdict(int)
    evidence_types = set()
    for response in responses:
        for evidence in response.ground_truth_evidence:
            evidence_types.add(evidence.source_type)
            evidence_coverage[evidence.source_type] += 1
    
    evidence_coverage_dict = {
        'total_evidence_items': sum(evidence_coverage.values()),
        'unique_evidence_types': len(evidence_types),
        'by_type': dict(evidence_coverage)
    }
    
    return AggregateResponse(
        agents_tested=n_agents,
        preference_breakdown=preference_breakdown,
        segment_insights=segment_summary,
        top_drivers=top_drivers,
        overall_entropy=overall_entropy,
        overall_confidence=overall_confidence,
        evidence_coverage=evidence_coverage_dict
    )

