"""
Bucket 2: Surveys & Interviews Ingestion

Handles:
- CSV survey data (Likert scales, rankings, free-text)
- TXT interview transcripts
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, Optional
from datetime import datetime

from .base import IngestionBase
from ..core.schema import DataRecord, BucketType, SourceType
from ..core.exceptions import IngestionError


class SurveysInterviewsIngester(IngestionBase):
    """
    Ingests survey CSV files and interview TXT files.
    
    CSV: Each row is a survey response
    TXT: Long-form interviews, chunked into records
    """
    
    def __init__(self, source_name: str, survey_name: Optional[str] = None):
        """
        Initialize surveys/interviews ingester.
        
        Args:
            source_name: Name of the source
            survey_name: Optional survey/interview identifier
        """
        super().__init__(bucket_id=BucketType.SURVEYS_INTERVIEWS.value, source_name=source_name)
        self.survey_name = survey_name or source_name
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate CSV or TXT file"""
        if not file_path.exists():
            return False
        suffix = file_path.suffix.lower()
        return suffix in ['.csv', '.txt']
    
    def ingest(self, file_path: Path,
               chunk_size: int = 1000,
               chunk_overlap: int = 200,
               brand_column: Optional[str] = None,
               **kwargs) -> Iterator[DataRecord]:
        """
        Ingest CSV or TXT file.
        
        Args:
            file_path: Path to file
            chunk_size: For TXT files, size of text chunks
            chunk_overlap: Overlap between chunks
            brand_column: For CSV, column name containing brand
            **kwargs: Additional parameters
        
        Yields:
            DataRecord objects
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            yield from self._ingest_csv(file_path, brand_column)
        elif suffix == '.txt':
            yield from self._ingest_txt(file_path, chunk_size, chunk_overlap)
        else:
            raise IngestionError(f"Unsupported file type: {suffix}")
    
    def _ingest_csv(self, file_path: Path, brand_column: Optional[str] = None) -> Iterator[DataRecord]:
        """Ingest CSV survey data"""
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
        
        # Identify text columns (likely free-text answers)
        text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if values are longer text (not just categories)
                sample_values = df[col].dropna().head(5)
                if len(sample_values) > 0:
                    avg_length = sample_values.astype(str).str.len().mean()
                    if avg_length > 20:  # Likely free-text
                        text_columns.append(col)
        
        for idx, row in df.iterrows():
            # Extract text content
            raw_text_parts = []
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
                        # Likert scales and rankings are usually categorical
                        if df[col].nunique() < 20:  # Likely categorical
                            categorical_fields[col] = str(value)
                        else:
                            structured_fields[col] = str(value)
                    else:
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
                    'survey_name': self.survey_name,
                    'response_index': int(idx),
                    'file_path': str(file_path),
                }
            )
            
            yield record
    
    def _ingest_txt(self, file_path: Path, chunk_size: int, chunk_overlap: int) -> Iterator[DataRecord]:
        """Ingest TXT interview file, chunking long text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        except Exception as e:
            raise IngestionError(f"Failed to read TXT file {file_path}: {e}")
        
        # Chunk the text
        chunks = self._chunk_text(full_text, chunk_size, chunk_overlap)
        
        parent_record_id = None
        for chunk_idx, chunk_text in enumerate(chunks):
            record = DataRecord(
                bucket_id=self.bucket_id,
                source_name=self.source_name,
                source_type=SourceType.TXT.value,
                raw_text=chunk_text,
                chunk_index=chunk_idx,
                parent_record_id=parent_record_id,
                metadata={
                    'survey_name': self.survey_name,
                    'file_path': str(file_path),
                    'total_chunks': len(chunks),
                }
            )
            
            # Set parent_record_id for first chunk
            if chunk_idx == 0:
                parent_record_id = record.record_id
            
            yield record
    
    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            
            start = end - chunk_overlap
        
        return chunks

