"""
Training script for Phase 1: Taste Embedding Model
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
from tqdm import tqdm
import os
import json
from datetime import datetime

from models import ProductEmbeddingModel, ContextEmbeddingModel, SegmentEmbeddingModel, CombinedEmbeddingModel
from data_utils import EmbeddingDataset, build_vocabularies

class PreferencePredictor(nn.Module):
    """
    Predicts preference/like probability from embeddings
    Used for training embeddings via preference prediction task
    """
    def __init__(self, product_dim: int = 128, context_dim: int = 64, segment_dim: int = 64):
        super().__init__()
        combined_dim = product_dim + context_dim + segment_dim
        self.predictor = nn.Sequential(
            nn.Linear(combined_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, z_product, z_context, z_segment):
        combined = torch.cat([z_product, z_context, z_segment], dim=1)
        return self.predictor(combined)


def train_epoch(model, predictor, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    predictor.train()
    total_loss = 0.0
    n_batches = 0
    
    for batch in tqdm(dataloader, desc="Training"):
        # Move to device
        product_inputs = {k: v.to(device) for k, v in batch['product'].items()}
        context_inputs = {k: v.to(device) for k, v in batch['context'].items()}
        segment_inputs = {k: v.to(device) for k, v in batch['segment'].items()}
        targets = batch['target'].to(device)
        
        # Forward pass
        z_product, z_context, z_segment = model(product_inputs, context_inputs, segment_inputs)
        
        # Predict preference
        pred = predictor(z_product, z_context, z_segment)
        
        # Loss
        loss = criterion(pred, targets)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def validate(model, predictor, dataloader, criterion, device):
    """Validate model"""
    model.eval()
    predictor.eval()
    total_loss = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validating"):
            product_inputs = {k: v.to(device) for k, v in batch['product'].items()}
            context_inputs = {k: v.to(device) for k, v in batch['context'].items()}
            segment_inputs = {k: v.to(device) for k, v in batch['segment'].items()}
            targets = batch['target'].to(device)
            
            z_product, z_context, z_segment = model(product_inputs, context_inputs, segment_inputs)
            pred = predictor(z_product, z_context, z_segment)
            loss = criterion(pred, targets)
            
            total_loss += loss.item()
            n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def train_phase1(data_dir: str = 'data', 
                output_dir: str = 'checkpoints',
                batch_size: int = 32,
                learning_rate: float = 0.001,
                n_epochs: int = 50,
                device: str = None):
    """Main training function"""
    
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Load data
    print("Loading data...")
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
    segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
    intent_logs_df = pd.read_csv(os.path.join(data_dir, 'intent_logs.csv'))
    
    # Build vocabularies
    print("Building vocabularies...")
    vocabularies = build_vocabularies(products_df)
    
    # Get vocabulary sizes
    ingredient_vocab_size = len(vocabularies['ingredient'].word_to_idx)
    tag_vocab_size = len(vocabularies['tag'].word_to_idx)
    text_vocab_size = len(vocabularies['text'].word_to_idx)
    
    print(f"Ingredient vocab size: {ingredient_vocab_size}")
    print(f"Tag vocab size: {tag_vocab_size}")
    print(f"Text vocab size: {text_vocab_size}")
    
    # Create dataset
    dataset = EmbeddingDataset(
        products_df, contexts_df, segments_df, intent_logs_df,
        vocabularies, max_ingredients=10, max_tags=8, max_text_len=50
    )
    
    # Split train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create models
    print("Initializing models...")
    
    # Get vocab sizes for context and segment
    time_of_days = sorted(contexts_df['time_of_day'].unique())
    locations = sorted(contexts_df['location'].unique())
    occasions = sorted(contexts_df['occasion'].unique())
    age_buckets = sorted(segments_df['age_bucket'].unique())
    regions = sorted(segments_df['region'].unique())
    psychographics = sorted(segments_df['psychographic'].unique())
    
    product_model = ProductEmbeddingModel(
        vocab_size=max(ingredient_vocab_size, tag_vocab_size, text_vocab_size),
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
    
    combined_model = CombinedEmbeddingModel(product_model, context_model, segment_model)
    predictor = PreferencePredictor(product_dim=128, context_dim=64, segment_dim=64)
    
    combined_model = combined_model.to(device)
    predictor = predictor.to(device)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(
        list(combined_model.parameters()) + list(predictor.parameters()),
        lr=learning_rate
    )
    
    # Training loop
    print("Starting training...")
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    for epoch in range(n_epochs):
        print(f"\nEpoch {epoch+1}/{n_epochs}")
        
        train_loss = train_epoch(combined_model, predictor, train_loader, criterion, optimizer, device)
        val_loss = validate(combined_model, predictor, val_loader, criterion, device)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            checkpoint = {
                'epoch': epoch,
                'product_model_state_dict': product_model.state_dict(),
                'context_model_state_dict': context_model.state_dict(),
                'segment_model_state_dict': segment_model.state_dict(),
                'predictor_state_dict': predictor.state_dict(),
                'vocabularies': vocabularies,
                'train_losses': train_losses,
                'val_losses': val_losses,
                'vocab_sizes': {
                    'ingredient': ingredient_vocab_size,
                    'tag': tag_vocab_size,
                    'text': text_vocab_size,
                    'time_of_day': len(time_of_days),
                    'location': len(locations),
                    'occasion': len(occasions),
                    'age': len(age_buckets),
                    'region': len(regions),
                    'psychographic': len(psychographics)
                }
            }
            torch.save(checkpoint, os.path.join(output_dir, 'best_model.pt'))
            print(f"Saved best model (val_loss: {val_loss:.4f})")
    
    # Save final model
    checkpoint = {
        'epoch': n_epochs,
        'product_model_state_dict': product_model.state_dict(),
        'context_model_state_dict': context_model.state_dict(),
        'segment_model_state_dict': segment_model.state_dict(),
        'predictor_state_dict': predictor.state_dict(),
        'vocabularies': vocabularies,
        'train_losses': train_losses,
        'val_losses': val_losses,
        'vocab_sizes': {
            'ingredient': ingredient_vocab_size,
            'tag': tag_vocab_size,
            'text': text_vocab_size,
            'time_of_day': len(time_of_days),
            'location': len(locations),
            'occasion': len(occasions),
            'age': len(age_buckets),
            'region': len(regions),
            'psychographic': len(psychographics)
        }
    }
    torch.save(checkpoint, os.path.join(output_dir, 'final_model.pt'))
    
    print("\nTraining complete!")
    print(f"Best validation loss: {best_val_loss:.4f}")
    
    return combined_model, predictor, vocabularies, train_losses, val_losses


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='data')
    parser.add_argument('--output_dir', type=str, default='checkpoints')
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--n_epochs', type=int, default=50)
    
    args = parser.parse_args()
    
    train_phase1(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        n_epochs=args.n_epochs
    )

