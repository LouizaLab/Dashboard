"""
Example: Using Data Engine with your existing Phase 1 data

This shows how to ingest the McDonald's, Burger King, and Wendy's menu data
that you already have in Phase_1_Taste_Embedding_Model/data/raw/
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Now import from the package
from Data_Engine.data_engine import DataEngine

# Optional: sentence-transformers for semantic search
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


def main():
    """Ingest existing menu data"""
    
    print("=" * 60)
    print("Ingesting Existing Menu Data")
    print("=" * 60)
    
    # Initialize engine
    storage_dir = Path(__file__).parent.parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings (optional)
    encoder = None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("\nLoading embedding model...")
        try:
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            engine.set_embedding_fn(lambda text: encoder.encode(text))
            print("✓ Model loaded")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
            print("Continuing without semantic search (structured queries only)...")
    else:
        print("\n⚠ sentence-transformers not installed.")
        print("Installing with: pip install sentence-transformers")
        print("Continuing without semantic search (structured queries only)...")
    
    # Path to your existing data
    data_dir = Path(__file__).parent.parent.parent / "Phase_1_Taste_Embedding_Model" / "data" / "raw"
    
    # List of files to ingest
    files_to_ingest = [
        ("mcdonalds.csv", "mcdonalds_menu", "Item", "Category"),
        ("burger-king-menu.csv", "burger_king_menu", "ITEM", "CATEGORY"),
        ("wendys-menu.csv", "wendys_menu", "Item", "Category"),
    ]
    
    all_records = []
    
    for filename, source_name, item_col, category_col in files_to_ingest:
        file_path = data_dir / filename
        
        if not file_path.exists():
            print(f"\n⚠ File not found: {file_path}")
            continue
        
        print(f"\nIngesting {filename}...")
        try:
            records = engine.ingest_online_dataset(
                file_path=file_path,
                source_name=source_name,
                text_columns=[item_col, category_col],
                brand_column=item_col  # Using item as brand identifier
            )
            print(f"  ✓ Created {len(records)} records")
            all_records.extend(records)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    if not all_records:
        print("\nNo records to index. Check file paths.")
        return
    
    # Index all records
    print(f"\nIndexing {len(all_records)} total records...")
    try:
        # Only generate embeddings if encoder is available
        engine.index_records(
            all_records,
            generate_embeddings=(encoder is not None),
            enrich_text=True
        )
        print("✓ All records indexed!")
    except Exception as e:
        print(f"✗ Error indexing: {e}")
        return
    
    # Example queries
    print("\n" + "=" * 60)
    print("Example Queries")
    print("=" * 60)
    
    # Semantic search (only if encoder available)
    if encoder:
        # Search for burgers
        print("\n1. Semantic search: 'burger'")
        try:
            results = engine.search("burger", top_k=5)
            print(f"   Found {len(results)} results")
            for i, r in enumerate(results[:5], 1):
                item = r.structured_fields.get('Item') or r.structured_fields.get('ITEM', 'N/A')
                print(f"   {i}. {item}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Search for breakfast items
        print("\n2. Semantic search: 'breakfast'")
        try:
            results = engine.search("breakfast", top_k=5)
            print(f"   Found {len(results)} results")
            for i, r in enumerate(results[:5], 1):
                item = r.structured_fields.get('Item') or r.structured_fields.get('ITEM', 'N/A')
                print(f"   {i}. {item}")
        except Exception as e:
            print(f"   Error: {e}")
    else:
        print("\n⚠ Semantic search skipped (sentence-transformers not available)")
    
    # Query by source (works without embeddings)
    print("\n3. Query by source: 'mcdonalds_menu'")
    mcd_records = engine.get_by_filters({"source_name": "mcdonalds_menu"})
    print(f"   Found {len(mcd_records)} McDonald's items")
    for i, r in enumerate(mcd_records[:5], 1):
        item = r.structured_fields.get('Item') or r.structured_fields.get('ITEM', 'N/A')
        print(f"   {i}. {item}")
    
    # Hybrid query (only if encoder available)
    if encoder:
        print("\n4. Hybrid: 'chicken' + McDonald's source")
        try:
            results = engine.search(
                "chicken",
                filters={"source_name": "mcdonalds_menu"},
                top_k=5
            )
            print(f"   Found {len(results)} results")
            for i, r in enumerate(results[:5], 1):
                item = r.structured_fields.get('Item', 'N/A')
                print(f"   {i}. {item}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # More structured queries (work without embeddings)
    print("\n5. Query by brand (structured)")
    brand_records = engine.get_by_filters({"categorical_fields.brand": "McDonald's"})
    print(f"   Found {len(brand_records)} records")
    
    print("\n" + "=" * 60)
    print("Done! Your data is now searchable.")
    print(f"Storage: {storage_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

