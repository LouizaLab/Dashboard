"""
Minimal training script - skips text encoding to avoid mutex issues
Uses only tags, nutrition, and category features
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

import torch
torch.set_num_threads(1)

import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from tqdm import tqdm
import json
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle


class MinimalProductDataset(Dataset):
    """Dataset without text encoding - uses only tags, nutrition, category"""
    
    def __init__(self, products_df, tag_vocab=None, category_encoder=None, nutrition_scaler=None):
        self.df = products_df.reset_index(drop=True)
        
        # Build tag vocabulary
        if tag_vocab is None:
            self.tag_vocab = self._build_tag_vocab()
        else:
            self.tag_vocab = tag_vocab
        
        # Build category encoder
        if category_encoder is None:
            self.category_encoder = LabelEncoder()
            self.category_encoder.fit(self.df['category'].fillna('Unknown'))
        else:
            self.category_encoder = category_encoder
        
        # Build nutrition scaler
        if nutrition_scaler is None:
            self.nutrition_scaler = StandardScaler()
            nutrition_data = self._extract_nutrition()
            self.nutrition_scaler.fit(nutrition_data)
        else:
            self.nutrition_scaler = nutrition_scaler
    
    def _build_tag_vocab(self):
        all_tags = set()
        for tags_str in self.df['sensory_tags'].fillna(''):
            if tags_str:
                tags = [t.strip() for t in str(tags_str).split(',')]
                all_tags.update(tags)
        return {tag: idx for idx, tag in enumerate(sorted(all_tags))}
    
    def _extract_nutrition(self):
        nutrition_list = []
        for nut_json in self.df['nutrition_json']:
            if pd.notna(nut_json):
                try:
                    nut = json.loads(nut_json)
                    nutrition_list.append([
                        nut.get('calories', 0),
                        nut.get('sugar_g', 0),
                        nut.get('fat_g', 0),
                        nut.get('protein_g', 0),
                        nut.get('sodium_mg', 0),
                        nut.get('caffeine_mg', 0)
                    ])
                except:
                    nutrition_list.append([0, 0, 0, 0, 0, 0])
            else:
                nutrition_list.append([0, 0, 0, 0, 0, 0])
        return np.array(nutrition_list)
    
    def _get_tag_indices(self, tags_str):
        tag_vector = torch.zeros(len(self.tag_vocab), dtype=torch.float32)
        if pd.notna(tags_str) and tags_str:
            tags = [t.strip() for t in str(tags_str).split(',')]
            for tag in tags:
                if tag in self.tag_vocab:
                    tag_vector[self.tag_vocab[tag]] = 1.0
        return tag_vector
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Dummy text embedding (zeros) - we'll skip text for now
        text_emb = torch.zeros(384)  # Match expected dimension
        
        # Tag indices
        tag_indices = self._get_tag_indices(row.get('sensory_tags', ''))
        
        # Nutrition
        nutrition = [0, 0, 0, 0, 0, 0]
        if pd.notna(row.get('nutrition_json')):
            try:
                nut = json.loads(row['nutrition_json'])
                nutrition = [
                    nut.get('calories', 0),
                    nut.get('sugar_g', 0),
                    nut.get('fat_g', 0),
                    nut.get('protein_g', 0),
                    nut.get('sodium_mg', 0),
                    nut.get('caffeine_mg', 0)
                ]
            except:
                pass
        
        nutrition = torch.tensor(nutrition, dtype=torch.float32)
        nutrition = torch.tensor(
            self.nutrition_scaler.transform([nutrition.numpy()])[0],
            dtype=torch.float32
        )
        
        # Category
        category = str(row.get('category', 'Unknown'))
        category_id = self.category_encoder.transform([category])[0]
        category_id = torch.tensor(category_id, dtype=torch.long)
        
        # Label
        label = category_id.item()
        
        return {
            'text': text_emb,
            'tag_indices': tag_indices,
            'nutrition': nutrition,
            'category_id': category_id,
            'label': label,
            'product_id': row['product_id'],
            'product_name': row['product_name']
        }


class MinimalProductModel(nn.Module):
    """Simplified model without text encoder"""
    
    def __init__(self, tag_vocab_size, category_vocab_size, hidden_dim=256, output_dim=128):
        super().__init__()
        
        # Tag embeddings (multi-hot)
        self.tag_proj = nn.Sequential(
            nn.Linear(tag_vocab_size, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Nutrition projection
        self.nutrition_proj = nn.Sequential(
            nn.Linear(6, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Category embedding
        self.category_embedding = nn.Embedding(category_vocab_size, hidden_dim // 4)
        self.category_proj = nn.Linear(hidden_dim // 4, hidden_dim // 4)
        
        # Fusion (no text features)
        fusion_dim = hidden_dim // 2 + hidden_dim // 4 + hidden_dim // 4
        
        self.fusion = nn.Sequential(
            nn.Linear(fusion_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, tag_indices, nutrition, category_ids):
        # Tag features
        tag_features = self.tag_proj(tag_indices)
        
        # Nutrition features
        nutrition_features = self.nutrition_proj(nutrition)
        
        # Category features
        if category_ids.dim() > 1:
            category_ids = category_ids.squeeze(-1)
        category_emb = self.category_embedding(category_ids)
        category_features = self.category_proj(category_emb)
        
        # Concatenate
        combined = torch.cat([tag_features, nutrition_features, category_features], dim=1)
        
        # Final projection
        z_product = self.fusion(combined)
        
        # L2 normalize
        z_product = nn.functional.normalize(z_product, p=2, dim=1)
        
        return z_product


class ContrastiveLoss(nn.Module):
    def __init__(self, margin=1.0, temperature=0.1):
        super().__init__()
        self.margin = margin
        self.temperature = temperature
    
    def forward(self, embeddings, labels):
        batch_size = embeddings.size(0)
        similarity_matrix = torch.matmul(embeddings, embeddings.t())
        
        labels = labels.unsqueeze(1)
        positive_mask = (labels == labels.t()).float()
        negative_mask = 1 - positive_mask
        positive_mask.fill_diagonal_(0)
        
        similarity_matrix = similarity_matrix / self.temperature
        
        positive_loss = -torch.log(torch.sigmoid(similarity_matrix) + 1e-8) * positive_mask
        positive_loss = positive_loss.sum() / (positive_mask.sum() + 1e-8)
        
        negative_loss = -torch.log(torch.sigmoid(-similarity_matrix) + 1e-8) * negative_mask
        negative_loss = negative_loss.sum() / (negative_mask.sum() + 1e-8)
        
        return positive_loss + negative_loss


def train_epoch(model, train_loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    for batch in tqdm(train_loader, desc="Training"):
        tag_indices = batch['tag_indices'].to(device)
        nutrition = batch['nutrition'].to(device)
        category_ids = batch['category_id'].to(device)
        labels = batch['label'].to(device)
        
        embeddings = model(tag_indices, nutrition, category_ids)
        loss = criterion(embeddings, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def validate(model, val_loader, criterion, device):
    model.eval()
    total_loss = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validating"):
            tag_indices = batch['tag_indices'].to(device)
            nutrition = batch['nutrition'].to(device)
            category_ids = batch['category_id'].to(device)
            labels = batch['label'].to(device)
            
            embeddings = model(tag_indices, nutrition, category_ids)
            loss = criterion(embeddings, labels)
            
            total_loss += loss.item()
            n_batches += 1
    
    return total_loss / n_batches if n_batches > 0 else 0.0


def main():
    parser = argparse.ArgumentParser(description='Minimal Training (no text encoding)')
    parser.add_argument('--data', type=str, default='data/processed/products.csv')
    parser.add_argument('--output_dir', type=str, default='models')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--hidden_dim', type=int, default=256)
    parser.add_argument('--output_dim', type=int, default=128)
    parser.add_argument('--train_ratio', type=float, default=0.8)
    
    args = parser.parse_args()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load data
    data_path = Path(args.data)
    products_df = pd.read_csv(data_path)
    print(f"Loaded {len(products_df)} products")
    
    # Split data
    n = len(products_df)
    n_train = int(n * args.train_ratio)
    train_df = products_df.iloc[:n_train].copy()
    val_df = products_df.iloc[n_train:].copy()
    
    # Create datasets
    train_dataset = MinimalProductDataset(train_df)
    val_dataset = MinimalProductDataset(
        val_df,
        tag_vocab=train_dataset.tag_vocab,
        category_encoder=train_dataset.category_encoder,
        nutrition_scaler=train_dataset.nutrition_scaler
    )
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    print(f"Tag vocab size: {len(train_dataset.tag_vocab)}")
    print(f"Category vocab size: {len(train_dataset.category_encoder.classes_)}")
    
    # Create model
    model = MinimalProductModel(
        tag_vocab_size=len(train_dataset.tag_vocab),
        category_vocab_size=len(train_dataset.category_encoder.classes_),
        hidden_dim=args.hidden_dim,
        output_dim=args.output_dim
    ).to(device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Training setup
    criterion = ContrastiveLoss(margin=1.0, temperature=0.1)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    print("\nStarting training (without text features)...")
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
            model_path = output_dir / 'best_model_minimal.pt'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'train_loss': train_loss,
                'tag_vocab': train_dataset.tag_vocab,
                'category_classes': train_dataset.category_encoder.classes_.tolist(),
                'nutrition_scaler_mean': train_dataset.nutrition_scaler.mean_.tolist(),
                'nutrition_scaler_scale': train_dataset.nutrition_scaler.scale_.tolist(),
            }, model_path)
            print(f"  ✓ Saved best model (val_loss: {val_loss:.4f})")
    
    print(f"\n✓ Training complete! Best val loss: {best_val_loss:.4f}")


if __name__ == '__main__':
    main()

