"""
Main Data Engine Orchestration

High-level API for ingesting, indexing, and retrieving data.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import numpy as np

from .core.schema import DataRecord
from .core.exceptions import DataEngineException
from .ingestion import (
    OnlineDatasetsIngester,
    SurveysInterviewsIngester,
    FinancialDataIngester,
)
from .indexing.index_manager import IndexManager
from .retrieval.retrieval_manager import RetrievalManager
from .enrichment.text_cleaner import TextCleaner
from .enrichment.sentiment_analyzer import SentimentAnalyzer


class DataEngine:
    """
    Main Data Engine class.
    
    Provides high-level API for:
    - Ingesting data from all buckets
    - Indexing with optional enrichment
    - Retrieving via multiple query types
    """
    
    def __init__(self, storage_dir: Path, embedding_dim: int = 384):
        """
        Initialize Data Engine.
        
        Args:
            storage_dir: Directory for storage
            embedding_dim: Dimension for embeddings
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize core components
        self.index_manager = IndexManager(
            storage_dir=self.storage_dir,
            embedding_dim=embedding_dim
        )
        self.retrieval_manager = RetrievalManager(self.index_manager)
        
        # Initialize enrichment pipelines
        self.text_cleaner = TextCleaner()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Embedding function (can be set later)
        self.embedding_fn: Optional[Callable[[str], np.ndarray]] = None
    
    def ingest_online_dataset(self,
                              file_path: Path,
                              source_name: str,
                              text_columns: Optional[List[str]] = None,
                              brand_column: Optional[str] = None,
                              **kwargs) -> List[DataRecord]:
        """
        Ingest online dataset (Bucket 1).
        
        Args:
            file_path: Path to CSV file
            source_name: Source identifier
            text_columns: Columns to use as text
            brand_column: Column containing brand
            **kwargs: Additional parameters
        
        Returns:
            List of ingested DataRecord objects
        """
        ingester = OnlineDatasetsIngester(source_name=source_name)
        records = list(ingester.ingest(file_path, text_columns=text_columns, brand_column=brand_column, **kwargs))
        return records
    
    def ingest_survey(self,
                     file_path: Path,
                     source_name: str,
                     brand_column: Optional[str] = None,
                     **kwargs) -> List[DataRecord]:
        """
        Ingest survey/interview data (Bucket 2).
        
        Args:
            file_path: Path to CSV or TXT file
            source_name: Source identifier
            brand_column: Column containing brand (for CSV)
            **kwargs: Additional parameters
        
        Returns:
            List of ingested DataRecord objects
        """
        ingester = SurveysInterviewsIngester(source_name=source_name)
        records = list(ingester.ingest(file_path, brand_column=brand_column, **kwargs))
        return records
    
    def ingest_financial_data(self,
                             file_path: Path,
                             source_name: str,
                             client_id: str,
                             **kwargs) -> List[DataRecord]:
        """
        Ingest financial/foot-traffic data (Bucket 3).
        
        Args:
            file_path: Path to CSV file
            source_name: Source identifier
            client_id: Client identifier
            **kwargs: Additional parameters
        
        Returns:
            List of ingested DataRecord objects
        """
        ingester = FinancialDataIngester(source_name=source_name, client_id=client_id)
        records = list(ingester.ingest(file_path, **kwargs))
        return records
    
    def index_records(self,
                     records: List[DataRecord],
                     generate_embeddings: bool = False,
                     enrich_text: bool = True,
                     enrich_sentiment: bool = False) -> bool:
        """
        Index records with optional enrichment.
        
        Args:
            records: List of DataRecord objects
            generate_embeddings: Whether to generate embeddings (requires faiss-cpu)
            enrich_text: Whether to clean text
            enrich_sentiment: Whether to analyze sentiment
        
        Returns:
            True if successful
        
        Note:
            If generate_embeddings=True but FAISS is not installed, embeddings
            will be stored in records but not indexed for vector search.
        """
        # Apply enrichment
        enriched_records = records
        if enrich_text:
            enriched_records = self.text_cleaner.enrich_batch(enriched_records)
        
        if enrich_sentiment:
            enriched_records = self.sentiment_analyzer.enrich_batch(enriched_records)
        
        # Generate embeddings if requested
        embeddings = None
        if generate_embeddings:
            if not self.embedding_fn:
                raise DataEngineException("embedding_fn not set. Use set_embedding_fn() first.")
            
            embeddings = []
            for record in enriched_records:
                text = record.get_text_for_embedding()
                if text:
                    embedding = self.embedding_fn(text)
                    embeddings.append(embedding)
                    record.embedding = embedding.tolist()
                else:
                    # Create zero embedding if no text
                    embeddings.append(np.zeros(self.index_manager.embedding_dim))
            
            embeddings = np.array(embeddings)
        
        # Index (will handle FAISS availability check internally)
        try:
            return self.index_manager.index_batch(enriched_records, embeddings)
        except Exception as e:
            if "FAISS" in str(e) and not generate_embeddings:
                # If FAISS error but we're not using embeddings, just index metadata
                return self.index_manager.index_batch(enriched_records, None)
            raise
    
    def set_embedding_fn(self, embedding_fn: Callable[[str], np.ndarray]):
        """Set the embedding function for semantic search"""
        self.embedding_fn = embedding_fn
    
    def search(self,
              query: str,
              filters: Optional[Dict[str, Any]] = None,
              top_k: int = 10) -> List[DataRecord]:
        """
        Semantic search.
        
        Args:
            query: Text query
            filters: Optional metadata filters
            top_k: Number of results
        
        Returns:
            List of DataRecord objects
        """
        if not self.embedding_fn:
            raise DataEngineException("embedding_fn not set. Use set_embedding_fn() first.")
        
        return self.retrieval_manager.query_by_text(
            query,
            embedding_fn=self.embedding_fn,
            filters=filters,
            top_k=top_k
        )
    
    def get_by_brand(self, brand: str, limit: Optional[int] = None) -> List[DataRecord]:
        """Get records by brand"""
        return self.retrieval_manager.query_by_brand(brand, limit=limit)
    
    def get_by_bucket(self, bucket_id: int, limit: Optional[int] = None) -> List[DataRecord]:
        """Get records by bucket"""
        return self.retrieval_manager.query_by_bucket(bucket_id, limit=limit)
    
    def get_by_time_range(self, start_time: Any, end_time: Any, limit: Optional[int] = None) -> List[DataRecord]:
        """Get records by time range"""
        return self.retrieval_manager.query_by_time_range(start_time, end_time, limit=limit)
    
    def get_by_filters(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[DataRecord]:
        """Get records by filters"""
        return self.retrieval_manager.query_by_filters(filters, limit=limit)

