"""
Synthetic Data Generator for Phase 1: Taste Embedding Model
Generates products, contexts, segments, and intent/preference logs
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import random
from datetime import datetime, timedelta

class SyntheticDataGenerator:
    """Generate synthetic data for training the Taste Embedding Model"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Define vocabularies
        self.ingredients = [
            'water', 'sugar', 'citric_acid', 'caffeine', 'carbonation', 
            'natural_flavors', 'vitamin_c', 'sodium', 'potassium', 'calcium',
            'protein', 'fiber', 'antioxidants', 'probiotics', 'electrolytes',
            'green_tea_extract', 'ginseng', 'taurine', 'b_vitamins', 'coffee_extract'
        ]
        
        self.sensory_tags = [
            'sweet', 'sour', 'bitter', 'fizzy', 'creamy', 'spicy', 
            'refreshing', 'smooth', 'tart', 'rich', 'light', 'bold',
            'fruity', 'citrusy', 'herbal', 'earthy', 'floral', 'nutty'
        ]
        
        self.locations = ['home', 'work', 'bar', 'cafe', 'gym', 'outdoor', 'store']
        self.occasions = ['work', 'social', 'post_gym', 'late_night', 'morning', 'afternoon', 'evening']
        self.age_buckets = ['18-25', '26-35', '36-45', '46-55', '56+']
        self.regions = ['north', 'south', 'east', 'west', 'central']
        self.psychographics = ['health_focused', 'adventurous', 'budget_sensitive', 'premium_seeker', 'routine_lover']
        
        # Product categories
        self.categories = ['energy_drink', 'soda', 'juice', 'sports_drink', 'coffee_drink', 'tea', 'water_enhanced']
    
    def generate_products(self, n_products: int = 50) -> pd.DataFrame:
        """Generate synthetic product metadata"""
        products = []
        
        for i in range(n_products):
            # Sample category
            category = np.random.choice(self.categories)
            
            # Generate ingredients (3-8 per product)
            n_ingredients = np.random.randint(3, 9)
            product_ingredients = random.sample(self.ingredients, n_ingredients)
            
            # Generate sensory tags (2-5 per product)
            n_tags = np.random.randint(2, 6)
            sensory_tags = random.sample(self.sensory_tags, n_tags)
            
            # Generate nutrition based on category
            nutrition = self._generate_nutrition(category)
            
            # Generate text description
            description = self._generate_description(category, product_ingredients, sensory_tags)
            
            products.append({
                'product_id': f'prod_{i:03d}',
                'category': category,
                'ingredients': ','.join(product_ingredients),
                'sensory_tags': ','.join(sensory_tags),
                'sugar_g': nutrition['sugar'],
                'caffeine_mg': nutrition['caffeine'],
                'calories': nutrition['calories'],
                'protein_g': nutrition['protein'],
                'description': description,
                'price': round(np.random.uniform(1.5, 5.0), 2)
            })
        
        return pd.DataFrame(products)
    
    def _generate_nutrition(self, category: str) -> Dict:
        """Generate nutrition facts based on category"""
        base_nutrition = {
            'energy_drink': {'sugar': (15, 35), 'caffeine': (80, 200), 'calories': (50, 150), 'protein': (0, 5)},
            'soda': {'sugar': (25, 45), 'caffeine': (0, 50), 'calories': (100, 200), 'protein': (0, 0)},
            'juice': {'sugar': (20, 35), 'caffeine': (0, 0), 'calories': (80, 150), 'protein': (0, 2)},
            'sports_drink': {'sugar': (10, 25), 'caffeine': (0, 0), 'calories': (30, 100), 'protein': (0, 10)},
            'coffee_drink': {'sugar': (5, 25), 'caffeine': (50, 150), 'calories': (20, 150), 'protein': (0, 5)},
            'tea': {'sugar': (0, 15), 'caffeine': (20, 60), 'calories': (0, 50), 'protein': (0, 1)},
            'water_enhanced': {'sugar': (0, 5), 'caffeine': (0, 0), 'calories': (0, 10), 'protein': (0, 0)}
        }
        
        ranges = base_nutrition.get(category, base_nutrition['soda'])
        return {
            'sugar': np.random.uniform(*ranges['sugar']),
            'caffeine': np.random.uniform(*ranges['caffeine']),
            'calories': np.random.uniform(*ranges['calories']),
            'protein': np.random.uniform(*ranges['protein'])
        }
    
    def _generate_description(self, category: str, ingredients: List[str], tags: List[str]) -> str:
        """Generate a product description"""
        desc_templates = {
            'energy_drink': f"A {tags[0]} and {tags[1] if len(tags) > 1 else 'energizing'} {category} with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'natural flavors'}. Perfect for when you need a boost.",
            'soda': f"Classic {tags[0]} {category} with {tags[1] if len(tags) > 1 else 'refreshing'} taste. Made with {ingredients[0]}.",
            'juice': f"Fresh {tags[0]} {category} packed with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'vitamins'}. {tags[1] if len(tags) > 1 else 'Natural'} and delicious.",
            'sports_drink': f"Electrolyte-rich {category} with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'minerals'}. {tags[0]} and {tags[1] if len(tags) > 1 else 'refreshing'}.",
            'coffee_drink': f"{tags[0].capitalize()} {category} with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'coffee extract'}. {tags[1] if len(tags) > 1 else 'Smooth'} and {tags[2] if len(tags) > 2 else 'bold'}.",
            'tea': f"Premium {tags[0]} {category} infused with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'herbs'}. {tags[1] if len(tags) > 1 else 'Calming'} and {tags[2] if len(tags) > 2 else 'refreshing'}.",
            'water_enhanced': f"Enhanced {category} with {ingredients[0]} and {ingredients[1] if len(ingredients) > 1 else 'vitamins'}. {tags[0].capitalize()} and {tags[1] if len(tags) > 1 else 'light'}."
        }
        return desc_templates.get(category, f"A {tags[0]} {category} beverage.")
    
    def generate_segments(self, n_segments: int = 5) -> pd.DataFrame:
        """Generate user segment definitions"""
        segments = []
        
        for i in range(n_segments):
            segments.append({
                'segment_id': f'seg_{i:02d}',
                'age_bucket': np.random.choice(self.age_buckets),
                'region': np.random.choice(self.regions),
                'psychographic': np.random.choice(self.psychographics),
                'segment_name': f'Segment_{i+1}'
            })
        
        return pd.DataFrame(segments)
    
    def generate_contexts(self, n_contexts: int = 100) -> pd.DataFrame:
        """Generate context instances"""
        contexts = []
        
        for i in range(n_contexts):
            hour = np.random.randint(0, 24)
            time_of_day = self._get_time_of_day(hour)
            
            contexts.append({
                'context_id': f'ctx_{i:03d}',
                'time_of_day': time_of_day,
                'hour': hour,
                'location': np.random.choice(self.locations),
                'occasion': np.random.choice(self.occasions),
                'price_shown': round(np.random.uniform(1.0, 6.0), 2)
            })
        
        return pd.DataFrame(contexts)
    
    def _get_time_of_day(self, hour: int) -> str:
        """Convert hour to time of day category"""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'late_night'
    
    def generate_intent_logs(self, products: pd.DataFrame, segments: pd.DataFrame, 
                            contexts: pd.DataFrame, n_logs: int = 1000,
                            start_date: str = '2024-01-01') -> pd.DataFrame:
        """Generate intent/preference logs"""
        logs = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i in range(n_logs):
            # Sample random product, segment, context
            product = products.sample(1).iloc[0]
            segment = segments.sample(1).iloc[0]
            context = contexts.sample(1).iloc[0]
            
            # Generate preference value (0-1 scale, or rating 1-5)
            # Make it somewhat realistic based on segment preferences
            base_preference = np.random.uniform(0.3, 0.9)
            
            # Add some segment-product affinity (simplified)
            if segment['psychographic'] == 'health_focused' and product['sugar_g'] < 10:
                base_preference += 0.1
            elif segment['psychographic'] == 'budget_sensitive' and product['price'] < 2.5:
                base_preference += 0.1
            
            preference = np.clip(base_preference, 0.0, 1.0)
            rating = int(np.round(preference * 4) + 1)  # Convert to 1-5 scale
            
            # Generate timestamp
            days_offset = np.random.randint(0, 30)
            timestamp = start + timedelta(days=days_offset, hours=np.random.randint(0, 24))
            
            logs.append({
                'log_id': f'log_{i:04d}',
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'product_id': product['product_id'],
                'segment_id': segment['segment_id'],
                'context_id': context['context_id'],
                'preference_value': round(preference, 3),
                'rating': rating,
                'liked': 1 if preference > 0.6 else 0
            })
        
        return pd.DataFrame(logs)
    
    def generate_all_data(self, n_products: int = 50, n_segments: int = 5,
                         n_contexts: int = 100, n_logs: int = 1000) -> Dict[str, pd.DataFrame]:
        """Generate all synthetic data"""
        print("Generating synthetic data...")
        
        products = self.generate_products(n_products)
        segments = self.generate_segments(n_segments)
        contexts = self.generate_contexts(n_contexts)
        intent_logs = self.generate_intent_logs(products, segments, contexts, n_logs)
        
        print(f"Generated {len(products)} products, {len(segments)} segments, "
              f"{len(contexts)} contexts, {len(intent_logs)} intent logs")
        
        return {
            'products': products,
            'segments': segments,
            'contexts': contexts,
            'intent_logs': intent_logs
        }
    
    def save_data(self, data: Dict[str, pd.DataFrame], output_dir: str = 'data'):
        """Save all data to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for name, df in data.items():
            filepath = os.path.join(output_dir, f'{name}.csv')
            df.to_csv(filepath, index=False)
            print(f"Saved {filepath}")

