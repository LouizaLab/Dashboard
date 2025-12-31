"""
Data loading utilities for Phase 1: Taste Embedding Model
"""

import pandas as pd
import numpy as np
import json
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle


class ProductDataset(Dataset):
    """
    Dataset for product embeddings
    """
    
    def __init__(self, 
                 products_df: pd.DataFrame,
                 text_encoder=None,
                 tag_vocab: Optional[Dict[str, int]] = None,
                 category_encoder: Optional[LabelEncoder] = None,
                 nutrition_scaler: Optional[StandardScaler] = None,
                 device: str = 'cpu'):
        self.df = products_df.reset_index(drop=True)
        self.device = device
        
        # Text encoder (sentence-transformers)
        self.text_encoder = text_encoder
        
        # Build tag vocabulary if not provided
        if tag_vocab is None:
            self.tag_vocab = self._build_tag_vocab()
        else:
            self.tag_vocab = tag_vocab
        
        # Build category encoder if not provided
        if category_encoder is None:
            self.category_encoder = LabelEncoder()
            self.category_encoder.fit(self.df['category'].fillna('Unknown'))
        else:
            self.category_encoder = category_encoder
        
        # Build nutrition scaler if not provided
        if nutrition_scaler is None:
            self.nutrition_scaler = StandardScaler()
            nutrition_data = self._extract_nutrition()
            self.nutrition_scaler.fit(nutrition_data)
        else:
            self.nutrition_scaler = nutrition_scaler
        
        # Pre-compute text embeddings if encoder is available
        self.text_embeddings = None
        if self.text_encoder is not None:
            self._precompute_text_embeddings()
    
    def _build_tag_vocab(self) -> Dict[str, int]:
        """Build vocabulary for sensory tags"""
        all_tags = set()
        for tags_str in self.df['sensory_tags'].fillna(''):
            if tags_str:
                tags = [t.strip() for t in str(tags_str).split(',')]
                all_tags.update(tags)
        
        tag_vocab = {tag: idx for idx, tag in enumerate(sorted(all_tags))}
        return tag_vocab
    
    def _extract_nutrition(self) -> np.ndarray:
        """Extract nutrition features as numpy array"""
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
    
    def _precompute_text_embeddings(self):
        """Pre-compute text embeddings for all products"""
        print("Pre-computing text embeddings...")
        import os
        import threading
        # Avoid tokenizer lock issues
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['OMP_NUM_THREADS'] = '1'
        
        # Ensure single-threaded encoding
        if hasattr(threading, 'main_thread'):
            # Use main thread only
            pass
        
        texts = []
        for idx, row in self.df.iterrows():
            # Combine description and ingredients
            desc = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
            ing = str(row.get('ingredients', '')) if pd.notna(row.get('ingredients')) else ''
            text = f"{desc} {ing}".strip()
            if not text:
                text = str(row.get('product_name', ''))
            texts.append(text)
        
        # Encode in batches
        batch_size = 32
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f"  Encoding batch {batch_num}/{total_batches}...")
            batch_emb = self.text_encoder.encode(batch_texts, convert_to_tensor=True, device=self.device, show_progress_bar=False)
            embeddings.append(batch_emb.cpu())
        
        self.text_embeddings = torch.cat(embeddings, dim=0)
        print(f"✓ Pre-computed {len(self.text_embeddings)} text embeddings")
    
    def _get_tag_indices(self, tags_str: str) -> torch.Tensor:
        """Convert tag string to multi-hot vector"""
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
        
        # Text embedding
        if self.text_embeddings is not None:
            text_emb = self.text_embeddings[idx]
        else:
            # Fallback: create dummy embedding
            text_emb = torch.zeros(384)  # Default dimension for all-MiniLM-L6-v2
        
        # Tag indices (multi-hot)
        tag_indices = self._get_tag_indices(row.get('sensory_tags', ''))
        
        # Nutrition features
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
        
        # Category ID
        category = str(row.get('category', 'Unknown'))
        category_id = self.category_encoder.transform([category])[0]
        category_id = torch.tensor(category_id, dtype=torch.long)
        
        # Label for contrastive learning (use category as similarity proxy)
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


def create_data_loaders(products_df: pd.DataFrame,
                       text_encoder,
                       train_ratio: float = 0.8,
                       batch_size: int = 32,
                       device: str = 'cpu') -> Tuple[DataLoader, DataLoader, Dict]:
    """
    Create train and validation data loaders
    
    Returns:
        train_loader, val_loader, metadata (vocabularies, encoders, scalers)
    """
    # Split data
    n = len(products_df)
    n_train = int(n * train_ratio)
    train_df = products_df.iloc[:n_train].copy()
    val_df = products_df.iloc[n_train:].copy()
    
    # Create datasets
    train_dataset = ProductDataset(train_df, text_encoder=text_encoder, device=device)
    
    # Use same vocabularies and encoders for validation
    val_dataset = ProductDataset(
        val_df,
        text_encoder=text_encoder,
        tag_vocab=train_dataset.tag_vocab,
        category_encoder=train_dataset.category_encoder,
        nutrition_scaler=train_dataset.nutrition_scaler,
        device=device
    )
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Metadata
    metadata = {
        'tag_vocab': train_dataset.tag_vocab,
        'category_encoder': train_dataset.category_encoder,
        'nutrition_scaler': train_dataset.nutrition_scaler,
        'tag_vocab_size': len(train_dataset.tag_vocab),
        'category_vocab_size': len(train_dataset.category_encoder.classes_)
    }
    
    return train_loader, val_loader, metadata


def save_metadata(metadata: Dict, save_path: Path):
    """Save metadata (vocabularies, encoders, scalers)"""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays and sklearn objects to serializable format
    save_dict = {
        'tag_vocab': metadata['tag_vocab'],
        'tag_vocab_size': metadata['tag_vocab_size'],
        'category_vocab_size': metadata['category_vocab_size'],
        'category_classes': metadata['category_encoder'].classes_.tolist(),
        'nutrition_scaler_mean': metadata['nutrition_scaler'].mean_.tolist(),
        'nutrition_scaler_scale': metadata['nutrition_scaler'].scale_.tolist()
    }
    
    with open(save_path, 'wb') as f:
        pickle.dump(save_dict, f)
    
    # Also save sklearn objects separately
    sklearn_path = save_path.parent / (save_path.stem + '_sklearn.pkl')
    sklearn_dict = {
        'category_encoder': metadata['category_encoder'],
        'nutrition_scaler': metadata['nutrition_scaler']
    }
    with open(sklearn_path, 'wb') as f:
        pickle.dump(sklearn_dict, f)


def load_metadata(load_path: Path) -> Dict:
    """Load metadata"""
    with open(load_path, 'rb') as f:
        metadata = pickle.load(f)
    
    # Load sklearn objects
    sklearn_path = load_path.parent / (load_path.stem + '_sklearn.pkl')
    with open(sklearn_path, 'rb') as f:
        sklearn_metadata = pickle.load(f)
    
    metadata.update(sklearn_metadata)
    return metadata

