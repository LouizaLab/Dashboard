"""
Data Engine Adapter

Wraps the existing Data Engine to provide a consistent interface
for the RAG graph system.
"""

from typing import List, Dict, Any, Optional, Callable
import numpy as np

from Data_Engine.core.schema import DataRecord
from Data_Engine.data_engine import DataEngine
from Data_Engine.retrieval.retrieval_manager import RetrievalManager


class DataEngineAdapter:
    """
    Adapter for Data Engine that provides the interface expected by RAG graph.
    
    This wraps the existing DataEngine and RetrievalManager to expose:
    - hybrid_query: semantic + structured filters
    - query_structured: structured filters only
    - query_by_brand: brand-based queries with optional sentiment
    """
    
    def __init__(self, data_engine: DataEngine):
        """
        Initialize adapter.
        
        Args:
            data_engine: DataEngine instance
        """
        self.data_engine = data_engine
        self.retrieval_manager = data_engine.retrieval_manager
        self.embedding_fn = data_engine.embedding_fn
    
    def hybrid_query(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        bucket_ids: Optional[List[int]] = None,
    ) -> List[DataRecord]:
        """
        Hybrid query combining semantic search and structured filters.
        
        Args:
            query_text: Natural language query
            filters: Optional metadata filters
            top_k: Number of results
            bucket_ids: Optional list of bucket IDs to filter by
            
        Returns:
            List of DataRecord objects
        """
        if filters is None:
            filters = {}
        
        # Add bucket filter if specified
        if bucket_ids:
            # Filter by bucket_ids after retrieval
            all_results = []
            for bucket_id in bucket_ids:
                bucket_filters = {**filters, "bucket_id": bucket_id}
                try:
                    if self.embedding_fn:
                        results = self.retrieval_manager.query_by_text(
                            prompt=query_text,
                            embedding_fn=self.embedding_fn,
                            filters=bucket_filters,
                            top_k=top_k,
                        )
                    else:
                        results = self.retrieval_manager.query_by_filters(
                            filters=bucket_filters,
                            limit=top_k,
                        )
                    all_results.extend(results)
                except Exception:
                    # Fallback to structured query
                    results = self.retrieval_manager.query_by_filters(
                        filters=bucket_filters,
                        limit=top_k,
                    )
                    all_results.extend(results)
            
            # Deduplicate and limit
            seen_ids = set()
            unique_results = []
            for record in all_results:
                if record.record_id not in seen_ids:
                    seen_ids.add(record.record_id)
                    unique_results.append(record)
                    if len(unique_results) >= top_k:
                        break
            return unique_results
        else:
            # Query all buckets
            try:
                if self.embedding_fn:
                    return self.retrieval_manager.query_by_text(
                        prompt=query_text,
                        embedding_fn=self.embedding_fn,
                        filters=filters,
                        top_k=top_k,
                    )
                else:
                    return self.retrieval_manager.query_by_filters(
                        filters=filters,
                        limit=top_k,
                    )
            except Exception:
                return self.retrieval_manager.query_by_filters(
                    filters=filters,
                    limit=top_k,
                )
    
    def query_structured(
        self,
        filters: Dict[str, Any],
        top_k: int = 10,
        bucket_ids: Optional[List[int]] = None,
    ) -> List[DataRecord]:
        """
        Query using only structured filters (no semantic search).
        
        Args:
            filters: Metadata filters
            top_k: Number of results
            bucket_ids: Optional list of bucket IDs to filter by
            
        Returns:
            List of DataRecord objects
        """
        if bucket_ids:
            all_results = []
            for bucket_id in bucket_ids:
                bucket_filters = {**filters, "bucket_id": bucket_id}
                results = self.retrieval_manager.query_by_filters(
                    filters=bucket_filters,
                    limit=top_k,
                )
                all_results.extend(results)
            
            # Deduplicate and limit
            seen_ids = set()
            unique_results = []
            for record in all_results:
                if record.record_id not in seen_ids:
                    seen_ids.add(record.record_id)
                    unique_results.append(record)
                    if len(unique_results) >= top_k:
                        break
            return unique_results
        else:
            return self.retrieval_manager.query_by_filters(
                filters=filters,
                limit=top_k,
            )
    
    def query_by_brand(
        self,
        brand: str,
        sentiment: Optional[str] = None,
        top_k: int = 10,
    ) -> List[DataRecord]:
        """
        Query records by brand with optional sentiment filter.
        
        Args:
            brand: Brand name
            sentiment: Optional sentiment filter ("positive", "negative", or None)
            top_k: Number of results
            
        Returns:
            List of DataRecord objects
        """
        sentiment_value = None
        if sentiment == "positive":
            sentiment_value = 0.0  # Positive sentiment threshold
        elif sentiment == "negative":
            sentiment_value = -1.0  # Negative sentiment threshold
        
        return self.retrieval_manager.query_by_brand(
            brand=brand,
            sentiment=sentiment_value,
            limit=top_k,
        )
    
    def set_embedding_fn(self, embedding_fn: Callable[[str], np.ndarray]):
        """Set the embedding function for semantic search"""
        self.data_engine.set_embedding_fn(embedding_fn)
        self.embedding_fn = embedding_fn

