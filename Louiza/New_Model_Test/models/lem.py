"""
Large Emotional Model (LEM) - Sequence model for next-state prediction.

Architecture:
- Input: embedded previous action + embedded context
- Latent: inferred emotional-taste state z_t
- Output: next action prediction
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional


class ActionEmbedding(nn.Module):
    """Embed actions (category + brand) into dense vectors."""
    
    def __init__(self, n_categories: int, n_brands: int, embed_dim: int = 32):
        super().__init__()
        self.category_embed = nn.Embedding(n_categories, embed_dim // 2)
        self.brand_embed = nn.Embedding(n_brands + 1, embed_dim // 2)  # +1 for 'none'
        self.embed_dim = embed_dim
    
    def forward(self, category_idx: torch.Tensor, brand_idx: torch.Tensor) -> torch.Tensor:
        """
        Args:
            category_idx: (batch_size,) category indices
            brand_idx: (batch_size,) brand indices
        """
        cat_emb = self.category_embed(category_idx)
        brand_emb = self.brand_embed(brand_idx)
        return torch.cat([cat_emb, brand_emb], dim=-1)


class ContextEmbedding(nn.Module):
    """Embed context signals into dense vectors."""
    
    def __init__(
        self,
        time_of_day_vocab: int = 4,
        day_type_vocab: int = 2,
        promo_vocab: int = 3,
        social_vocab: int = 3,
        embed_dim: int = 32
    ):
        super().__init__()
        self.time_embed = nn.Embedding(time_of_day_vocab, embed_dim // 4)
        self.day_embed = nn.Embedding(day_type_vocab, embed_dim // 4)
        self.promo_embed = nn.Embedding(promo_vocab, embed_dim // 4)
        self.social_embed = nn.Embedding(social_vocab, embed_dim // 4)
        self.embed_dim = embed_dim
    
    def forward(
        self,
        time_idx: torch.Tensor,
        day_idx: torch.Tensor,
        promo_idx: torch.Tensor,
        social_idx: torch.Tensor
    ) -> torch.Tensor:
        """Embed all context signals."""
        time_emb = self.time_embed(time_idx)
        day_emb = self.day_embed(day_idx)
        promo_emb = self.promo_embed(promo_idx)
        social_emb = self.social_embed(social_idx)
        return torch.cat([time_emb, day_emb, promo_emb, social_emb], dim=-1)


class LEM(nn.Module):
    """
    Large Emotional Model - Sequence model for consumer behavior prediction.
    
    Uses GRU to model temporal dynamics of latent emotional-taste states.
    """
    
    def __init__(
        self,
        n_categories: int = 4,
        n_brands: int = 3,
        action_embed_dim: int = 32,
        context_embed_dim: int = 32,
        latent_dim: int = 64,
        hidden_dim: int = 128,
        n_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.n_categories = n_categories
        self.n_brands = n_brands
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        
        # Embeddings
        self.action_embed = ActionEmbedding(n_categories, n_brands, action_embed_dim)
        self.context_embed = ContextEmbedding(embed_dim=context_embed_dim)
        
        # Input projection
        input_dim = action_embed_dim + context_embed_dim
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # GRU for temporal dynamics
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            dropout=dropout if n_layers > 1 else 0,
            batch_first=True
        )
        
        # Latent state projection
        self.latent_proj = nn.Sequential(
            nn.Linear(hidden_dim, latent_dim),
            nn.Tanh()  # Bound latent state
        )
        
        # Output heads
        self.category_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, n_categories)
        )
        
        self.brand_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, n_brands + 1)  # +1 for 'none'
        )
        
        self.spend_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(
        self,
        action_category: torch.Tensor,
        action_brand: torch.Tensor,
        context_time: torch.Tensor,
        context_day: torch.Tensor,
        context_promo: torch.Tensor,
        context_social: torch.Tensor,
        hidden: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            action_category: (batch_size, seq_len) category indices
            action_brand: (batch_size, seq_len) brand indices
            context_*: (batch_size, seq_len) context indices
            hidden: Optional initial hidden state
        
        Returns:
            Dictionary with predictions and latent states
        """
        batch_size, seq_len = action_category.shape
        
        # Embed actions and context
        action_emb = self.action_embed(
            action_category.reshape(-1),
            action_brand.reshape(-1)
        ).reshape(batch_size, seq_len, -1)
        
        context_emb = self.context_embed(
            context_time.reshape(-1),
            context_day.reshape(-1),
            context_promo.reshape(-1),
            context_social.reshape(-1)
        ).reshape(batch_size, seq_len, -1)
        
        # Combine
        combined = torch.cat([action_emb, context_emb], dim=-1)
        x = self.input_proj(combined)
        
        # GRU
        gru_out, hidden_out = self.gru(x, hidden)
        
        # Latent state (for interpretability)
        latent_states = self.latent_proj(gru_out)  # (batch, seq_len, latent_dim)
        
        # Predictions
        category_logits = self.category_head(gru_out)  # (batch, seq_len, n_categories)
        brand_logits = self.brand_head(gru_out)  # (batch, seq_len, n_brands + 1)
        spend_pred = self.spend_head(gru_out).squeeze(-1)  # (batch, seq_len)
        
        return {
            'category_logits': category_logits,
            'brand_logits': brand_logits,
            'spend_pred': spend_pred,
            'latent_states': latent_states,
            'hidden': hidden_out
        }
    
    def predict_next(
        self,
        action_category: torch.Tensor,
        action_brand: torch.Tensor,
        context_time: torch.Tensor,
        context_day: torch.Tensor,
        context_promo: torch.Tensor,
        context_social: torch.Tensor,
        hidden: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Predict next action given current state.
        
        Args:
            All inputs: (batch_size,) single timestep
        
        Returns:
            Dictionary with predictions
        """
        # Add sequence dimension
        action_category = action_category.unsqueeze(1)
        action_brand = action_brand.unsqueeze(1)
        context_time = context_time.unsqueeze(1)
        context_day = context_day.unsqueeze(1)
        context_promo = context_promo.unsqueeze(1)
        context_social = context_social.unsqueeze(1)
        
        output = self.forward(
            action_category, action_brand,
            context_time, context_day, context_promo, context_social,
            hidden
        )
        
        # Remove sequence dimension
        return {
            'category_logits': output['category_logits'].squeeze(1),
            'brand_logits': output['brand_logits'].squeeze(1),
            'spend_pred': output['spend_pred'].squeeze(1),
            'latent_states': output['latent_states'].squeeze(1),
            'hidden': output['hidden']
        }


def compute_loss(
    predictions: Dict[str, torch.Tensor],
    targets: Dict[str, torch.Tensor],
    alpha: float = 1.0,
    beta: float = 0.1,
    gamma: float = 0.01
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Compute training loss.
    
    Loss = alpha * NLL(next action) + beta * temporal smoothness + gamma * entropy regularization
    
    Args:
        predictions: Model outputs
        targets: Ground truth
        alpha: Weight for NLL
        beta: Weight for smoothness
        gamma: Weight for entropy
    
    Returns:
        Total loss and loss components
    """
    # NLL for category
    category_logits = predictions['category_logits']  # (batch, n_categories)
    category_target = targets['category']  # (batch,)
    nll_category = F.cross_entropy(category_logits, category_target)
    
    # NLL for brand
    brand_logits = predictions['brand_logits']  # (batch, n_brands + 1)
    brand_target = targets['brand']  # (batch,)
    nll_brand = F.cross_entropy(brand_logits, brand_target)
    
    nll_total = nll_category + nll_brand
    
    # Temporal smoothness on latent states
    # (if we have sequence data)
    latent_states = predictions['latent_states']  # (batch, latent_dim) or (batch, seq_len, latent_dim)
    if len(latent_states.shape) == 3:
        # Sequence: compute smoothness between consecutive states
        state_diff = latent_states[:, 1:, :] - latent_states[:, :-1, :]
        smoothness_loss = (state_diff ** 2).mean()
    else:
        # Single timestep: no smoothness
        smoothness_loss = torch.tensor(0.0, device=latent_states.device)
    
    # Entropy regularization (encourage uncertainty when appropriate)
    category_probs = F.softmax(category_logits, dim=-1)
    brand_probs = F.softmax(brand_logits, dim=-1)
    
    # Compute entropy
    cat_entropy = -(category_probs * F.log_softmax(category_logits, dim=-1)).sum(dim=-1).mean()
    brand_entropy = -(brand_probs * F.log_softmax(brand_logits, dim=-1)).sum(dim=-1).mean()
    
    # Entropy regularization: encourage moderate entropy (not too high, not too low)
    target_entropy = 1.5  # Target entropy level
    entropy_loss = ((cat_entropy + brand_entropy) - target_entropy) ** 2
    
    # Total loss
    total_loss = (
        alpha * nll_total +
        beta * smoothness_loss +
        gamma * entropy_loss
    )
    
    loss_dict = {
        'total': total_loss.item(),
        'nll': nll_total.item(),
        'nll_category': nll_category.item(),
        'nll_brand': nll_brand.item(),
        'smoothness': smoothness_loss.item(),
        'entropy_reg': entropy_loss.item(),
        'entropy': (cat_entropy + brand_entropy).item()
    }
    
    return total_loss, loss_dict

