"""
Example: Semantic Search with Embeddings

Demonstrates how to use semantic similarity search with embeddings.
"""

from pathlib import Path
import sys
import numpy as np

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.ingestion.bucket1_online_datasets import OnlineDatasetsIngester
from Data_Engine.indexing.index_manager import IndexManager
from Data_Engine.retrieval.retrieval_manager import RetrievalManager
from Data_Engine.enrichment.text_cleaner import TextCleaner


def create_simple_embedding(text: str) -> np.ndarray:
    """
    Simple embedding function (placeholder).
    
    In production, use:
    - sentence-transformers
    - OpenAI embeddings
    - Custom model from Phase 1
    """
    # Placeholder: return random embedding
    # TODO: Replace with actual embedding model
    import hashlib
    hash_obj = hashlib.md5(text.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    np.random.seed(hash_int % 2**32)
    return np.random.randn(384).astype('float32')


def main():
    """Example semantic search"""
    
    storage_dir = Path(__file__).parent.parent / "storage_data"
    index_manager = IndexManager(storage_dir=storage_dir, embedding_dim=384)
    text_cleaner = TextCleaner()
    
    # Ingest some data
    data_dir = Path(__file__).parent.parent.parent / "Phase_1_Taste_Embedding_Model" / "data" / "raw"
    csv_file = data_dir / "mcdonalds.csv"
    
    if csv_file.exists():
        ingester = OnlineDatasetsIngester(
            source_name="mcdonalds_menu",
            dataset_name="menu_items"
        )
        
        records = list(ingester.ingest(csv_file, text_columns=["Item", "Category"]))
        print(f"Ingested {len(records)} records")
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = []
        enriched_records = []
        
        for record in records:
            enriched = text_cleaner.enrich(record)
            text = enriched.get_text_for_embedding()
            if text:
                embedding = create_simple_embedding(text)
                embeddings.append(embedding)
                enriched.embedding = embedding.tolist()
                enriched_records.append(enriched)
        
        embeddings_array = np.array(embeddings)
        print(f"Generated {len(embeddings_array)} embeddings")
        
        # Index with embeddings
        print("Indexing with embeddings...")
        index_manager.index_batch(enriched_records, embeddings_array)
        print("✓ Indexed records with embeddings")
        
        # Semantic search
        retrieval_manager = RetrievalManager(index_manager)
        
        print("\nSemantic search examples:")
        
        # Search for burgers
        query = "juicy burger with cheese"
        print(f"\nQuery: '{query}'")
        results = retrieval_manager.query_by_text(
            query,
            embedding_fn=create_simple_embedding,
            top_k=5
        )
        print(f"Found {len(results)} results")
        for i, record in enumerate(results[:3], 1):
            print(f"  {i}. {record.structured_fields.get('Item', 'N/A')}")
        
        # Hybrid search with filters
        print(f"\nHybrid query: '{query}' + brand filter")
        results = retrieval_manager.hybrid_query(
            query,
            embedding_fn=create_simple_embedding,
            filters={"brand": "Big Mac"},
            top_k=5
        )
        print(f"Found {len(results)} results")
    else:
        print(f"File not found: {csv_file}")
        print("Note: This example requires data files from Phase_1_Taste_Embedding_Model")


if __name__ == "__main__":
    main()

