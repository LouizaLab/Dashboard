"""
Retrieval layer

Agent-ready APIs for querying indexed data:
- Semantic similarity search
- Structured filtering
- Hybrid queries
- Brand/time/bucket queries
"""

from .retrieval_manager import RetrievalManager

__all__ = ['RetrievalManager']

