"""
Phase 1: Taste Embedding Models
Product, Context, and Segment Embedding architectures
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class ProductEmbeddingModel(nn.Module):
    """
    Encodes product metadata into z_product embedding
    Input: ingredients, sensory tags, nutrition, description text
    Output: z_product (128D vector)
    """
    
    def __init__(self, 
                 vocab_size: int = 100,
                 embedding_dim: int = 64,
                 hidden_dim: int = 128,
                 output_dim: int = 128,
                 max_ingredients: int = 10,
                 max_tags: int = 8):
        super().__init__()
        
        # Ingredient embeddings
        self.ingredient_embedding = nn.Embedding(vocab_size, embedding_dim)
        
        # Sensory tag embeddings
        self.tag_embedding = nn.Embedding(vocab_size, embedding_dim)
        
        # Nutrition features (sugar, caffeine, calories, protein)
        self.nutrition_proj = nn.Linear(4, embedding_dim)
        
        # Text description encoder (simple LSTM)
        self.text_embedding = nn.Embedding(vocab_size, embedding_dim)
        self.text_lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        
        # Combine all features
        # Ingredients: max_ingredients * embedding_dim
        # Tags: max_tags * embedding_dim  
        # Nutrition: embedding_dim
        # Text: hidden_dim * 2 (bidirectional)
        combined_dim = max_ingredients * embedding_dim + max_tags * embedding_dim + embedding_dim + hidden_dim * 2
        
        self.fusion = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.max_ingredients = max_ingredients
        self.max_tags = max_tags
    
    def forward(self, ingredient_ids, tag_ids, nutrition, text_ids=None):
        """
        Args:
            ingredient_ids: [batch_size, max_ingredients] - tokenized ingredient IDs
            tag_ids: [batch_size, max_tags] - tokenized tag IDs
            nutrition: [batch_size, 4] - [sugar, caffeine, calories, protein]
            text_ids: [batch_size, seq_len] - tokenized description (optional)
        """
        batch_size = ingredient_ids.size(0)
        
        # Embed ingredients
        ingredient_emb = self.ingredient_embedding(ingredient_ids)  # [B, max_ing, emb_dim]
        ingredient_emb = ingredient_emb.view(batch_size, -1)  # [B, max_ing * emb_dim]
        
        # Embed tags
        tag_emb = self.tag_embedding(tag_ids)  # [B, max_tags, emb_dim]
        tag_emb = tag_emb.view(batch_size, -1)  # [B, max_tags * emb_dim]
        
        # Project nutrition
        nutrition_emb = self.nutrition_proj(nutrition)  # [B, emb_dim]
        
        # Encode text description
        if text_ids is not None and text_ids.size(1) > 0:
            text_emb = self.text_embedding(text_ids)  # [B, seq_len, emb_dim]
            text_out, (hidden, _) = self.text_lstm(text_emb)
            # Use last hidden state from both directions
            text_features = text_out[:, -1, :]  # [B, hidden_dim * 2]
        else:
            text_features = torch.zeros(batch_size, self.text_lstm.hidden_size * 2, 
                                      device=ingredient_ids.device)
        
        # Concatenate all features
        combined = torch.cat([ingredient_emb, tag_emb, nutrition_emb, text_features], dim=1)
        
        # Final projection
        z_product = self.fusion(combined)
        
        # L2 normalize
        z_product = F.normalize(z_product, p=2, dim=1)
        
        return z_product


class ContextEmbeddingModel(nn.Module):
    """
    Encodes context into z_context embedding
    Input: time-of-day, location, occasion, price
    Output: z_context (64D vector)
    """
    
    def __init__(self,
                 time_of_day_vocab: int = 4,
                 location_vocab: int = 7,
                 occasion_vocab: int = 7,
                 embedding_dim: int = 32,
                 hidden_dim: int = 64,
                 output_dim: int = 64):
        super().__init__()
        
        # Categorical embeddings
        self.time_embedding = nn.Embedding(time_of_day_vocab, embedding_dim)
        self.location_embedding = nn.Embedding(location_vocab, embedding_dim)
        self.occasion_embedding = nn.Embedding(occasion_vocab, embedding_dim)
        
        # Price projection
        self.price_proj = nn.Linear(1, embedding_dim)
        
        # Combine
        combined_dim = embedding_dim * 3 + embedding_dim  # 3 categorical + price
        
        self.fusion = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, time_of_day_ids, location_ids, occasion_ids, price):
        """
        Args:
            time_of_day_ids: [batch_size] - time of day category IDs
            location_ids: [batch_size] - location IDs
            occasion_ids: [batch_size] - occasion IDs
            price: [batch_size, 1] - price value
        """
        # Squeeze dimensions if needed (handle both [B] and [B, 1] cases)
        if time_of_day_ids.dim() > 1:
            time_of_day_ids = time_of_day_ids.squeeze(-1)
        if location_ids.dim() > 1:
            location_ids = location_ids.squeeze(-1)
        if occasion_ids.dim() > 1:
            occasion_ids = occasion_ids.squeeze(-1)
        if price.dim() == 1:
            price = price.unsqueeze(-1)
        
        # Embed categorical features
        time_emb = self.time_embedding(time_of_day_ids)  # [B, emb_dim]
        location_emb = self.location_embedding(location_ids)  # [B, emb_dim]
        occasion_emb = self.occasion_embedding(occasion_ids)  # [B, emb_dim]
        
        # Project price
        price_emb = self.price_proj(price)  # [B, emb_dim]
        
        # Concatenate
        combined = torch.cat([time_emb, location_emb, occasion_emb, price_emb], dim=1)
        
        # Final projection
        z_context = self.fusion(combined)
        
        # L2 normalize
        z_context = F.normalize(z_context, p=2, dim=1)
        
        return z_context


class SegmentEmbeddingModel(nn.Module):
    """
    Encodes user segment into z_segment embedding
    Input: age bucket, region, psychographic
    Output: z_segment (64D vector)
    """
    
    def __init__(self,
                 age_vocab: int = 5,
                 region_vocab: int = 5,
                 psychographic_vocab: int = 5,
                 embedding_dim: int = 32,
                 hidden_dim: int = 64,
                 output_dim: int = 64):
        super().__init__()
        
        # Embedding tables
        self.age_embedding = nn.Embedding(age_vocab, embedding_dim)
        self.region_embedding = nn.Embedding(region_vocab, embedding_dim)
        self.psychographic_embedding = nn.Embedding(psychographic_vocab, embedding_dim)
        
        # Combine
        combined_dim = embedding_dim * 3
        
        self.fusion = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, age_ids, region_ids, psychographic_ids):
        """
        Args:
            age_ids: [batch_size] - age bucket IDs
            region_ids: [batch_size] - region IDs
            psychographic_ids: [batch_size] - psychographic IDs
        """
        # Squeeze dimensions if needed (handle both [B] and [B, 1] cases)
        if age_ids.dim() > 1:
            age_ids = age_ids.squeeze(-1)
        if region_ids.dim() > 1:
            region_ids = region_ids.squeeze(-1)
        if psychographic_ids.dim() > 1:
            psychographic_ids = psychographic_ids.squeeze(-1)
        
        # Embed features
        age_emb = self.age_embedding(age_ids)  # [B, emb_dim]
        region_emb = self.region_embedding(region_ids)  # [B, emb_dim]
        psychographic_emb = self.psychographic_embedding(psychographic_ids)  # [B, emb_dim]
        
        # Concatenate
        combined = torch.cat([age_emb, region_emb, psychographic_emb], dim=1)
        
        # Final projection
        z_segment = self.fusion(combined)
        
        # L2 normalize
        z_segment = F.normalize(z_segment, p=2, dim=1)
        
        return z_segment


class CombinedEmbeddingModel(nn.Module):
    """
    Combines all three embeddings for end-to-end training
    """
    
    def __init__(self, product_model, context_model, segment_model):
        super().__init__()
        self.product_model = product_model
        self.context_model = context_model
        self.segment_model = segment_model
    
    def forward(self, product_inputs, context_inputs, segment_inputs):
        z_product = self.product_model(**product_inputs)
        z_context = self.context_model(**context_inputs)
        z_segment = self.segment_model(**segment_inputs)
        return z_product, z_context, z_segment

