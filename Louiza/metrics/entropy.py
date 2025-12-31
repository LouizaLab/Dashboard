"""
Entropy and Confidence Metrics

Maps retrieval results to uncertainty metrics using information theory.
"""

import math
from typing import List, Dict, Any, Optional
from collections import Counter

from Data_Engine.core.schema import DataRecord


def binary_entropy(p: float) -> float:
    """
    Compute binary entropy: H(p) = -p log p - (1-p) log (1-p)
    
    Args:
        p: Probability in [0, 1]
        
    Returns:
        Entropy value (bits)
    """
    if p <= 0 or p >= 1:
        return 0.0
    
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def bucket_entropy(records: List[DataRecord]) -> float:
    """
    Compute multi-class entropy over buckets/sources.
    
    H = -Σ p_i log p_i
    where p_i is the normalized contribution by bucket or source.
    
    Args:
        records: List of DataRecord objects
        
    Returns:
        Entropy value (bits)
    """
    if not records:
        return 0.0
    
    # Count records per bucket
    bucket_counts = Counter(record.bucket_id for record in records)
    total = len(records)
    
    # Compute probabilities
    entropy = 0.0
    for count in bucket_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def source_entropy(records: List[DataRecord]) -> float:
    """
    Compute entropy over sources (source_name).
    
    Args:
        records: List of DataRecord objects
        
    Returns:
        Entropy value (bits)
    """
    if not records:
        return 0.0
    
    source_counts = Counter(record.source_name for record in records if record.source_name)
    total = len(records)
    
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in source_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def calibrated_confidence(
    base_conf: float,
    coverage: Dict[str, Any],
    contradictions: float = 0.0,
    missing_buckets: Optional[List[int]] = None,
) -> float:
    """
    Calibrate confidence score based on coverage and contradictions.
    
    Args:
        base_conf: Base confidence score (0.0-1.0)
        coverage: Coverage dict with buckets_used, counts_by_bucket, etc.
        contradictions: Contradiction penalty (0.0-1.0)
        missing_buckets: List of bucket IDs that should have been queried but weren't
        
    Returns:
        Calibrated confidence score (0.0-1.0)
    """
    confidence = base_conf
    
    # Coverage penalty: missing expected buckets reduces confidence
    if missing_buckets:
        penalty = len(missing_buckets) * 0.1  # 10% per missing bucket
        confidence -= penalty
    
    # Contradiction penalty
    confidence -= contradictions * 0.2  # Up to 20% penalty
    
    # Bucket diversity bonus
    buckets_used = coverage.get("buckets_used", [])
    if len(buckets_used) >= 3:
        confidence += 0.1  # Bonus for multi-bucket coverage
    elif len(buckets_used) == 1:
        confidence -= 0.1  # Penalty for single bucket
    
    # Sample size bonus
    counts_by_bucket = coverage.get("counts_by_bucket", {})
    total_count = sum(counts_by_bucket.values())
    if total_count >= 20:
        confidence += 0.1
    elif total_count < 5:
        confidence -= 0.2
    
    return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]


def compute_evidence_mass(records: List[DataRecord]) -> Dict[str, Any]:
    """
    Compute "evidence mass" metrics:
    - Mass per bucket
    - Mass per time window
    - Mass per sentiment polarity
    
    Args:
        records: List of DataRecord objects
        
    Returns:
        Dictionary with evidence mass metrics
    """
    if not records:
        return {
            "mass_by_bucket": {},
            "mass_by_time_window": {},
            "mass_by_sentiment": {},
            "total_mass": 0,
        }
    
    # Mass by bucket
    mass_by_bucket = Counter(record.bucket_id for record in records)
    
    # Mass by time window (monthly bins)
    mass_by_time = {}
    for record in records:
        if record.timestamp:
            time_key = f"{record.timestamp.year}-{record.timestamp.month:02d}"
            mass_by_time[time_key] = mass_by_time.get(time_key, 0) + 1
    
    # Mass by sentiment polarity
    mass_by_sentiment = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "unknown": 0,
    }
    for record in records:
        if record.sentiment is None:
            mass_by_sentiment["unknown"] += 1
        elif record.sentiment > 0.1:
            mass_by_sentiment["positive"] += 1
        elif record.sentiment < -0.1:
            mass_by_sentiment["negative"] += 1
        else:
            mass_by_sentiment["neutral"] += 1
    
    return {
        "mass_by_bucket": dict(mass_by_bucket),
        "mass_by_time_window": mass_by_time,
        "mass_by_sentiment": mass_by_sentiment,
        "total_mass": len(records),
    }


def compute_coverage_penalty(
    expected_buckets: List[int],
    actual_buckets: List[int],
    intent_type: str,
) -> float:
    """
    Compute coverage penalty for missing buckets.
    
    Args:
        expected_buckets: Buckets that should have been queried
        actual_buckets: Buckets that were actually queried
        intent_type: Type of intent (affects which buckets are critical)
        
    Returns:
        Penalty value (0.0-1.0)
    """
    missing = set(expected_buckets) - set(actual_buckets)
    
    if not missing:
        return 0.0
    
    # Critical buckets for different intent types
    critical_buckets = {
        "sentiment_analysis": [2, 4],  # Surveys and scraped reviews
        "preference_discovery": [2, 4],
        "market_inference": [3],  # Financial data
        "demographic_comparison": [2],  # Surveys
    }
    
    critical = set(critical_buckets.get(intent_type, []))
    missing_critical = missing & critical
    
    # Penalty: 0.2 per missing critical bucket, 0.1 per missing non-critical
    penalty = len(missing_critical) * 0.2 + (len(missing) - len(missing_critical)) * 0.1
    
    return min(1.0, penalty)

