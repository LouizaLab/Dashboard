"""
Test script for Bucket 2: Surveys & Interviews Ingestion
"""
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from Data_Engine.ingestion import SurveysInterviewsIngester

def test_csv_ingestion():
    """Test CSV survey file ingestion"""
    print("=" * 70)
    print("Testing Bucket 2: Surveys & Interviews Ingestion")
    print("=" * 70)
    
    # Path to survey CSV files
    survey_dir = Path("Data_Engine/ingestion/bucket2_survey_interviews/survey_interviews")
    
    # Test with Chipotle Survey
    csv_file = survey_dir / "Chipotle Survey (Responses) - Form Responses 1.csv"
    
    if not csv_file.exists():
        print(f"❌ File not found: {csv_file}")
        return
    
    print(f"\n📄 Testing with: {csv_file.name}")
    print(f"   Path: {csv_file}")
    
    # Initialize ingester
    ingester = SurveysInterviewsIngester(
        source_name="chipotle_survey",
        survey_name="Chipotle Consumer Survey"
    )
    
    # Validate file
    if not ingester.validate_file(csv_file):
        print("❌ File validation failed")
        return
    
    print("✓ File validation passed")
    
    # Ingest records
    print("\n🔄 Ingesting records...")
    records = list(ingester.ingest(csv_file))
    
    print(f"✓ Successfully ingested {len(records)} records")
    
    if records:
        # Show first record details
        first_record = records[0]
        print("\n📊 First Record Details:")
        print(f"   Record ID: {first_record.record_id}")
        print(f"   Bucket ID: {first_record.bucket_id}")
        print(f"   Source: {first_record.source_name}")
        print(f"   Source Type: {first_record.source_type}")
        print(f"   Brand: {first_record.brand}")
        print(f"   Raw Text Length: {len(first_record.raw_text) if first_record.raw_text else 0} chars")
        print(f"   Structured Fields: {len(first_record.structured_fields)}")
        print(f"   Numerical Fields: {len(first_record.numerical_fields)}")
        print(f"   Categorical Fields: {len(first_record.categorical_fields)}")
        print(f"   Metadata: {first_record.metadata}")
        
        # Show sample of structured fields
        if first_record.structured_fields:
            print("\n   Sample Structured Fields:")
            for key, value in list(first_record.structured_fields.items())[:3]:
                print(f"      {key}: {str(value)[:50]}...")
        
        # Show sample of categorical fields
        if first_record.categorical_fields:
            print("\n   Sample Categorical Fields:")
            for key, value in list(first_record.categorical_fields.items())[:3]:
                print(f"      {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ Bucket 2 ingestion test completed successfully!")
    print("=" * 70)
    
    return records

def test_txt_ingestion():
    """Test TXT interview file ingestion"""
    print("\n" + "=" * 70)
    print("Testing TXT Interview Ingestion")
    print("=" * 70)
    
    # Path to interview TXT files
    interview_dir = Path("Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews")
    
    # Test with first interview
    txt_file = interview_dir / "Interview1.txt"
    
    if not txt_file.exists():
        print(f"❌ File not found: {txt_file}")
        return
    
    print(f"\n📄 Testing with: {txt_file.name}")
    print(f"   Path: {txt_file}")
    
    # Initialize ingester
    ingester = SurveysInterviewsIngester(
        source_name="11_labs_interviews",
        survey_name="Interview1"
    )
    
    # Validate file
    if not ingester.validate_file(txt_file):
        print("❌ File validation failed")
        return
    
    print("✓ File validation passed")
    
    # Ingest records (with chunking)
    print("\n🔄 Ingesting and chunking interview...")
    records = list(ingester.ingest(txt_file, chunk_size=1000, chunk_overlap=200))
    
    print(f"✓ Successfully chunked into {len(records)} records")
    
    if records:
        first_record = records[0]
        print("\n📊 First Chunk Details:")
        print(f"   Record ID: {first_record.record_id}")
        print(f"   Chunk Index: {first_record.chunk_index}")
        print(f"   Text Length: {len(first_record.raw_text)} chars")
        print(f"   Total Chunks: {first_record.metadata.get('total_chunks', 'N/A')}")
        print(f"   Sample Text: {first_record.raw_text[:200]}...")
    
    print("\n" + "=" * 70)
    print("✅ TXT ingestion test completed successfully!")
    print("=" * 70)
    
    return records

if __name__ == "__main__":
    try:
        # Test CSV ingestion
        csv_records = test_csv_ingestion()
        
        # Test TXT ingestion
        txt_records = test_txt_ingestion()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

