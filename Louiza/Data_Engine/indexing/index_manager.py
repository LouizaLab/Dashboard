"""
Index Manager

Orchestrates multi-indexing of DataRecords:
- Structured metadata indexing
- Semantic vector indexing
- Metadata filtering
"""

import numpy as np
from typing import List, Optional
from pathlib import Path

from ..core.schema import DataRecord
from ..core.exceptions import IndexingError
from ..storage.interfaces import StorageBackend, VectorStore, MetadataStore
from ..storage.local_storage import LocalStorageBackend, LocalVectorStore, LocalMetadataStore


class IndexManager:
    """
    Manages indexing of DataRecords across multiple index types.
    
    Coordinates:
    - Raw storage (StorageBackend)
    - Vector embeddings (VectorStore)
    - Metadata indexing (MetadataStore)
    """
    
    def __init__(self,
                 storage_dir: Path,
                 storage_backend: Optional[StorageBackend] = None,
                 vector_store: Optional[VectorStore] = None,
                 metadata_store: Optional[MetadataStore] = None,
                 embedding_dim: int = 384,
                 require_vector_store: bool = False):
        """
        Initialize index manager.
        
        Args:
            storage_dir: Directory for storage
            storage_backend: Storage backend (defaults to LocalStorageBackend)
            vector_store: Vector store (defaults to LocalVectorStore if FAISS available)
            metadata_store: Metadata store (defaults to LocalMetadataStore)
            embedding_dim: Dimension for embeddings
            require_vector_store: If True, raise error if vector store can't be created
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage backends
        self.storage_backend = storage_backend or LocalStorageBackend(self.storage_dir / "raw")
        
        # Initialize vector store (only if not provided and FAISS is available)
        if vector_store:
            self.vector_store = vector_store
        else:
            try:
                self.vector_store = LocalVectorStore(self.storage_dir / "vectors", dimension=embedding_dim)
            except Exception as e:
                if require_vector_store:
                    raise
                # Vector store not available, but that's OK if we're not using embeddings
                self.vector_store = None
        
        self.metadata_store = metadata_store or LocalMetadataStore(self.storage_dir / "metadata")
        
        self.embedding_dim = embedding_dim
    
    def index_record(self, record: DataRecord, embedding: Optional[np.ndarray] = None) -> bool:
        """
        Index a single DataRecord.
        
        Args:
            record: DataRecord to index
            embedding: Optional pre-computed embedding vector
        
        Returns:
            True if successful
        """
        try:
            # Validate record
            if not record.validate():
                raise IndexingError(f"Invalid record: {record.record_id}")
            
            # Store raw record
            self.storage_backend.save_record(record)
            
            # Index metadata
            self.metadata_store.index_record(record)
            
            # Index embedding if provided
            if embedding is not None:
                if not self.vector_store:
                    raise IndexingError(
                        "Cannot index embeddings: FAISS not installed. "
                        "Install with: pip install faiss-cpu"
                    )
                if embedding.shape[0] != self.embedding_dim:
                    raise IndexingError(
                        f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embedding.shape[0]}"
                    )
                self.vector_store.add_vectors([record.record_id], embedding.reshape(1, -1))
            
            return True
        
        except Exception as e:
            raise IndexingError(f"Failed to index record {record.record_id}: {e}")
    
    def index_batch(self, records: List[DataRecord], embeddings: Optional[np.ndarray] = None) -> bool:
        """
        Index multiple records in batch.
        
        Args:
            records: List of DataRecord objects
            embeddings: Optional array of embeddings (shape: [len(records), embedding_dim])
        
        Returns:
            True if successful
        """
        try:
            # Store all records
            for record in records:
                if not record.validate():
                    errors = record.get_validation_errors()
                    raise IndexingError(
                        f"Invalid record {record.record_id}: {', '.join(errors)}"
                    )
                self.storage_backend.save_record(record)
                self.metadata_store.index_record(record)
            
            # Add embeddings in batch if provided
            if embeddings is not None:
                if not self.vector_store:
                    raise IndexingError(
                        "Cannot index embeddings: FAISS not installed. "
                        "Install with: pip install faiss-cpu"
                    )
                if len(records) != embeddings.shape[0]:
                    raise IndexingError(
                        f"Record count mismatch: {len(records)} records, {embeddings.shape[0]} embeddings"
                    )
                if embeddings.shape[1] != self.embedding_dim:
                    raise IndexingError(
                        f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}"
                    )
                
                record_ids = [r.record_id for r in records]
                self.vector_store.add_vectors(record_ids, embeddings)
            
            return True
        
        except Exception as e:
            raise IndexingError(f"Failed to index batch: {e}")
    
    def get_record(self, record_id: str) -> Optional[DataRecord]:
        """Get a record by ID"""
        return self.storage_backend.load_record(record_id)
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a record from all indexes"""
        try:
            self.storage_backend.delete_record(record_id)
            self.metadata_store.delete_index(record_id)
            self.vector_store.delete_vector(record_id)
            return True
        except Exception as e:
            raise IndexingError(f"Failed to delete record {record_id}: {e}")

