"""
Generate embeddings for all products using trained model
"""

import torch
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import json
from sentence_transformers import SentenceTransformer
import faiss

from model import ProductEmbeddingModel
from data_loader import ProductDataset, load_metadata


def generate_embeddings(model, dataset, device, batch_size=32):
    """Generate embeddings for all products"""
    model.eval()
    embeddings = []
    product_ids = []
    product_names = []
    
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    with torch.no_grad():
        for batch in dataloader:
            text = batch['text'].to(device)
            tag_indices = batch['tag_indices'].to(device)
            nutrition = batch['nutrition'].to(device)
            category_ids = batch['category_id'].to(device)
            
            # Generate embeddings
            emb = model(
                text=text,
                tag_indices=tag_indices,
                nutrition=nutrition,
                category_ids=category_ids
            )
            
            embeddings.append(emb.cpu().numpy())
            product_ids.extend(batch['product_id'])
            product_names.extend(batch['product_name'])
    
    embeddings = np.vstack(embeddings)
    return embeddings, product_ids, product_names


def build_faiss_index(embeddings, metric='cosine'):
    """Build FAISS index for fast similarity search"""
    dim = embeddings.shape[1]
    
    if metric == 'cosine':
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity
    else:
        index = faiss.IndexFlatL2(dim)  # L2 distance
    
    index.add(embeddings.astype('float32'))
    return index


def main():
    parser = argparse.ArgumentParser(description='Generate product embeddings')
    parser.add_argument('--data', type=str, default='data/processed/products.csv',
                       help='Path to processed products CSV')
    parser.add_argument('--model_dir', type=str, default='models',
                       help='Directory containing trained model')
    parser.add_argument('--model_file', type=str, default='best_model.pt',
                       help='Model checkpoint file')
    parser.add_argument('--output_dir', type=str, default='embeddings',
                       help='Output directory for embeddings')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size for inference')
    parser.add_argument('--device', type=str, default='auto',
                       help='Device (auto, cpu, cuda)')
    
    args = parser.parse_args()
    
    # Device setup
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    print(f"Using device: {device}")
    
    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    print(f"Loading data from {data_path}...")
    products_df = pd.read_csv(data_path)
    print(f"Loaded {len(products_df)} products")
    
    # Load model checkpoint
    model_dir = Path(args.model_dir)
    model_path = model_dir / args.model_file
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location=device)
    
    # Load metadata
    metadata_path = model_dir / 'metadata.pkl'
    if metadata_path.exists():
        metadata = load_metadata(metadata_path)
    else:
        # Fallback: use metadata from checkpoint
        metadata = checkpoint.get('metadata', {})
        print("Warning: Using metadata from checkpoint")
    
    # Initialize text encoder
    args_dict = checkpoint.get('args', {})
    text_model_name = args_dict.get('text_model', 'all-MiniLM-L6-v2')
    print(f"Loading text encoder: {text_model_name}...")
    text_encoder = SentenceTransformer(text_model_name)
    text_dim = text_encoder.get_sentence_embedding_dimension()
    
    # Create dataset
    print("Creating dataset...")
    dataset = ProductDataset(
        products_df,
        text_encoder=text_encoder,
        tag_vocab=metadata.get('tag_vocab'),
        category_encoder=metadata.get('category_encoder'),
        nutrition_scaler=metadata.get('nutrition_scaler'),
        device=device
    )
    
    # Create model
    print("Creating model...")
    model = ProductEmbeddingModel(
        text_model_name=text_model_name,
        text_dim=text_dim,
        tag_vocab_size=metadata.get('tag_vocab_size', 20),
        category_vocab_size=metadata.get('category_vocab_size', 50),
        hidden_dim=args_dict.get('hidden_dim', 256),
        output_dim=args_dict.get('output_dim', 128),
        freeze_text_encoder=True  # Freeze during inference
    ).to(device)
    
    # Load model weights
    model.load_state_dict(checkpoint['model_state_dict'])
    print("Model loaded successfully")
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings, product_ids, product_names = generate_embeddings(
        model, dataset, device, batch_size=args.batch_size
    )
    
    print(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    
    # Save embeddings
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as numpy array
    embeddings_path = output_dir / 'product_embeddings.npy'
    np.save(embeddings_path, embeddings)
    print(f"Saved embeddings to {embeddings_path}")
    
    # Save metadata
    metadata_dict = {
        'product_ids': product_ids,
        'product_names': product_names,
        'embedding_dim': embeddings.shape[1],
        'num_products': len(embeddings)
    }
    
    metadata_path = output_dir / 'product_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata_dict, f, indent=2)
    print(f"Saved metadata to {metadata_path}")
    
    # Build and save FAISS index
    print("Building FAISS index...")
    index = build_faiss_index(embeddings, metric='cosine')
    index_path = output_dir / 'faiss_index.bin'
    faiss.write_index(index, str(index_path))
    print(f"Saved FAISS index to {index_path}")
    
    # Save index mapping
    index_mapping = {
        'product_ids': product_ids,
        'product_names': product_names
    }
    index_mapping_path = output_dir / 'faiss_index_mapping.json'
    with open(index_mapping_path, 'w') as f:
        json.dump(index_mapping, f, indent=2)
    print(f"Saved index mapping to {index_mapping_path}")
    
    print("\n✓ Embedding generation complete!")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    print(f"  FAISS index: {index_path}")


if __name__ == '__main__':
    main()

