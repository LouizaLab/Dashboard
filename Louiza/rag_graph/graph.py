"""
LangGraph RAG Retrieval Graph

Main graph orchestration that wires all nodes together.
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
    InterpretQueryNode,
    ExplorerAgentNode,
    PlanRetrievalNode,
    RetrieveParallelNode,
    CriticAgentNode,
    SynthesizeAgentNode,
    ScoreEntropyNode,
    Phase4AnchorNode,
)
from adapters.data_engine_adapter import DataEngineAdapter
from adapters.llm.interface import LLMClient
from phase4_client.interface import AnchorClient


class RAGGraph:
    """
    LangGraph-based RAG retrieval system with multi-agent patterns.
    
    Flow:
    1. interpret_query - Understand intent and extract entities
    2. explorer_agent - Expand queries and generate hypotheses
    3. plan_retrieval - Plan retrieval strategies per bucket
    4. retrieve_parallel - Execute parallel retrieval
    5. critic_agent - Validate evidence quality
    6. (optional) second retrieval pass if critic recommends
    7. synthesize_agent - Generate RAG-ready context
    8. score_entropy - Compute confidence and entropy metrics
    9. phase4_anchor - Integrate with Phase-4 anchoring (if applicable)
    
    Usage:
        graph = RAGGraph(data_engine_adapter, llm_client, anchor_client)
        result = graph.invoke("What do Gen Z prefer about McDonald's?")
    """
    
    def __init__(
        self,
        data_engine_adapter: DataEngineAdapter,
        llm_client: Optional[LLMClient] = None,
        anchor_client: Optional[AnchorClient] = None,
        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,
    ):
        """
        Initialize RAG graph.
        
        Args:
            data_engine_adapter: DataEngineAdapter instance
            llm_client: Optional LLM client for agent nodes
            anchor_client: Optional Phase-4 anchor client
            embedding_fn: Optional embedding function for semantic search
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is not installed. Install with: pip install langgraph"
            )
        
        self.data_engine_adapter = data_engine_adapter
        self.llm_client = llm_client
        self.anchor_client = anchor_client
        
        # Set embedding function if provided
        if embedding_fn:
            data_engine_adapter.set_embedding_fn(embedding_fn)
        
        # Initialize nodes
        self.interpret_query = InterpretQueryNode(llm_client=llm_client)
        self.explorer_agent = ExplorerAgentNode(llm_client=llm_client)
        self.plan_retrieval = PlanRetrievalNode()
        self.retrieve_parallel = RetrieveParallelNode(data_engine_adapter=data_engine_adapter)
        self.critic_agent = CriticAgentNode(llm_client=llm_client)
        self.synthesize_agent = SynthesizeAgentNode(llm_client=llm_client)
        self.score_entropy = ScoreEntropyNode()
        self.phase4_anchor = Phase4AnchorNode(anchor_client=anchor_client)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(RetrievalState)
        
        # Add nodes
        workflow.add_node("interpret_query", self.interpret_query)
        workflow.add_node("explorer_agent", self.explorer_agent)
        workflow.add_node("plan_retrieval", self.plan_retrieval)
        workflow.add_node("retrieve_parallel", self.retrieve_parallel)
        workflow.add_node("critic_agent", self.critic_agent)
        workflow.add_node("synthesize_agent", self.synthesize_agent)
        workflow.add_node("score_entropy", self.score_entropy)
        workflow.add_node("phase4_anchor", self.phase4_anchor)
        
        # Define edges
        workflow.set_entry_point("interpret_query")
        workflow.add_edge("interpret_query", "explorer_agent")
        workflow.add_edge("explorer_agent", "plan_retrieval")
        workflow.add_edge("plan_retrieval", "retrieve_parallel")
        
        # Conditional edge after retrieval: go to critic if first pass, synthesize if second pass
        def route_after_retrieval(state: RetrievalState) -> str:
            pass_count = state.get("retrieval_pass_count", 0)
            if pass_count == 0:
                return "critic_agent"
            else:
                # Already did second pass, go to synthesize
                return "synthesize_agent"
        
        workflow.add_conditional_edges(
            "retrieve_parallel",
            route_after_retrieval,
            {
                "critic_agent": "critic_agent",
                "synthesize_agent": "synthesize_agent",
            }
        )
        
        # Conditional edge: second retrieval pass if needed (max 1 extra pass)
        def should_retry(state: RetrievalState) -> str:
            pass_count = state.get("retrieval_pass_count", 0)
            needs_pass = state.get("needs_second_pass", False)
            
            # Only allow second pass if we haven't done one yet
            if needs_pass and pass_count == 0:
                return "retrieve_parallel"
            return "synthesize_agent"
        
        workflow.add_conditional_edges(
            "critic_agent",
            should_retry,
            {
                "retrieve_parallel": "retrieve_parallel",
                "synthesize_agent": "synthesize_agent",
            }
        )
        
        workflow.add_edge("synthesize_agent", "score_entropy")
        workflow.add_edge("score_entropy", "phase4_anchor")
        workflow.add_edge("phase4_anchor", END)
        
        return workflow.compile()
    
    def invoke(self, query: str) -> Dict[str, Any]:
        """
        Execute retrieval for a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary matching the output contract:
            {
                "query": str,
                "intent": dict,
                "entities": dict,
                "rag_context": str,
                "citations": list,
                "confidence": float,
                "entropy": dict,
                "coverage": dict,
                "phase4": dict,
            }
        """
        # Create initial state
        initial_state = create_initial_state(query)
        
        # Execute graph
        final_state = self.graph.invoke(initial_state)
        
        # Format output according to contract
        return {
            "query": final_state["query"],
            "intent": final_state["intent"],
            "entities": final_state["entities"],
            "rag_context": final_state["rag_context"],
            "citations": final_state["citations"],
            "confidence": final_state["confidence"],
            "entropy": final_state["entropy"],
            "coverage": final_state["coverage"],
            "phase4": final_state["phase4"],
        }
    
    def stream(self, query: str):
        """
        Stream retrieval execution (for debugging/observability).
        
        Args:
            query: Natural language query
            
        Yields:
            State updates as graph executes
        """
        initial_state = create_initial_state(query)
        
        for state_update in self.graph.stream(initial_state):
            yield state_update

