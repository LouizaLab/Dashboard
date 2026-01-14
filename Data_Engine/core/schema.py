"""
Core data schema for the Data Engine.

Defines the unified DataRecord structure that all ingested data must conform to.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass, field, asdict
import json


class BucketType(Enum):
    """Data bucket types"""
    ONLINE_DATASETS = 1
    SURVEYS_INTERVIEWS = 2
    FINANCIAL_DATA = 3
    SCRAPED_PUBLIC_DATA = 4


class SourceType(Enum):
    """Source data format types"""
    CSV = "csv"
    TXT = "txt"
    SCRAPED = "scraped"
    JSON = "json"


@dataclass
class DataRecord:
    """
    Unified data record schema for all ingested data.
    
    Every data point in the system becomes a DataRecord, ensuring
    consistent structure for indexing, retrieval, and agent access.
    
    Attributes:
        record_id: Unique identifier (UUID)
        bucket_id: Bucket type (1-4)
        source_name: Name/identifier of the source
        source_type: Format type (csv, txt, scraped, json)
        brand: Brand name if applicable (optional)
        timestamp: Event timestamp (when data was created/collected)
        ingestion_time: When this record was ingested into the system
        raw_text: Raw text content if applicable
        structured_fields: Dictionary of structured key-value pairs
        numerical_fields: Dictionary of numerical values
        categorical_fields: Dictionary of categorical values
        sentiment: Sentiment score if computed (optional)
        embedding: Vector embedding if computed (optional)
        metadata: Additional metadata dictionary
        client_id: Client identifier for bucket 3 (financial data)
        chunk_index: For chunked documents (interviews, long text)
        parent_record_id: For chunks, reference to parent record
    """
    
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bucket_id: int = 1
    source_name: str = ""
    source_type: str = "csv"
    brand: Optional[str] = None
    timestamp: Optional[datetime] = None
    ingestion_time: datetime = field(default_factory=datetime.utcnow)
    raw_text: Optional[str] = None
    structured_fields: Dict[str, Any] = field(default_factory=dict)
    numerical_fields: Dict[str, float] = field(default_factory=dict)
    categorical_fields: Dict[str, str] = field(default_factory=dict)
    sentiment: Optional[float] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    client_id: Optional[str] = None
    chunk_index: Optional[int] = None
    parent_record_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling datetime serialization"""
        data = asdict(self)
        # Convert datetime to ISO format strings
        if data.get('timestamp'):
            data['timestamp'] = data['timestamp'].isoformat() if isinstance(data['timestamp'], datetime) else data['timestamp']
        if data.get('ingestion_time'):
            data['ingestion_time'] = data['ingestion_time'].isoformat() if isinstance(data['ingestion_time'], datetime) else data['ingestion_time']
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataRecord':
        """Create DataRecord from dictionary"""
        # Parse datetime strings
        if 'timestamp' in data and data['timestamp']:
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        if 'ingestion_time' in data and data['ingestion_time']:
            if isinstance(data['ingestion_time'], str):
                data['ingestion_time'] = datetime.fromisoformat(data['ingestion_time'].replace('Z', '+00:00'))
        return cls(**data)
    
    def get_text_for_embedding(self) -> str:
        """
        Extract text content suitable for embedding.
        Combines raw_text and structured text fields.
        """
        text_parts = []
        
        if self.raw_text:
            text_parts.append(self.raw_text)
        
        # Add text-like structured fields
        for key, value in self.structured_fields.items():
            if isinstance(value, str) and len(value) > 0:
                # Skip very short values that are likely IDs
                if len(value) > 3:
                    text_parts.append(f"{key}: {value}")
        
        return " ".join(text_parts) if text_parts else ""
    
    def validate(self) -> bool:
        """
        Validate record has minimum required fields.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.source_name:
            return False
        if self.bucket_id not in [1, 2, 3, 4]:
            return False
        # Allow records with any data (text, structured, numerical, or categorical fields)
        # This is valid for structured data like financial records
        has_data = (
            bool(self.raw_text) or 
            bool(self.structured_fields) or 
            bool(self.numerical_fields) or 
            bool(self.categorical_fields)
        )
        return has_data
    
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors.
        
        Returns:
            List of error messages
        """
        errors = []
        if not self.source_name:
            errors.append("Missing source_name")
        if self.bucket_id not in [1, 2, 3, 4]:
            errors.append(f"Invalid bucket_id: {self.bucket_id} (must be 1-4)")
        has_data = (
            bool(self.raw_text) or 
            bool(self.structured_fields) or 
            bool(self.numerical_fields) or 
            bool(self.categorical_fields)
        )
        if not has_data:
            errors.append("Record has no data (no text, structured, numerical, or categorical fields)")
        return errors

