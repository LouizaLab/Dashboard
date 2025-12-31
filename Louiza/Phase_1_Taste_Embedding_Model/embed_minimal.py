"""
Generate embeddings using the minimal trained model
"""

import torch
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import json
from sklearn.preprocessing import StandardScaler, LabelEncoder

# FAISS is optional
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Warning: FAISS not installed. Install with: pip install faiss-cpu")

# Import the minimal model and dataset
from train_minimal import MinimalProductDataset, MinimalProductModel


def generate_embeddings(model, dataset, device, batch_size=32):
    """Generate embeddings for all products"""
    model.eval()
    embeddings = []
    product_ids = []
    product_names = []
    
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    with torch.no_grad():
        for batch in dataloader:
            tag_indices = batch['tag_indices'].to(device)
            nutrition = batch['nutrition'].to(device)
            category_ids = batch['category_id'].to(device)
            
            # Generate embeddings
            emb = model(tag_indices, nutrition, category_ids)
            
            embeddings.append(emb.cpu().numpy())
            product_ids.extend(batch['product_id'])
            product_names.extend(batch['product_name'])
    
    embeddings = np.vstack(embeddings)
    return embeddings, product_ids, product_names


def build_faiss_index(embeddings, metric='cosine'):
    """Build FAISS index for fast similarity search"""
    dim = embeddings.shape[1]
    
    if metric == 'cosine':
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dim)
    else:
        index = faiss.IndexFlatL2(dim)
    
    index.add(embeddings.astype('float32'))
    return index


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings from minimal model')
    parser.add_argument('--data', type=str, default='data/processed/products.csv',
                       help='Path to processed products CSV')
    parser.add_argument('--model_file', type=str, default='models/best_model_minimal.pt',
                       help='Path to trained model checkpoint')
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
    model_path = Path(args.model_file)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location=device)
    
    # Reconstruct dataset to get vocabularies and scalers
    print("Reconstructing dataset...")
    temp_dataset = MinimalProductDataset(products_df)
    
    # Load from checkpoint if available, otherwise use temp_dataset
    if 'tag_vocab' in checkpoint:
        tag_vocab = checkpoint['tag_vocab']
    else:
        tag_vocab = temp_dataset.tag_vocab
    
    if 'category_classes' in checkpoint:
        category_encoder = LabelEncoder()
        category_encoder.classes_ = np.array(checkpoint['category_classes'])
    else:
        category_encoder = temp_dataset.category_encoder
    
    if 'nutrition_scaler_mean' in checkpoint:
        nutrition_scaler = StandardScaler()
        nutrition_scaler.mean_ = np.array(checkpoint['nutrition_scaler_mean'])
        nutrition_scaler.scale_ = np.array(checkpoint['nutrition_scaler_scale'])
    else:
        nutrition_scaler = temp_dataset.nutrition_scaler
    
    # Create dataset with loaded vocabularies
    dataset = MinimalProductDataset(
        products_df,
        tag_vocab=tag_vocab,
        category_encoder=category_encoder,
        nutrition_scaler=nutrition_scaler
    )
    
    # Create model
    print("Creating model...")
    model = MinimalProductModel(
        tag_vocab_size=len(tag_vocab),
        category_vocab_size=len(category_encoder.classes_),
        hidden_dim=checkpoint.get('hidden_dim', 256),
        output_dim=checkpoint.get('output_dim', 128)
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
        'num_products': len(embeddings),
        'model_type': 'minimal'
    }
    
    metadata_path = output_dir / 'product_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata_dict, f, indent=2)
    print(f"Saved metadata to {metadata_path}")
    
    # Build and save FAISS index (optional)
    if HAS_FAISS:
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
    else:
        print("Skipping FAISS index (not installed)")
    
    print("\n✓ Embedding generation complete!")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    if HAS_FAISS:
        print(f"  FAISS index: {index_path}")


if __name__ == '__main__':
    main()

