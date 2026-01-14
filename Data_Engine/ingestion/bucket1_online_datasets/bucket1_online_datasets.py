"""
Bucket 1: Online Datasets Ingestion

Handles:
- CSV files from Kaggle, public datasets, research datasets
- Structured, column-driven data
- Static or periodically updated datasets
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, Optional, List
from datetime import datetime

from ..base import IngestionBase
from ...core.schema import DataRecord, BucketType, SourceType
from ...core.exceptions import IngestionError


class OnlineDatasetsIngester(IngestionBase):
    """
    Ingests CSV files from online datasets (Kaggle, public datasets, etc.).
    
    CSV files are structured, column-driven data. Each row becomes a DataRecord.
    Supports text columns, brand columns, and automatic field classification.
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
        """Validate CSV file - Bucket 1 only accepts CSV files"""
        if not file_path.exists():
            return False
        suffix = file_path.suffix.lower()
        return suffix == '.csv'
    
    def ingest(self, file_path: Path,
               text_columns: Optional[List[str]] = None,
               brand_column: Optional[str] = None,
               **kwargs) -> Iterator[DataRecord]:
        """
        Ingest CSV file from online dataset.
        
        Args:
            file_path: Path to CSV file
            text_columns: List of column names to use as text content (auto-detected if None)
            brand_column: Column name containing brand/identifier (optional)
            **kwargs: Additional parameters
        
        Yields:
            DataRecord objects
        """
        if not self.validate_file(file_path):
            raise IngestionError(f"Invalid file type for Bucket 1: {file_path}. Only CSV files are supported.")
        
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
        
        if df.empty:
            raise IngestionError(f"CSV file {file_path} is empty")
        
        # Auto-detect text columns if not specified
        if text_columns is None:
            text_columns = self._detect_text_columns(df)
        
        # Process each row
        for idx, row in df.iterrows():
            # Extract text content from specified columns
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
            
            # Classify fields into structured, numerical, and categorical
            structured_fields = {}
            numerical_fields = {}
            categorical_fields = {}
            
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    continue
                
                # Skip text columns that are already in raw_text
                if text_columns and col in text_columns:
                    continue
                
                # Skip brand column (already extracted)
                if brand_column and col == brand_column:
                    continue
                
                # Classify by data type
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32', 'int', 'float']:
                    numerical_fields[col] = float(value)
                elif df[col].dtype == 'object' or df[col].dtype == 'string':
                    # Determine if categorical or structured text
                    if df[col].nunique() < min(50, len(df) * 0.1):  # Likely categorical (few unique values)
                        categorical_fields[col] = str(value)
                    else:
                        # Structured text field
                        structured_fields[col] = str(value)
                else:
                    # Other types (datetime, etc.) - store as string in structured
                    structured_fields[col] = str(value)
            
            record = DataRecord(
                bucket_id=self.bucket_id,
                source_name=self.source_name,
                source_type=SourceType.CSV.value,
                brand=brand,
                raw_text=raw_text,
                structured_fields=structured_fields,
                numerical_fields=numerical_fields,
                categorical_fields=categorical_fields,
                metadata={
                    'dataset_name': self.dataset_name,
                    'row_index': int(idx),
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                }
            )
            
            yield record
    
    def _detect_text_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Auto-detect text columns in DataFrame.
        
        Looks for object/string columns with longer average text length.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of column names likely to contain text content
        """
        text_columns = []
        
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype == 'string':
                # Sample values to check average length
                sample_values = df[col].dropna().head(20)
                if len(sample_values) > 0:
                    # Convert to string and calculate average length
                    avg_length = sample_values.astype(str).str.len().mean()
                    
                    # Consider it a text column if average length > 15 characters
                    # and has reasonable variance (not all same length)
                    if avg_length > 15:
                        text_columns.append(col)
        
        return text_columns


