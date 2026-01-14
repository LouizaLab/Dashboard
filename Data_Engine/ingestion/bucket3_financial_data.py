"""
Bucket 3: Financial / Foot-Traffic Data Ingestion

Handles CSV files with:
- Credit card aggregates
- Transaction summaries
- Foot traffic / mobility data
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, Optional
from datetime import datetime

from .base import IngestionBase
from ..core.schema import DataRecord, BucketType, SourceType
from ..core.exceptions import IngestionError


class FinancialDataIngester(IngestionBase):
    """
    Ingests financial and foot-traffic CSV data.
    
    Assumes time-series data with client-scoped namespaces.
    Each row represents a transaction or traffic event.
    """
    
    def __init__(self, source_name: str, client_id: Optional[str] = None):
        """
        Initialize financial data ingester.
        
        Args:
            source_name: Name of the source
            client_id: Client identifier (required for bucket 3)
        """
        super().__init__(bucket_id=BucketType.FINANCIAL_DATA.value, source_name=source_name)
        self.client_id = client_id
        if not client_id:
            raise IngestionError("client_id is required for financial data ingestion")
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate CSV file"""
        if not file_path.exists():
            return False
        if not file_path.suffix.lower() == '.csv':
            return False
        return True
    
    def ingest(self, file_path: Path,
               timestamp_column: Optional[str] = None,
               amount_column: Optional[str] = None,
               location_column: Optional[str] = None,
               brand_column: Optional[str] = None,
               **kwargs) -> Iterator[DataRecord]:
        """
        Ingest financial/foot-traffic CSV file.
        
        Args:
            file_path: Path to CSV file
            timestamp_column: Column name containing timestamp
            amount_column: Column name containing transaction amount
            location_column: Column name containing location
            brand_column: Column name containing brand/merchant
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
        
        # Auto-detect timestamp column if not specified
        if timestamp_column is None:
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['time', 'date', 'timestamp', 'datetime']):
                    timestamp_column = col
                    break
        
        for idx, row in df.iterrows():
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
            
            # Extract brand
            brand = None
            if brand_column and brand_column in row:
                brand_val = row[brand_column]
                if pd.notna(brand_val):
                    brand = str(brand_val).strip()
            
            # Build structured fields
            structured_fields = {}
            numerical_fields = {}
            categorical_fields = {}
            
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                        numerical_fields[col] = float(value)
                    elif df[col].dtype == 'object':
                        # Location and similar fields are categorical
                        if df[col].nunique() < len(df) * 0.3:  # Less than 30% unique
                            categorical_fields[col] = str(value)
                        else:
                            structured_fields[col] = str(value)
                    else:
                        structured_fields[col] = str(value)
            
            # Create descriptive text from key fields
            text_parts = []
            if brand:
                text_parts.append(f"Brand: {brand}")
            if location_column and location_column in row:
                text_parts.append(f"Location: {row[location_column]}")
            if amount_column and amount_column in row:
                text_parts.append(f"Amount: {row[amount_column]}")
            raw_text = " | ".join(text_parts) if text_parts else None
            
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
                client_id=self.client_id,
                metadata={
                    'file_path': str(file_path),
                    'row_index': int(idx),
                    'data_type': 'financial' if amount_column else 'foot_traffic',
                }
            )
            
            yield record

