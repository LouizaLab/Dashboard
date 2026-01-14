"""
Quick test script for Data Engine queries

This shows both structured queries (no embeddings needed) and semantic search (requires embeddings)
"""

from Data_Engine.data_engine import DataEngine
from pathlib import Path

# Initialize
engine = DataEngine(storage_dir=Path("./Data_Engine/storage_data"))

print("=" * 60)
print("Data Engine Query Test")
print("=" * 60)

# ============================================================
# STRUCTURED QUERIES (No embeddings needed)
# ============================================================
print("\n1. Structured Queries (No embeddings required)")
print("-" * 60)

# Query by source
mcd_items = engine.get_by_filters({"source_name": "mcdonalds_menu"}, limit=5)
print(f"\n✓ McDonald's items: {len(mcd_items)} found")
if mcd_items:
    for i, item in enumerate(mcd_items[:3], 1):
        item_name = item.structured_fields.get('Item', 'N/A')
        print(f"   {i}. {item_name}")

# Query by category
burgers = engine.get_by_filters({"categorical_fields.Category": "Burgers"}, limit=5)
print(f"\n✓ Burgers: {len(burgers)} found")
if burgers:
    for i, item in enumerate(burgers[:3], 1):
        item_name = item.structured_fields.get('Item') or item.structured_fields.get('ITEM', 'N/A')
        print(f"   {i}. {item_name}")

# Query by bucket
all_records = engine.get_by_bucket(bucket_id=1, limit=5)
print(f"\n✓ Total records in bucket 1: {len(all_records)} found")

# ============================================================
# SEMANTIC SEARCH (Requires embeddings)
# ============================================================
print("\n" + "=" * 60)
print("2. Semantic Search (Requires sentence-transformers)")
print("-" * 60)

try:
    from sentence_transformers import SentenceTransformer
    
    print("\nSetting up embeddings...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    engine.set_embedding_fn(lambda text: encoder.encode(text))
    print("✓ Embeddings ready!")
    
    # Now semantic search will work
    print("\nSearching for 'breakfast'...")
    results = engine.search("breakfast", top_k=10)
    print(f"✓ Found {len(results)} results")
    
    for i, item in enumerate(results[:5], 1):
        item_name = item.structured_fields.get('Item') or item.structured_fields.get('ITEM', 'N/A')
        print(f"   {i}. {item_name}")
    
    print("\nSearching for 'burger'...")
    results = engine.search("burger", top_k=5)
    print(f"✓ Found {len(results)} results")
    
    for i, item in enumerate(results[:3], 1):
        item_name = item.structured_fields.get('Item') or item.structured_fields.get('ITEM', 'N/A')
        print(f"   {i}. {item_name}")
        
except ImportError:
    print("\n⚠ sentence-transformers not installed")
    print("   Install with: pip install sentence-transformers")
    print("   Semantic search disabled - structured queries still work!")
    
except Exception as e:
    print(f"\n✗ Error with semantic search: {e}")
    print("   Structured queries still work!")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
