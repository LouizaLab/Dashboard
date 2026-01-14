"""
Local file-based storage implementations.

These use simple file storage and can be swapped for cloud/DB implementations.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from ..core.schema import DataRecord

# Optional import for FAISS (vector storage)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from ..core.schema import DataRecord
from ..core.exceptions import StorageError
from .interfaces import StorageBackend, VectorStore, MetadataStore


class LocalStorageBackend(StorageBackend):
    """Local file-based storage for raw records"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir = self.storage_dir / "records"
        self.records_dir.mkdir(exist_ok=True)
        self.index_file = self.storage_dir / "record_index.json"
        self._load_index()
    
    def _load_index(self):
        """Load the record index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠ Warning: Corrupted record index file detected: {e}")
                print(f"   Recreating index from scratch...")
                # Backup corrupted file
                backup_file = self.index_file.with_suffix('.json.corrupted')
                import shutil
                shutil.copy2(self.index_file, backup_file)
                print(f"   Corrupted file backed up to: {backup_file}")
                # Initialize fresh index
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save the record index"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def save_record(self, record: DataRecord, defer_save: bool = False) -> bool:
        """Save a data record"""
        try:
            record_file = self.records_dir / f"{record.record_id}.json"
            with open(record_file, 'w') as f:
                json.dump(record.to_dict(), f, indent=2, default=str)
            
            # Update index
            self.index[record.record_id] = {
                'bucket_id': record.bucket_id,
                'source_name': record.source_name,
                'brand': record.brand,
                'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                'ingestion_time': record.ingestion_time.isoformat(),
            }
            if not defer_save:
                self._save_index()
            return True
        except Exception as e:
            raise StorageError(f"Failed to save record {record.record_id}: {e}")
    
    def save_records_batch(self, records: List[DataRecord]) -> bool:
        """Save multiple records efficiently"""
        try:
            # Save all record files
            for record in records:
                record_file = self.records_dir / f"{record.record_id}.json"
                with open(record_file, 'w') as f:
                    json.dump(record.to_dict(), f, indent=2, default=str)
                
                # Update index in memory
                self.index[record.record_id] = {
                    'bucket_id': record.bucket_id,
                    'source_name': record.source_name,
                    'brand': record.brand,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                    'ingestion_time': record.ingestion_time.isoformat(),
                }
            
            # Save index once at the end
            self._save_index()
            return True
        except Exception as e:
            raise StorageError(f"Failed to save batch: {e}")
    
    def load_record(self, record_id: str) -> Optional[DataRecord]:
        """Load a data record by ID"""
        record_file = self.records_dir / f"{record_id}.json"
        if not record_file.exists():
            return None
        
        try:
            with open(record_file, 'r') as f:
                data = json.load(f)
            return DataRecord.from_dict(data)
        except Exception as e:
            raise StorageError(f"Failed to load record {record_id}: {e}")
    
    def load_records_batch(self, record_ids: List[str]) -> Dict[str, DataRecord]:
        """
        Load multiple records efficiently in batch.
        
        Args:
            record_ids: List of record IDs to load
            
        Returns:
            Dictionary mapping record_id to DataRecord (only includes successfully loaded records)
        """
        records = {}
        for record_id in record_ids:
            record = self.load_record(record_id)
            if record:
                records[record_id] = record
        return records
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a data record"""
        record_file = self.records_dir / f"{record_id}.json"
        if record_file.exists():
            record_file.unlink()
        
        if record_id in self.index:
            del self.index[record_id]
            self._save_index()
        
        return True
    
    def list_records(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[str]:
        """List record IDs matching filters"""
        record_ids = list(self.index.keys())
        
        if filters:
            filtered = []
            for record_id in record_ids:
                record = self.load_record(record_id)
                if record and self._matches_filters(record, filters):
                    filtered.append(record_id)
            record_ids = filtered
        
        if limit:
            record_ids = record_ids[:limit]
        
        return record_ids
    
    def _matches_filters(self, record: DataRecord, filters: Dict[str, Any]) -> bool:
        """Check if record matches filters"""
        for key, value in filters.items():
            if key == 'bucket_id' and record.bucket_id != value:
                return False
            elif key == 'brand' and record.brand != value:
                return False
            elif key == 'source_name' and record.source_name != value:
                return False
            # Add more filter types as needed
        return True


class LocalVectorStore(VectorStore):
    """Local FAISS-based vector store"""
    
    def __init__(self, storage_dir: Path, dimension: int = 384):
        if not FAISS_AVAILABLE:
            raise StorageError(
                "FAISS is not installed. Install it with: pip install faiss-cpu "
                "(or faiss-gpu for GPU support). "
                "If you don't need semantic search, use generate_embeddings=False when indexing."
            )
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self.index_file = self.storage_dir / "vector_index.faiss"
        self.id_file = self.storage_dir / "vector_ids.json"
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.record_ids = []
        self._load_index()
    
    def _load_index(self):
        """Load existing index if available"""
        if not FAISS_AVAILABLE:
            return
        
        if self.index_file.exists() and self.id_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.id_file, 'r') as f:
                    self.record_ids = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")
                self.index = faiss.IndexFlatL2(self.dimension)
                self.record_ids = []
    
    def _save_index(self):
        """Save index to disk"""
        if not FAISS_AVAILABLE:
            return
        faiss.write_index(self.index, str(self.index_file))
        with open(self.id_file, 'w') as f:
            json.dump(self.record_ids, f)
    
    def add_vectors(self, record_ids: List[str], vectors: np.ndarray) -> bool:
        """Add vectors with associated record IDs"""
        if not FAISS_AVAILABLE:
            raise StorageError("FAISS is not installed. Install with: pip install faiss-cpu")
        
        if vectors.shape[1] != self.dimension:
            raise StorageError(f"Vector dimension mismatch: expected {self.dimension}, got {vectors.shape[1]}")
        
        # Convert to float32 for FAISS
        vectors = vectors.astype('float32')
        
        # Add to index
        self.index.add(vectors)
        self.record_ids.extend(record_ids)
        self._save_index()
        return True
    
    def search(self, query_vector: np.ndarray, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """Search for similar vectors"""
        if not FAISS_AVAILABLE:
            raise StorageError("FAISS is not installed. Install with: pip install faiss-cpu")
        
        if query_vector.shape[0] != self.dimension:
            raise StorageError(f"Query dimension mismatch: expected {self.dimension}, got {query_vector.shape[0]}")
        
        query_vector = query_vector.reshape(1, -1).astype('float32')
        
        # FAISS search
        distances, indices = self.index.search(query_vector, min(top_k, len(self.record_ids)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.record_ids):
                record_id = self.record_ids[idx]
                # Apply filters if provided (would need metadata store for this)
                results.append((record_id, float(dist)))
        
        return results
    
    def get_vector(self, record_id: str) -> Optional[np.ndarray]:
        """Get vector for a specific record ID"""
        if record_id not in self.record_ids:
            return None
        
        idx = self.record_ids.index(record_id)
        # FAISS doesn't support direct retrieval, would need to store separately
        # For now, return None (can be enhanced with separate storage)
        return None
    
    def delete_vector(self, record_id: str) -> bool:
        """Delete a vector (FAISS limitation: requires rebuilding)"""
        if record_id not in self.record_ids:
            return False
        
        # FAISS doesn't support deletion easily, would need to rebuild
        # For production, consider using a different backend or storing vectors separately
        idx = self.record_ids.index(record_id)
        # Mark as deleted (would need to rebuild index)
        return True
    
    def get_dimension(self) -> int:
        """Get the dimension of stored vectors"""
        return self.dimension


class LocalMetadataStore(MetadataStore):
    """Local JSON-based metadata store"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "metadata_index.json"
        self._load_index()
    
    def _load_index(self):
        """Load metadata index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠ Warning: Corrupted metadata index file detected: {e}")
                print(f"   Recreating index from scratch...")
                # Backup corrupted file
                backup_file = self.index_file.with_suffix('.json.corrupted')
                import shutil
                shutil.copy2(self.index_file, backup_file)
                print(f"   Corrupted file backed up to: {backup_file}")
                # Initialize fresh index
                self.index = {
                    'by_bucket': {},
                    'by_brand': {},
                    'by_source': {},
                    'by_client': {},
                    'by_time': [],
                    'records': {}
                }
        else:
            self.index = {
                'by_bucket': {},
                'by_brand': {},
                'by_source': {},
                'by_client': {},
                'by_time': [],
                'records': {}
            }
    
    def _save_index(self):
        """Save metadata index"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2, default=str)
    
    def index_record(self, record: DataRecord) -> bool:
        """Index a record's metadata"""
        record_id = record.record_id
        
        # Index by bucket
        bucket_id = str(record.bucket_id)
        if bucket_id not in self.index['by_bucket']:
            self.index['by_bucket'][bucket_id] = []
        if record_id not in self.index['by_bucket'][bucket_id]:
            self.index['by_bucket'][bucket_id].append(record_id)
        
        # Index by brand
        if record.brand:
            if record.brand not in self.index['by_brand']:
                self.index['by_brand'][record.brand] = []
            if record_id not in self.index['by_brand'][record.brand]:
                self.index['by_brand'][record.brand].append(record_id)
        
        # Index by source
        if record.source_name:
            if record.source_name not in self.index['by_source']:
                self.index['by_source'][record.source_name] = []
            if record_id not in self.index['by_source'][record.source_name]:
                self.index['by_source'][record.source_name].append(record_id)
        
        # Index by client
        if record.client_id:
            if record.client_id not in self.index['by_client']:
                self.index['by_client'][record.client_id] = []
            if record_id not in self.index['by_client'][record.client_id]:
                self.index['by_client'][record.client_id].append(record_id)
        
        # Index by time
        if record.timestamp:
            timestamp_str = record.timestamp.isoformat() if isinstance(record.timestamp, datetime) else str(record.timestamp)
            self.index['by_time'].append({
                'record_id': record_id,
                'timestamp': timestamp_str
            })
        
        # Store full metadata
        self.index['records'][record_id] = {
            'bucket_id': record.bucket_id,
            'source_name': record.source_name,
            'brand': record.brand,
            'client_id': record.client_id,
            'timestamp': record.timestamp.isoformat() if record.timestamp else None,
            'categorical_fields': record.categorical_fields,
            'numerical_fields': record.numerical_fields,
        }
        
        self._save_index()
        return True
    
    def query_by_bucket(self, bucket_id: int, limit: Optional[int] = None) -> List[str]:
        """Query records by bucket ID"""
        bucket_key = str(bucket_id)
        record_ids = self.index['by_bucket'].get(bucket_key, [])
        if limit:
            record_ids = record_ids[:limit]
        return record_ids
    
    def query_by_brand(self, brand: str, limit: Optional[int] = None) -> List[str]:
        """Query records by brand"""
        record_ids = self.index['by_brand'].get(brand, [])
        if limit:
            record_ids = record_ids[:limit]
        return record_ids
    
    def query_by_time_range(self, start_time: Any, end_time: Any, limit: Optional[int] = None) -> List[str]:
        """Query records by time range"""
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        record_ids = []
        for entry in self.index['by_time']:
            timestamp_str = entry['timestamp']
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if start_time <= timestamp <= end_time:
                record_ids.append(entry['record_id'])
        
        if limit:
            record_ids = record_ids[:limit]
        return record_ids
    
    def query_by_filters(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[str]:
        """Query records by arbitrary filters"""
        # Start with all records
        all_record_ids = set(self.index['records'].keys())
        
        # Apply filters
        for key, value in filters.items():
            matching_ids = set()
            
            if key == 'bucket_id':
                matching_ids = set(self.query_by_bucket(value))
            elif key == 'brand':
                matching_ids = set(self.query_by_brand(value))
            elif key == 'source_name':
                matching_ids = set(self.index['by_source'].get(value, []))
            elif key == 'client_id':
                matching_ids = set(self.index['by_client'].get(value, []))
            elif key.startswith('categorical_fields.'):
                field_name = key.replace('categorical_fields.', '')
                for record_id, metadata in self.index['records'].items():
                    if metadata['categorical_fields'].get(field_name) == value:
                        matching_ids.add(record_id)
            elif key.startswith('numerical_fields.'):
                field_name = key.replace('numerical_fields.', '')
                # Support min/max ranges
                if isinstance(value, dict):
                    min_val = value.get('min')
                    max_val = value.get('max')
                    for record_id, metadata in self.index['records'].items():
                        field_val = metadata['numerical_fields'].get(field_name)
                        if field_val is not None:
                            if min_val is not None and field_val < min_val:
                                continue
                            if max_val is not None and field_val > max_val:
                                continue
                            matching_ids.add(record_id)
                else:
                    # Exact match
                    for record_id, metadata in self.index['records'].items():
                        if metadata['numerical_fields'].get(field_name) == value:
                            matching_ids.add(record_id)
            
            all_record_ids &= matching_ids
        
        record_ids = list(all_record_ids)
        if limit:
            record_ids = record_ids[:limit]
        return record_ids
    
    def delete_index(self, record_id: str) -> bool:
        """Remove a record from the index"""
        # Remove from all indexes
        for bucket_ids in self.index['by_bucket'].values():
            if record_id in bucket_ids:
                bucket_ids.remove(record_id)
        
        for brand_ids in self.index['by_brand'].values():
            if record_id in brand_ids:
                brand_ids.remove(record_id)
        
        for source_ids in self.index['by_source'].values():
            if record_id in source_ids:
                source_ids.remove(record_id)
        
        for client_ids in self.index['by_client'].values():
            if record_id in client_ids:
                client_ids.remove(record_id)
        
        self.index['by_time'] = [e for e in self.index['by_time'] if e['record_id'] != record_id]
        
        if record_id in self.index['records']:
            del self.index['records'][record_id]
        
        self._save_index()
        return True

