"""
LangGraph-based RAG System with Multi-Agent Retrieval

This module provides a production-grade, modular RAG system that:
- Integrates with the Data Engine for retrieval
- Uses multi-agent patterns (Explorer, Critic, Synthesizer)
- Maps retrieval confidence to entropy metrics
- Integrates with Phase-4 ground-truth anchoring
"""

from .graph import RAGGraph
from .state import RetrievalState, create_initial_state

__all__ = ["RAGGraph", "RetrievalState", "create_initial_state"]

