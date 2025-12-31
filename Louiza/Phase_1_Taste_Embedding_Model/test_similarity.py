"""
Simple script to test product similarity using generated embeddings
"""

import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity

# Load embeddings
print("Loading embeddings...")
embeddings = np.load('embeddings/product_embeddings.npy')

# Load metadata
with open('embeddings/product_metadata.json', 'r') as f:
    metadata = json.load(f)

product_names = metadata['product_names']
product_ids = metadata['product_ids']

print(f"Loaded {len(embeddings)} product embeddings (dimension: {embeddings.shape[1]})")


def find_similar(product_name, top_k=5):
    """Find similar products"""
    if product_name not in product_names:
        print(f"✗ Product '{product_name}' not found")
        print(f"  Available products (first 10): {product_names[:10]}")
        return []
    
    idx = product_names.index(product_name)
    query = embeddings[idx:idx+1]
    
    # Compute cosine similarity
    similarities = cosine_similarity(query, embeddings)[0]
    
    # Get top k (excluding self)
    top_indices = np.argsort(similarities)[::-1][1:top_k+1]
    
    results = []
    for i in top_indices:
        results.append((product_names[i], similarities[i]))
    
    return results


def show_all_products():
    """Show all available products"""
    print(f"\nAll {len(product_names)} products:")
    for i, name in enumerate(product_names, 1):
        print(f"  {i}. {name}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Product Similarity Search")
    print("="*70)
    
    # Show some example searches
    test_products = [
        "Coca Cola- 16 fl oz",
        "Chicken McNuggets®",
        "Dave's Single"
    ]
    
    for product in test_products:
        if product in product_names:
            print(f"\nProducts similar to '{product}':")
            similar = find_similar(product, top_k=5)
            if similar:
                for i, (name, sim) in enumerate(similar, 1):
                    print(f"  {i}. {name} (similarity: {sim:.4f})")
            print()
    
    # Interactive mode
    print("\n" + "="*70)
    print("Interactive Mode - Enter product names to find similar products")
    print("(Type 'list' to see all products, 'quit' to exit)")
    print("="*70)
    
    while True:
        query = input("\nEnter product name: ").strip()
        
        if query.lower() == 'quit':
            break
        elif query.lower() == 'list':
            show_all_products()
        elif query:
            similar = find_similar(query, top_k=5)
            if similar:
                print(f"\nProducts similar to '{query}':")
                for i, (name, sim) in enumerate(similar, 1):
                    print(f"  {i}. {name} (similarity: {sim:.4f})")
            else:
                print(f"No results found for '{query}'")

