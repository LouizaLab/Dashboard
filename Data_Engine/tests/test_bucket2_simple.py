#!/usr/bin/env python3
"""
Simple test for Bucket 2: Surveys & Interviews Ingestion

Run this script to test the Bucket 2 ingestion functionality.
Make sure you're in the Consumer_Engine directory when running.

Usage:
    python3 test_bucket2_simple.py
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test that we can import the ingester"""
    try:
        from .ingestion.bucket2_surveys_interviews import SurveysInterviewsIngester
        print("✓ Import successful")
        return SurveysInterviewsIngester
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_basic_usage():
    """Test basic usage"""
    ingester_class = test_import()
    if not ingester_class:
        return
    
    print("\n" + "=" * 60)
    print("Testing Basic Usage")
    print("=" * 60)
    
    # Create instance
    try:
        ingester = ingester_class(
            source_name="test_survey",
            survey_name="Test Survey"
        )
        print(f"✓ Created ingester instance")
        print(f"  Bucket ID: {ingester.bucket_id}")
        print(f"  Source Name: {ingester.source_name}")
        print(f"  Survey Name: {ingester.survey_name}")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test file validation
    csv_file = project_root / "Data_Engine/ingestion/bucket2_survey_interviews/survey_interviews/Chipotle Survey (Responses) - Form Responses 1.csv"
    
    if csv_file.exists():
        print(f"\n✓ CSV file exists: {csv_file.name}")
        
        try:
            is_valid = ingester.validate_file(csv_file)
            print(f"✓ File validation: {is_valid}")
            
            if is_valid:
                print("\n🔄 Testing ingestion (first 3 records only)...")
                records = []
                for i, record in enumerate(ingester.ingest(csv_file)):
                    records.append(record)
                    if i >= 2:  # Only get first 3
                        break
                
                print(f"✓ Successfully ingested {len(records)} records (showing first 3)")
                
                if records:
                    rec = records[0]
                    print(f"\n📊 First Record:")
                    print(f"   Record ID: {rec.record_id[:20]}...")
                    print(f"   Bucket: {rec.bucket_id}")
                    print(f"   Source: {rec.source_name}")
                    print(f"   Raw Text Length: {len(rec.raw_text) if rec.raw_text else 0} chars")
                    print(f"   Structured Fields: {len(rec.structured_fields)}")
                    print(f"   Numerical Fields: {len(rec.numerical_fields)}")
                    print(f"   Categorical Fields: {len(rec.categorical_fields)}")
                    
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n⚠️  CSV file not found: {csv_file}")

if __name__ == "__main__":
    test_basic_usage()
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

