"""
Data Engine

Production-ready data ingestion, indexing, and retrieval system.
"""

from .data_engine import DataEngine
from .core.schema import DataRecord, BucketType, SourceType
from .indexing.index_manager import IndexManager
from .retrieval.retrieval_manager import RetrievalManager

__version__ = "1.0.0"

__all__ = [
    'DataEngine',
    'DataRecord',
    'BucketType',
    'SourceType',
    'IndexManager',
    'RetrievalManager',
]

