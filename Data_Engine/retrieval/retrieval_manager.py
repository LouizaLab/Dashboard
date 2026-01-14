"""
Retrieval Manager

Provides clean APIs for querying indexed data.
Designed for use by RAG pipelines, LangGraph, and multi-agent systems.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..core.schema import DataRecord
from ..core.exceptions import RetrievalError
from ..indexing.index_manager import IndexManager
from ..storage.interfaces import VectorStore, MetadataStore


class RetrievalManager:
    """
    Manages retrieval of indexed data.
    
    Provides APIs for:
    - Semantic similarity search
    - Structured filtering
    - Hybrid queries (semantic + filters)
    - Brand/time/bucket queries
    """
    
    def __init__(self, index_manager: IndexManager):
        """
        Initialize retrieval manager.
        
        Args:
            index_manager: IndexManager instance
        """
        self.index_manager = index_manager
        self.vector_store = index_manager.vector_store  # May be None if FAISS not available
        self.metadata_store = index_manager.metadata_store
        self.storage_backend = index_manager.storage_backend
    
    def query_by_text(self, 
                     prompt: str,
                     embedding_fn,
                     filters: Optional[Dict[str, Any]] = None,
                     top_k: int = 10) -> List[DataRecord]:
        """
        Query by text using semantic similarity.
        
        Optimized to use batch loading and reduce redundant record loads.
        
        Args:
            prompt: Text query
            embedding_fn: Function that takes text and returns embedding vector
            filters: Optional metadata filters
            top_k: Number of results to return
        
        Returns:
            List of DataRecord objects
        
        Raises:
            RetrievalError: If vector store is not available (FAISS not installed)
        """
        if not self.vector_store:
            raise RetrievalError(
                "Semantic search requires FAISS. Install with: pip install faiss-cpu"
            )
        
        try:
            # Generate embedding for query
            query_embedding = embedding_fn(prompt)
            if isinstance(query_embedding, np.ndarray):
                query_vector = query_embedding.flatten()
            else:
                query_vector = np.array(query_embedding).flatten()
            
            # Determine how many results to fetch
            # If filters are simple (bucket_id, brand, source_name), use metadata store first
            if filters and self._can_use_metadata_filtering(filters):
                # Use metadata store to pre-filter, then semantic search
                prefiltered_ids = set(self.metadata_store.query_by_filters(filters, limit=None))
                if prefiltered_ids:
                    # Search more results since we'll filter
                    search_k = min(top_k * 3, len(prefiltered_ids))
                else:
                    # No matches in metadata, return empty
                    return []
            else:
                prefiltered_ids = None
                # Get more results for filtering (reduced multiplier for performance)
                search_k = top_k + 10 if filters else top_k
            
            # Search vector store
            results = self.vector_store.search(query_vector, top_k=search_k)
            
            # Apply pre-filtering if available
            if prefiltered_ids is not None:
                results = [(rid, score) for rid, score in results if rid in prefiltered_ids]
            
            # Limit results before loading
            results = results[:top_k * 2] if filters else results[:top_k]
            
            # Batch load all records at once
            record_ids = [rid for rid, _ in results]
            if hasattr(self.storage_backend, 'load_records_batch'):
                records_dict = self.storage_backend.load_records_batch(record_ids)
            else:
                # Fallback to individual loading if batch method not available
                records_dict = {}
                for rid in record_ids:
                    record = self.storage_backend.load_record(rid)
                    if record:
                        records_dict[rid] = record
            
            # Apply filters if provided and not already pre-filtered
            if filters and not self._can_use_metadata_filtering(filters):
                filtered_results = []
                for record_id, score in results:
                    if record_id in records_dict:
                        record = records_dict[record_id]
                        if self._matches_filters(record, filters):
                            filtered_results.append((record_id, score))
                results = filtered_results[:top_k]
            else:
                results = results[:top_k]
            
            # Build final list maintaining score order
            records = []
            seen_ids = set()
            for record_id, score in results:
                if record_id in records_dict and record_id not in seen_ids:
                    records.append(records_dict[record_id])
                    seen_ids.add(record_id)
            
            return records
        
        except Exception as e:
            raise RetrievalError(f"Failed to query by text: {e}")
    
    def _can_use_metadata_filtering(self, filters: Dict[str, Any]) -> bool:
        """
        Check if filters can be efficiently applied using metadata store.
        
        Returns True if all filters are simple metadata fields that the
        metadata store can handle without loading full records.
        """
        # Metadata store can efficiently filter by these fields
        metadata_fields = {'bucket_id', 'brand', 'source_name', 'client_id'}
        categorical_prefix = 'categorical_fields.'
        numerical_prefix = 'numerical_fields.'
        
        for key in filters.keys():
            if key not in metadata_fields:
                if not (key.startswith(categorical_prefix) or key.startswith(numerical_prefix)):
                    # Complex filter that requires full record inspection
                    return False
        return True
    
    def query_by_brand(self, 
                      brand: str,
                      sentiment: Optional[float] = None,
                      limit: Optional[int] = None) -> List[DataRecord]:
        """
        Query records by brand.
        
        Args:
            brand: Brand name
            sentiment: Optional sentiment filter (min value)
            limit: Maximum number of results
        
        Returns:
            List of DataRecord objects
        """
        try:
            record_ids = self.metadata_store.query_by_brand(brand, limit=limit)
            
            # Batch load records
            if hasattr(self.storage_backend, 'load_records_batch'):
                records_dict = self.storage_backend.load_records_batch(record_ids)
                records = list(records_dict.values())
            else:
                # Fallback to individual loading
                records = []
                for record_id in record_ids:
                    record = self.storage_backend.load_record(record_id)
                    if record:
                        records.append(record)
            
            # Apply sentiment filter if provided
            if sentiment is not None:
                records = [r for r in records if r.sentiment is not None and r.sentiment >= sentiment]
            
            return records
        
        except Exception as e:
            raise RetrievalError(f"Failed to query by brand: {e}")
    
    def query_by_bucket(self, bucket_id: int, limit: Optional[int] = None) -> List[DataRecord]:
        """
        Query records by bucket ID.
        
        Args:
            bucket_id: Bucket ID (1-4)
            limit: Maximum number of results
        
        Returns:
            List of DataRecord objects
        """
        try:
            record_ids = self.metadata_store.query_by_bucket(bucket_id, limit=limit)
            
            # Batch load records
            if hasattr(self.storage_backend, 'load_records_batch'):
                records_dict = self.storage_backend.load_records_batch(record_ids)
                return list(records_dict.values())
            else:
                # Fallback to individual loading
                records = []
                for record_id in record_ids:
                    record = self.storage_backend.load_record(record_id)
                    if record:
                        records.append(record)
                return records
        
        except Exception as e:
            raise RetrievalError(f"Failed to query by bucket: {e}")
    
    def query_by_time_range(self, 
                           start_time: Any,
                           end_time: Any,
                           limit: Optional[int] = None) -> List[DataRecord]:
        """
        Query records by time range.
        
        Args:
            start_time: Start datetime
            end_time: End datetime
            limit: Maximum number of results
        
        Returns:
            List of DataRecord objects
        """
        try:
            record_ids = self.metadata_store.query_by_time_range(start_time, end_time, limit=limit)
            
            # Batch load records
            if hasattr(self.storage_backend, 'load_records_batch'):
                records_dict = self.storage_backend.load_records_batch(record_ids)
                return list(records_dict.values())
            else:
                # Fallback to individual loading
                records = []
                for record_id in record_ids:
                    record = self.storage_backend.load_record(record_id)
                    if record:
                        records.append(record)
                return records
        
        except Exception as e:
            raise RetrievalError(f"Failed to query by time range: {e}")
    
    def hybrid_query(self,
                    prompt: str,
                    embedding_fn,
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: int = 10) -> List[DataRecord]:
        """
        Hybrid query combining semantic search and structured filters.
        
        Args:
            prompt: Text query
            embedding_fn: Function that takes text and returns embedding
            filters: Metadata filters
            top_k: Number of results
        
        Returns:
            List of DataRecord objects
        """
        # Use query_by_text which already supports filters
        return self.query_by_text(prompt, embedding_fn, filters=filters, top_k=top_k)
    
    def query_by_filters(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[DataRecord]:
        """
        Query records by arbitrary filters.
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
        
        Returns:
            List of DataRecord objects
        """
        try:
            record_ids = self.metadata_store.query_by_filters(filters, limit=limit)
            
            # Batch load records
            if hasattr(self.storage_backend, 'load_records_batch'):
                records_dict = self.storage_backend.load_records_batch(record_ids)
                return list(records_dict.values())
            else:
                # Fallback to individual loading
                records = []
                for record_id in record_ids:
                    record = self.storage_backend.load_record(record_id)
                    if record:
                        records.append(record)
                return records
        
        except Exception as e:
            raise RetrievalError(f"Failed to query by filters: {e}")
    
    def _matches_filters(self, record: DataRecord, filters: Dict[str, Any]) -> bool:
        """Check if record matches filters"""
        for key, value in filters.items():
            if key == 'bucket_id' and record.bucket_id != value:
                return False
            elif key == 'brand' and record.brand != value:
                return False
            elif key == 'source_name' and record.source_name != value:
                return False
            elif key == 'client_id' and record.client_id != value:
                return False
            elif key.startswith('categorical_fields.'):
                field_name = key.replace('categorical_fields.', '')
                if record.categorical_fields.get(field_name) != value:
                    return False
            elif key.startswith('numerical_fields.'):
                field_name = key.replace('numerical_fields.', '')
                field_value = record.numerical_fields.get(field_name)
                if field_value is None:
                    return False
                if isinstance(value, dict):
                    if 'min' in value and field_value < value['min']:
                        return False
                    if 'max' in value and field_value > value['max']:
                        return False
                elif field_value != value:
                    return False
        return True

