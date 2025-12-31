"""
Full training script with text encoding using simple encoder (works on macOS)
This is the recommended script for training the complete model with all features
"""

import os
# CRITICAL: Set these BEFORE any other imports
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Import torch first and set threading
import torch
torch.set_num_threads(1)

# Set before importing transformers
import warnings
warnings.filterwarnings('ignore')

import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from tqdm import tqdm
import json
import warnings
warnings.filterwarnings('ignore')

# Use simple text encoder (avoids macOS mutex issues)
from text_encoder_simple import SentenceTransformerWrapper

from model import ProductEmbeddingModel, ContrastiveLoss
from data_loader import create_data_loaders, save_metadata


def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    for batch in tqdm(train_loader, desc="Training"):
        text = batch['text'].to(device)
        tag_indices = batch['tag_indices'].to(device)
        nutrition = batch['nutrition'].to(device)
        category_ids = batch['category_id'].to(device)
        labels = batch['label'].to(device)
        
        embeddings = model(
            text=text,
            tag_indices=tag_indices,
            nutrition=nutrition,
            category_ids=category_ids
        )
        
        loss = criterion(embeddings, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def validate(model, val_loader, criterion, device):
    """Validate model"""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validating"):
            text = batch['text'].to(device)
            tag_indices = batch['tag_indices'].to(device)
            nutrition = batch['nutrition'].to(device)
            category_ids = batch['category_id'].to(device)
            labels = batch['label'].to(device)
            
            embeddings = model(
                text=text,
                tag_indices=tag_indices,
                nutrition=nutrition,
                category_ids=category_ids
            )
            
            loss = criterion(embeddings, labels)
            
            total_loss += loss.item()
            n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def main():
    parser = argparse.ArgumentParser(description='Train Full Product Embedding Model (with text)')
    parser.add_argument('--data', type=str, default='data/processed/products.csv',
                       help='Path to processed products CSV')
    parser.add_argument('--output_dir', type=str, default='models',
                       help='Output directory for model and metadata')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3,
                       help='Learning rate')
    parser.add_argument('--hidden_dim', type=int, default=256,
                       help='Hidden dimension')
    parser.add_argument('--output_dim', type=int, default=128,
                       help='Output embedding dimension')
    parser.add_argument('--train_ratio', type=float, default=0.8,
                       help='Train/validation split ratio')
    parser.add_argument('--device', type=str, default='auto',
                       help='Device (auto, cpu, cuda)')
    parser.add_argument('--text_model', type=str, default='all-MiniLM-L6-v2',
                       help='Sentence transformer model name')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Phase 1: Full Taste Embedding Model Training")
    print("=" * 70)
    print("Features: Text + Tags + Nutrition + Category")
    print("=" * 70)
    
    # Device setup
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    print(f"\nUsing device: {device}")
    
    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    print(f"\nLoading data from {data_path}...")
    products_df = pd.read_csv(data_path)
    print(f"✓ Loaded {len(products_df)} products")
    
    # Initialize text encoder using simple encoder (avoids mutex issues)
    print(f"\n{'='*70}")
    print(f"Loading text encoder: {args.text_model}")
    print(f"{'='*70}")
    print("  Using simple text encoder (transformers-based, avoids macOS mutex issues)")
    
    try:
        text_encoder = SentenceTransformerWrapper(args.text_model, device='cpu')
        text_dim = text_encoder.get_sentence_embedding_dimension()
        print(f"✓ Text encoder loaded successfully!")
        print(f"  Dimension: {text_dim}")
        print(f"{'='*70}\n")
    except Exception as e:
        print(f"\n✗ Error loading text encoder: {e}")
        print("\nTroubleshooting:")
        print("  1. Install transformers: pip install transformers")
        print("  2. Try: pip install --upgrade transformers")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Create data loaders
    print("Creating data loaders...")
    print("  (Pre-computing text embeddings for all products - may take a moment)")
    try:
        train_loader, val_loader, metadata = create_data_loaders(
            products_df,
            text_encoder=text_encoder,
            train_ratio=args.train_ratio,
            batch_size=args.batch_size,
            device=str(device)
        )
        print(f"✓ Data loaders created")
        print(f"  Train batches: {len(train_loader)}")
        print(f"  Val batches: {len(val_loader)}")
        print(f"  Tag vocab size: {metadata['tag_vocab_size']}")
        print(f"  Category vocab size: {metadata['category_vocab_size']}")
    except Exception as e:
        print(f"✗ Error creating data loaders: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Create model
    print("\nCreating model...")
    try:
        model = ProductEmbeddingModel(
            text_model_name=args.text_model,
            text_dim=text_dim,
            tag_vocab_size=metadata['tag_vocab_size'],
            category_vocab_size=metadata['category_vocab_size'],
            hidden_dim=args.hidden_dim,
            output_dim=args.output_dim,
            freeze_text_encoder=False,  # Fine-tune text encoder
            text_encoder=text_encoder  # Pass pre-loaded encoder
        ).to(device)
        
        print(f"✓ Model created")
        print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
    except Exception as e:
        print(f"✗ Error creating model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Loss and optimizer
    criterion = ContrastiveLoss(margin=1.0, temperature=0.1)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training loop
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    print(f"\n{'='*70}")
    print("Starting training...")
    print(f"{'='*70}\n")
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        train_losses.append(train_loss)
        
        val_loss = validate(model, val_loader, criterion, device)
        val_losses.append(val_loss)
        
        scheduler.step(val_loss)
        
        print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, LR: {optimizer.param_groups[0]['lr']:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            model_path = output_dir / 'best_model.pt'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'train_loss': train_loss,
                'metadata': metadata,
                'args': vars(args)
            }, model_path)
            print(f"  ✓ Saved best model (val_loss: {val_loss:.4f})")
        
        if (epoch + 1) % 10 == 0:
            checkpoint_path = output_dir / f'checkpoint_epoch_{epoch+1}.pt'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'train_loss': train_loss,
                'metadata': metadata,
                'args': vars(args)
            }, checkpoint_path)
    
    # Save final model
    final_model_path = output_dir / 'final_model.pt'
    torch.save({
        'epoch': args.epochs,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_loss': val_loss,
        'train_loss': train_loss,
        'metadata': metadata,
        'args': vars(args)
    }, final_model_path)
    
    # Save metadata
    metadata_path = output_dir / 'metadata.pkl'
    save_metadata(metadata, metadata_path)
    
    # Save training history
    history = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'best_val_loss': best_val_loss
    }
    history_path = output_dir / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"\n{'='*70}")
    print("✓ Training complete!")
    print(f"{'='*70}")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Model saved to: {output_dir}")
    print(f"  - best_model.pt (best validation loss)")
    print(f"  - final_model.pt (final epoch)")
    print(f"Metadata saved to: {metadata_path}")
    print(f"Training history saved to: {history_path}")


if __name__ == '__main__':
    import sys
    main()

