"""
Indexing layer

Multi-indexing system:
- Structured index (metadata, filters)
- Semantic index (vector embeddings)
- Metadata index (brand, time, bucket)
"""

from .index_manager import IndexManager

__all__ = ['IndexManager']

