"""
Synthetic data generation for consumer behavior modeling.

Generates:
- 5,000 consumers with fixed base traits
- 100 time steps per consumer
- Latent emotional-taste states
- Observable actions and context
- Ground-truth state transitions
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
import os


class ConsumerDataGenerator:
    """Generates synthetic consumer behavior data."""
    
    def __init__(self, n_consumers: int = 5000, n_timesteps: int = 100, seed: int = 42):
        """
        Initialize data generator.
        
        Args:
            n_consumers: Number of consumers to generate
            n_timesteps: Number of time steps per consumer
            seed: Random seed for reproducibility
        """
        self.n_consumers = n_consumers
        self.n_timesteps = n_timesteps
        self.seed = seed
        np.random.seed(seed)
        
        # Fixed base traits (do not change over time)
        self.trait_names = [
            'sweet_affinity',
            'price_sensitivity',
            'novelty_seeking',
            'health_consciousness',
            'brand_loyalty'
        ]
        
        # Latent state dimensions
        self.state_names = [
            'craving_sweet',
            'craving_salty',
            'fatigue',
            'novelty_drive',
            'guilt',
            'brand_attachment',
            'price_alertness'
        ]
        
        # Action categories
        self.categories = ['fast_food', 'healthy_food', 'dessert', 'skip']
        
        # Brands
        self.brands = ['Brand_A', 'Brand_B', 'Brand_C']
        
        # Context options
        self.time_of_day_options = ['morning', 'afternoon', 'evening', 'night']
        self.day_type_options = ['weekday', 'weekend']
        self.promo_exposure_options = ['none', 'discount', 'ad']
        self.social_context_options = ['alone', 'friends', 'family']
        
    def generate_base_traits(self) -> np.ndarray:
        """Generate fixed base traits for all consumers."""
        traits = np.random.uniform(0, 1, size=(self.n_consumers, len(self.trait_names)))
        return traits
    
    def generate_context(self) -> Dict[str, np.ndarray]:
        """Generate context signals for all timesteps."""
        contexts = {
            'time_of_day': np.random.choice(
                self.time_of_day_options,
                size=(self.n_consumers, self.n_timesteps)
            ),
            'day_type': np.random.choice(
                self.day_type_options,
                size=(self.n_consumers, self.n_timesteps)
            ),
            'promo_exposure': np.random.choice(
                self.promo_exposure_options,
                size=(self.n_consumers, self.n_timesteps),
                p=[0.7, 0.2, 0.1]  # Most timesteps have no promo
            ),
            'social_context': np.random.choice(
                self.social_context_options,
                size=(self.n_consumers, self.n_timesteps)
            )
        }
        return contexts
    
    def compute_action_probabilities(
        self,
        state: np.ndarray,
        context: Dict[str, str],
        base_traits: np.ndarray
    ) -> np.ndarray:
        """
        Compute action probabilities based on state, context, and traits.
        
        Returns:
            Probability distribution over [fast_food, healthy_food, dessert, skip]
        """
        probs = np.zeros(4)
        
        # Base probabilities from state
        probs[0] = state[1] * 0.3 + state[2] * 0.2  # fast_food: salty craving + fatigue
        probs[1] = state[4] * 0.4 + base_traits[3] * 0.3  # healthy_food: guilt + health consciousness
        probs[2] = state[0] * 0.5 + (1 - state[4]) * 0.2  # dessert: sweet craving + low guilt
        probs[3] = (1 - state[0] - state[1]) * 0.3 + state[2] * 0.2  # skip: low cravings + fatigue
        
        # Context adjustments
        if context['time_of_day'] == 'morning':
            probs[1] *= 1.5  # More healthy in morning
            probs[2] *= 0.5  # Less dessert
        elif context['time_of_day'] == 'evening':
            probs[2] *= 1.5  # More dessert in evening
            probs[3] *= 0.7  # Less skipping
        
        if context['day_type'] == 'weekend':
            probs[0] *= 1.3  # More fast food on weekends
            probs[2] *= 1.2  # More dessert
        
        if context['promo_exposure'] == 'discount':
            probs[0] *= 1.4  # Promotions increase fast food
            probs[3] *= 0.6  # Less skipping
        
        if context['social_context'] == 'friends':
            probs[0] *= 1.2  # More fast food with friends
            probs[2] *= 1.3  # More dessert
        
        # Normalize
        probs = np.maximum(probs, 0.01)  # Avoid zeros
        probs = probs / probs.sum()
        
        return probs
    
    def compute_brand_probabilities(
        self,
        brand_attachment: float,
        base_loyalty: float
    ) -> np.ndarray:
        """Compute brand selection probabilities."""
        probs = np.ones(3) * 0.1  # Base probability
        
        # Attachment and loyalty increase probability of preferred brand
        preferred_idx = int(base_loyalty * 3) % 3
        probs[preferred_idx] += brand_attachment * 0.5 + base_loyalty * 0.3
        
        # Normalize
        probs = probs / probs.sum()
        return probs
    
    def compute_spend(
        self,
        category: str,
        price_alertness: float,
        price_sensitivity: float,
        promo_exposure: str
    ) -> float:
        """Compute spend amount based on category and price sensitivity."""
        base_spends = {
            'fast_food': 12.0,
            'healthy_food': 15.0,
            'dessert': 8.0,
            'skip': 0.0
        }
        
        if category == 'skip':
            return 0.0
        
        base = base_spends[category]
        
        # Price sensitivity reduces spend
        spend = base * (1 - price_sensitivity * 0.3)
        
        # Price alertness (from state) further reduces
        spend = spend * (1 - price_alertness * 0.2)
        
        # Promotions increase spend
        if promo_exposure == 'discount':
            spend = spend * 1.2
        
        # Add noise
        spend = max(0, spend + np.random.normal(0, base * 0.1))
        
        return spend
    
    def state_transition(
        self,
        state: np.ndarray,
        action: Dict[str, any],
        context: Dict[str, str],
        base_traits: np.ndarray
    ) -> np.ndarray:
        """
        Ground-truth state transition dynamics.
        
        Rules:
        - Indulgent actions increase guilt and fatigue
        - Novelty decays without exploration
        - Repeated brand usage increases attachment
        - Promotions temporarily suppress price sensitivity
        """
        next_state = state.copy()
        
        category = action['category']
        brand = action['brand']
        spend = action['spend']
        
        # Indulgent actions increase guilt and fatigue
        if category == 'fast_food' or category == 'dessert':
            next_state[4] = min(1.0, state[4] + 0.15)  # guilt
            next_state[2] = min(1.0, state[2] + 0.1)   # fatigue
        
        # Healthy actions reduce guilt
        if category == 'healthy_food':
            next_state[4] = max(0.0, state[4] - 0.2)  # guilt
            next_state[2] = max(0.0, state[2] - 0.1)  # fatigue
        
        # Skipping reduces cravings but increases fatigue
        if category == 'skip':
            next_state[0] = max(0.0, state[0] - 0.1)  # sweet craving
            next_state[1] = max(0.0, state[1] - 0.1)  # salty craving
            next_state[2] = min(1.0, state[2] + 0.05)  # fatigue
        
        # Novelty drive decays naturally
        next_state[3] = state[3] * 0.95
        
        # Using same brand increases attachment
        # (We'll track this in the simulation loop)
        
        # Promotions suppress price alertness temporarily
        if context['promo_exposure'] == 'discount':
            next_state[6] = max(0.0, state[6] - 0.3)  # price_alertness
        
        # Natural dynamics: cravings evolve
        next_state[0] = state[0] * 0.9 + base_traits[0] * 0.1  # sweet craving toward base affinity
        next_state[1] = state[1] * 0.9 + (1 - base_traits[0]) * 0.1  # salty craving
        
        # Price alertness returns toward base sensitivity
        next_state[6] = state[6] * 0.8 + base_traits[1] * 0.2
        
        # Add noise
        noise = np.random.normal(0, 0.05, size=len(state))
        next_state = np.clip(next_state + noise, 0, 1)
        
        return next_state
    
    def generate(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate complete dataset.
        
        Returns:
            events_df: DataFrame with user_id, timestep, action, brand, spend, context
            states_hidden: Array of shape (n_consumers, n_timesteps, n_state_dims) with true states
        """
        print(f"Generating data for {self.n_consumers} consumers over {self.n_timesteps} timesteps...")
        
        # Generate base traits
        base_traits = self.generate_base_traits()
        
        # Generate contexts
        contexts = self.generate_context()
        
        # Initialize states
        states_hidden = np.zeros((self.n_consumers, self.n_timesteps, len(self.state_names)))
        
        # Initialize with random states
        states_hidden[:, 0, :] = np.random.uniform(0, 0.5, size=(self.n_consumers, len(self.state_names)))
        
        # Track brand history for attachment
        brand_history = {}
        
        # Generate events
        events = []
        
        for user_id in range(self.n_consumers):
            brand_history[user_id] = []
            
            for t in range(self.n_timesteps):
                state = states_hidden[user_id, t, :]
                
                # Get context for this timestep
                context = {
                    'time_of_day': contexts['time_of_day'][user_id, t],
                    'day_type': contexts['day_type'][user_id, t],
                    'promo_exposure': contexts['promo_exposure'][user_id, t],
                    'social_context': contexts['social_context'][user_id, t]
                }
                
                # Compute action probabilities
                action_probs = self.compute_action_probabilities(
                    state, context, base_traits[user_id]
                )
                
                # Sample category
                category = np.random.choice(self.categories, p=action_probs)
                
                # Compute brand probabilities
                brand_attachment = state[5]  # brand_attachment from state
                brand_probs = self.compute_brand_probabilities(
                    brand_attachment, base_traits[user_id, 4]  # brand_loyalty
                )
                
                # Sample brand (if not skipping)
                if category != 'skip':
                    brand = np.random.choice(self.brands, p=brand_probs)
                    brand_history[user_id].append(brand)
                else:
                    brand = None
                
                # Compute spend
                spend = self.compute_spend(
                    category,
                    state[6],  # price_alertness
                    base_traits[user_id, 1],  # price_sensitivity
                    context['promo_exposure']
                )
                
                # Record event
                events.append({
                    'user_id': user_id,
                    'timestep': t,
                    'category': category,
                    'brand': brand if brand else 'none',
                    'spend': spend,
                    'time_of_day': context['time_of_day'],
                    'day_type': context['day_type'],
                    'promo_exposure': context['promo_exposure'],
                    'social_context': context['social_context']
                })
                
                # Update brand attachment based on recent history
                if len(brand_history[user_id]) > 0:
                    recent_brands = brand_history[user_id][-5:]  # Last 5 actions
                    if len(set(recent_brands)) == 1:  # Same brand repeated
                        states_hidden[user_id, t, 5] = min(1.0, states_hidden[user_id, t, 5] + 0.1)
                
                # Compute next state (if not last timestep)
                if t < self.n_timesteps - 1:
                    action = {
                        'category': category,
                        'brand': brand,
                        'spend': spend
                    }
                    next_state = self.state_transition(
                        state, action, context, base_traits[user_id]
                    )
                    states_hidden[user_id, t + 1, :] = next_state
        
        events_df = pd.DataFrame(events)
        
        print(f"Generated {len(events)} events")
        print(f"State shape: {states_hidden.shape}")
        
        return events_df, states_hidden


def main():
    """Generate and save data."""
    generator = ConsumerDataGenerator(n_consumers=5000, n_timesteps=100, seed=42)
    events_df, states_hidden = generator.generate()
    
    # Save events
    os.makedirs('data', exist_ok=True)
    events_df.to_csv('data/events.csv', index=False)
    print("Saved data/events.csv")
    
    # Save hidden states
    np.save('data/states_hidden.npy', states_hidden)
    print("Saved data/states_hidden.npy")
    
    # Print summary
    print("\nData Summary:")
    print(f"Total events: {len(events_df)}")
    print(f"Category distribution:")
    print(events_df['category'].value_counts())
    print(f"\nAverage spend: ${events_df['spend'].mean():.2f}")
    print(f"State statistics:")
    print(f"  Mean: {states_hidden.mean(axis=(0,1))}")
    print(f"  Std: {states_hidden.std(axis=(0,1))}")


if __name__ == '__main__':
    main()

