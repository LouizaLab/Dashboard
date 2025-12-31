"""
Training script for Phase 2: Behavioral Dynamic Engine
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
from tqdm import tqdm
import os
from datetime import datetime

from models_phase2 import BehavioralDynamicEngine
from models import ProductEmbeddingModel, ContextEmbeddingModel, SegmentEmbeddingModel
from data_phase2 import SequenceDataset

def load_phase1_models(checkpoint_path: str, data_dir: str = 'data', device='cpu'):
    """Load trained Phase 1 models"""
    # Load data to get vocab sizes
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
    segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    vocabularies = checkpoint['vocabularies']
    
    # Get vocab sizes
    if 'vocab_sizes' in checkpoint:
        vocab_sizes = checkpoint['vocab_sizes']
        vocab_size = max(vocab_sizes['ingredient'], vocab_sizes['tag'], vocab_sizes['text'])
        
        product_model = ProductEmbeddingModel(
            vocab_size=vocab_size,
            embedding_dim=64,
            hidden_dim=128,
            output_dim=128
        )
        
        context_model = ContextEmbeddingModel(
            time_of_day_vocab=vocab_sizes['time_of_day'],
            location_vocab=vocab_sizes['location'],
            occasion_vocab=vocab_sizes['occasion'],
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
        
        segment_model = SegmentEmbeddingModel(
            age_vocab=vocab_sizes['age'],
            region_vocab=vocab_sizes['region'],
            psychographic_vocab=vocab_sizes['psychographic'],
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
    else:
        # Fallback
        vocab_size = max(
            len(vocabularies['ingredient'].word_to_idx),
            len(vocabularies['tag'].word_to_idx),
            len(vocabularies['text'].word_to_idx)
        )
        
        time_of_days = sorted(contexts_df['time_of_day'].unique())
        locations = sorted(contexts_df['location'].unique())
        occasions = sorted(contexts_df['occasion'].unique())
        age_buckets = sorted(segments_df['age_bucket'].unique())
        regions = sorted(segments_df['region'].unique())
        psychographics = sorted(segments_df['psychographic'].unique())
        
        product_model = ProductEmbeddingModel(
            vocab_size=vocab_size,
            embedding_dim=64,
            hidden_dim=128,
            output_dim=128
        )
        
        context_model = ContextEmbeddingModel(
            time_of_day_vocab=len(time_of_days),
            location_vocab=len(locations),
            occasion_vocab=len(occasions),
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
        
        segment_model = SegmentEmbeddingModel(
            age_vocab=len(age_buckets),
            region_vocab=len(regions),
            psychographic_vocab=len(psychographics),
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
    
    # Load weights
    product_model.load_state_dict(checkpoint['product_model_state_dict'])
    context_model.load_state_dict(checkpoint['context_model_state_dict'])
    segment_model.load_state_dict(checkpoint['segment_model_state_dict'])
    
    product_model.to(device)
    context_model.to(device)
    segment_model.to(device)
    
    product_model.eval()
    context_model.eval()
    segment_model.eval()
    
    return {
        'product': product_model,
        'context': context_model,
        'segment': segment_model
    }, vocabularies


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    for batch in tqdm(dataloader, desc="Training"):
        z_segment = batch['z_segment'].to(device)  # [B, segment_dim]
        z_products = batch['z_products'].to(device)  # [B, seq_len, product_dim] from DataLoader
        z_contexts = batch['z_contexts'].to(device)  # [B, seq_len, context_dim]
        targets = batch['targets'].to(device)  # [B, seq_len, 1]
        
        # Transpose to [seq_len, B, dim] format
        z_products = z_products.transpose(0, 1)  # [seq_len, B, product_dim]
        z_contexts = z_contexts.transpose(0, 1)  # [seq_len, B, context_dim]
        targets = targets.transpose(0, 1)  # [seq_len, B, 1]
        
        # Forward pass through sequence
        predictions = model.forward_sequence(z_segment, z_products, z_contexts)
        # predictions: [seq_len, B, 1]
        
        # Reshape for loss computation
        predictions = predictions.reshape(-1, 1)  # [seq_len * B, 1]
        targets = targets.reshape(-1, 1)  # [seq_len * B, 1]
        
        # Loss
        loss = criterion(predictions, targets)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def validate(model, dataloader, criterion, device):
    """Validate model"""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validating"):
            z_segment = batch['z_segment'].to(device)
            z_products = batch['z_products'].to(device)
            z_contexts = batch['z_contexts'].to(device)
            targets = batch['targets'].to(device)
            
            # Transpose to [seq_len, B, dim] format
            z_products = z_products.transpose(0, 1)
            z_contexts = z_contexts.transpose(0, 1)
            targets = targets.transpose(0, 1)
            
            predictions = model.forward_sequence(z_segment, z_products, z_contexts)
            
            predictions = predictions.reshape(-1, 1)
            targets = targets.reshape(-1, 1)
            
            loss = criterion(predictions, targets)
            
            total_loss += loss.item()
            n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def train_phase2(phase1_checkpoint: str = 'checkpoints/best_model.pt',
                data_dir: str = 'data',
                output_dir: str = 'checkpoints_phase2',
                batch_size: int = 8,
                learning_rate: float = 0.001,
                n_epochs: int = 30,
                sequence_length: int = 10,
                device: str = None):
    """Main training function for Phase 2"""
    
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Load Phase 1 models
    print("Loading Phase 1 models...")
    phase1_models, vocabularies = load_phase1_models(phase1_checkpoint, data_dir, device)
    
    # Load data
    print("Loading data...")
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
    segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
    intent_logs_df = pd.read_csv(os.path.join(data_dir, 'intent_logs.csv'))
    
    # Create dataset
    print(f"Creating sequence dataset (length={sequence_length})...")
    dataset = SequenceDataset(
        intent_logs_df, products_df, contexts_df, segments_df,
        phase1_models, vocabularies, device, sequence_length
    )
    
    print(f"Created {len(dataset)} sequences")
    
    # Split train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create Phase 2 model
    print("Initializing Phase 2 model...")
    model = BehavioralDynamicEngine(
        segment_dim=64,
        product_dim=128,
        context_dim=64,
        state_dim=128,
        hidden_dim=256
    )
    model = model.to(device)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    print("Starting training...")
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    for epoch in range(n_epochs):
        print(f"\nEpoch {epoch+1}/{n_epochs}")
        
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = validate(model, val_loader, criterion, device)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'train_losses': train_losses,
                'val_losses': val_losses,
                'sequence_length': sequence_length,
            }, os.path.join(output_dir, 'best_model_phase2.pt'))
            print(f"Saved best model (val_loss: {val_loss:.4f})")
    
    # Save final model
    torch.save({
        'epoch': n_epochs,
        'model_state_dict': model.state_dict(),
        'train_losses': train_losses,
        'val_losses': val_losses,
        'sequence_length': sequence_length,
    }, os.path.join(output_dir, 'final_model_phase2.pt'))
    
    print("\nTraining complete!")
    print(f"Best validation loss: {best_val_loss:.4f}")
    
    return model, train_losses, val_losses


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase1_checkpoint', type=str, default='checkpoints/best_model.pt')
    parser.add_argument('--data_dir', type=str, default='data')
    parser.add_argument('--output_dir', type=str, default='checkpoints_phase2')
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--n_epochs', type=int, default=30)
    parser.add_argument('--sequence_length', type=int, default=10)
    
    args = parser.parse_args()
    
    train_phase2(
        phase1_checkpoint=args.phase1_checkpoint,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        n_epochs=args.n_epochs,
        sequence_length=args.sequence_length
    )

