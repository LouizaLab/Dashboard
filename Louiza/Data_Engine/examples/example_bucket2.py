"""
Example: Ingesting Surveys & Interviews (Bucket 2)

Demonstrates how to ingest CSV survey data and TXT interview files.
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.ingestion.bucket2_surveys_interviews import SurveysInterviewsIngester
from Data_Engine.indexing.index_manager import IndexManager
from Data_Engine.enrichment.text_cleaner import TextCleaner


def main():
    """Example ingestion for surveys and interviews"""
    
    storage_dir = Path(__file__).parent.parent / "storage_data"
    index_manager = IndexManager(storage_dir=storage_dir)
    text_cleaner = TextCleaner()
    
    # Example 1: Ingest CSV survey data
    print("Example 1: CSV Survey Data")
    ingester_csv = SurveysInterviewsIngester(
        source_name="customer_survey_2024",
        survey_name="food_preferences_survey"
    )
    
    # Create a sample CSV for demonstration
    sample_csv = Path(__file__).parent / "sample_survey.csv"
    if not sample_csv.exists():
        print(f"Creating sample survey CSV: {sample_csv}")
        import pandas as pd
        df = pd.DataFrame({
            'respondent_id': [1, 2, 3],
            'brand_preference': ['McDonald\'s', 'Burger King', 'Wendy\'s'],
            'rating': [4, 5, 3],
            'free_text': [
                'Love the Big Mac, always fresh',
                'Whopper is amazing, best burger',
                'Frosty is my favorite dessert'
            ]
        })
        df.to_csv(sample_csv, index=False)
    
    if sample_csv.exists():
        records = list(ingester_csv.ingest(sample_csv, brand_column="brand_preference"))
        print(f"Created {len(records)} survey records")
        
        enriched = text_cleaner.enrich_batch(records)
        index_manager.index_batch(enriched)
        print(f"✓ Indexed {len(enriched)} records")
    
    # Example 2: Ingest TXT interview file
    print("\nExample 2: TXT Interview File")
    ingester_txt = SurveysInterviewsIngester(
        source_name="customer_interview_2024",
        survey_name="qualitative_interviews"
    )
    
    sample_txt = Path(__file__).parent / "sample_interview.txt"
    if not sample_txt.exists():
        print(f"Creating sample interview TXT: {sample_txt}")
        with open(sample_txt, 'w') as f:
            f.write("""
            Interview with Customer A
            
            Q: What are your favorite fast food restaurants?
            A: I really enjoy McDonald's for breakfast items. Their Egg McMuffin is consistently good.
            I also like Burger King's Whopper, especially when I'm craving a larger burger.
            
            Q: What factors influence your choice?
            A: Convenience is key. I usually go to whatever is closest. But I also care about
            freshness and taste. Price matters too, especially for lunch.
            
            Q: Any brands you avoid?
            A: I tend to avoid places that feel unclean or have slow service. Brand reputation
            matters to me.
            """)
    
    if sample_txt.exists():
        records = list(ingester_txt.ingest(sample_txt, chunk_size=500, chunk_overlap=100))
        print(f"Created {len(records)} interview chunks")
        
        enriched = text_cleaner.enrich_batch(records)
        index_manager.index_batch(enriched)
        print(f"✓ Indexed {len(enriched)} chunks")


if __name__ == "__main__":
    main()

