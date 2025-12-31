"""
Base scraper class for Bucket 4

All scrapers inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional
from datetime import datetime

from ..base import IngestionBase
from ...core.schema import DataRecord, BucketType, SourceType
from ...core.exceptions import IngestionError


class BaseScraper(IngestionBase):
    """
    Base class for all scrapers.
    
    Scrapers fetch data from external sources (Google Reviews, Reddit, etc.)
    and convert them to DataRecord format.
    """
    
    def __init__(self, source_name: str, platform: str):
        """
        Initialize scraper.
        
        Args:
            source_name: Name of the source
            platform: Platform name (e.g., "google_reviews", "reddit")
        """
        super().__init__(bucket_id=BucketType.SCRAPED_PUBLIC_DATA.value, source_name=source_name)
        self.platform = platform
    
    def validate_file(self, file_path) -> bool:
        """Scrapers don't use file paths"""
        return False
    
    @abstractmethod
    def scrape(self, query: str, brand: Optional[str] = None, limit: Optional[int] = None, **kwargs) -> Iterator[DataRecord]:
        """
        Scrape data from the platform.
        
        Args:
            query: Search query or identifier
            brand: Brand name to filter by
            limit: Maximum number of records to scrape
            **kwargs: Platform-specific parameters
        
        Yields:
            DataRecord objects
        """
        pass
    
    def ingest(self, file_path=None, **kwargs) -> Iterator[DataRecord]:
        """
        For scrapers, ingest() calls scrape().
        file_path is ignored.
        """
        # Extract query from kwargs or use source_name
        query = kwargs.get('query', self.source_name)
        brand = kwargs.get('brand')
        limit = kwargs.get('limit')
        
        yield from self.scrape(query=query, brand=brand, limit=limit, **kwargs)
    
    def _create_record(self, 
                      text: str,
                      brand: Optional[str] = None,
                      timestamp: Optional[datetime] = None,
                      sentiment: Optional[float] = None,
                      metadata: Optional[dict] = None) -> DataRecord:
        """
        Helper to create a DataRecord from scraped content.
        
        Args:
            text: Scraped text content
            brand: Brand name
            timestamp: When content was created
            sentiment: Sentiment score if available
            metadata: Additional metadata
        
        Returns:
            DataRecord
        """
        return DataRecord(
            bucket_id=self.bucket_id,
            source_name=self.source_name,
            source_type=SourceType.SCRAPED.value,
            brand=brand,
            timestamp=timestamp,
            raw_text=text,
            sentiment=sentiment,
            metadata={
                'platform': self.platform,
                **(metadata or {})
            }
        )

