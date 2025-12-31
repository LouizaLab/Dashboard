"""
Synthesize Agent Node

Generates RAG-ready context with citations.
"""

import json
from typing import Dict, Any

from ..state import RetrievalState, log_decision
from ..prompts.synthesize_agent import SYNTHESIZE_PROMPT
from ..utils import summarize_records_for_prompt
from adapters.llm.interface import LLMClient


class SynthesizeAgentNode:
    """
    Node 6: Synthesizer Agent
    
    Purpose:
    - Produce RAG-ready context string
    - Generate citations with metadata
    - Organize evidence by bucket/source type
    """
    
    BUCKET_NAMES = {
        1: "Online Datasets",
        2: "Survey Evidence",
        3: "Market/Financial Evidence",
        4: "Public Sentiment Evidence",
    }
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize synthesizer agent.
        
        Args:
            llm_client: Optional LLM client for synthesis
        """
        self.llm_client = llm_client
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute context synthesis.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with rag_context and citations populated
        """
        query = state["query"]
        retrieved = state["retrieved"]
        retrieved_by_bucket = state["retrieved_by_bucket"]
        evidence_summary = state["evidence_summary"]
        
        if self.llm_client and retrieved:
            # Use LLM for synthesis
            try:
                records_summary = summarize_records_for_prompt(retrieved, max_records=20)
                
                prompt = SYNTHESIZE_PROMPT.format(
                    query=query,
                    retrieved_records_summary=records_summary,
                    evidence_summary=str(evidence_summary),
                )
                response = self.llm_client.generate_structured(
                    prompt=prompt,
                    system_prompt="You are a Synthesizer agent. Always respond with valid JSON.",
                )
                
                state["rag_context"] = response.get("rag_context", "")
                state["citations"] = response.get("citations", [])
                
            except Exception as e:
                # Fallback to rule-based synthesis
                state["rag_context"], state["citations"] = self._rule_based_synthesis(
                    retrieved, retrieved_by_bucket
                )
        else:
            # Rule-based synthesis
            state["rag_context"], state["citations"] = self._rule_based_synthesis(
                retrieved, retrieved_by_bucket
            )
        
        # Log decision
        log_decision(state, "synthesize_agent", {
            "context_length": len(state["rag_context"]),
            "citations_count": len(state["citations"]),
        })
        
        return state
    
    def _rule_based_synthesis(
        self,
        retrieved: list,
        retrieved_by_bucket: Dict[int, list],
    ):
        """Fallback rule-based synthesis"""
        context_parts = []
        citations = []
        
        # Group by bucket
        for bucket_id in sorted(retrieved_by_bucket.keys()):
            bucket_records = retrieved_by_bucket[bucket_id]
            if not bucket_records:
                continue
            
            bucket_name = self.BUCKET_NAMES.get(bucket_id, f"Bucket {bucket_id}")
            context_parts.append(f"\n=== {bucket_name} ===")
            
            for i, record in enumerate(bucket_records[:5], 1):  # Limit to top 5 per bucket
                text = record.get_text_for_embedding()
                if text:
                    # Truncate long text
                    if len(text) > 500:
                        text = text[:500] + "..."
                    context_parts.append(f"\n[{i}] {text}")
                
                # Add structured fields if relevant
                if record.structured_fields:
                    key_fields = {k: v for k, v in list(record.structured_fields.items())[:3]}
                    if key_fields:
                        context_parts.append(f"    Fields: {key_fields}")
                
                # Generate citation
                citation = {
                    "record_id": record.record_id,
                    "bucket_id": record.bucket_id,
                    "source_name": record.source_name,
                    "brand": record.brand,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                }
                citations.append(citation)
        
        # Add notes section
        if context_parts:
            context_parts.append("\n=== Notes & Caveats ===")
            context_parts.append("Evidence compiled from multiple sources. Citations provided for traceability.")
        
        rag_context = "\n".join(context_parts) if context_parts else "No evidence retrieved."
        
        return rag_context, citations

