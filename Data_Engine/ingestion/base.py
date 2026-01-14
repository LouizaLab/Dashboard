"""
Base ingestion class

All ingestion modules inherit from this base class.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Iterator
from ..core.schema import DataRecord
from ..core.exceptions import IngestionError


class IngestionBase(ABC):
    """
    Base class for all ingestion modules.
    
    Each bucket has its own ingester that:
    1. Validates input files
    2. Extracts raw content
    3. Attaches source metadata
    4. Yields standardized DataRecord objects
    """
    
    def __init__(self, bucket_id: int, source_name: str):
        """
        Initialize ingester.
        
        Args:
            bucket_id: Bucket type (1-4)
            source_name: Name/identifier for this source
        """
        self.bucket_id = bucket_id
        self.source_name = source_name
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that file is acceptable for this ingester.
        
        Returns:
            True if file is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def ingest(self, file_path: Path, **kwargs) -> Iterator[DataRecord]:
        """
        Ingest a file and yield DataRecord objects.
        
        Args:
            file_path: Path to file to ingest
            **kwargs: Additional parameters specific to ingester
        
        Yields:
            DataRecord objects
        """
        pass
    
    def ingest_batch(self, file_paths: List[Path], **kwargs) -> Iterator[DataRecord]:
        """
        Ingest multiple files.
        
        Args:
            file_paths: List of file paths
            **kwargs: Additional parameters
        
        Yields:
            DataRecord objects from all files
        """
        for file_path in file_paths:
            if not self.validate_file(file_path):
                raise IngestionError(f"Invalid file for ingester: {file_path}")
            
            try:
                for record in self.ingest(file_path, **kwargs):
                    yield record
            except Exception as e:
                raise IngestionError(f"Failed to ingest {file_path}: {e}")

