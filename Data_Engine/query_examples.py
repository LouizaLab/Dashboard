"""
Data Engine Query Examples

This script demonstrates all the different ways to query data from the Data Engine.
Run this after you've ingested data using ingest_phase1_data.py
"""

from pathlib import Path
import sys
from datetime import datetime, timedelta

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


def print_results(title, results, max_display=5):
    """Helper function to print query results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Found {len(results)} result(s)")
    
    if not results:
        print("No results found.")
        return
    
    for i, record in enumerate(results[:max_display], 1):
        print(f"\n{i}. Record ID: {record.record_id[:8]}...")
        print(f"   Source: {record.source_name}")
        print(f"   Brand: {record.brand or 'N/A'}")
        
        # Show structured fields
        if record.structured_fields:
            # Try to find common fields
            for field in ['Item', 'ITEM', 'name', 'Name']:
                if field in record.structured_fields:
                    print(f"   Item: {record.structured_fields[field]}")
                    break
            
            for field in ['Category', 'CATEGORY', 'category']:
                if field in record.structured_fields:
                    print(f"   Category: {record.structured_fields[field]}")
                    break
        
        # Show text preview
        if record.raw_text:
            text_preview = record.raw_text[:100] + "..." if len(record.raw_text) > 100 else record.raw_text
            print(f"   Text: {text_preview}")
    
    if len(results) > max_display:
        print(f"\n... and {len(results) - max_display} more result(s)")


def main():
    """Demonstrate various query methods"""
    
    print("=" * 60)
    print("Data Engine Query Examples")
    print("=" * 60)
    
    # Initialize engine
    storage_dir = Path(__file__).parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings (optional, for semantic search)
    encoder = None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("\nLoading embedding model for semantic search...")
        try:
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            engine.set_embedding_fn(lambda text: encoder.encode(text))
            print("✓ Semantic search enabled")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
    else:
        print("\n⚠ Semantic search disabled (install sentence-transformers to enable)")
        print("   Structured queries will still work!")
    
    # Check if we have data
    print("\nChecking for indexed data...")
    try:
        all_records = engine.get_by_bucket(bucket_id=1, limit=1)
        if not all_records:
            print("⚠ No data found in the engine!")
            print("   Please run: python Data_Engine/ingest_phase1_data.py")
            return
        print(f"✓ Found indexed data")
    except Exception as e:
        print(f"✗ Error checking data: {e}")
        return
    
    print("\n" + "=" * 60)
    print("QUERY EXAMPLES")
    print("=" * 60)
    
    # ============================================================
    # 1. QUERY BY BRAND
    # ============================================================
    print("\n" + "=" * 60)
    print("1. Query by Brand")
    print("=" * 60)
    
    # Get all McDonald's items
    print("\n1a. Get all McDonald's items:")
    try:
        mcd_records = engine.get_by_brand("McDonald's", limit=10)
        print_results("McDonald's Items", mcd_records, max_display=3)
    except Exception as e:
        print(f"Error: {e}")
    
    # Note: Brand might be stored as item name, so let's try a different approach
    print("\n1b. Get items from mcdonalds_menu source:")
    try:
        mcd_source = engine.get_by_filters({"source_name": "mcdonalds_menu"}, limit=10)
        print_results("McDonald's Menu Items", mcd_source, max_display=3)
    except Exception as e:
        print(f"Error: {e}")
    
    # ============================================================
    # 2. QUERY BY SOURCE
    # ============================================================
    print("\n" + "=" * 60)
    print("2. Query by Source")
    print("=" * 60)
    
    sources = ["mcdonalds_menu", "burger_king_menu", "wendys_menu"]
    
    for source in sources:
        print(f"\n2. Get all items from {source}:")
        try:
            records = engine.get_by_filters({"source_name": source}, limit=5)
            print_results(f"{source} Items", records, max_display=3)
        except Exception as e:
            print(f"Error: {e}")
    
    # ============================================================
    # 3. QUERY BY BUCKET
    # ============================================================
    print("\n" + "=" * 60)
    print("3. Query by Bucket")
    print("=" * 60)
    
    print("\n3. Get all records from Bucket 1 (Online Datasets):")
    try:
        bucket_records = engine.get_by_bucket(bucket_id=1, limit=10)
        print_results("Bucket 1 Records", bucket_records, max_display=3)
    except Exception as e:
        print(f"Error: {e}")
    
    # ============================================================
    # 4. QUERY BY FILTERS (Structured)
    # ============================================================
    print("\n" + "=" * 60)
    print("4. Query by Filters (Structured Queries)")
    print("=" * 60)
    
    # Filter by category
    print("\n4a. Get items with Category='Burgers':")
    try:
        burger_records = engine.get_by_filters({
            "categorical_fields.Category": "Burgers"
        }, limit=10)
        print_results("Burgers", burger_records, max_display=3)
    except Exception as e:
        print(f"Error: {e}")
    
    # Filter by multiple criteria
    print("\n4b. Get McDonald's items from Breakfast category:")
    try:
        breakfast_mcd = engine.get_by_filters({
            "source_name": "mcdonalds_menu",
            "categorical_fields.Category": "Breakfast"
        }, limit=10)
        print_results("McDonald's Breakfast Items", breakfast_mcd, max_display=3)
    except Exception as e:
        print(f"Error: {e}")
    
    # Filter by numerical fields (if any)
    print("\n4c. Example: Filter by numerical field (if calories exist):")
    try:
        # This is just an example - adjust based on your data
        high_cal = engine.get_by_filters({
            "numerical_fields.Calories": {"min": 500}
        }, limit=5)
        if high_cal:
            print_results("High Calorie Items", high_cal, max_display=3)
        else:
            print("   (No numerical fields found in this example)")
    except Exception as e:
        print(f"   (This filter may not apply to your data)")
    
    # ============================================================
    # 5. SEMANTIC SEARCH (if embeddings available)
    # ============================================================
    if encoder:
        print("\n" + "=" * 60)
        print("5. Semantic Search")
        print("=" * 60)
        
        queries = [
            "burger",
            "breakfast items",
            "chicken sandwich",
            "dessert",
            "salad"
        ]
        
        for query in queries:
            print(f"\n5. Semantic search: '{query}'")
            try:
                results = engine.search(query, top_k=5)
                print_results(f"Results for '{query}'", results, max_display=3)
            except Exception as e:
                print(f"Error: {e}")
    else:
        print("\n" + "=" * 60)
        print("5. Semantic Search (Disabled)")
        print("=" * 60)
        print("\n⚠ Semantic search requires sentence-transformers")
        print("   Install with: pip install sentence-transformers")
        print("   Then re-run this script to see semantic search examples")
    
    # ============================================================
    # 6. HYBRID QUERIES (Semantic + Filters)
    # ============================================================
    if encoder:
        print("\n" + "=" * 60)
        print("6. Hybrid Queries (Semantic + Filters)")
        print("=" * 60)
        
        print("\n6a. Search 'burger' + filter by source:")
        try:
            results = engine.search(
                "burger",
                filters={"source_name": "mcdonalds_menu"},
                top_k=5
            )
            print_results("McDonald's Burgers (semantic)", results, max_display=3)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n6b. Search 'chicken' + filter by category:")
        try:
            results = engine.search(
                "chicken",
                filters={"categorical_fields.Category": "Chicken & Sandwiches"},
                top_k=5
            )
            print_results("Chicken Items (semantic + filter)", results, max_display=3)
        except Exception as e:
            print(f"Error: {e}")
    
    # ============================================================
    # 7. TIME-BASED QUERIES (if timestamps exist)
    # ============================================================
    print("\n" + "=" * 60)
    print("7. Time-Based Queries")
    print("=" * 60)
    
    print("\n7. Get records from last 30 days:")
    try:
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now()
        time_records = engine.get_by_time_range(start_time, end_time, limit=10)
        if time_records:
            print_results("Recent Records", time_records, max_display=3)
        else:
            print("   (No records with timestamps in this example)")
    except Exception as e:
        print(f"   (Time-based queries require timestamp data)")
    
    # ============================================================
    # 8. COMBINING MULTIPLE QUERIES
    # ============================================================
    print("\n" + "=" * 60)
    print("8. Combining Multiple Queries")
    print("=" * 60)
    
    print("\n8. Get items from multiple sources:")
    try:
        all_menu_items = []
        for source in ["mcdonalds_menu", "burger_king_menu", "wendys_menu"]:
            items = engine.get_by_filters({"source_name": source}, limit=5)
            all_menu_items.extend(items)
        
        print(f"   Found {len(all_menu_items)} items across all menus")
        print_results("All Menu Items", all_menu_items[:10], max_display=5)
    except Exception as e:
        print(f"Error: {e}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("QUERY SUMMARY")
    print("=" * 60)
    
    print("\nAvailable Query Methods:")
    print("  1. engine.get_by_brand(brand_name)")
    print("  2. engine.get_by_bucket(bucket_id)")
    print("  3. engine.get_by_filters(filters_dict)")
    print("  4. engine.get_by_time_range(start, end)")
    print("  5. engine.search(query_text)  # Requires embeddings")
    print("  6. engine.search(query_text, filters=...)  # Hybrid")
    
    print("\nFilter Examples:")
    print("  - By source: {'source_name': 'mcdonalds_menu'}")
    print("  - By category: {'categorical_fields.Category': 'Burgers'}")
    print("  - By numerical: {'numerical_fields.Calories': {'min': 500}}")
    print("  - Multiple: {'source_name': '...', 'bucket_id': 1}")
    
    print("\n" + "=" * 60)
    print("Done! Try modifying these examples for your use case.")
    print("=" * 60)


if __name__ == "__main__":
    main()

