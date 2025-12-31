"""
Simple script to ingest Phase 1 menu data into Data Engine

This script reads all CSV files from Phase_1_Taste_Embedding_Model/data/raw/
and ingests them into the Data Engine.
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
    """Ingest Phase 1 menu data into Data Engine"""
    
    print("=" * 60)
    print("Ingesting Phase 1 Menu Data into Data Engine")
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
    
    # Path to Phase 1 data
    phase1_data_dir = Path(__file__).parent.parent / "Phase_1_Taste_Embedding_Model" / "data" / "raw"
    
    if not phase1_data_dir.exists():
        print(f"\n✗ Error: Phase 1 data directory not found: {phase1_data_dir}")
        return
    
    print(f"\nLooking for CSV files in: {phase1_data_dir}")
    
    # Find all CSV files
    csv_files = list(phase1_data_dir.glob("*.csv"))
    
    if not csv_files:
        print("✗ No CSV files found!")
        return
    
    print(f"Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {f.name}")
    
    # Configuration for each file (you can customize these)
    file_configs = {
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
    
    all_records = []
    
    # Ingest each file
    for csv_file in csv_files:
        filename = csv_file.name
        print(f"\n{'='*60}")
        print(f"Ingesting: {filename}")
        print(f"{'='*60}")
        
        # Get config for this file, or use defaults
        config = file_configs.get(filename, {
            "source_name": filename.replace(".csv", "").replace("-", "_"),
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
    
    # Index all records
    print(f"\n{'='*60}")
    print(f"Indexing {len(all_records)} total records...")
    print(f"{'='*60}")
    
    try:
        engine.index_records(
            all_records,
            generate_embeddings=(encoder is not None),
            enrich_text=True
        )
        print("✓ All records indexed successfully!")
    except Exception as e:
        print(f"✗ Error indexing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"✓ Ingested {len(all_records)} records from {len(csv_files)} file(s)")
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
    print("Done! Your Phase 1 data is now in the Data Engine.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

