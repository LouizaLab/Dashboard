"""
Prompt Templates for RAG Graph Nodes

Contains prompt templates for:
- Query interpretation
- Query expansion (Explorer agent)
- Evidence critique (Critic agent)
- Context synthesis (Synthesizer agent)
"""

from .interpret_query import INTERPRET_QUERY_PROMPT
from .explorer_agent import EXPLORER_PROMPT
from .critic_agent import CRITIC_PROMPT
from .synthesize_agent import SYNTHESIZE_PROMPT

__all__ = [
    "INTERPRET_QUERY_PROMPT",
    "EXPLORER_PROMPT",
    "CRITIC_PROMPT",
    "SYNTHESIZE_PROMPT",
]

