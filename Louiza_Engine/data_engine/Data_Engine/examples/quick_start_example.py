"""
Quick Start Example - Run this to see the Data Engine in action!

This example demonstrates:
1. Ingesting data from CSV files
2. Indexing with embeddings
3. Semantic search
4. Filter-based queries
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Now import from the package
from Data_Engine.data_engine import DataEngine
import pandas as pd

# Optional: sentence-transformers for semantic search
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


def create_sample_data():
    """Create sample data files if they don't exist"""
    data_dir = Path(__file__).parent / "sample_data"
    data_dir.mkdir(exist_ok=True)
    
    # Sample product data
    products_file = data_dir / "products.csv"
    if not products_file.exists():
        print("Creating sample products.csv...")
        df = pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5],
            'name': ['Big Mac', 'Whopper', 'Baconator', 'Quarter Pounder', 'Double Whopper'],
            'brand': ['McDonald\'s', 'Burger King', 'Wendy\'s', 'McDonald\'s', 'Burger King'],
            'category': ['Burger', 'Burger', 'Burger', 'Burger', 'Burger'],
            'description': [
                'Classic burger with special sauce',
                'Flame-grilled beef patty',
                'Bacon lover\'s dream burger',
                'Quarter pound of beef',
                'Double flame-grilled patties'
            ],
            'price': [5.99, 6.49, 7.99, 6.29, 7.49]
        })
        df.to_csv(products_file, index=False)
        print(f"✓ Created {products_file}")
    
    return products_file


def main():
    """Main example"""
    print("=" * 60)
    print("Data Engine Quick Start Example")
    print("=" * 60)
    
    # Step 1: Create sample data
    print("\n[Step 1] Creating sample data...")
    sample_file = create_sample_data()
    
    # Step 2: Initialize Data Engine
    print("\n[Step 2] Initializing Data Engine...")
    storage_dir = Path(__file__).parent.parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings (this may take a moment on first run)
    encoder = None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("Loading embedding model (this may take a moment)...")
        try:
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            engine.set_embedding_fn(lambda text: encoder.encode(text))
            print("✓ Embedding model loaded")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
            print("Continuing without embeddings (structured queries only)...")
    else:
        print("⚠ sentence-transformers not installed.")
        print("   Install with: pip install sentence-transformers")
        print("   Continuing without semantic search (structured queries only)...")
    
    # Step 3: Ingest data
    print("\n[Step 3] Ingesting data...")
    try:
        records = engine.ingest_online_dataset(
            file_path=sample_file,
            source_name="sample_products",
            text_columns=["name", "description"],
            brand_column="brand"
        )
        print(f"✓ Ingested {len(records)} records")
        
        # Show first record
        if records:
            print(f"\nSample record:")
            print(f"  ID: {records[0].record_id[:8]}...")
            print(f"  Brand: {records[0].brand}")
            print(f"  Text: {records[0].raw_text[:50]}...")
    except Exception as e:
        print(f"✗ Error ingesting: {e}")
        return
    
    # Step 4: Index records
    print("\n[Step 4] Indexing records...")
    try:
        engine.index_records(
            records,
            generate_embeddings=(encoder is not None),
            enrich_text=True
        )
        print("✓ Records indexed")
    except Exception as e:
        print(f"✗ Error indexing: {e}")
        return
    
    # Step 5: Query examples
    print("\n[Step 5] Query Examples")
    print("-" * 60)
    
    # Query by brand
    print("\n1. Query by brand: 'McDonald's'")
    try:
        mcd_records = engine.get_by_brand("McDonald's")
        print(f"   Found {len(mcd_records)} records")
        for r in mcd_records[:3]:
            print(f"   - {r.structured_fields.get('name', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Query by bucket
    print("\n2. Query by bucket (Bucket 1 = Online Datasets)")
    try:
        bucket_records = engine.get_by_bucket(bucket_id=1)
        print(f"   Found {len(bucket_records)} records")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Semantic search (if embeddings available)
    if encoder:
        print("\n3. Semantic search: 'flame grilled burger'")
        try:
            results = engine.search("flame grilled burger", top_k=3)
            print(f"   Found {len(results)} results")
            for i, r in enumerate(results, 1):
                name = r.structured_fields.get('name', 'N/A')
                brand = r.brand or 'N/A'
                print(f"   {i}. {name} ({brand})")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Filter-based query
    print("\n4. Filter query: brand='Burger King'")
    try:
        filtered = engine.get_by_filters({"brand": "Burger King"})
        print(f"   Found {len(filtered)} records")
        for r in filtered:
            print(f"   - {r.structured_fields.get('name', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Hybrid query (semantic + filters)
    if encoder:
        print("\n5. Hybrid query: 'burger' + brand filter")
        try:
            hybrid_results = engine.search(
                "burger",
                filters={"brand": "McDonald's"},
                top_k=2
            )
            print(f"   Found {len(hybrid_results)} results")
            for r in hybrid_results:
                print(f"   - {r.structured_fields.get('name', 'N/A')}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print(f"Storage directory: {storage_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

