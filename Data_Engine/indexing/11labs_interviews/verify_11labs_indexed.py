"""
Verification script to check if 11 Labs interview data is indexed and retrievable
"""

from pathlib import Path
import sys

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

from Data_Engine.data_engine import DataEngine


def main():
    """Verify 11 Labs data is indexed"""
    print("=" * 70)
    print("VERIFYING 11 LABS INTERVIEW DATA IN INDEX")
    print("=" * 70)
    
    # Initialize engine
    storage_dir = Path(__file__).parent.parent.parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Check 1: Query by source_name
    print("\n1. Querying by source_name='11_labs_interviews':")
    try:
        records = engine.get_by_filters({"source_name": "11_labs_interviews"})
        print(f"   ✓ Found {len(records)} records")
        
        if records:
            print(f"\n   Sample records:")
            for i, record in enumerate(records[:5], 1):
                print(f"   {i}. Record ID: {record.record_id}")
                print(f"      Bucket: {record.bucket_id}")
                print(f"      Source: {record.source_name}")
                print(f"      File: {record.metadata.get('file_path', 'N/A') if record.metadata else 'N/A'}")
                print(f"      Text preview: {record.raw_text[:150] if record.raw_text else 'N/A'}...")
                print()
        else:
            print("   ✗ No records found!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 2: Query Bucket 2 and filter for 11 labs
    print("\n2. Querying Bucket 2 (Surveys & Interviews):")
    try:
        bucket2_records = engine.get_by_bucket(2)
        print(f"   ✓ Found {len(bucket2_records)} total records in Bucket 2")
        
        eleven_labs_records = [r for r in bucket2_records if r.source_name == "11_labs_interviews"]
        print(f"   ✓ Found {len(eleven_labs_records)} records from 11 Labs")
        
        if eleven_labs_records:
            # Group by file
            by_file = {}
            for record in eleven_labs_records:
                file_path = record.metadata.get('file_path', 'unknown') if record.metadata else 'unknown'
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(record)
            
            print(f"\n   Files indexed:")
            for file_path, file_records in sorted(by_file.items()):
                print(f"   - {Path(file_path).name}: {len(file_records)} chunks")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 3: Check storage directly
    print("\n3. Checking storage directory:")
    storage_path = storage_dir / "raw" / "records"
    if storage_path.exists():
        record_files = list(storage_path.glob("*.json"))
        print(f"   ✓ Found {len(record_files)} record files in storage")
        
        # Check metadata index
        metadata_path = storage_dir / "metadata" / "metadata_index.json"
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Count 11 labs records in metadata
            eleven_labs_in_meta = []
            if 'records' in metadata:
                for record_id, record_meta in metadata['records'].items():
                    if record_meta.get('source_name') == '11_labs_interviews':
                        eleven_labs_in_meta.append(record_id)
            
            print(f"   ✓ Found {len(eleven_labs_in_meta)} 11 Labs records in metadata index")
        else:
            print("   ⚠ Metadata index not found")
    else:
        print("   ⚠ Storage directory not found")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    try:
        records = engine.get_by_filters({"source_name": "11_labs_interviews"})
        if records:
            print("✅ 11 Labs interview data IS indexed and retrievable")
            print(f"   Total records: {len(records)}")
        else:
            print("❌ 11 Labs interview data is NOT indexed")
            print("   Run: python ingest_all_buckets.py")
    except Exception as e:
        print(f"❌ Error during verification: {e}")


if __name__ == "__main__":
    main()

