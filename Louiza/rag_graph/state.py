"""
LangGraph State for RAG Retrieval System

Defines the state that flows through all nodes in the retrieval graph.
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

from Data_Engine.core.schema import DataRecord


class RetrievalState(TypedDict):
    """
    LangGraph state for the RAG retrieval system.
    
    This state flows through all nodes and accumulates information
    as the retrieval graph executes.
    """
    
    # Input
    query: str
    
    # Query Understanding (from interpret_query)
    intent: Dict[str, Any]  # Intent classification: type, confidence, etc.
    entities: Dict[str, Any]  # Extracted entities: brands, segments, time_range, metrics, keywords
    
    # Exploration (from explorer_agent)
    expanded_queries: List[str]  # Query expansions
    exploration_notes: List[str]  # Hypotheses and exploration angles
    
    # Retrieval Planning (from plan_retrieval)
    retrieval_plan: Dict[int, Dict[str, Any]]  # Per-bucket retrieval strategies
    
    # Retrieval Results (from retrieve_parallel)
    retrieved: List[DataRecord]  # All retrieved records (deduplicated)
    retrieved_by_bucket: Dict[int, List[DataRecord]]  # Results per bucket
    
    # Evidence Analysis (from critic_agent)
    evidence_summary: Dict[str, Any]  # Counts, sample sizes, coverage
    contradictions: List[str]  # Detected contradictions
    critique_notes: List[str]  # Critic's analysis
    needs_second_pass: bool  # Whether a second retrieval pass is needed
    retrieval_pass_count: int  # Number of retrieval passes completed
    
    # Synthesis (from synthesize_agent)
    rag_context: str  # Final RAG-ready context string
    citations: List[Dict[str, Any]]  # Citation metadata
    
    # Confidence & Entropy (from score_entropy)
    confidence: float  # Overall confidence score (0.0-1.0)
    entropy: Dict[str, Any]  # Entropy metrics: binary_entropy, bucket_entropy, coverage_penalty, notes
    
    # Coverage Metrics
    coverage: Dict[str, Any]  # buckets_used, counts_by_bucket, time_span
    
    # Phase-4 Integration (from phase4_anchor)
    phase4: Dict[str, Any]  # Anchor outputs: anchored_score, updated_confidence, calibration_details, warnings
    
    # Metadata
    execution_log: List[Dict[str, Any]]  # Log of decisions made
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
        query=query,
        intent={},
        entities={},
        expanded_queries=[],
        exploration_notes=[],
        retrieval_plan={},
        retrieved=[],
        retrieved_by_bucket={},
        evidence_summary={},
        contradictions=[],
        critique_notes=[],
        needs_second_pass=False,
        retrieval_pass_count=0,
        rag_context="",
        citations=[],
        confidence=0.0,
        entropy={},
        coverage={},
        phase4={},
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

