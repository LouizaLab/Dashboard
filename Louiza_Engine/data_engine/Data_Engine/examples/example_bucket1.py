"""
Example: Ingesting Online Datasets (Bucket 1)

Demonstrates how to ingest CSV files from online datasets.
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.ingestion.bucket1_online_datasets import OnlineDatasetsIngester
from Data_Engine.indexing.index_manager import IndexManager
from Data_Engine.enrichment.text_cleaner import TextCleaner
from Data_Engine.retrieval.retrieval_manager import RetrievalManager


def main():
    """Example ingestion and indexing pipeline"""
    
    # Setup paths
    data_dir = Path(__file__).parent.parent.parent / "Phase_1_Taste_Embedding_Model" / "data" / "raw"
    storage_dir = Path(__file__).parent.parent / "storage_data"
    
    # Initialize ingester
    ingester = OnlineDatasetsIngester(
        source_name="kaggle_food_reviews",
        dataset_name="food_preferences"
    )
    
    # Initialize index manager
    index_manager = IndexManager(storage_dir=storage_dir)
    
    # Initialize enrichment pipeline
    text_cleaner = TextCleaner()
    
    # Example: Ingest a CSV file
    csv_file = data_dir / "mcdonalds.csv"
    if csv_file.exists():
        print(f"Ingesting {csv_file}...")
        
        records = list(ingester.ingest(
            csv_file,
            text_columns=["Item", "Category", "Calories"],  # Specify text columns
            brand_column="Item",  # Use Item as brand identifier
        ))
        
        print(f"Created {len(records)} records")
        
        # Enrich records
        enriched_records = text_cleaner.enrich_batch(records)
        
        # Index records (without embeddings for now)
        print("Indexing records...")
        index_manager.index_batch(enriched_records)
        
        print(f"✓ Successfully indexed {len(enriched_records)} records")
        
        # Example retrieval
        retrieval_manager = RetrievalManager(index_manager)
        
        # Query by brand
        print("\nQuerying by brand...")
        brand_records = retrieval_manager.query_by_brand("Big Mac", limit=5)
        print(f"Found {len(brand_records)} records for 'Big Mac'")
        
        # Query by bucket
        print("\nQuerying by bucket...")
        bucket_records = retrieval_manager.query_by_bucket(bucket_id=1, limit=10)
        print(f"Found {len(bucket_records)} records in bucket 1")
    else:
        print(f"File not found: {csv_file}")


if __name__ == "__main__":
    main()

