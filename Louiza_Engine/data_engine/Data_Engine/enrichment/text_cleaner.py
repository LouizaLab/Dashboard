"""
Text cleaning enrichment

Cleans and normalizes text content in records.
"""

import re
from typing import Optional

from .base import EnrichmentPipeline
from ..core.schema import DataRecord


class TextCleaner(EnrichmentPipeline):
    """
    Cleans raw text in DataRecord objects.
    
    Performs:
    - Remove extra whitespace
    - Normalize unicode
    - Remove URLs
    - Remove email addresses
    - Basic normalization
    """
    
    def __init__(self, 
                 remove_urls: bool = True,
                 remove_emails: bool = True,
                 normalize_whitespace: bool = True):
        """
        Initialize text cleaner.
        
        Args:
            remove_urls: Remove URLs from text
            remove_emails: Remove email addresses
            normalize_whitespace: Normalize whitespace
        """
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.normalize_whitespace = normalize_whitespace
    
    def enrich(self, record: DataRecord) -> DataRecord:
        """Clean text in record"""
        if not record.raw_text:
            return record
        
        text = record.raw_text
        
        # Remove URLs
        if self.remove_urls:
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        if self.remove_emails:
            text = re.sub(r'\S+@\S+', '', text)
        
        # Normalize whitespace
        if self.normalize_whitespace:
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        
        record.raw_text = text
        return record

