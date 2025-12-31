"""
Bucket 1: Online Datasets Ingestion

Handles CSV files from Kaggle, public datasets, research datasets.
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, Optional, Dict, Any
from datetime import datetime

from .base import IngestionBase
from ..core.schema import DataRecord, BucketType, SourceType
from ..core.exceptions import IngestionError


class OnlineDatasetsIngester(IngestionBase):
    """
    Ingests CSV files from online datasets (Kaggle, public datasets).
    
    Assumes structured CSV format with columns.
    Each row becomes a DataRecord with structured_fields populated.
    """
    
    def __init__(self, source_name: str, dataset_name: Optional[str] = None):
        """
        Initialize online datasets ingester.
        
        Args:
            source_name: Name of the source (e.g., "kaggle_food_reviews")
            dataset_name: Optional dataset identifier
        """
        super().__init__(bucket_id=BucketType.ONLINE_DATASETS.value, source_name=source_name)
        self.dataset_name = dataset_name or source_name
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate CSV file"""
        if not file_path.exists():
            return False
        if not file_path.suffix.lower() == '.csv':
            return False
        return True
    
    def ingest(self, file_path: Path, 
               text_columns: Optional[list] = None,
               brand_column: Optional[str] = None,
               timestamp_column: Optional[str] = None,
               **kwargs) -> Iterator[DataRecord]:
        """
        Ingest CSV file.
        
        Args:
            file_path: Path to CSV file
            text_columns: List of column names to combine as raw_text
            brand_column: Column name containing brand information
            timestamp_column: Column name containing timestamp
            **kwargs: Additional parameters
        
        Yields:
            DataRecord objects
        """
        try:
            # Try UTF-8 first, then fallback to other encodings
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # Try common encodings
                for encoding in ['latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise IngestionError(f"Could not decode CSV file {file_path} with any supported encoding")
        except Exception as e:
            raise IngestionError(f"Failed to read CSV file {file_path}: {e}")
        
        # Default text columns if not specified
        if text_columns is None:
            # Try to infer text columns (string columns with reasonable length)
            text_columns = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check if it looks like text (not just IDs)
                    sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else ""
                    if isinstance(sample, str) and len(sample) > 10:
                        text_columns.append(col)
        
        for idx, row in df.iterrows():
            # Extract text content
            raw_text_parts = []
            if text_columns:
                for col in text_columns:
                    if col in row and pd.notna(row[col]):
                        raw_text_parts.append(str(row[col]))
            raw_text = " ".join(raw_text_parts) if raw_text_parts else None
            
            # Extract brand
            brand = None
            if brand_column and brand_column in row:
                brand_val = row[brand_column]
                if pd.notna(brand_val):
                    brand = str(brand_val).strip()
            
            # Extract timestamp
            timestamp = None
            if timestamp_column and timestamp_column in row:
                timestamp_val = row[timestamp_column]
                if pd.notna(timestamp_val):
                    try:
                        timestamp = pd.to_datetime(timestamp_val)
                        if isinstance(timestamp, pd.Timestamp):
                            timestamp = timestamp.to_pydatetime()
                    except:
                        pass
            
            # Build structured fields (all columns)
            structured_fields = {}
            numerical_fields = {}
            categorical_fields = {}
            
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    # Determine field type
                    if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                        numerical_fields[col] = float(value)
                    elif df[col].dtype == 'object':
                        # Check if it's categorical (limited unique values)
                        if df[col].nunique() < len(df) * 0.5:  # Less than 50% unique
                            categorical_fields[col] = str(value)
                        else:
                            structured_fields[col] = str(value)
                    else:
                        structured_fields[col] = str(value)
            
            # Create record
            record = DataRecord(
                bucket_id=self.bucket_id,
                source_name=self.source_name,
                source_type=SourceType.CSV.value,
                brand=brand,
                timestamp=timestamp,
                raw_text=raw_text,
                structured_fields=structured_fields,
                numerical_fields=numerical_fields,
                categorical_fields=categorical_fields,
                metadata={
                    'dataset_name': self.dataset_name,
                    'row_index': int(idx),
                    'file_path': str(file_path),
                }
            )
            
            yield record

