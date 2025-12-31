"""
Abstract storage interfaces.

These interfaces allow swapping implementations (local → cloud, FAISS → Pinecone)
without changing the rest of the codebase.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from ..core.schema import DataRecord


class StorageBackend(ABC):
    """Abstract interface for raw data storage"""
    
    @abstractmethod
    def save_record(self, record: DataRecord) -> bool:
        """Save a data record"""
        pass
    
    @abstractmethod
    def load_record(self, record_id: str) -> Optional[DataRecord]:
        """Load a data record by ID"""
        pass
    
    @abstractmethod
    def delete_record(self, record_id: str) -> bool:
        """Delete a data record"""
        pass
    
    @abstractmethod
    def list_records(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[str]:
        """List record IDs matching filters"""
        pass


class VectorStore(ABC):
    """Abstract interface for vector embeddings storage"""
    
    @abstractmethod
    def add_vectors(self, record_ids: List[str], vectors: np.ndarray) -> bool:
        """Add vectors with associated record IDs"""
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        Search for similar vectors.
        Returns: List of (record_id, distance/score) tuples
        """
        pass
    
    @abstractmethod
    def get_vector(self, record_id: str) -> Optional[np.ndarray]:
        """Get vector for a specific record ID"""
        pass
    
    @abstractmethod
    def delete_vector(self, record_id: str) -> bool:
        """Delete a vector"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of stored vectors"""
        pass


class MetadataStore(ABC):
    """Abstract interface for metadata indexing"""
    
    @abstractmethod
    def index_record(self, record: DataRecord) -> bool:
        """Index a record's metadata"""
        pass
    
    @abstractmethod
    def query_by_bucket(self, bucket_id: int, limit: Optional[int] = None) -> List[str]:
        """Query records by bucket ID"""
        pass
    
    @abstractmethod
    def query_by_brand(self, brand: str, limit: Optional[int] = None) -> List[str]:
        """Query records by brand"""
        pass
    
    @abstractmethod
    def query_by_time_range(self, start_time: Any, end_time: Any, limit: Optional[int] = None) -> List[str]:
        """Query records by time range"""
        pass
    
    @abstractmethod
    def query_by_filters(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[str]:
        """
        Query records by arbitrary filters.
        Filters can include:
        - bucket_id
        - brand
        - source_name
        - client_id
        - categorical_fields.{key}
        - numerical_fields.{key} (with min/max)
        """
        pass
    
    @abstractmethod
    def delete_index(self, record_id: str) -> bool:
        """Remove a record from the index"""
        pass

