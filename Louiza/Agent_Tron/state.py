"""
RetrievalState: The shared state object for the LangGraph retrieval system.

This state flows through all nodes and accumulates:
- Parsed intent
- Inferred entities
- Retrieval plans
- Retrieved documents
- Aggregated context
- Confidence scores
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass, field

from Data_Engine.core.schema import DataRecord


class RetrievalState(TypedDict):
    """
    LangGraph state for the retrieval system.
    
    This state flows through all nodes and accumulates information
    as the retrieval graph executes.
    """
    
    # Input
    original_query: str
    
    # Query Understanding
    parsed_intent: Dict[str, Any]  # Intent classification results
    inferred_entities: Dict[str, Any]  # Extracted entities (brands, products, demographics, etc.)
    
    # Routing & Planning
    target_buckets: List[int]  # Which buckets to query (1-4)
    retrieval_plan: Dict[int, Dict[str, Any]]  # Per-bucket retrieval strategies
    
    # Retrieval Results
    retrieved_documents: List[DataRecord]  # All retrieved records
    bucket_results: Dict[int, List[DataRecord]]  # Results per bucket
    
    # Aggregation & Output
    aggregated_context: str  # Final context string for RAG
    citations: List[Dict[str, Any]]  # Citation metadata for each source
    
    # Quality Metrics
    confidence_score: float  # Overall confidence (0.0-1.0)
    coverage: Dict[str, Any]  # Coverage report (buckets_used, time_span, etc.)
    
    # Metadata
    execution_log: List[Dict[str, Any]]  # Log of decisions made by the graph
    start_time: Optional[datetime]
    end_time: Optional[datetime]


def create_initial_state(query: str) -> RetrievalState:
    """
    Create initial state from a query.
    
    Args:
        query: Natural language query
        
    Returns:
        Initial RetrievalState with query populated
    """
    return RetrievalState(
        original_query=query,
        parsed_intent={},
        inferred_entities={},
        target_buckets=[],
        retrieval_plan={},
        retrieved_documents=[],
        bucket_results={},
        aggregated_context="",
        citations=[],
        confidence_score=0.0,
        coverage={},
        execution_log=[],
        start_time=datetime.utcnow(),
        end_time=None,
    )


def log_decision(state: RetrievalState, node_name: str, decision: Dict[str, Any]) -> RetrievalState:
    """
    Log a decision made by a node.
    
    Args:
        state: Current state
        node_name: Name of the node making the decision
        decision: Decision details
        
    Returns:
        Updated state with log entry
    """
    log_entry = {
        "node": node_name,
        "timestamp": datetime.utcnow().isoformat(),
        "decision": decision,
    }
    state["execution_log"].append(log_entry)
    return state

