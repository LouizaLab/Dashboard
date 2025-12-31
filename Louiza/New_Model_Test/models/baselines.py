"""
Baseline models for comparison.

Baseline A: Random predictor
Baseline B: Static preference model (uses only initial traits)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from scipy.stats import entropy


class RandomBaseline:
    """Baseline A: Predicts actions uniformly at random."""
    
    def __init__(self, categories: list, brands: list):
        self.categories = categories
        self.brands = brands
        self.n_categories = len(categories)
        self.n_brands = len(brands)
    
    def predict(self, n_samples: int) -> Dict[str, np.ndarray]:
        """Predict random actions."""
        category_probs = np.ones(self.n_categories) / self.n_categories
        brand_probs = np.ones(self.n_brands) / self.n_brands
        
        categories = np.random.choice(
            self.categories,
            size=n_samples,
            p=category_probs
        )
        
        brands = np.random.choice(
            self.brands,
            size=n_samples,
            p=brand_probs
        )
        
        return {
            'categories': categories,
            'brands': brands,
            'category_probs': np.tile(category_probs, (n_samples, 1)),
            'brand_probs': np.tile(brand_probs, (n_samples, 1))
        }
    
    def compute_entropy(self, n_samples: int) -> float:
        """Compute expected entropy of predictions."""
        category_probs = np.ones(self.n_categories) / self.n_categories
        brand_probs = np.ones(self.n_brands) / self.n_brands
        
        cat_entropy = entropy(category_probs, base=2)
        brand_entropy = entropy(brand_probs, base=2)
        
        return cat_entropy + brand_entropy


class StaticPreferenceBaseline:
    """Baseline B: Uses only initial base traits, ignoring time evolution."""
    
    def __init__(self, categories: list, brands: list):
        self.categories = categories
        self.brands = brands
        self.n_categories = len(categories)
        self.n_brands = len(brands)
    
    def fit(self, events_df: pd.DataFrame, base_traits: np.ndarray):
        """
        Fit baseline using base traits.
        
        Args:
            events_df: DataFrame with events
            base_traits: Array of shape (n_consumers, n_traits)
        """
        self.base_traits = base_traits
        self.n_consumers = len(base_traits)
        
        # Learn mapping from traits to action preferences
        # Simple heuristic: map traits to probabilities
        print("Fitting static preference baseline...")
    
    def predict(
        self,
        user_ids: np.ndarray,
        contexts: Dict[str, np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """
        Predict actions based on static traits.
        
        Args:
            user_ids: Array of user IDs
            contexts: Optional context dict (ignored for static model)
        
        Returns:
            Dictionary with predictions
        """
        n_samples = len(user_ids)
        categories = []
        brands = []
        category_probs_list = []
        brand_probs_list = []
        
        for user_id in user_ids:
            traits = self.base_traits[user_id]
            
            # Map traits to category probabilities
            # sweet_affinity -> dessert
            # health_consciousness -> healthy_food
            # price_sensitivity -> skip (if high)
            # novelty_seeking -> fast_food
            
            cat_probs = np.array([
                traits[2] * 0.3 + (1 - traits[3]) * 0.2,  # fast_food: novelty + low health
                traits[3] * 0.4 + traits[4] * 0.1,  # healthy_food: health + loyalty
                traits[0] * 0.5,  # dessert: sweet affinity
                traits[1] * 0.3  # skip: price sensitivity
            ])
            cat_probs = np.maximum(cat_probs, 0.01)
            cat_probs = cat_probs / cat_probs.sum()
            
            # Brand selection based on loyalty
            brand_probs = np.ones(self.n_brands) * 0.1
            preferred_idx = int(traits[4] * self.n_brands) % self.n_brands
            brand_probs[preferred_idx] += traits[4] * 0.7
            brand_probs = brand_probs / brand_probs.sum()
            
            # Sample
            category = np.random.choice(self.categories, p=cat_probs)
            brand = np.random.choice(self.brands, p=brand_probs)
            
            categories.append(category)
            brands.append(brand)
            category_probs_list.append(cat_probs)
            brand_probs_list.append(brand_probs)
        
        return {
            'categories': np.array(categories),
            'brands': np.array(brands),
            'category_probs': np.array(category_probs_list),
            'brand_probs': np.array(brand_probs_list)
        }
    
    def compute_entropy(self, user_ids: np.ndarray) -> float:
        """Compute average entropy of predictions."""
        predictions = self.predict(user_ids)
        entropies = []
        
        for i in range(len(user_ids)):
            cat_entropy = entropy(predictions['category_probs'][i], base=2)
            brand_entropy = entropy(predictions['brand_probs'][i], base=2)
            entropies.append(cat_entropy + brand_entropy)
        
        return np.mean(entropies)


def evaluate_baseline(
    baseline,
    events_df: pd.DataFrame,
    base_traits: np.ndarray = None
) -> Dict[str, float]:
    """
    Evaluate a baseline model.
    
    Returns:
        Dictionary with metrics: accuracy, category_accuracy, nll, entropy
    """
    n_samples = len(events_df)
    
    if isinstance(baseline, RandomBaseline):
        predictions = baseline.predict(n_samples)
    else:
        predictions = baseline.predict(events_df['user_id'].values)
    
    # Accuracy (exact match)
    exact_match = (
        (predictions['categories'] == events_df['category'].values) &
        (predictions['brands'] == events_df['brand'].values)
    )
    accuracy = exact_match.mean()
    
    # Category accuracy
    category_accuracy = (predictions['categories'] == events_df['category'].values).mean()
    
    # Negative log likelihood
    nll = 0.0
    for i in range(n_samples):
        true_cat = events_df.iloc[i]['category']
        true_brand = events_df.iloc[i]['brand']
        
        cat_idx = baseline.categories.index(true_cat)
        cat_prob = predictions['category_probs'][i, cat_idx]
        
        if true_brand != 'none':
            brand_idx = baseline.brands.index(true_brand)
            brand_prob = predictions['brand_probs'][i, brand_idx]
        else:
            brand_prob = 1.0
        
        nll -= np.log(max(cat_prob * brand_prob, 1e-10))
    
    nll = nll / n_samples
    
    # Entropy
    if isinstance(baseline, RandomBaseline):
        pred_entropy = baseline.compute_entropy(n_samples)
    else:
        pred_entropy = baseline.compute_entropy(events_df['user_id'].values)
    
    return {
        'accuracy': accuracy,
        'category_accuracy': category_accuracy,
        'nll': nll,
        'entropy': pred_entropy
    }

