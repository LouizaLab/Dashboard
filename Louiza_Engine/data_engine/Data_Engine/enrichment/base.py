"""
Base enrichment pipeline

All enrichment modules inherit from this base class.
"""

from abc import ABC, abstractmethod
from ..core.schema import DataRecord


class EnrichmentPipeline(ABC):
    """
    Base class for enrichment pipelines.
    
    Enrichment is optional and modular - can be applied selectively.
    """
    
    @abstractmethod
    def enrich(self, record: DataRecord) -> DataRecord:
        """
        Enrich a DataRecord.
        
        Args:
            record: Input record
        
        Returns:
            Enriched record (may be modified in-place or new instance)
        """
        pass
    
    def enrich_batch(self, records: list) -> list:
        """
        Enrich multiple records.
        
        Args:
            records: List of DataRecord objects
        
        Returns:
            List of enriched records
        """
        return [self.enrich(record) for record in records]

