"""
Data utilities for Phase 2: Sequence generation and processing
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple
import random
from datetime import datetime, timedelta

class SequenceDataset(Dataset):
    """
    Dataset for training Phase 2 on sequences of interactions
    Each sample is a sequence of (product, context, preference) tuples
    """
    
    def __init__(self, 
                 intent_logs_df: pd.DataFrame,
                 products_df: pd.DataFrame,
                 contexts_df: pd.DataFrame,
                 segments_df: pd.DataFrame,
                 phase1_models,
                 vocabularies,
                 device='cpu',
                 sequence_length: int = 10,
                 max_sequences_per_user: int = None):
        """
        Args:
            intent_logs_df: DataFrame with intent logs
            phase1_models: Trained Phase 1 models (product, context, segment)
            vocabularies: Vocabularies from Phase 1
            sequence_length: Length of sequences to generate
        """
        self.intent_logs_df = intent_logs_df
        self.products_df = products_df
        self.contexts_df = contexts_df
        self.segments_df = segments_df
        self.phase1_models = phase1_models
        self.vocabularies = vocabularies
        self.device = device
        self.sequence_length = sequence_length
        
        # Group logs by segment_id
        self.segment_logs = {}
        for segment_id in segments_df['segment_id'].unique():
            segment_logs = intent_logs_df[intent_logs_df['segment_id'] == segment_id].copy()
            segment_logs = segment_logs.sort_values('timestamp')
            if max_sequences_per_user:
                segment_logs = segment_logs.head(max_sequences_per_user * sequence_length)
            self.segment_logs[segment_id] = segment_logs
        
        # Create sequences
        self.sequences = self._create_sequences()
        
        # Create mappings
        self._create_mappings()
    
    def _create_mappings(self):
        """Create ID mappings"""
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
    
    def _create_sequences(self):
        """Create sequences from logs"""
        sequences = []
        
        for segment_id, logs in self.segment_logs.items():
            if len(logs) < self.sequence_length:
                continue
            
            # Create overlapping sequences
            for i in range(len(logs) - self.sequence_length + 1):
                sequence = logs.iloc[i:i+self.sequence_length]
                sequences.append({
                    'segment_id': segment_id,
                    'sequence': sequence,
                    'start_idx': i
                })
        
        return sequences
    
    def __len__(self):
        return len(self.sequences)
    
    def _encode_product(self, product_row):
        """Encode product using Phase 1 model"""
        # Encode ingredients
        ingredients = product_row['ingredients'].split(',')
        ingredient_ids = []
        for ing in ingredients[:10]:
            ing_id = self.vocabularies['ingredient'].word_to_idx.get(ing.strip(), 0)
            ingredient_ids.append(ing_id)
        while len(ingredient_ids) < 10:
            ingredient_ids.append(1)
        
        # Encode tags
        tags = product_row['sensory_tags'].split(',')
        tag_ids = []
        for tag in tags[:8]:
            tag_id = self.vocabularies['tag'].word_to_idx.get(tag.strip(), 0)
            tag_ids.append(tag_id)
        while len(tag_ids) < 8:
            tag_ids.append(1)
        
        # Nutrition
        nutrition = torch.FloatTensor([
            product_row['sugar_g'],
            product_row['caffeine_mg'],
            product_row['calories'],
            product_row['protein_g']
        ]).unsqueeze(0)
        
        # Text
        text_ids = self.vocabularies['text'].encode(product_row['description'], 50)
        
        # Encode (keep on CPU, will move to device in training)
        ingredient_ids_t = torch.LongTensor([ingredient_ids])
        tag_ids_t = torch.LongTensor([tag_ids])
        text_ids_t = torch.LongTensor([text_ids])
        
        with torch.no_grad():
            z_product = self.phase1_models['product'](
                ingredient_ids_t, tag_ids_t, nutrition, text_ids_t
            )
        
        return z_product[0]  # Remove batch dimension
    
    def _encode_context(self, context_row):
        """Encode context using Phase 1 model"""
        time_of_day_id = self.time_of_day_to_idx[context_row['time_of_day']]
        location_id = self.location_to_idx[context_row['location']]
        occasion_id = self.occasion_to_idx[context_row['occasion']]
        price = torch.FloatTensor([[context_row['price_shown']]])
        
        time_ids_t = torch.LongTensor([[time_of_day_id]])
        location_ids_t = torch.LongTensor([[location_id]])
        occasion_ids_t = torch.LongTensor([[occasion_id]])
        
        with torch.no_grad():
            z_context = self.phase1_models['context'](
                time_ids_t, location_ids_t, occasion_ids_t, price
            )
        
        return z_context[0]  # Remove batch dimension
    
    def _encode_segment(self, segment_row):
        """Encode segment using Phase 1 model"""
        age_id = self.age_to_idx[segment_row['age_bucket']]
        region_id = self.region_to_idx[segment_row['region']]
        psychographic_id = self.psychographic_to_idx[segment_row['psychographic']]
        
        age_ids_t = torch.LongTensor([[age_id]])
        region_ids_t = torch.LongTensor([[region_id]])
        psychographic_ids_t = torch.LongTensor([[psychographic_id]])
        
        with torch.no_grad():
            z_segment = self.phase1_models['segment'](
                age_ids_t, region_ids_t, psychographic_ids_t
            )
        
        return z_segment[0]  # Remove batch dimension
    
    def __getitem__(self, idx):
        seq_data = self.sequences[idx]
        sequence = seq_data['sequence']
        segment_id = seq_data['segment_id']
        
        # Get segment
        segment = self.segments_df[self.segments_df['segment_id'] == segment_id].iloc[0]
        z_segment = self._encode_segment(segment)
        
        # Encode sequence
        z_products = []
        z_contexts = []
        targets = []
        
        for _, log in sequence.iterrows():
            # Get product
            product = self.products_df[self.products_df['product_id'] == log['product_id']].iloc[0]
            z_product = self._encode_product(product)
            z_products.append(z_product)
            
            # Get context
            context = self.contexts_df[self.contexts_df['context_id'] == log['context_id']].iloc[0]
            z_context = self._encode_context(context)
            z_contexts.append(z_context)
            
            # Target
            target = torch.FloatTensor([log['preference_value']])
            targets.append(target)
        
        # Stack into tensors
        z_products = torch.stack(z_products, dim=0)  # [seq_len, product_dim]
        z_contexts = torch.stack(z_contexts, dim=0)  # [seq_len, context_dim]
        targets = torch.stack(targets, dim=0)  # [seq_len, 1]
        
        return {
            'z_segment': z_segment,
            'z_products': z_products,
            'z_contexts': z_contexts,
            'targets': targets,
            'segment_id': segment_id
        }

