"""
Phase-4 Anchoring Client

Integration boundary for Phase-4 ground-truth anchoring system.
Provides adapters for calling Phase-4 anchoring from the RAG system.
"""

from .interface import AnchorClient
from .schemas import AnchorRequest, AnchorResponse
from .local_subprocess_client import LocalSubprocessClient
from .http_client import HTTPClient

__all__ = [
    "AnchorClient",
    "AnchorRequest",
    "AnchorResponse",
    "LocalSubprocessClient",
    "HTTPClient",
]

