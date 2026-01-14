#!/usr/bin/env python3
"""
Simple script to chunk interview files by User responses without requiring embeddings.

This script:
1. Finds all interview TXT files
2. Chunks them by User response boundaries
3. Saves records directly to storage (no embeddings needed)
"""

import sys
from pathlib import Path
import json
import uuid
from datetime import datetime
import re

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.core.schema import DataRecord, SourceType, BucketType


def chunk_by_user_responses(text: str) -> list:
    """
    Chunk text by User response boundaries.
    
    Each chunk contains one User response (no Agent prompts).
    """
    chunks = []
    
    # Find all User response boundaries
    user_pattern = re.compile(r'User:\s*', re.IGNORECASE)
    user_matches = list(user_pattern.finditer(text))
    
    if len(user_matches) > 1:
        # Chunk by User responses
        for i, match in enumerate(user_matches):
            start = match.start()
            
            # End of this User response (start of next User response, or end of text)
            if i + 1 < len(user_matches):
                end = user_matches[i + 1].start()
            else:
                end = len(text)
            
            # Extract User response chunk
            chunk = text[start:end].strip()
            
            # Only include if chunk has substantial content (at least 50 chars)
            if len(chunk) >= 50:
                chunks.append(chunk)
    else:
        # Fallback: if no User patterns, try to extract User content
        # Remove Agent prompts and keep only User responses
        lines = text.split('\n')
        user_lines = []
        in_user_response = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if re.match(r'^User:\s*', line, re.IGNORECASE):
                in_user_response = True
                user_text = re.sub(r'^User:\s*', '', line, flags=re.IGNORECASE)
                if user_text:
                    user_lines.append(user_text)
            elif re.match(r'^Agent:\s*', line, re.IGNORECASE):
                in_user_response = False
            elif in_user_response:
                user_lines.append(line)
        
        if user_lines:
            chunks.append(' '.join(user_lines))
    
    return chunks


def find_11labs_interview_files() -> list:
    """Find all 11 Labs interview TXT files"""
    script_dir = Path(__file__).parent
    interview_dir = script_dir / "ingestion" / "bucket2_survey_interviews" / "11_labs_interviews"
    
    if not interview_dir.exists():
        return []
    
    return list(interview_dir.glob("*.txt"))


def save_record(record: DataRecord, storage_dir: Path):
    """Save a DataRecord to JSON file"""
    records_dir = storage_dir / "raw" / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    
    record_file = records_dir / f"{record.record_id}.json"
    
    # Convert record to dict
    record_dict = {
        "record_id": record.record_id,
        "bucket_id": record.bucket_id,
        "source_name": record.source_name,
        "source_type": record.source_type,
        "brand": record.brand,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        "ingestion_time": record.ingestion_time.isoformat(),
        "raw_text": record.raw_text,
        "structured_fields": record.structured_fields,
        "numerical_fields": record.numerical_fields,
        "categorical_fields": record.categorical_fields,
        "sentiment": record.sentiment,
        "embedding": record.embedding,
        "metadata": record.metadata,
        "client_id": record.client_id,
        "chunk_index": record.chunk_index,
        "parent_record_id": record.parent_record_id,
    }
    
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(record_dict, f, indent=2, ensure_ascii=False)


def main():
    """Main function"""
    print("=" * 70)
    print("SIMPLE INTERVIEW CHUNKING (No Embeddings Required)")
    print("=" * 70)
    
    # Find interview files
    interview_files = find_11labs_interview_files()
    
    if not interview_files:
        print("\n⚠ No interview files found!")
        print(f"   Looking in: {Path(__file__).parent / 'ingestion' / 'bucket2_survey_interviews' / '11_labs_interviews'}")
        return
    
    print(f"\n📁 Found {len(interview_files)} interview file(s)")
    
    # Storage directory
    storage_dir = Path(__file__).parent / "storage_data"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    total_records = 0
    
    for interview_file in interview_files:
        try:
            print(f"\n📄 Processing: {interview_file.name}")
            
            # Read file
            with open(interview_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            # Chunk by User responses
            chunks = chunk_by_user_responses(full_text)
            
            if not chunks:
                print(f"   ⚠ No User responses found, skipping")
                continue
            
            print(f"   ✓ Found {len(chunks)} User response chunks")
            
            # Create records
            parent_record_id = None
            file_records = []
            
            for chunk_idx, chunk_text in enumerate(chunks):
                record = DataRecord(
                    bucket_id=BucketType.SURVEYS_INTERVIEWS.value,
                    source_name="11_labs_interviews",
                    source_type=SourceType.TXT.value,
                    raw_text=chunk_text,
                    chunk_index=chunk_idx,
                    parent_record_id=parent_record_id,
                    metadata={
                        'survey_name': interview_file.stem,
                        'file_path': str(interview_file),
                        'total_chunks': len(chunks),
                        'chunked_by': 'user_responses',
                    }
                )
                
                # Set parent_record_id for first chunk
                if chunk_idx == 0:
                    parent_record_id = record.record_id
                
                # Save record
                save_record(record, storage_dir)
                file_records.append(record)
            
            total_records += len(file_records)
            print(f"   ✓ Created {len(file_records)} records")
            
        except Exception as e:
            print(f"   ✗ Error processing {interview_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"✓ COMPLETE: Created {total_records} total records")
    print(f"  Records saved to: {storage_dir / 'raw' / 'records'}")
    print(f"\n  Next step: Run indexing (with or without embeddings)")
    print(f"  python3 Data_Engine/ingest_all_buckets.py --no-embeddings")


if __name__ == "__main__":
    main()

