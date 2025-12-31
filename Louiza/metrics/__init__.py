"""
Confidence and Entropy Metrics

Provides functions for computing confidence scores and entropy metrics
from retrieval results.
"""

from .entropy import (
    binary_entropy,
    bucket_entropy,
    calibrated_confidence,
    compute_evidence_mass,
)

__all__ = [
    "binary_entropy",
    "bucket_entropy",
    "calibrated_confidence",
    "compute_evidence_mass",
]

