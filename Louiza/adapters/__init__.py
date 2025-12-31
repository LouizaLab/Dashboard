"""
Adapters for external dependencies

Provides abstraction layers for:
- Data Engine (wraps existing DataEngine)
- LLM providers (OpenAI, Anthropic, etc.)
- Embedding providers
"""

from .data_engine_adapter import DataEngineAdapter
from .llm.interface import LLMClient
from .llm.openai_client import OpenAIClient
from .llm.mock_client import MockLLMClient

__all__ = [
    "DataEngineAdapter",
    "LLMClient",
    "OpenAIClient",
    "MockLLMClient",
]

