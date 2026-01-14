"""
Comprehensive ingestion script for all buckets (1-4)

This script:
1. Ingests Bucket 1: Online datasets (CSV files)
2. Ingests Bucket 2: Surveys & Interviews (CSV surveys + TXT interviews including 11 Labs)
3. Ingests Bucket 3: Financial data (CSV files)
4. Ingests Bucket 4: Scraped data (if available)
5. Verifies all data is indexed and retrievable

Performance optimizations:
- Batch embedding generation (much faster than one-by-one)
- Option to skip embeddings for faster indexing (metadata-only)
- Progress indicators for long-running operations
"""

from pathlib import Path
import sys
from typing import List, Dict, Any
from collections import defaultdict

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.data_engine import DataEngine
from Data_Engine.core.schema import DataRecord

# Optional: sentence-transformers for semantic search
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


def find_11labs_interview_files() -> List[Path]:
    """Find all 11 Labs interview TXT files"""
    interview_dir = Path(__file__).parent / "ingestion" / "bucket2_survey_interviews" / "11_labs_interviews"
    
    if not interview_dir.exists():
        print(f"⚠ 11 Labs interview directory not found: {interview_dir}")
        return []
    
    # Find all .txt files
    txt_files = sorted(interview_dir.glob("*.txt"))
    
    # Filter out non-interview files (like README, scripts, etc.)
    interview_files = [f for f in txt_files if f.name.startswith("Interview") or f.name.isdigit()]
    
    return interview_files


def ingest_bucket1(engine: DataEngine) -> List[DataRecord]:
    """Ingest Bucket 1: Online datasets"""
    print("\n" + "=" * 70)
    print("BUCKET 1: Online Datasets")
    print("=" * 70)
    
    records = []
    
    # Phase 1 menu data
    phase1_data_dir = parent_dir / "Anchored_LPM" / "P1_Taste_Embedding_Model" / "data" / "raw"
    if phase1_data_dir.exists():
        csv_files = list(phase1_data_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                print(f"\n  📄 Ingesting: {csv_file.name}")
                file_records = list(engine.ingest_online_dataset(
                    file_path=csv_file,
                    source_name=f"phase1_{csv_file.stem}",
                    text_columns=None,  # Auto-detect
                    brand_column=None
                ))
                records.extend(file_records)
                print(f"     ✓ Created {len(file_records)} records")
            except Exception as e:
                print(f"     ✗ Error: {e}")
    
    # Online datasets folder
    online_data_dir = Path(__file__).parent / "ingestion" / "bucket1_online_datasets" / "food_online_data"
    if online_data_dir.exists():
        csv_files = list(online_data_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                print(f"\n  📄 Ingesting: {csv_file.name}")
                file_records = list(engine.ingest_online_dataset(
                    file_path=csv_file,
                    source_name=f"online_{csv_file.stem}",
                    text_columns=None,  # Auto-detect
                    brand_column=None
                ))
                records.extend(file_records)
                print(f"     ✓ Created {len(file_records)} records")
            except Exception as e:
                print(f"     ✗ Error: {e}")
    
    print(f"\n  ✓ Bucket 1: Total {len(records)} records")
    return records


def ingest_bucket2(engine: DataEngine) -> List[DataRecord]:
    """Ingest Bucket 2: Surveys & Interviews (including 11 Labs)"""
    print("\n" + "=" * 70)
    print("BUCKET 2: Surveys & Interviews")
    print("=" * 70)
    
    records = []
    
    # 1. CSV Survey files
    survey_dir = Path(__file__).parent / "ingestion" / "bucket2_survey_interviews" / "survey_interviews"
    if survey_dir.exists():
        csv_files = list(survey_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                print(f"\n  📄 Ingesting survey: {csv_file.name}")
                file_records = list(engine.ingest_survey(
                    file_path=csv_file,
                    source_name=f"survey_{csv_file.stem}",
                    brand_column=None
                ))
                records.extend(file_records)
                print(f"     ✓ Created {len(file_records)} records")
            except Exception as e:
                print(f"     ✗ Error: {e}")
    
    # 2. 11 Labs Interview files (CRITICAL)
    print("\n  🎤 11 Labs Interviews:")
    interview_files = find_11labs_interview_files()
    
    if not interview_files:
        print("     ⚠ No 11 Labs interview files found!")
    else:
        print(f"     Found {len(interview_files)} interview file(s)")
        
        for interview_file in interview_files:
            try:
                print(f"\n     📄 Ingesting: {interview_file.name}")
                # Use source_name that identifies it as 11 labs
                file_records = list(engine.ingest_survey(
                    file_path=interview_file,
                    source_name="11_labs_interviews",  # Consistent source name
                    chunk_size=1000,  # Chunk long interviews
                    chunk_overlap=200
                ))
                records.extend(file_records)
                print(f"        ✓ Created {len(file_records)} chunked records")
            except Exception as e:
                print(f"        ✗ Error ingesting {interview_file.name}: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n  ✓ Bucket 2: Total {len(records)} records")
    return records


def ingest_bucket3(engine: DataEngine) -> List[DataRecord]:
    """Ingest Bucket 3: Financial data"""
    print("\n" + "=" * 70)
    print("BUCKET 3: Financial Data")
    print("=" * 70)
    
    records = []
    
    # Check for financial data files
    # Note: Bucket 3 typically requires client_id
    # You may need to adjust this based on your actual financial data location
    
    print("  ℹ Bucket 3 ingestion requires client_id and specific file structure")
    print("  ℹ Skipping for now (no files configured)")
    
    return records


def ingest_bucket4(engine: DataEngine) -> List[DataRecord]:
    """Ingest Bucket 4: Scraped data"""
    print("\n" + "=" * 70)
    print("BUCKET 4: Scraped Public Data")
    print("=" * 70)
    
    records = []
    
    # Check for scraped data CSV files
    scrapers_dir = Path(__file__).parent / "ingestion" / "bucket4_scrapers"
    
    # Look for processed CSV files in scraper subdirectories
    processed_files = []
    if scrapers_dir.exists():
        for subdir in scrapers_dir.iterdir():
            if subdir.is_dir():
                csv_files = list(subdir.glob("processed_*.csv"))
                processed_files.extend(csv_files)
    
    if processed_files:
        for csv_file in processed_files:
            try:
                print(f"\n  📄 Ingesting scraped data: {csv_file.name}")
                # Treat scraped CSVs as online datasets (Bucket 1) or surveys (Bucket 2)
                # depending on structure. For now, treat as online dataset
                file_records = list(engine.ingest_online_dataset(
                    file_path=csv_file,
                    source_name=f"scraped_{csv_file.parent.name}",
                    text_columns=None,
                    brand_column=None
                ))
                records.extend(file_records)
                print(f"     ✓ Created {len(file_records)} records")
            except Exception as e:
                print(f"     ✗ Error: {e}")
    else:
        print("  ℹ No processed scraped data files found")
    
    print(f"\n  ✓ Bucket 4: Total {len(records)} records")
    return records


def verify_indexed_data(engine: DataEngine, all_records: List[DataRecord]):
    """Verify that data is indexed and retrievable"""
    print("\n" + "=" * 70)
    print("VERIFICATION: Checking Indexed Data")
    print("=" * 70)
    
    # Group records by bucket
    by_bucket = defaultdict(list)
    by_source = defaultdict(list)
    
    for record in all_records:
        by_bucket[record.bucket_id].append(record)
        by_source[record.source_name].append(record)
    
    # Check each bucket
    print("\n📊 Records by Bucket:")
    for bucket_id in sorted(by_bucket.keys()):
        count = len(by_bucket[bucket_id])
        print(f"  Bucket {bucket_id}: {count} records")
    
    # Check 11 Labs specifically
    print("\n🎤 11 Labs Interview Records:")
    if "11_labs_interviews" in by_source:
        count = len(by_source["11_labs_interviews"])
        print(f"  ✓ Found {count} records from source '11_labs_interviews'")
        
        # Try to retrieve them
        try:
            retrieved = engine.get_by_filters({"source_name": "11_labs_interviews"})
            print(f"  ✓ Successfully retrieved {len(retrieved)} records from index")
            
            if retrieved:
                sample = retrieved[0]
                print(f"\n  Sample record:")
                print(f"    ID: {sample.record_id}")
                print(f"    Bucket: {sample.bucket_id}")
                print(f"    Source: {sample.source_name}")
                print(f"    Text preview: {sample.raw_text[:200] if sample.raw_text else 'N/A'}...")
                if sample.metadata:
                    print(f"    File: {sample.metadata.get('file_path', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Error retrieving records: {e}")
    else:
        print("  ✗ No records found with source_name '11_labs_interviews'")
    
    # Try bucket 2 query
    print("\n📋 Bucket 2 Records:")
    try:
        bucket2_records = engine.get_by_bucket(2)
        print(f"  ✓ Retrieved {len(bucket2_records)} records from Bucket 2")
        
        # Count 11 labs in bucket 2
        eleven_labs_count = sum(1 for r in bucket2_records if r.source_name == "11_labs_interviews")
        print(f"  ✓ {eleven_labs_count} of these are from 11 Labs")
    except Exception as e:
        print(f"  ✗ Error querying Bucket 2: {e}")


def main():
    """Main ingestion function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest all buckets into Data Engine')
    parser.add_argument('--no-embeddings', action='store_true', 
                       help='Skip embedding generation for faster indexing (metadata-only)')
    parser.add_argument('--batch-size', type=int, default=5000,
                       help='Batch size for indexing (default: 5000)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("COMPREHENSIVE DATA ENGINE INGESTION")
    print("All Buckets (1-4) including 11 Labs Interviews")
    print("=" * 70)
    
    # Initialize engine
    storage_dir = Path(__file__).parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings (optional)
    encoder = None
    if args.no_embeddings:
        print("\n⚡ Fast mode: Skipping embedding generation")
        print("   (Use without --no-embeddings to enable semantic search)")
    elif SENTENCE_TRANSFORMERS_AVAILABLE:
        print("\n📦 Loading embedding model...")
        try:
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            engine.set_embedding_fn(lambda text: encoder.encode(text))
            print("✓ Model loaded - semantic search enabled")
            print("   (Use --no-embeddings flag for faster indexing without embeddings)")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
            print("Continuing without semantic search...")
    else:
        print("\n⚠ sentence-transformers not installed.")
        print("   Install with: pip install sentence-transformers")
        print("   Continuing without semantic search (structured queries only)...")
    
    # Ingest all buckets
    all_records = []
    
    # Bucket 1
    bucket1_records = ingest_bucket1(engine)
    all_records.extend(bucket1_records)
    
    # Bucket 2 (includes 11 Labs)
    bucket2_records = ingest_bucket2(engine)
    all_records.extend(bucket2_records)
    
    # Bucket 3
    bucket3_records = ingest_bucket3(engine)
    all_records.extend(bucket3_records)
    
    # Bucket 4
    bucket4_records = ingest_bucket4(engine)
    all_records.extend(bucket4_records)
    
    if not all_records:
        print("\n✗ No records were ingested. Check errors above.")
        return
    
    # Index all records
    print("\n" + "=" * 70)
    print(f"INDEXING: {len(all_records)} total records")
    if encoder:
        print("  Mode: With embeddings (semantic search enabled)")
    else:
        print("  Mode: Metadata-only (no embeddings)")
    print("=" * 70)
    
    BATCH_SIZE = args.batch_size
    total_batches = (len(all_records) + BATCH_SIZE - 1) // BATCH_SIZE
    
    try:
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(all_records))
            batch_records = all_records[start_idx:end_idx]
            
            print(f"\nProcessing batch {batch_num + 1}/{total_batches} "
                  f"(records {start_idx + 1}-{end_idx} of {len(all_records)})...")
            
            # Generate embeddings in batch (MUCH faster than one-by-one)
            embeddings = None
            if encoder:
                import numpy as np
                print(f"  Generating embeddings for {len(batch_records)} records...")
                # Collect all texts first
                texts = []
                text_indices = []
                for i, record in enumerate(batch_records):
                    text = record.get_text_for_embedding()
                    if text:
                        texts.append(text)
                        text_indices.append(i)
                
                # Batch encode all texts at once (much faster!)
                if texts:
                    # Use batch encoding - sentence-transformers handles batching internally
                    # but we can also do explicit batching for very large sets
                    EMBEDDING_BATCH_SIZE = 64  # Process 64 texts at a time
                    batch_embeddings = []
                    
                    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
                        batch_texts = texts[i:i+EMBEDDING_BATCH_SIZE]
                        batch_emb = encoder.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)
                        batch_embeddings.append(batch_emb)
                    
                    # Combine all embeddings
                    all_embeddings = np.vstack(batch_embeddings) if batch_embeddings else np.array([])
                    
                    # Create full embeddings array (with zeros for records without text)
                    embeddings = np.zeros((len(batch_records), encoder.get_sentence_embedding_dimension()))
                    for emb_idx, record_idx in enumerate(text_indices):
                        embeddings[record_idx] = all_embeddings[emb_idx]
                        batch_records[record_idx].embedding = all_embeddings[emb_idx].tolist()
                    
                    print(f"  ✓ Generated {len(texts)} embeddings")
                else:
                    # No texts, create zero embeddings
                    embeddings = np.zeros((len(batch_records), encoder.get_sentence_embedding_dimension()))
            
            # Index batch (pass embeddings directly to avoid re-generating)
            print(f"  Indexing batch...")
            if embeddings is not None:
                # Pass embeddings directly to avoid re-generation
                engine.index_manager.index_batch(batch_records, embeddings)
            else:
                # No embeddings, just index metadata
                engine.index_records(
                    batch_records,
                    generate_embeddings=False,  # Don't generate embeddings again
                    enrich_text=True
                )
            
            print(f"✓ Batch {batch_num + 1}/{total_batches} indexed")
        
        print("\n✓ All records indexed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠ Indexing interrupted by user.")
        return
    except Exception as e:
        print(f"\n✗ Error indexing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify indexed data
    verify_indexed_data(engine, all_records)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Ingested {len(all_records)} total records")
    print(f"✓ Storage location: {storage_dir}")
    
    # Count 11 Labs records
    eleven_labs_count = sum(1 for r in all_records if r.source_name == "11_labs_interviews")
    print(f"✓ 11 Labs interview records: {eleven_labs_count}")
    
    if encoder:
        print("✓ Semantic search enabled")
    else:
        print("⚠ Semantic search disabled (install sentence-transformers to enable)")
    
    print("\n" + "=" * 70)
    print("✅ INGESTION COMPLETE!")
    print("=" * 70)
    print("\nYou can now query the data:")
    print("  # Get 11 Labs interviews:")
    print("  records = engine.get_by_filters({'source_name': '11_labs_interviews'})")
    print("  # Get all Bucket 2 records:")
    print("  records = engine.get_by_bucket(2)")
    if encoder:
        print("  # Semantic search:")
        print("  results = engine.search('consumer preferences', top_k=10)")


if __name__ == "__main__":
    main()

