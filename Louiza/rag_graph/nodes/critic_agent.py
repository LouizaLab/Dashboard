"""
Critic Agent Node

Validates evidence quality and detects issues.
"""

import json
from typing import Dict, Any

from ..state import RetrievalState, log_decision
from ..prompts.critic_agent import CRITIC_PROMPT
from ..utils import compute_evidence_summary
from adapters.llm.interface import LLMClient


class CriticAgentNode:
    """
    Node 5: Critic Agent
    
    Purpose:
    - Validate evidence quality
    - Detect contradictions
    - Identify missing buckets
    - Flag sample size issues
    """
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize critic agent.
        
        Args:
            llm_client: Optional LLM client for critique
        """
        self.llm_client = llm_client
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute evidence critique.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with critique_notes, contradictions, and evidence_summary
        """
        query = state["query"]
        intent = state["intent"]
        retrieved = state["retrieved"]
        retrieved_by_bucket = state["retrieved_by_bucket"]
        
        # Compute evidence summary
        evidence_summary = compute_evidence_summary(retrieved, retrieved_by_bucket)
        state["evidence_summary"] = evidence_summary
        
        if self.llm_client and retrieved:
            # Use LLM for critique
            try:
                prompt = CRITIC_PROMPT.format(
                    query=query,
                    intent=intent,
                    evidence_summary=str(evidence_summary),
                    buckets_used=list(retrieved_by_bucket.keys()),
                    counts_by_bucket={bid: len(recs) for bid, recs in retrieved_by_bucket.items()},
                )
                response = self.llm_client.generate_structured(
                    prompt=prompt,
                    system_prompt="You are a Critic agent. Always respond with valid JSON.",
                )
                
                state["critique_notes"] = response.get("critique_notes", [])
                state["contradictions"] = response.get("contradictions", [])
                state["needs_second_pass"] = response.get("needs_second_pass", False)
                
                # Update evidence_summary with coverage report
                coverage_report = response.get("coverage_report", {})
                evidence_summary["coverage_report"] = coverage_report
                state["evidence_summary"] = evidence_summary
                
            except Exception as e:
                # Fallback to rule-based critique
                state["critique_notes"], state["contradictions"], state["needs_second_pass"] = \
                    self._rule_based_critique(retrieved, retrieved_by_bucket, intent, evidence_summary)
        else:
            # Rule-based critique
            state["critique_notes"], state["contradictions"], state["needs_second_pass"] = \
                self._rule_based_critique(retrieved, retrieved_by_bucket, intent, evidence_summary)
        
        # Log decision
        log_decision(state, "critic_agent", {
            "critique_notes": state["critique_notes"],
            "contradictions": state["contradictions"],
            "needs_second_pass": state["needs_second_pass"],
        })
        
        return state
    
    def _rule_based_critique(
        self,
        retrieved: list,
        retrieved_by_bucket: Dict[int, list],
        intent: Dict[str, Any],
        evidence_summary: Dict[str, Any],
    ):
        """Fallback rule-based critique"""
        critique_notes = []
        contradictions = []
        needs_second_pass = False
        
        # Check sample sizes
        counts_by_bucket = evidence_summary.get("counts_by_bucket", {})
        for bucket_id, count in counts_by_bucket.items():
            if count < 5:
                critique_notes.append(f"Bucket {bucket_id} has only {count} records (low sample size)")
                needs_second_pass = True
        
        # Check bucket coverage
        intent_type = intent.get("primary_intent", "")
        buckets_used = list(retrieved_by_bucket.keys())
        
        expected_buckets = {
            "sentiment_analysis": [2, 4],
            "preference_discovery": [2, 4],
            "market_inference": [3],
            "demographic_comparison": [2],
        }
        
        expected = expected_buckets.get(intent_type, [])
        missing = set(expected) - set(buckets_used)
        
        if missing:
            critique_notes.append(f"Missing expected buckets: {list(missing)}")
            needs_second_pass = True
        
        # Check for contradictions in sentiment
        if intent_type == "sentiment_analysis":
            sentiments = [r.sentiment for r in retrieved if r.sentiment is not None]
            if len(sentiments) > 1:
                positive_count = sum(1 for s in sentiments if s > 0.1)
                negative_count = sum(1 for s in sentiments if s < -0.1)
                
                if positive_count > 0 and negative_count > 0:
                    if abs(positive_count - negative_count) < len(sentiments) * 0.3:
                        contradictions.append("Mixed sentiment signals: both positive and negative evidence present")
        
        # Check time alignment
        time_span = evidence_summary.get("time_span")
        if time_span and time_span.get("days", 0) > 365:
            critique_notes.append(f"Records span {time_span['days']} days - may not align with query time range")
        
        return critique_notes, contradictions, needs_second_pass

