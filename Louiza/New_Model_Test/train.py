"""
Training script for Large Emotional Model (LEM).
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


class ConsumerDataset(Dataset):
    """Dataset for consumer behavior sequences."""
    
    def __init__(
        self,
        events_df: pd.DataFrame,
        category_to_idx: dict,
        brand_to_idx: dict,
        context_to_idx: dict,
        sequence_length: int = 10
    ):
        self.events_df = events_df.sort_values(['user_id', 'timestep'])
        self.category_to_idx = category_to_idx
        self.brand_to_idx = brand_to_idx
        self.context_to_idx = context_to_idx
        self.sequence_length = sequence_length
        
        # Group by user
        self.user_groups = self.events_df.groupby('user_id')
        self.user_ids = list(self.user_groups.groups.keys())
        
        # Build sequences
        self.sequences = []
        for user_id in self.user_ids:
            user_events = self.user_groups.get_group(user_id).reset_index(drop=True)
            for i in range(len(user_events) - sequence_length):
                seq = user_events.iloc[i:i + sequence_length + 1]
                self.sequences.append({
                    'user_id': user_id,
                    'start_idx': i,
                    'end_idx': i + sequence_length
                })
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        seq_info = self.sequences[idx]
        user_id = seq_info['user_id']
        user_events = self.user_groups.get_group(user_id).reset_index(drop=True)
        
        start = seq_info['start_idx']
        end = seq_info['end_idx'] + 1
        
        seq_events = user_events.iloc[start:end]
        
        # Convert to indices
        categories = [self.category_to_idx[c] for c in seq_events['category'].values]
        brands = [self.brand_to_idx.get(b, self.brand_to_idx['none']) for b in seq_events['brand'].values]
        
        time_of_day = [self.context_to_idx['time_of_day'][t] for t in seq_events['time_of_day'].values]
        day_type = [self.context_to_idx['day_type'][d] for d in seq_events['day_type'].values]
        promo = [self.context_to_idx['promo_exposure'][p] for p in seq_events['promo_exposure'].values]
        social = [self.context_to_idx['social_context'][s] for s in seq_events['social_context'].values]
        
        spends = seq_events['spend'].values.astype(np.float32)
        
        return {
            'category': torch.tensor(categories, dtype=torch.long),
            'brand': torch.tensor(brands, dtype=torch.long),
            'time_of_day': torch.tensor(time_of_day, dtype=torch.long),
            'day_type': torch.tensor(day_type, dtype=torch.long),
            'promo': torch.tensor(promo, dtype=torch.long),
            'social': torch.tensor(social, dtype=torch.long),
            'spend': torch.tensor(spends, dtype=torch.float32),
            'user_id': user_id
        }


def create_vocabularies(events_df: pd.DataFrame):
    """Create vocabulary mappings."""
    categories = sorted(events_df['category'].unique())
    brands = sorted([b for b in events_df['brand'].unique() if b != 'none'])
    brands = ['none'] + brands  # 'none' first
    
    category_to_idx = {cat: idx for idx, cat in enumerate(categories)}
    brand_to_idx = {brand: idx for idx, brand in enumerate(brands)}
    
    context_to_idx = {
        'time_of_day': {val: idx for idx, val in enumerate(sorted(events_df['time_of_day'].unique()))},
        'day_type': {val: idx for idx, val in enumerate(sorted(events_df['day_type'].unique()))},
        'promo_exposure': {val: idx for idx, val in enumerate(sorted(events_df['promo_exposure'].unique()))},
        'social_context': {val: idx for idx, val in enumerate(sorted(events_df['social_context'].unique()))}
    }
    
    return category_to_idx, brand_to_idx, context_to_idx


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
    """Main training loop."""
    # Hyperparameters
    batch_size = 128
    sequence_length = 50
    learning_rate = 0.001
    n_epochs = 2
    alpha = 1.0  # NLL weight
    beta = 0   # Smoothness weight
    gamma = 0  # Entropy regularization weight
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
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
    
    # Create model
    model = LEM(
        n_categories=len(category_to_idx),
        n_brands=len(brand_to_idx) - 1,  # Exclude 'none'
        latent_dim=64,
        hidden_dim=128,
        n_layers=2
    ).to(device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    
    # Training loop
    best_val_nll = float('inf')
    train_history = []
    val_history = []
    
    for epoch in range(n_epochs):
        print(f"\nEpoch {epoch + 1}/{n_epochs}")
        
        # Train
        train_metrics = train_epoch(model, train_loader, optimizer, device, alpha, beta, gamma)
        train_history.append(train_metrics)
        
        # Validate
        val_metrics = validate(model, val_loader, device)
        val_history.append(val_metrics)
        
        scheduler.step(val_metrics['nll'])
        
        print(f"Train Loss: {train_metrics['loss']:.4f}, NLL: {train_metrics['nll']:.4f}")
        print(f"Val NLL: {val_metrics['nll']:.4f}, Accuracy: {val_metrics['accuracy']:.4f}, Entropy: {val_metrics['entropy']:.4f}")
        
        # Save best model
        if val_metrics['nll'] < best_val_nll:
            best_val_nll = val_metrics['nll']
            torch.save({
                'model_state_dict': model.state_dict(),
                'vocab': vocab,
                'epoch': epoch,
                'val_metrics': val_metrics
            }, 'models/lem_best.pt')
            print("Saved best model")
    
    # Save training history
    history = {
        'train': train_history,
        'val': val_history
    }
    with open('eval/training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    print("\nTraining complete!")
    print(f"Best validation NLL: {best_val_nll:.4f}")


if __name__ == '__main__':
    main()

