"""
Score Entropy Node

Computes confidence scores and entropy metrics.
"""

from typing import Dict, Any

from ..state import RetrievalState, log_decision
from metrics.entropy import (
    binary_entropy,
    bucket_entropy,
    calibrated_confidence,
    compute_evidence_mass,
    compute_coverage_penalty,
)


class ScoreEntropyNode:
    """
    Node 7: Entropy Scorer
    
    Purpose:
    - Compute confidence score from retrieval results
    - Calculate entropy metrics (binary, bucket, coverage)
    - Compute evidence mass metrics
    """
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute entropy scoring.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with confidence and entropy populated
        """
        retrieved = state["retrieved"]
        retrieved_by_bucket = state["retrieved_by_bucket"]
        intent = state["intent"]
        contradictions = state["contradictions"]
        evidence_summary = state["evidence_summary"]
        
        # Compute base confidence
        base_confidence = self._compute_base_confidence(retrieved, retrieved_by_bucket, evidence_summary)
        
        # Compute coverage penalty
        expected_buckets = self._get_expected_buckets(intent)
        actual_buckets = list(retrieved_by_bucket.keys())
        coverage_penalty = compute_coverage_penalty(
            expected_buckets=expected_buckets,
            actual_buckets=actual_buckets,
            intent_type=intent.get("primary_intent", "general_query"),
        )
        
        # Compute contradiction penalty
        contradiction_penalty = len(contradictions) * 0.1  # 10% per contradiction
        
        # Calibrate confidence
        coverage_dict = {
            "buckets_used": actual_buckets,
            "counts_by_bucket": {bid: len(recs) for bid, recs in retrieved_by_bucket.items()},
        }
        
        calibrated_conf = calibrated_confidence(
            base_conf=base_confidence,
            coverage=coverage_dict,
            contradictions=contradiction_penalty,
            missing_buckets=list(set(expected_buckets) - set(actual_buckets)),
        )
        
        state["confidence"] = calibrated_conf
        
        # Compute entropy metrics
        binary_ent = binary_entropy(calibrated_conf)
        bucket_ent = bucket_entropy(retrieved)
        
        # Compute evidence mass
        evidence_mass = compute_evidence_mass(retrieved)
        
        # Build entropy dict
        entropy = {
            "binary_entropy": binary_ent,
            "bucket_entropy": bucket_ent,
            "coverage_penalty": coverage_penalty,
            "contradiction_penalty": contradiction_penalty,
            "evidence_mass": evidence_mass,
            "notes": self._generate_entropy_notes(calibrated_conf, binary_ent, bucket_ent),
        }
        
        state["entropy"] = entropy
        
        # Update coverage
        state["coverage"] = {
            "buckets_used": actual_buckets,
            "counts_by_bucket": {bid: len(recs) for bid, recs in retrieved_by_bucket.items()},
            "time_span": evidence_summary.get("time_span"),
            "total_records": len(retrieved),
        }
        
        # Log decision
        log_decision(state, "score_entropy", {
            "confidence": calibrated_conf,
            "entropy": entropy,
        })
        
        return state
    
    def _compute_base_confidence(
        self,
        retrieved: list,
        retrieved_by_bucket: Dict[int, list],
        evidence_summary: Dict[str, Any],
    ) -> float:
        """Compute base confidence score"""
        if not retrieved:
            return 0.0
        
        score = 0.0
        
        # Number of sources (more = better, with diminishing returns)
        num_sources = len(retrieved)
        score += min(num_sources / 20, 0.3)  # Max 0.3
        
        # Bucket diversity
        num_buckets = len(retrieved_by_bucket)
        score += min(num_buckets / 4, 0.2)  # Max 0.2
        
        # Sample size bonus
        total_count = evidence_summary.get("total_records", 0)
        if total_count >= 20:
            score += 0.2
        elif total_count >= 10:
            score += 0.1
        elif total_count < 5:
            score -= 0.2
        
        return min(score, 1.0)
    
    def _get_expected_buckets(self, intent: Dict[str, Any]) -> list[int]:
        """Get expected buckets for intent type"""
        intent_type = intent.get("primary_intent", "general_query")
        
        expected = {
            "sentiment_analysis": [2, 4],
            "preference_discovery": [2, 4],
            "market_inference": [3],
            "demographic_comparison": [2],
            "behavioral_evolution": [2, 4],
        }
        
        return expected.get(intent_type, [1, 2, 3, 4])
    
    def _generate_entropy_notes(
        self,
        confidence: float,
        binary_entropy: float,
        bucket_entropy: float,
    ) -> list[str]:
        """Generate human-readable entropy notes"""
        notes = []
        
        if confidence < 0.3:
            notes.append("Low confidence: Consider expanding search or adding more buckets")
        elif confidence > 0.7:
            notes.append("High confidence: Good evidence coverage")
        
        if binary_entropy > 0.8:
            notes.append("High uncertainty: Evidence is ambiguous")
        
        if bucket_entropy < 0.5:
            notes.append("Low bucket diversity: Results concentrated in few buckets")
        
        return notes

