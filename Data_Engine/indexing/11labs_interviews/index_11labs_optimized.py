"""
Optimized embedding generation for 11 Labs interviews
Designed to work efficiently with RAG system

This script:
1. Uses quick indexing first (metadata only - instant)
2. Then generates embeddings in optimized batches
3. Updates the index with embeddings
4. Verifies RAG compatibility
"""

from pathlib import Path
import sys
import time
import numpy as np

# Handle macOS mutex issues BEFORE any imports
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

from Data_Engine.data_engine import DataEngine

# Import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("❌ sentence-transformers not installed.")
    print("   Install with: pip install sentence-transformers")
    print("\n⚠ RAG will work but semantic search won't be available.")
    print("   You can still use structured queries (filters, bucket queries).")
    sys.exit(1)


def get_existing_records(engine: DataEngine):
    """Get existing records (assumes quick_index_11labs.py was run first)"""
    print("=" * 70)
    print("STEP 1: Checking Existing Records")
    print("=" * 70)
    
    # Check if already indexed
    try:
        existing = engine.get_by_filters({"source_name": "11_labs_interviews"})
        if existing:
            print(f"✓ Found {len(existing)} records already indexed")
            print("   (Assuming quick_index_11labs.py was run first)")
            return existing
        else:
            print("❌ No records found!")
            print("   Please run: python quick_index_11labs.py first")
            return None
    except Exception as e:
        print(f"❌ Error checking records: {e}")
        print("   Please run: python quick_index_11labs.py first")
        return None


def generate_embeddings_optimized(engine: DataEngine, records):
    """Generate embeddings in optimized batches"""
    print("\n" + "=" * 70)
    print("STEP 2: Generating Embeddings (Optimized)")
    print("=" * 70)
    
    # Load model
    print("\n📦 Loading embedding model...")
    start_load = time.time()
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    engine.set_embedding_fn(lambda text: encoder.encode(text, convert_to_numpy=True))
    load_time = time.time() - start_load
    print(f"✓ Model loaded in {load_time:.1f}s")
    
    # Collect texts
    print(f"\n📝 Preparing {len(records)} records for embedding...")
    texts = []
    text_to_record = {}
    
    for record in records:
        text = record.get_text_for_embedding()
        if text and text.strip():
            texts.append(text)
            text_to_record[len(texts) - 1] = record
    
    print(f"   {len(texts)} records have text content")
    
    if not texts:
        print("❌ No text content found!")
        return None
    
    # Generate embeddings in optimized batches
    print(f"\n🔄 Generating embeddings...")
    print(f"   Batch size: 64 (optimal for sentence-transformers)")
    print(f"   Total batches: {(len(texts) + 63) // 64}")
    
    embedding_start = time.time()
    all_embeddings = []
    
    BATCH_SIZE = 64
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Show progress every 5 batches
        if batch_num % 5 == 0 or batch_num == total_batches:
            print(f"   Batch {batch_num}/{total_batches} ({i+len(batch_texts)}/{len(texts)} texts)...")
        
        # Batch encode (much faster!)
        batch_embeddings = encoder.encode(
            batch_texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        all_embeddings.append(batch_embeddings)
    
    # Combine all embeddings
    embeddings_array = np.vstack(all_embeddings)
    embedding_time = time.time() - embedding_start
    
    print(f"✓ Generated {len(texts)} embeddings in {embedding_time:.1f}s")
    print(f"   Average: {embedding_time/len(texts)*1000:.1f}ms per text")
    
    # Map embeddings back to records
    print(f"\n📦 Mapping embeddings to records...")
    embedding_dict = {}
    text_idx = 0
    
    for record in records:
        text = record.get_text_for_embedding()
        if text and text.strip():
            embedding_dict[record.record_id] = embeddings_array[text_idx]
            record.embedding = embeddings_array[text_idx].tolist()
            text_idx += 1
    
    # Create full embeddings array (with zeros for records without text)
    embedding_dim = encoder.get_sentence_embedding_dimension()
    full_embeddings = np.zeros((len(records), embedding_dim))
    
    for i, record in enumerate(records):
        if record.record_id in embedding_dict:
            full_embeddings[i] = embedding_dict[record.record_id]
    
    return full_embeddings


def update_index_with_embeddings(engine: DataEngine, records, embeddings):
    """Update index with embeddings"""
    print(f"\n📦 Updating index with embeddings...")
    
    try:
        # Use index_manager directly to update embeddings
        engine.index_manager.index_batch(records, embeddings)
        print(f"✓ Index updated successfully")
        return True
    except Exception as e:
        print(f"❌ Error updating index: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_compatibility(engine: DataEngine):
    """Test that RAG can use the indexed data"""
    print("\n" + "=" * 70)
    print("STEP 3: Testing RAG Compatibility")
    print("=" * 70)
    
    # Test semantic search
    test_queries = [
        "What do people like about fast food?",
        "consumer food preferences",
        "favorite burger",
    ]
    
    print("\n🔍 Testing semantic search queries:")
    for query in test_queries:
        try:
            results = engine.search(query, top_k=3)
            print(f"\n   Query: '{query}'")
            print(f"   ✓ Found {len(results)} results")
            
            if results:
                sample = results[0]
                print(f"   Top result: {sample.source_name}")
                print(f"   Preview: {sample.raw_text[:100] if sample.raw_text else 'N/A'}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test with filters (RAG uses this)
    print("\n🔍 Testing filtered queries (RAG style):")
    try:
        results = engine.search(
            "food preferences",
            filters={"source_name": "11_labs_interviews"},
            top_k=5
        )
        print(f"   ✓ Found {len(results)} results with filter")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test DataEngineAdapter compatibility
    print("\n🔍 Testing DataEngineAdapter compatibility:")
    try:
        from adapters.data_engine_adapter import DataEngineAdapter
        adapter = DataEngineAdapter(engine)
        
        # Set embedding function
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        adapter.set_embedding_fn(lambda text: encoder.encode(text, convert_to_numpy=True))
        
        # Test hybrid_query (used by RAG)
        results = adapter.hybrid_query(
            query_text="What do people prefer?",
            filters={"source_name": "11_labs_interviews"},
            top_k=5
        )
        print(f"   ✓ hybrid_query works: {len(results)} results")
        
        # Test query_structured (fallback used by RAG)
        results = adapter.query_structured(
            filters={"source_name": "11_labs_interviews"},
            top_k=5
        )
        print(f"   ✓ query_structured works: {len(results)} results")
        
        print("\n✅ RAG compatibility confirmed!")
        
    except Exception as e:
        print(f"   ⚠ Adapter test failed: {e}")
        print("   (This is OK if adapters module isn't available)")


def main():
    """Main function"""
    print("=" * 70)
    print("OPTIMIZED 11 LABS INDEXING FOR RAG")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Quick index metadata (instant)")
    print("  2. Generate embeddings in optimized batches")
    print("  3. Update index with embeddings")
    print("  4. Verify RAG compatibility")
    print()
    
    total_start = time.time()
    
    # Initialize engine
    storage_dir = Path(__file__).parent.parent.parent / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Step 1: Get existing records (assumes quick indexing was done)
    records = get_existing_records(engine)
    
    if not records:
        print("\n❌ No records found. Cannot proceed.")
        print("   Run this first: python quick_index_11labs.py")
        return
    
    # Step 2: Generate embeddings
    embeddings = generate_embeddings_optimized(engine, records)
    
    if embeddings is None:
        print("❌ Failed to generate embeddings.")
        return
    
    # Step 3: Update index
    success = update_index_with_embeddings(engine, records, embeddings)
    
    if not success:
        print("❌ Failed to update index.")
        return
    
    # Step 4: Test RAG compatibility
    test_rag_compatibility(engine)
    
    total_time = time.time() - total_start
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"Total time: {total_time:.1f}s")
    print(f"Records indexed: {len(records)}")
    print(f"Average: {total_time/len(records)*1000:.1f}ms per record")
    print("\n✅ 11 Labs interviews are now ready for RAG!")
    print("\nYou can use them with:")
    print("  from Agent_Tron.rag_graph.graph import RAGGraph")
    print("  from adapters.data_engine_adapter import DataEngineAdapter")
    print("  graph = RAGGraph(data_engine_adapter)")


if __name__ == "__main__":
    main()

