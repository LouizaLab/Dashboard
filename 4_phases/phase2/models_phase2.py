"""
Phase 2: Behavioral Dynamic Engine
Models for behavioral state and state transitions
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class BehavioralState(nn.Module):
    """
    Represents latent behavioral state s_t
    Components:
    - z_taste: stable taste preferences (from z_segment initially)
    - z_novelty: novelty vs routine preference
    - z_habit: habit strength / inertia
    - z_health: health vs indulgence bias
    - z_price: price sensitivity
    """
    
    def __init__(self, segment_dim: int = 64, state_dim: int = 128):
        super().__init__()
        self.state_dim = state_dim
        
        # Initialize state components from segment embedding
        # Each component is a learned projection from segment
        self.taste_proj = nn.Linear(segment_dim, state_dim // 5)
        self.novelty_proj = nn.Linear(segment_dim, state_dim // 5)
        self.habit_proj = nn.Linear(segment_dim, state_dim // 5)
        self.health_proj = nn.Linear(segment_dim, state_dim // 5)
        self.price_proj = nn.Linear(segment_dim, state_dim // 5)
        
        # Remaining dimensions for flexibility
        remaining = state_dim - 5 * (state_dim // 5)
        if remaining > 0:
            self.extra_proj = nn.Linear(segment_dim, remaining)
        else:
            self.extra_proj = None
    
    def initialize_from_segment(self, z_segment):
        """
        Initialize state from segment embedding
        Args:
            z_segment: [batch_size, segment_dim]
        Returns:
            s_t: [batch_size, state_dim]
        """
        batch_size = z_segment.size(0)
        
        # Project each component
        z_taste = self.taste_proj(z_segment)
        z_novelty = self.novelty_proj(z_segment)
        z_habit = self.habit_proj(z_segment)
        z_health = self.health_proj(z_segment)
        z_price = self.price_proj(z_segment)
        
        # Combine
        components = [z_taste, z_novelty, z_habit, z_health, z_price]
        
        if self.extra_proj is not None:
            z_extra = self.extra_proj(z_segment)
            components.append(z_extra)
        
        s_t = torch.cat(components, dim=1)
        
        # Normalize
        s_t = F.normalize(s_t, p=2, dim=1)
        
        return s_t
    
    def get_components(self, s_t):
        """
        Extract individual components from state vector
        Args:
            s_t: [batch_size, state_dim]
        Returns:
            dict with components
        """
        comp_size = self.state_dim // 5
        
        return {
            'z_taste': s_t[:, :comp_size],
            'z_novelty': s_t[:, comp_size:2*comp_size],
            'z_habit': s_t[:, 2*comp_size:3*comp_size],
            'z_health': s_t[:, 3*comp_size:4*comp_size],
            'z_price': s_t[:, 4*comp_size:5*comp_size]
        }


class ObservationModel(nn.Module):
    """
    Observation Model: P(like | s_t, z_product, z_context)
    Predicts intent/preference from current state and product/context
    """
    
    def __init__(self, 
                 state_dim: int = 128,
                 product_dim: int = 128,
                 context_dim: int = 64,
                 hidden_dim: int = 256,
                 output_type: str = 'probability'):
        super().__init__()
        self.output_type = output_type
        
        # Combine state, product, and context
        combined_dim = state_dim + product_dim + context_dim
        
        self.predictor = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        if output_type == 'probability':
            self.output_activation = nn.Sigmoid()
        elif output_type == 'rating':
            self.output_activation = lambda x: torch.clamp(x, 0.0, 1.0)
        else:
            self.output_activation = nn.Identity()
    
    def forward(self, s_t, z_product, z_context):
        """
        Args:
            s_t: [batch_size, state_dim] - current behavioral state
            z_product: [batch_size, product_dim] - product embedding
            z_context: [batch_size, context_dim] - context embedding
        Returns:
            y_pred: [batch_size, 1] - predicted preference/intent
        """
        combined = torch.cat([s_t, z_product, z_context], dim=1)
        output = self.predictor(combined)
        return self.output_activation(output)


class StateTransitionModel(nn.Module):
    """
    State Transition Model: s_{t+1} = f(s_t, z_product, z_context, y_t)
    Models how behavioral state evolves based on interactions
    """
    
    def __init__(self,
                 state_dim: int = 128,
                 product_dim: int = 128,
                 context_dim: int = 64,
                 hidden_dim: int = 256):
        super().__init__()
        
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        
        # Project state to hidden dimension
        self.state_proj = nn.Linear(state_dim, hidden_dim)
        
        # Project interaction (product + context + outcome) to hidden dimension
        interaction_dim = product_dim + context_dim + 1
        self.interaction_proj = nn.Sequential(
            nn.Linear(interaction_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Use GRU for temporal dynamics
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        
        # Project GRU output back to state space
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, state_dim)
        )
        
        # Residual connection strength
        self.residual_weight = nn.Parameter(torch.tensor(0.5))
    
    def forward(self, s_t, z_product, z_context, y_t):
        """
        Args:
            s_t: [batch_size, state_dim] - current state
            z_product: [batch_size, product_dim] - product embedding
            z_context: [batch_size, context_dim] - context embedding
            y_t: [batch_size, 1] - observed preference/outcome
        Returns:
            s_{t+1}: [batch_size, state_dim] - next state
        """
        # Project state to hidden dimension
        s_t_hidden = self.state_proj(s_t)
        
        # Combine product, context, and outcome
        interaction = torch.cat([z_product, z_context, y_t], dim=1)
        interaction_hidden = self.interaction_proj(interaction)
        
        # GRU update
        h_next = self.gru(interaction_hidden, s_t_hidden)
        
        # Project back to state space
        s_t_next = self.output_proj(h_next)
        
        # Residual connection (state doesn't change too drastically)
        s_t_next = (1 - self.residual_weight) * s_t + self.residual_weight * s_t_next
        
        # Normalize
        s_t_next = F.normalize(s_t_next, p=2, dim=1)
        
        return s_t_next


class BehavioralDynamicEngine(nn.Module):
    """
    Complete Behavioral Dynamic Engine combining all components
    """
    
    def __init__(self,
                 segment_dim: int = 64,
                 product_dim: int = 128,
                 context_dim: int = 64,
                 state_dim: int = 128,
                 hidden_dim: int = 256):
        super().__init__()
        
        self.state_model = BehavioralState(segment_dim, state_dim)
        self.observation_model = ObservationModel(state_dim, product_dim, context_dim, hidden_dim)
        self.transition_model = StateTransitionModel(state_dim, product_dim, context_dim, hidden_dim)
        
        self.state_dim = state_dim
        self.product_dim = product_dim
        self.context_dim = context_dim
    
    def initialize_state(self, z_segment):
        """Initialize state from segment embedding"""
        return self.state_model.initialize_from_segment(z_segment)
    
    def predict_intent(self, s_t, z_product, z_context):
        """Predict intent from current state"""
        return self.observation_model(s_t, z_product, z_context)
    
    def update_state(self, s_t, z_product, z_context, y_t):
        """Update state based on interaction"""
        return self.transition_model(s_t, z_product, z_context, y_t)
    
    def forward_sequence(self, z_segment, z_products, z_contexts, return_states=False):
        """
        Forward pass through a sequence of interactions
        Args:
            z_segment: [batch_size, segment_dim] - segment embedding
            z_products: [seq_len, batch_size, product_dim] - product embeddings
            z_contexts: [seq_len, batch_size, context_dim] - context embeddings
            return_states: if True, return all states
        Returns:
            predictions: [seq_len, batch_size, 1] - predicted preferences
            states: [seq_len+1, batch_size, state_dim] - all states (if return_states=True)
        """
        seq_len, batch_size = z_products.size(0), z_products.size(1)
        
        # Initialize state
        s_t = self.initialize_state(z_segment)  # [batch_size, state_dim]
        
        predictions = []
        states = [s_t] if return_states else None
        
        for t in range(seq_len):
            # Extract time step t: [batch_size, dim]
            z_product_t = z_products[t]  # [batch_size, product_dim]
            z_context_t = z_contexts[t]  # [batch_size, context_dim]
            
            # Predict intent
            y_pred_t = self.predict_intent(s_t, z_product_t, z_context_t)  # [batch_size, 1]
            predictions.append(y_pred_t)
            
            # Update state (using predicted value for next state)
            s_t = self.update_state(s_t, z_product_t, z_context_t, y_pred_t)  # [batch_size, state_dim]
            
            if return_states:
                states.append(s_t)
        
        predictions = torch.stack(predictions, dim=0)  # [seq_len, batch_size, 1]
        
        if return_states:
            states = torch.stack(states, dim=0)  # [seq_len+1, batch_size, state_dim]
            return predictions, states
        
        return predictions

