"""
LangGraph State Machine for Intelligent Retrieval

This graph orchestrates the multi-step retrieval reasoning process:
Query → Interpreter → Router → Strategy → Retrieval → Aggregation → Confidence → Output
"""

from typing import Dict, Any, Optional, Callable
import numpy as np

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create dummy classes for type hints
    class StateGraph:
        pass
    class END:
        pass

from .state import RetrievalState, create_initial_state
from .nodes import (
    QueryInterpreterNode,
    BucketRouterNode,
    StrategySelectorNode,
    ParallelRetrieversNode,
    EvidenceAggregatorNode,
    ConfidenceScorerNode,
)
from Data_Engine.retrieval.retrieval_manager import RetrievalManager


class RetrievalGraph:
    """
    LangGraph-based retrieval system.
    
    This graph treats retrieval as a multi-step reasoning problem:
    1. Understand user intent
    2. Decide which data buckets are relevant
    3. Select retrieval strategies per bucket
    4. Execute parallel retrieval
    5. Aggregate evidence
    6. Score confidence and coverage
    
    Usage:
        graph = RetrievalGraph(retrieval_manager, embedding_fn)
        result = graph.retrieve("What do Gen Z prefer about McDonald's?")
    """
    
    def __init__(
        self,
        retrieval_manager: RetrievalManager,
        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,
    ):
        """
        Initialize retrieval graph.
        
        Args:
            retrieval_manager: RetrievalManager instance from Data Engine
            embedding_fn: Optional embedding function for semantic search
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is not installed. Install with: pip install langgraph"
            )
        
        self.retrieval_manager = retrieval_manager
        self.embedding_fn = embedding_fn
        
        # Initialize nodes
        self.query_interpreter = QueryInterpreterNode()
        self.bucket_router = BucketRouterNode()
        self.strategy_selector = StrategySelectorNode()
        self.parallel_retrievers = ParallelRetrieversNode(
            retrieval_manager=retrieval_manager,
            embedding_fn=embedding_fn,
        )
        self.evidence_aggregator = EvidenceAggregatorNode()
        self.confidence_scorer = ConfidenceScorerNode()
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(RetrievalState)
        
        # Add nodes
        workflow.add_node("query_interpreter", self.query_interpreter)
        workflow.add_node("bucket_router", self.bucket_router)
        workflow.add_node("strategy_selector", self.strategy_selector)
        workflow.add_node("parallel_retrievers", self.parallel_retrievers)
        workflow.add_node("evidence_aggregator", self.evidence_aggregator)
        workflow.add_node("confidence_scorer", self.confidence_scorer)
        
        # Define edges (linear flow)
        workflow.set_entry_point("query_interpreter")
        workflow.add_edge("query_interpreter", "bucket_router")
        workflow.add_edge("bucket_router", "strategy_selector")
        workflow.add_edge("strategy_selector", "parallel_retrievers")
        workflow.add_edge("parallel_retrievers", "evidence_aggregator")
        workflow.add_edge("evidence_aggregator", "confidence_scorer")
        workflow.add_edge("confidence_scorer", END)
        
        return workflow.compile()
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Execute retrieval for a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with:
            - query: Original query
            - context: Aggregated context string
            - citations: List of citation metadata
            - confidence_score: Confidence score (0.0-1.0)
            - coverage: Coverage report
            - execution_log: Log of decisions made
        """
        # Create initial state
        initial_state = create_initial_state(query)
        
        # Execute graph
        final_state = self.graph.invoke(initial_state)
        
        # Format output
        return {
            "query": final_state["original_query"],
            "context": final_state["aggregated_context"],
            "citations": final_state["citations"],
            "confidence_score": final_state["confidence_score"],
            "coverage": final_state["coverage"],
            "execution_log": final_state["execution_log"],
            "parsed_intent": final_state["parsed_intent"],
            "inferred_entities": final_state["inferred_entities"],
            "target_buckets": final_state["target_buckets"],
            "num_documents": len(final_state["retrieved_documents"]),
        }
    
    def retrieve_stream(self, query: str):
        """
        Stream retrieval execution (for debugging/observability).
        
        Args:
            query: Natural language query
            
        Yields:
            State updates as graph executes
        """
        initial_state = create_initial_state(query)
        
        for state in self.graph.stream(initial_state):
            yield state
    
    def get_graph_visualization(self) -> str:
        """
        Get a string representation of the graph structure.
        
        Returns:
            Graph visualization string
        """
        return """
        Retrieval Graph Flow:
        
        START
          ↓
        [Query Interpreter]
          ↓ (parsed_intent, inferred_entities)
        [Bucket Router]
          ↓ (target_buckets)
        [Strategy Selector]
          ↓ (retrieval_plan)
        [Parallel Retrievers]
          ↓ (retrieved_documents, bucket_results)
        [Evidence Aggregator]
          ↓ (aggregated_context, citations)
        [Confidence Scorer]
          ↓ (confidence_score, coverage)
        END
        """


# Fallback implementation if LangGraph is not available
class RetrievalGraphFallback:
    """
    Fallback implementation that executes nodes sequentially
    without LangGraph (for testing/debugging).
    """
    
    def __init__(
        self,
        retrieval_manager: RetrievalManager,
        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,
    ):
        self.retrieval_manager = retrieval_manager
        self.embedding_fn = embedding_fn
        
        # Initialize nodes
        self.query_interpreter = QueryInterpreterNode()
        self.bucket_router = BucketRouterNode()
        self.strategy_selector = StrategySelectorNode()
        self.parallel_retrievers = ParallelRetrieversNode(
            retrieval_manager=retrieval_manager,
            embedding_fn=embedding_fn,
        )
        self.evidence_aggregator = EvidenceAggregatorNode()
        self.confidence_scorer = ConfidenceScorerNode()
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        """Execute retrieval sequentially"""
        state = create_initial_state(query)
        
        # Execute nodes in sequence
        state = self.query_interpreter(state)
        state = self.bucket_router(state)
        state = self.strategy_selector(state)
        state = self.parallel_retrievers(state)
        state = self.evidence_aggregator(state)
        state = self.confidence_scorer(state)
        
        # Format output
        return {
            "query": state["original_query"],
            "context": state["aggregated_context"],
            "citations": state["citations"],
            "confidence_score": state["confidence_score"],
            "coverage": state["coverage"],
            "execution_log": state["execution_log"],
            "parsed_intent": state["parsed_intent"],
            "inferred_entities": state["inferred_entities"],
            "target_buckets": state["target_buckets"],
            "num_documents": len(state["retrieved_documents"]),
        }

