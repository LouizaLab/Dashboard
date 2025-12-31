"""
Data preprocessing and encoding utilities for Phase 1
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple
import re

class Vocabulary:
    """Simple vocabulary builder for text tokens"""
    
    def __init__(self):
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.word_counts = {}
        self.unk_token = '<UNK>'
        self.pad_token = '<PAD>'
        self.unk_idx = 0
        self.pad_idx = 1
        
    def build(self, texts: List[str], min_count: int = 1):
        """Build vocabulary from texts"""
        # Reset
        self.word_to_idx = {self.unk_token: self.unk_idx, self.pad_token: self.pad_idx}
        self.idx_to_word = {self.unk_idx: self.unk_token, self.pad_idx: self.pad_token}
        self.word_counts = {}
        
        # Count words
        for text in texts:
            words = self._tokenize(text)
            for word in words:
                self.word_counts[word] = self.word_counts.get(word, 0) + 1
        
        # Build vocab (starting from index 2)
        idx = 2
        for word, count in sorted(self.word_counts.items()):
            if count >= min_count:
                self.word_to_idx[word] = idx
                self.idx_to_word[idx] = word
                idx += 1
        
        return len(self.word_to_idx)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()
    
    def encode(self, text: str, max_len: int = None) -> List[int]:
        """Encode text to sequence of indices"""
        words = self._tokenize(text)
        indices = [self.word_to_idx.get(word, self.unk_idx) for word in words]
        
        if max_len:
            if len(indices) > max_len:
                indices = indices[:max_len]
            else:
                indices = indices + [self.pad_idx] * (max_len - len(indices))
        
        return indices


class EmbeddingDataset(Dataset):
    """Dataset for training embeddings"""
    
    def __init__(self, products_df: pd.DataFrame, contexts_df: pd.DataFrame,
                 segments_df: pd.DataFrame, intent_logs_df: pd.DataFrame,
                 vocabularies: Dict, max_ingredients: int = 10, max_tags: int = 8,
                 max_text_len: int = 50):
        self.products_df = products_df
        self.contexts_df = contexts_df
        self.segments_df = segments_df
        self.intent_logs_df = intent_logs_df
        
        self.vocabularies = vocabularies
        self.max_ingredients = max_ingredients
        self.max_tags = max_tags
        self.max_text_len = max_text_len
        
        # Create lookup dictionaries
        self.product_lookup = {row['product_id']: idx for idx, row in products_df.iterrows()}
        self.context_lookup = {row['context_id']: idx for idx, row in contexts_df.iterrows()}
        self.segment_lookup = {row['segment_id']: idx for idx, row in segments_df.iterrows()}
        
        # Create mappings for categorical features
        self._create_mappings()
    
    def _create_mappings(self):
        """Create ID mappings for categorical features"""
        # Time of day
        time_of_days = sorted(self.contexts_df['time_of_day'].unique())
        self.time_of_day_to_idx = {td: idx for idx, td in enumerate(time_of_days)}
        
        # Location
        locations = sorted(self.contexts_df['location'].unique())
        self.location_to_idx = {loc: idx for idx, loc in enumerate(locations)}
        
        # Occasion
        occasions = sorted(self.contexts_df['occasion'].unique())
        self.occasion_to_idx = {occ: idx for idx, occ in enumerate(occasions)}
        
        # Age bucket
        age_buckets = sorted(self.segments_df['age_bucket'].unique())
        self.age_to_idx = {age: idx for idx, age in enumerate(age_buckets)}
        
        # Region
        regions = sorted(self.segments_df['region'].unique())
        self.region_to_idx = {reg: idx for idx, reg in enumerate(regions)}
        
        # Psychographic
        psychographics = sorted(self.segments_df['psychographic'].unique())
        self.psychographic_to_idx = {psy: idx for idx, psy in enumerate(psychographics)}
    
    def __len__(self):
        return len(self.intent_logs_df)
    
    def __getitem__(self, idx):
        log = self.intent_logs_df.iloc[idx]
        
        # Get product data
        product_idx = self.product_lookup[log['product_id']]
        product = self.products_df.iloc[product_idx]
        
        # Encode ingredients
        ingredients = product['ingredients'].split(',')
        ingredient_ids = []
        for ing in ingredients[:self.max_ingredients]:
            ing_id = self.vocabularies['ingredient'].word_to_idx.get(ing.strip(), 0)
            ingredient_ids.append(ing_id)
        # Pad
        while len(ingredient_ids) < self.max_ingredients:
            ingredient_ids.append(1)  # PAD
        
        # Encode tags
        tags = product['sensory_tags'].split(',')
        tag_ids = []
        for tag in tags[:self.max_tags]:
            tag_id = self.vocabularies['tag'].word_to_idx.get(tag.strip(), 0)
            tag_ids.append(tag_id)
        # Pad
        while len(tag_ids) < self.max_tags:
            tag_ids.append(1)  # PAD
        
        # Nutrition
        nutrition = torch.FloatTensor([
            product['sugar_g'],
            product['caffeine_mg'],
            product['calories'],
            product['protein_g']
        ])
        
        # Encode description
        text_ids = self.vocabularies['text'].encode(product['description'], self.max_text_len)
        
        # Get context data
        context_idx = self.context_lookup[log['context_id']]
        context = self.contexts_df.iloc[context_idx]
        
        time_of_day_id = self.time_of_day_to_idx[context['time_of_day']]
        location_id = self.location_to_idx[context['location']]
        occasion_id = self.occasion_to_idx[context['occasion']]
        price = torch.FloatTensor([context['price_shown']])
        
        # Get segment data
        segment_idx = self.segment_lookup[log['segment_id']]
        segment = self.segments_df.iloc[segment_idx]
        
        age_id = self.age_to_idx[segment['age_bucket']]
        region_id = self.region_to_idx[segment['region']]
        psychographic_id = self.psychographic_to_idx[segment['psychographic']]
        
        # Target (preference value)
        target = torch.FloatTensor([log['preference_value']])
        
        return {
            'product': {
                'ingredient_ids': torch.LongTensor(ingredient_ids),
                'tag_ids': torch.LongTensor(tag_ids),
                'nutrition': nutrition,
                'text_ids': torch.LongTensor(text_ids)
            },
            'context': {
                'time_of_day_ids': torch.tensor(time_of_day_id, dtype=torch.long),
                'location_ids': torch.tensor(location_id, dtype=torch.long),
                'occasion_ids': torch.tensor(occasion_id, dtype=torch.long),
                'price': price
            },
            'segment': {
                'age_ids': torch.tensor(age_id, dtype=torch.long),
                'region_ids': torch.tensor(region_id, dtype=torch.long),
                'psychographic_ids': torch.tensor(psychographic_id, dtype=torch.long)
            },
            'target': target,
            'product_id': product['product_id'],
            'segment_id': segment['segment_id'],
            'context_id': context['context_id']
        }


def build_vocabularies(products_df: pd.DataFrame) -> Dict:
    """Build vocabularies from product data"""
    vocabularies = {
        'ingredient': Vocabulary(),
        'tag': Vocabulary(),
        'text': Vocabulary()
    }
    
    # Build ingredient vocabulary
    all_ingredients = []
    for ingredients_str in products_df['ingredients']:
        all_ingredients.extend([ing.strip() for ing in ingredients_str.split(',')])
    vocabularies['ingredient'].build(all_ingredients, min_count=1)
    
    # Build tag vocabulary
    all_tags = []
    for tags_str in products_df['sensory_tags']:
        all_tags.extend([tag.strip() for tag in tags_str.split(',')])
    vocabularies['tag'].build(all_tags, min_count=1)
    
    # Build text vocabulary
    all_descriptions = products_df['description'].tolist()
    vocabularies['text'].build(all_descriptions, min_count=1)
    
    return vocabularies

