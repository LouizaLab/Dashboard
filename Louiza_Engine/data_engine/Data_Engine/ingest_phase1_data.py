"""
Unified script to ingest online datasets into Data Engine (Bucket 1)

This script ingests CSV files from:
1. Phase 1 menu data (Phase_1_Taste_Embedding_Model/data/raw/)
2. Online datasets folder (Data_Engine/ingestion/bucket1_online_datasets/online_data/)

All data goes into Bucket 1 (Online Datasets).
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.data_engine import DataEngine

# Optional: sentence-transformers for semantic search
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


def main():
    """Ingest all online datasets into Data Engine"""
    
    print("=" * 60)
    print("Ingesting Online Datasets into Data Engine (Bucket 1)")
    print("=" * 60)
    
    # Initialize engine
    storage_dir = Path(__file__).parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings (optional)
    encoder = None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("\nLoading embedding model...")
        try:
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            engine.set_embedding_fn(lambda text: encoder.encode(text))
            print("✓ Model loaded - semantic search enabled")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
            print("Continuing without semantic search...")
    else:
        print("\n⚠ sentence-transformers not installed.")
        print("   Install with: pip install sentence-transformers")
        print("   Continuing without semantic search (structured queries only)...")
    
    # Collect CSV files from multiple sources
    all_csv_files = []
    
    # 1. Phase 1 menu data
    phase1_data_dir = Path(__file__).parent.parent / "Phase_1_Taste_Embedding_Model" / "data" / "raw"
    if phase1_data_dir.exists():
        phase1_files = list(phase1_data_dir.glob("*.csv"))
        if phase1_files:
            print(f"\nFound {len(phase1_files)} Phase 1 menu file(s):")
            for f in phase1_files:
                print(f"  - {f.name} (Phase 1)")
            all_csv_files.extend([(f, "phase1") for f in phase1_files])
    else:
        print(f"\n⚠ Phase 1 data directory not found: {phase1_data_dir}")
        print("   Skipping Phase 1 menu data...")
    
    # 2. Online datasets folder
    online_data_dir = Path(__file__).parent / "ingestion" / "bucket1_online_datasets" / "online_data"
    if online_data_dir.exists():
        online_files = list(online_data_dir.glob("*.csv"))
        if online_files:
            print(f"\nFound {len(online_files)} online dataset file(s):")
            for f in online_files:
                print(f"  - {f.name} (Online datasets)")
            all_csv_files.extend([(f, "online") for f in online_files])
    else:
        print(f"\n⚠ Online data directory not found: {online_data_dir}")
        print("   Skipping online datasets...")
    
    if not all_csv_files:
        print("\n✗ No CSV files found in any location!")
        print("\nTo add data:")
        print("  1. Place menu CSVs in: Phase_1_Taste_Embedding_Model/data/raw/")
        print("  2. Place online datasets in: Data_Engine/ingestion/bucket1_online_datasets/online_data/")
        return
    
    print(f"\n{'='*60}")
    print(f"Total: {len(all_csv_files)} CSV file(s) to ingest")
    print(f"{'='*60}")
    
    # Configuration for Phase 1 menu files (you can customize these)
    phase1_configs = {
        "mcdonalds.csv": {
            "source_name": "mcdonalds_menu",
            "text_columns": ["Item", "Category"],
            "brand_column": "Item"
        },
        "burger-king-menu.csv": {
            "source_name": "burger_king_menu",
            "text_columns": ["ITEM", "CATEGORY"],
            "brand_column": "ITEM"
        },
        "wendys-menu.csv": {
            "source_name": "wendys_menu",
            "text_columns": ["Item", "Category"],
            "brand_column": "Item"
        },
        "mcd.csv": {
            "source_name": "mcd_menu_alt",
            "text_columns": ["Item", "Category"],
            "brand_column": "Item"
        }
    }
    
    # Configuration for online datasets (common patterns)
    online_configs = {
        "English dataset.csv": {
            "source_name": "kaggle_english_tweets",
            "text_columns": ["orjinaltweet", "editedtweet"],
            "brand_column": "marka_type"
        }
    }
    
    all_records = []
    
    # Ingest each file
    for csv_file, file_type in all_csv_files:
        filename = csv_file.name
        print(f"\n{'='*60}")
        print(f"Ingesting: {filename} ({file_type})")
        print(f"{'='*60}")
        
        # Get config based on file type
        if file_type == "phase1":
            config = phase1_configs.get(filename, {
                "source_name": filename.replace(".csv", "").replace("-", "_"),
                "text_columns": None,  # Auto-detect
                "brand_column": None
            })
        else:  # online
            config = online_configs.get(filename, {
                "source_name": filename.replace(".csv", "").replace("-", "_").replace(" ", "_"),
                "text_columns": None,  # Auto-detect
                "brand_column": None
            })
        
        try:
            records = engine.ingest_online_dataset(
                file_path=csv_file,
                source_name=config["source_name"],
                text_columns=config.get("text_columns"),
                brand_column=config.get("brand_column")
            )
            
            records_list = list(records)
            print(f"✓ Created {len(records_list)} records")
            all_records.extend(records_list)
            
        except Exception as e:
            print(f"✗ Error ingesting {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    if not all_records:
        print("\n✗ No records were ingested. Check errors above.")
        return
    
    # Index all records in batches with progress
    print(f"\n{'='*60}")
    print(f"Indexing {len(all_records)} total records...")
    print(f"{'='*60}")
    
    # For large datasets, process in batches to show progress
    BATCH_SIZE = 5000  # Process 5k records at a time
    total_batches = (len(all_records) + BATCH_SIZE - 1) // BATCH_SIZE
    
    try:
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(all_records))
            batch_records = all_records[start_idx:end_idx]
            
            print(f"\nProcessing batch {batch_num + 1}/{total_batches} "
                  f"(records {start_idx + 1}-{end_idx} of {len(all_records)})...")
            
            # For very large datasets, skip text enrichment to speed things up
            # Text enrichment can be done later if needed
            enrich_text = len(all_records) < 50000  # Only enrich if < 50k records
            
            engine.index_records(
                batch_records,
                generate_embeddings=(encoder is not None),
                enrich_text=enrich_text
            )
            
            print(f"✓ Batch {batch_num + 1}/{total_batches} indexed "
                  f"({end_idx}/{len(all_records)} records)")
        
        print("\n✓ All records indexed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠ Indexing interrupted by user.")
        print(f"   Progress: {len(all_records)} records ingested, "
              f"but indexing was incomplete.")
        print("   You can re-run this script - it will skip already-ingested records.")
        return
    except Exception as e:
        print(f"✗ Error indexing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"✓ Ingested {len(all_records)} records from {len(all_csv_files)} file(s)")
    print(f"✓ Storage location: {storage_dir}")
    
    if encoder:
        print("✓ Semantic search enabled")
        print("\nYou can now search with:")
        print("  results = engine.search('burger', top_k=10)")
    else:
        print("⚠ Semantic search disabled (install sentence-transformers to enable)")
        print("\nYou can still query with:")
        print("  results = engine.get_by_brand('McDonald\\'s')")
        print("  results = engine.get_by_filters({'source_name': 'mcdonalds_menu'})")
    
    print(f"\n{'='*60}")
    print("Done! Your online datasets are now in the Data Engine.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

