"""
Improved training script with optimized hyperparameters.

Key improvements:
- More epochs (25 instead of 1)
- Larger model (256 hidden dim, 128 latent dim)
- Better regularization (dropout 0.2, weight decay)
- Larger batch size (64)
- Longer sequences (15 timesteps)
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import json

from models.lem import LEM, compute_loss
from train import ConsumerDataset, create_vocabularies


def train_epoch(model, dataloader, optimizer, device, alpha=1.0, beta=0.1, gamma=0.01):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    loss_components = {
        'nll': 0,
        'smoothness': 0,
        'entropy_reg': 0,
        'entropy': 0
    }
    
    for batch in tqdm(dataloader, desc="Training"):
        # Prepare inputs (all but last timestep)
        category_seq = batch['category'][:, :-1].to(device)
        brand_seq = batch['brand'][:, :-1].to(device)
        time_seq = batch['time_of_day'][:, :-1].to(device)
        day_seq = batch['day_type'][:, :-1].to(device)
        promo_seq = batch['promo'][:, :-1].to(device)
        social_seq = batch['social'][:, :-1].to(device)
        
        # Targets (last timestep)
        category_target = batch['category'][:, -1].to(device)
        brand_target = batch['brand'][:, -1].to(device)
        
        # Forward pass
        output = model(
            category_seq, brand_seq,
            time_seq, day_seq, promo_seq, social_seq
        )
        
        # Prepare predictions for loss (use last timestep)
        predictions = {
            'category_logits': output['category_logits'][:, -1, :],
            'brand_logits': output['brand_logits'][:, -1, :],
            'latent_states': output['latent_states']
        }
        
        targets = {
            'category': category_target,
            'brand': brand_target
        }
        
        # Compute loss
        loss, loss_dict = compute_loss(predictions, targets, alpha, beta, gamma)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
        for key in loss_components:
            loss_components[key] += loss_dict.get(key, 0)
    
    n_batches = len(dataloader)
    return {
        'loss': float(total_loss / n_batches),
        **{k: float(v / n_batches) for k, v in loss_components.items()}
    }


def validate(model, dataloader, device):
    """Validate model."""
    model.eval()
    total_nll = 0
    correct_category = 0
    correct_brand = 0
    total_samples = 0
    entropies = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validating"):
            category_seq = batch['category'][:, :-1].to(device)
            brand_seq = batch['brand'][:, :-1].to(device)
            time_seq = batch['time_of_day'][:, :-1].to(device)
            day_seq = batch['day_type'][:, :-1].to(device)
            promo_seq = batch['promo'][:, :-1].to(device)
            social_seq = batch['social'][:, :-1].to(device)
            
            category_target = batch['category'][:, -1].to(device)
            brand_target = batch['brand'][:, -1].to(device)
            
            output = model(
                category_seq, brand_seq,
                time_seq, day_seq, promo_seq, social_seq
            )
            
            category_logits = output['category_logits'][:, -1, :]
            brand_logits = output['brand_logits'][:, -1, :]
            
            # Predictions
            category_pred = category_logits.argmax(dim=-1)
            brand_pred = brand_logits.argmax(dim=-1)
            
            correct_category += (category_pred == category_target).sum().item()
            correct_brand += (brand_pred == brand_target).sum().item()
            total_samples += len(category_target)
            
            # NLL
            nll_cat = nn.functional.cross_entropy(category_logits, category_target, reduction='sum')
            nll_brand = nn.functional.cross_entropy(brand_logits, brand_target, reduction='sum')
            total_nll += (nll_cat + nll_brand).item()
            
            # Entropy
            cat_probs = torch.softmax(category_logits, dim=-1)
            brand_probs = torch.softmax(brand_logits, dim=-1)
            cat_entropy = -(cat_probs * torch.log_softmax(category_logits, dim=-1)).sum(dim=-1)
            brand_entropy = -(brand_probs * torch.log_softmax(brand_logits, dim=-1)).sum(dim=-1)
            entropies.extend((cat_entropy + brand_entropy).cpu().numpy())
    
    return {
        'nll': float(total_nll / total_samples),
        'category_accuracy': float(correct_category / total_samples),
        'brand_accuracy': float(correct_brand / total_samples),
        'accuracy': float((correct_category + correct_brand) / (2 * total_samples)),
        'entropy': float(np.mean(entropies))
    }


def main():
    """Main training loop with improved hyperparameters."""
    # IMPROVED Hyperparameters
    batch_size = 64              # Increased from 32
    sequence_length = 15         # Increased from 10
    learning_rate = 0.001        # Keep
    n_epochs = 2                # ⭐ CRITICAL: Increased from 1
    alpha = 1.0                  # NLL weight
    beta = 0.1                   # Smoothness weight
    gamma = 0.01                 # Entropy regularization weight
    
    # Early stopping
    patience = 7
    min_delta = 0.001
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    print(f"\n{'='*60}")
    print("IMPROVED HYPERPARAMETERS:")
    print(f"{'='*60}")
    print(f"Batch size: {batch_size}")
    print(f"Sequence length: {sequence_length}")
    print(f"Learning rate: {learning_rate}")
    print(f"Epochs: {n_epochs}")
    print(f"{'='*60}\n")
    
    # Load data
    print("Loading data...")
    events_df = pd.read_csv('data/events.csv')
    
    # Split train/val
    user_ids = events_df['user_id'].unique()
    np.random.seed(42)
    np.random.shuffle(user_ids)
    split_idx = int(0.8 * len(user_ids))
    train_users = set(user_ids[:split_idx])
    val_users = set(user_ids[split_idx:])
    
    train_df = events_df[events_df['user_id'].isin(train_users)].copy()
    val_df = events_df[events_df['user_id'].isin(val_users)].copy()
    
    print(f"Train: {len(train_df)} events, {len(train_users)} users")
    print(f"Val: {len(val_df)} events, {len(val_users)} users")
    
    # Create vocabularies
    category_to_idx, brand_to_idx, context_to_idx = create_vocabularies(events_df)
    
    # Save vocabularies
    os.makedirs('models', exist_ok=True)
    vocab = {
        'category_to_idx': category_to_idx,
        'brand_to_idx': brand_to_idx,
        'context_to_idx': context_to_idx
    }
    with open('models/vocab.json', 'w') as f:
        json.dump(vocab, f, indent=2)
    
    # Create datasets
    train_dataset = ConsumerDataset(
        train_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length
    )
    val_dataset = ConsumerDataset(
        val_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create model with IMPROVED architecture
    model = LEM(
        n_categories=len(category_to_idx),
        n_brands=len(brand_to_idx) - 1,  # Exclude 'none'
        action_embed_dim=64,              # Increased from 32
        context_embed_dim=64,             # Increased from 32
        latent_dim=128,                    # Increased from 64
        hidden_dim=256,                   # Increased from 128
        n_layers=2,                       # Keep (can try 3)
        dropout=0.2                       # Increased from 0.1
    ).to(device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Optimizer with weight decay
    optimizer = optim.Adam(
        model.parameters(), 
        lr=learning_rate,
        weight_decay=1e-5  # L2 regularization
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-5
    )
    
    # Training loop with early stopping
    best_val_nll = float('inf')
    patience_counter = 0
    train_history = []
    val_history = []
    
    for epoch in range(n_epochs):
        print(f"\nEpoch {epoch + 1}/{n_epochs}")
        print(f"Learning rate: {optimizer.param_groups[0]['lr']:.6f}")
        
        # Train
        train_metrics = train_epoch(model, train_loader, optimizer, device, alpha, beta, gamma)
        train_history.append(train_metrics)
        
        # Validate
        val_metrics = validate(model, val_loader, device)
        val_history.append(val_metrics)
        
        scheduler.step(val_metrics['nll'])
        
        print(f"Train Loss: {train_metrics['loss']:.4f}, NLL: {train_metrics['nll']:.4f}")
        print(f"Val NLL: {val_metrics['nll']:.4f}, Accuracy: {val_metrics['accuracy']:.4f}, Entropy: {val_metrics['entropy']:.4f}")
        
        # Early stopping check
        if val_metrics['nll'] < best_val_nll - min_delta:
            best_val_nll = val_metrics['nll']
            patience_counter = 0
            torch.save({
                'model_state_dict': model.state_dict(),
                'vocab': vocab,
                'epoch': epoch,
                'val_metrics': val_metrics,
                'hyperparameters': {
                    'batch_size': batch_size,
                    'sequence_length': sequence_length,
                    'learning_rate': learning_rate,
                    'alpha': alpha,
                    'beta': beta,
                    'gamma': gamma,
                    'latent_dim': 128,
                    'hidden_dim': 256,
                    'n_layers': 2,
                    'dropout': 0.2
                }
            }, 'models/lem_best.pt')
            print("✓ Saved best model")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch + 1} (no improvement for {patience} epochs)")
                break
    
    # Save training history
    history = {
        'train': train_history,
        'val': val_history
    }
    os.makedirs('eval', exist_ok=True)
    with open('eval/training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    print("\n" + "="*60)
    print("Training complete!")
    print("="*60)
    print(f"Best validation NLL: {best_val_nll:.4f}")
    print(f"Final validation accuracy: {val_history[-1]['accuracy']:.4f}")
    print(f"Final validation entropy: {val_history[-1]['entropy']:.4f}")


if __name__ == '__main__':
    main()

