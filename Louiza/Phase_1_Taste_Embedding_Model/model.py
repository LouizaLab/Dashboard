"""
Phase 1: Taste Embedding Model
Product embedding architecture for food & beverage products
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, Optional


class ProductEmbeddingModel(nn.Module):
    """
    Encodes product metadata into z_product embedding
    
    Input modalities:
    - Text: description + ingredients (using sentence-transformers)
    - Sensory tags: multi-hot encoding
    - Nutrition: normalized numeric features
    - Category: categorical embedding
    
    Output: z_product (128D normalized vector)
    """
    
    def __init__(self, 
                 text_model_name: str = 'all-MiniLM-L6-v2',
                 text_dim: int = 384,
                 tag_vocab_size: int = 20,
                 tag_embed_dim: int = 32,
                 nutrition_dim: int = 6,
                 category_vocab_size: int = 50,
                 category_embed_dim: int = 32,
                 hidden_dim: int = 256,
                 output_dim: int = 128,
                 freeze_text_encoder: bool = False,
                 text_encoder: Optional[SentenceTransformer] = None):
        super().__init__()
        
        # Text encoder (sentence-transformers) - use provided encoder or create new one
        if text_encoder is not None:
            self.text_encoder = text_encoder
        else:
            self.text_encoder = SentenceTransformer(text_model_name)
        if freeze_text_encoder:
            for param in self.text_encoder.parameters():
                param.requires_grad = False
        
        # Project text embedding to smaller dimension
        self.text_proj = nn.Linear(text_dim, hidden_dim // 2)
        
        # Sensory tag embeddings (multi-hot)
        self.tag_embedding = nn.Embedding(tag_vocab_size, tag_embed_dim)
        self.tag_proj = nn.Linear(tag_embed_dim, hidden_dim // 4)
        
        # Nutrition features projection
        self.nutrition_proj = nn.Sequential(
            nn.Linear(nutrition_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Category embedding
        self.category_embedding = nn.Embedding(category_vocab_size, category_embed_dim)
        self.category_proj = nn.Linear(category_embed_dim, hidden_dim // 4)
        
        # Fusion layer
        # Input: text (hidden_dim//2) + tags (hidden_dim//4) + nutrition (hidden_dim//4) + category (hidden_dim//4)
        fusion_input_dim = hidden_dim // 2 + hidden_dim // 4 + hidden_dim // 4 + hidden_dim // 4
        
        self.fusion = nn.Sequential(
            nn.Linear(fusion_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.output_dim = output_dim
        self.tag_vocab_size = tag_vocab_size
        
    def forward(self, 
                 text: Optional[torch.Tensor] = None,
                 tag_indices: Optional[torch.Tensor] = None,
                 nutrition: Optional[torch.Tensor] = None,
                 category_ids: Optional[torch.Tensor] = None):
        """
        Args:
            text: [batch_size, text_dim] - pre-encoded text embeddings OR list of strings
            tag_indices: [batch_size, num_tags] - multi-hot tag indices
            nutrition: [batch_size, nutrition_dim] - normalized nutrition features
            category_ids: [batch_size] - category IDs
        """
        batch_size = None
        device = None
        
        # Determine batch size and device
        if text is not None:
            if isinstance(text, list):
                # Encode text strings
                with torch.no_grad() if not self.training else torch.enable_grad():
                    text_emb = self.text_encoder.encode(text, convert_to_tensor=True, device=self._get_device())
                batch_size = text_emb.size(0)
                device = text_emb.device
            else:
                text_emb = text
                batch_size = text_emb.size(0)
                device = text_emb.device
        elif tag_indices is not None:
            batch_size = tag_indices.size(0)
            device = tag_indices.device
        elif nutrition is not None:
            batch_size = nutrition.size(0)
            device = nutrition.device
        elif category_ids is not None:
            batch_size = category_ids.size(0)
            device = category_ids.device
        else:
            raise ValueError("At least one input must be provided")
        
        # Encode text
        if text is not None:
            if isinstance(text, list):
                # Already encoded above
                pass
            else:
                text_emb = text
            text_features = self.text_proj(text_emb)  # [B, hidden_dim//2]
        else:
            # Use correct dimension: hidden_dim // 2
            text_features = torch.zeros(batch_size, self.text_proj.out_features, device=device)
        
        # Encode tags (multi-hot aggregation)
        if tag_indices is not None:
            # tag_indices: [B, num_tags] - binary or indices
            if tag_indices.dim() == 2 and tag_indices.dtype == torch.long:
                # Indices: use embedding lookup
                tag_emb = self.tag_embedding(tag_indices)  # [B, num_tags, tag_embed_dim]
                tag_emb = tag_emb.mean(dim=1)  # Average pooling
            else:
                # Multi-hot: [B, vocab_size] binary
                tag_emb = torch.matmul(tag_indices.float(), self.tag_embedding.weight)  # [B, tag_embed_dim]
                # Normalize by number of active tags
                tag_count = tag_indices.sum(dim=1, keepdim=True).clamp(min=1)
                tag_emb = tag_emb / tag_count
            tag_features = self.tag_proj(tag_emb)  # [B, hidden_dim//4]
        else:
            tag_features = torch.zeros(batch_size, self.fusion[0].in_features // 4, device=device)
        
        # Encode nutrition
        if nutrition is not None:
            nutrition_features = self.nutrition_proj(nutrition)  # [B, hidden_dim//4]
        else:
            nutrition_features = torch.zeros(batch_size, self.fusion[0].in_features // 4, device=device)
        
        # Encode category
        if category_ids is not None:
            if category_ids.dim() > 1:
                category_ids = category_ids.squeeze(-1)
            category_emb = self.category_embedding(category_ids)  # [B, category_embed_dim]
            category_features = self.category_proj(category_emb)  # [B, hidden_dim//4]
        else:
            category_features = torch.zeros(batch_size, self.fusion[0].in_features // 4, device=device)
        
        # Concatenate all features
        combined = torch.cat([text_features, tag_features, nutrition_features, category_features], dim=1)
        
        # Final projection
        z_product = self.fusion(combined)
        
        # L2 normalize
        z_product = F.normalize(z_product, p=2, dim=1)
        
        return z_product
    
    def _get_device(self):
        """Get the device of the model parameters"""
        return next(self.parameters()).device


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss for metric learning
    Pulls similar products together, pushes different products apart
    """
    
    def __init__(self, margin: float = 1.0, temperature: float = 0.1):
        super().__init__()
        self.margin = margin
        self.temperature = temperature
    
    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor):
        """
        Args:
            embeddings: [batch_size, embed_dim] - normalized embeddings
            labels: [batch_size] - product labels (same label = similar)
        """
        batch_size = embeddings.size(0)
        
        # Compute pairwise cosine similarity
        similarity_matrix = torch.matmul(embeddings, embeddings.t())  # [B, B]
        
        # Create positive mask (same label)
        labels = labels.unsqueeze(1)  # [B, 1]
        positive_mask = (labels == labels.t()).float()  # [B, B]
        negative_mask = 1 - positive_mask
        
        # Remove diagonal (self-similarity)
        positive_mask.fill_diagonal_(0)
        
        # Contrastive loss: maximize similarity for positives, minimize for negatives
        # Using temperature-scaled softmax
        similarity_matrix = similarity_matrix / self.temperature
        
        # Positive pairs loss (maximize similarity)
        positive_loss = -torch.log(torch.sigmoid(similarity_matrix) + 1e-8) * positive_mask
        positive_loss = positive_loss.sum() / (positive_mask.sum() + 1e-8)
        
        # Negative pairs loss (minimize similarity)
        negative_loss = -torch.log(torch.sigmoid(-similarity_matrix) + 1e-8) * negative_mask
        negative_loss = negative_loss.sum() / (negative_mask.sum() + 1e-8)
        
        total_loss = positive_loss + negative_loss
        
        return total_loss


# Keep legacy models for backward compatibility
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
