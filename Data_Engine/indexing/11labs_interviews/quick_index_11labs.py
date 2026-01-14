"""
Quick indexing script for 11 Labs interviews ONLY
Skips embeddings for maximum speed - indexes metadata only
"""

from pathlib import Path
import sys
import time

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

from Data_Engine.data_engine import DataEngine


def main():
    """Quick index 11 Labs interviews without embeddings"""
    print("=" * 70)
    print("QUICK INDEX: 11 Labs Interviews (Metadata Only)")
    print("=" * 70)
    print("\n⚡ Fast mode: Skipping embeddings for speed")
    print("   (Data will be indexed but semantic search won't work)")
    print("   (You can still query by source_name, bucket, filters)\n")
    
    # Initialize engine
    storage_dir = Path(__file__).parent.parent.parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Find interview files
    interview_dir = Path(__file__).parent.parent.parent / "ingestion" / "bucket2_survey_interviews" / "11_labs_interviews"
    
    if not interview_dir.exists():
        print(f"❌ Interview directory not found: {interview_dir}")
        return
    
    # Find all interview TXT files
    interview_files = sorted([
        f for f in interview_dir.glob("*.txt")
        if f.name.startswith("Interview") or f.name.isdigit()
    ])
    
    if not interview_files:
        print(f"❌ No interview files found in {interview_dir}")
        return
    
    print(f"📁 Found {len(interview_files)} interview file(s)\n")
    
    # Ingest all interviews
    all_records = []
    start_time = time.time()
    
    for i, interview_file in enumerate(interview_files, 1):
        print(f"[{i}/{len(interview_files)}] Ingesting: {interview_file.name}...", end=" ")
        
        try:
            records = list(engine.ingest_survey(
                file_path=interview_file,
                source_name="11_labs_interviews",
                chunk_size=1000,
                chunk_overlap=200
            ))
            all_records.extend(records)
            print(f"✓ {len(records)} chunks")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    ingest_time = time.time() - start_time
    print(f"\n✓ Ingested {len(all_records)} total records in {ingest_time:.1f}s")
    
    if not all_records:
        print("\n❌ No records to index!")
        return
    
    # Index WITHOUT embeddings (fast!)
    print(f"\n📦 Indexing {len(all_records)} records (no embeddings)...")
    index_start = time.time()
    
    try:
        # Index in smaller batches for progress visibility
        BATCH_SIZE = 1000
        total_batches = (len(all_records) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(all_records))
            batch_records = all_records[start_idx:end_idx]
            
            engine.index_records(
                batch_records,
                generate_embeddings=False,  # NO EMBEDDINGS = FAST!
                enrich_text=True  # Still clean text
            )
            
            print(f"  ✓ Batch {batch_num + 1}/{total_batches} indexed ({end_idx}/{len(all_records)} records)")
        
        index_time = time.time() - index_start
        total_time = time.time() - start_time
        
        print(f"\n✅ Indexing complete!")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Records indexed: {len(all_records)}")
        print(f"   Average: {total_time/len(all_records)*1000:.1f}ms per record")
        
    except Exception as e:
        print(f"\n❌ Error indexing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify
    print("\n🔍 Verifying indexed data...")
    try:
        retrieved = engine.get_by_filters({"source_name": "11_labs_interviews"})
        print(f"✅ Successfully retrieved {len(retrieved)} records from index")
        
        if retrieved:
            print(f"\n📊 Sample record:")
            sample = retrieved[0]
            print(f"   ID: {sample.record_id}")
            print(f"   Source: {sample.source_name}")
            print(f"   Bucket: {sample.bucket_id}")
            print(f"   File: {Path(sample.metadata.get('file_path', 'N/A')).name if sample.metadata else 'N/A'}")
            print(f"   Text preview: {sample.raw_text[:100] if sample.raw_text else 'N/A'}...")
    except Exception as e:
        print(f"⚠ Verification error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ DONE! 11 Labs interviews are now indexed and retrievable")
    print("=" * 70)
    print("\nYou can query them with:")
    print("  records = engine.get_by_filters({'source_name': '11_labs_interviews'})")
    print("  records = engine.get_by_bucket(2)")


if __name__ == "__main__":
    main()

