"""
Validation utilities for Agent-Tron
"""

import numpy as np
from typing import Dict


def validate_distribution(distribution: Dict[str, float], tolerance: float = 0.01) -> bool:
    """
    Validate that distribution sums to ~1
    Returns: True if valid, raises ValueError if invalid
    """
    total = sum(distribution.values())
    if abs(total - 1.0) > tolerance:
        raise ValueError(
            f"Distribution does not sum to 1.0 (sum={total:.6f}, tolerance={tolerance})"
        )
    return True


def compute_entropy(distribution: Dict[str, float]) -> float:
    """Compute entropy of distribution"""
    probs = np.array(list(distribution.values()))
    probs = probs[probs > 0]  # Remove zeros
    entropy = -np.sum(probs * np.log2(probs))
    return float(entropy)


def compute_confidence(distribution: Dict[str, float]) -> float:
    """Compute confidence as max probability"""
    max_prob = max(distribution.values())
    return float(max_prob)


def extract_dominant_drivers(distribution: Dict[str, float], top_k: int = 3) -> list:
    """
    Extract top drivers from distribution
    Returns: list of dicts with {'product_id': str, 'probability': float}
    """
    sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    drivers = [
        {'product_id': product_id, 'probability': float(prob)}
        for product_id, prob in sorted_items[:top_k]
    ]
    return drivers

