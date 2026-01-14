#!/usr/bin/env python3
"""
Compile datasets from Data_Engine ingestion directory into LPM-compatible schemas.

This script:
1. Reads datasets from bucket1_online_datasets (reviews, sentiment, ratings)
2. Extracts brands, regions, and entities
3. Transforms review/sentiment data into survey responses and preference scores
4. Generates price/promo/availability schedules from aggregated data
5. Creates observed metrics from review aggregations
6. Outputs all data in the required schema format for LPM consumption

Usage:
    python scripts/compile_ingestion_data_for_lpm.py \
        --start-week 1 \
        --num-weeks 52 \
        --seed 42 \
        --output-dir data/synthetic/
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.versioning import generate_data_version
from common.seeds import SeedManager


class IngestionDataCompiler:
    """
    Compiles ingestion datasets into LPM-compatible schemas.
    """
    
    def __init__(self, start_week: int, num_weeks: int, seed: int, data_version: Optional[str] = None):
        """
        Initialize compiler.
        
        Args:
            start_week: Starting week ID
            num_weeks: Number of weeks to generate
            seed: Random seed for reproducibility
            data_version: Optional data version ID (auto-generated if None)
        """
        self.start_week = start_week
        self.num_weeks = num_weeks
        self.seed = seed
        self.seed_manager = SeedManager(base_seed=seed)
        self.data_version = data_version or generate_data_version()
        
        # Initialize RNGs
        self.rng_entities = self.seed_manager.get_rng("entities")
        self.rng_prices = self.seed_manager.get_rng("prices")
        self.rng_promos = self.seed_manager.get_rng("promos")
        self.rng_surveys = self.seed_manager.get_rng("surveys")
        self.rng_aggregates = self.seed_manager.get_rng("aggregates")
        
        # Data paths
        self.ingestion_dir = Path(__file__).parent.parent / "data_engine" / "Data_Engine" / "ingestion"
        self.bucket1_dir = self.ingestion_dir / "bucket1_online_datasets"
        
        # Extracted entities
        self.brands = None
        self.regions = None
        self.channels = None
        
        # Loaded datasets
        self.mcdonalds_reviews = None
        self.english_tweets = None
        self.restaurant_ratings = None
        
    def load_datasets(self):
        """Load all available datasets from ingestion directory."""
        print("Loading datasets from ingestion directory...")
        
        # 1. McDonald's Sentiment Reviews
        mcd_file = self.bucket1_dir / "food_online_data" / "McDonaldsSentimentReviews.csv"
        if mcd_file.exists():
            try:
                self.mcdonalds_reviews = pd.read_csv(mcd_file)
                print(f"  ✓ Loaded {len(self.mcdonalds_reviews)} McDonald's reviews")
            except Exception as e:
                print(f"  ⚠ Could not load McDonald's reviews: {e}")
        
        # 2. English Tweets Dataset
        english_file = self.bucket1_dir / "food_online_data" / "English dataset.csv"
        if english_file.exists():
            try:
                self.english_tweets = pd.read_csv(english_file)
                print(f"  ✓ Loaded {len(self.english_tweets)} English tweets")
            except Exception as e:
                print(f"  ⚠ Could not load English tweets: {e}")
        
        # 3. Restaurant Ratings
        ratings_file = self.bucket1_dir / "numerical_food_data" / "restaurant_ratings_reviews.csv"
        if ratings_file.exists():
            try:
                self.restaurant_ratings = pd.read_csv(ratings_file)
                print(f"  ✓ Loaded {len(self.restaurant_ratings)} restaurant ratings")
            except Exception as e:
                print(f"  ⚠ Could not load restaurant ratings: {e}")
        
        print(f"✓ Dataset loading complete")
    
    def normalize_brand_name(self, name: str) -> str:
        """Normalize brand names to consolidate variants."""
        if pd.isna(name):
            return None
        
        name_lower = str(name).lower().strip()
        
        # Brand normalization mapping
        brand_normalizations = {
            'mcdonald': "McDonald's",
            "mcdonald's": "McDonald's",
            'mcdonalds': "McDonald's",
            'mcd': "McDonald's",
            'kfc': "KFC",
            'kfc ': "KFC",
            'burger king': "Burger King",
            'bk': "Burger King",
            'wendy': "Wendy's",
            "wendy's": "Wendy's",
            'subway': "Subway",
            'domino': "Domino's",
            "domino's": "Domino's",
            'dominos': "Domino's",
            'taco bell': "Taco Bell",
            'pizza hut': "Pizza Hut",
            'starbucks': "Starbucks",
            'dunkin': "Dunkin'",
            "dunkin'": "Dunkin'",
            'burger': "Burger King"  # Generic "Burger" likely refers to Burger King
        }
        
        # Check for exact matches first
        if name_lower in brand_normalizations:
            return brand_normalizations[name_lower]
        
        # Check for partial matches
        for key, normalized in brand_normalizations.items():
            if key in name_lower:
                return normalized
        
        # If no match, return title case
        return str(name).strip().title()
    
    def extract_entities(self):
        """Extract brands, regions, and channels from datasets."""
        print("\nExtracting entities...")
        
        brands_set = set()
        regions_set = set()
        
        # Extract brands from various sources with normalization
        if self.english_tweets is not None and 'marka_type' in self.english_tweets.columns:
            brands_from_tweets = self.english_tweets['marka_type'].dropna().unique()
            for b in brands_from_tweets:
                normalized = self.normalize_brand_name(b)
                if normalized:
                    brands_set.add(normalized)
        
        if self.restaurant_ratings is not None and 'name' in self.restaurant_ratings.columns:
            # Extract fast food brands from restaurant names
            fast_food_keywords = ['mcdonald', 'burger king', 'wendy', 'kfc', 'taco bell', 
                                 'subway', 'pizza hut', 'domino', 'starbucks', 'dunkin']
            restaurant_names = self.restaurant_ratings['name'].str.lower().dropna()
            for name in restaurant_names:
                for keyword in fast_food_keywords:
                    if keyword in name:
                        normalized = self.normalize_brand_name(keyword)
                        if normalized:
                            brands_set.add(normalized)
        
        # Add McDonald's explicitly if we have reviews
        if self.mcdonalds_reviews is not None:
            brands_set.add("McDonald's")
        
        # If no brands found, use defaults
        if not brands_set:
            brands_set = {"McDonald's", "Burger King", "Wendy's", "KFC", "Taco Bell"}
        
        print(f"  Found {len(brands_set)} unique brands after normalization: {sorted(brands_set)}")
        
        # Extract regions
        if self.english_tweets is not None and 'userlocation' in self.english_tweets.columns:
            locations = self.english_tweets['userlocation'].dropna().unique()
            for loc in locations:
                loc_str = str(loc).strip()
                if loc_str and loc_str != 'nan':
                    # Map to US regions
                    if 'united states' in loc_str.lower() or 'us' in loc_str.lower():
                        regions_set.add("US_North")
                        regions_set.add("US_South")
                        regions_set.add("US_West")
                        regions_set.add("US_East")
        
        if self.restaurant_ratings is not None and 'state' in self.restaurant_ratings.columns:
            states = self.restaurant_ratings['state'].dropna().unique()
            # Map states to regions (simplified)
            state_to_region = {
                'CA': 'US_West', 'OR': 'US_West', 'WA': 'US_West',
                'TX': 'US_South', 'FL': 'US_South', 'GA': 'US_South',
                'NY': 'US_East', 'MA': 'US_East', 'PA': 'US_East',
                'IL': 'US_North', 'MI': 'US_North', 'OH': 'US_North'
            }
            for state in states:
                if state in state_to_region:
                    regions_set.add(state_to_region[state])
        
        # If no regions found, use defaults
        if not regions_set:
            regions_set = {"US_North", "US_South", "US_West", "US_East"}
        
        # Create entity DataFrames
        brands_list = sorted(list(brands_set))
        self.brands = pd.DataFrame({
            'brand_id': [f"BRAND_{i:02d}" for i in range(1, len(brands_list) + 1)],
            'name': brands_list,
            'category': ['Fast Food'] * len(brands_list)
        })
        
        regions_list = sorted(list(regions_set))
        self.regions = pd.DataFrame({
            'region_id': [f"REGION_{i:02d}" for i in range(1, len(regions_list) + 1)],
            'name': regions_list
        })
        
        # Create brand_id to name mapping
        self.brand_id_to_name = dict(zip(self.brands['brand_id'], self.brands['name']))
        self.name_to_brand_id = {v: k for k, v in self.brand_id_to_name.items()}
        
        # Create region_id to name mapping
        self.region_id_to_name = dict(zip(self.regions['region_id'], self.regions['name']))
        self.name_to_region_id = {v: k for k, v in self.region_id_to_name.items()}
        
        # Channels (default)
        self.channels = pd.DataFrame({
            'channel_id': ['CHANNEL_01', 'CHANNEL_02'],
            'name': ['drive_thru', 'dine_in']
        })
        
        print(f"  ✓ Extracted {len(self.brands)} brands: {', '.join(brands_list[:5])}{'...' if len(brands_list) > 5 else ''}")
        print(f"  ✓ Extracted {len(self.regions)} regions: {', '.join(regions_list)}")
        print(f"  ✓ Created {len(self.channels)} channels")
    
    def generate_survey_responses(self) -> pd.DataFrame:
        """Transform review/sentiment data into survey responses."""
        print("\nGenerating survey responses from review data...")
        
        rows = []
        respondent_counter = 1
        
        # Process McDonald's reviews
        if self.mcdonalds_reviews is not None and 'review' in self.mcdonalds_reviews.columns:
            mcd_brand_id = self.name_to_brand_id.get("McDonald's", self.brands.iloc[0]['brand_id'])
            
            for idx, row in self.mcdonalds_reviews.iterrows():
                if pd.notna(row.get('review')):
                    # Sample weeks (not all reviews)
                    if self.rng_surveys.random() < 0.1:  # 10% sampling
                        week_id = self.rng_surveys.integers(
                            self.start_week, 
                            self.start_week + self.num_weeks
                        )
                        region_id = self.rng_surveys.choice(self.regions['region_id'].values)
                        
                        # Convert review to preference score (0-1)
                        # Simple heuristic: longer reviews = higher engagement = higher preference
                        review_text = str(row['review'])
                        preference_score = min(1.0, len(review_text) / 200.0)  # Normalize by length
                        preference_score += self.rng_surveys.normal(0, 0.2)
                        preference_score = np.clip(preference_score, 0.0, 1.0)
                        
                        rows.append({
                            'respondent_id': f"RESP_{respondent_counter:05d}",
                            'week_id': week_id,
                            'region_id': region_id,
                            'brand_id': mcd_brand_id,
                            'preference_score': preference_score
                        })
                        respondent_counter += 1
        
        # Process English tweets
        if self.english_tweets is not None:
            for idx, row in self.english_tweets.iterrows():
                if pd.notna(row.get('marka_type')) and pd.notna(row.get('sentiment')):
                    brand_name_raw = str(row['marka_type']).strip()
                    brand_name = self.normalize_brand_name(brand_name_raw)
                    brand_id = self.name_to_brand_id.get(brand_name) if brand_name else None
                    
                    if brand_id and self.rng_surveys.random() < 0.05:  # 5% sampling
                        week_id = self.rng_surveys.integers(
                            self.start_week,
                            self.start_week + self.num_weeks
                        )
                        
                        # Map location to region
                        location = str(row.get('userlocation', '')).lower()
                        if 'united states' in location or 'us' in location:
                            region_id = self.rng_surveys.choice(self.regions['region_id'].values)
                        else:
                            region_id = self.rng_surveys.choice(self.regions['region_id'].values)
                        
                        # Convert sentiment to preference score
                        sentiment = str(row.get('sentiment', 'neutral')).lower()
                        if 'negatif' in sentiment or 'negative' in sentiment:
                            base_score = 0.3
                        elif 'positif' in sentiment or 'positive' in sentiment:
                            base_score = 0.7
                        else:
                            base_score = 0.5
                        
                        # Add polarity if available
                        if pd.notna(row.get('polarity')):
                            try:
                                polarity = float(row['polarity'])
                                base_score = 0.5 + polarity * 0.3  # Scale to 0.2-0.8
                            except:
                                pass
                        
                        preference_score = base_score + self.rng_surveys.normal(0, 0.15)
                        preference_score = np.clip(preference_score, 0.0, 1.0)
                        
                        rows.append({
                            'respondent_id': f"RESP_{respondent_counter:05d}",
                            'week_id': week_id,
                            'region_id': region_id,
                            'brand_id': brand_id,
                            'preference_score': preference_score
                        })
                        respondent_counter += 1
        
        # Process restaurant ratings
        if self.restaurant_ratings is not None:
            for idx, row in self.restaurant_ratings.iterrows():
                if pd.notna(row.get('name')) and pd.notna(row.get('avg_rating')):
                    restaurant_name_raw = str(row['name'])
                    restaurant_name_normalized = self.normalize_brand_name(restaurant_name_raw)
                    
                    # Match to brand using normalized name
                    brand_id = None
                    if restaurant_name_normalized:
                        brand_id = self.name_to_brand_id.get(restaurant_name_normalized)
                    
                    # Fallback: check if any brand name appears in restaurant name
                    if not brand_id:
                        restaurant_name_lower = restaurant_name_raw.lower()
                        for brand_name, bid in self.name_to_brand_id.items():
                            if brand_name.lower() in restaurant_name_lower:
                                brand_id = bid
                                break
                    
                    if brand_id and self.rng_surveys.random() < 0.02:  # 2% sampling
                        week_id = self.rng_surveys.integers(
                            self.start_week,
                            self.start_week + self.num_weeks
                        )
                        
                        # Map state to region
                        state = str(row.get('state', ''))
                        state_to_region = {
                            'CA': 'US_West', 'OR': 'US_West', 'WA': 'US_West',
                            'TX': 'US_South', 'FL': 'US_South', 'GA': 'US_South',
                            'NY': 'US_East', 'MA': 'US_East', 'PA': 'US_East',
                            'IL': 'US_North', 'MI': 'US_North', 'OH': 'US_North'
                        }
                        region_name = state_to_region.get(state, 'US_North')
                        region_id = self.name_to_region_id.get(region_name, self.regions.iloc[0]['region_id'])
                        
                        # Convert rating to preference score
                        try:
                            avg_rating = float(row['avg_rating'])
                            preference_score = avg_rating / 5.0  # Normalize to 0-1
                            preference_score += self.rng_surveys.normal(0, 0.1)
                            preference_score = np.clip(preference_score, 0.0, 1.0)
                        except:
                            preference_score = 0.5
                        
                        rows.append({
                            'respondent_id': f"RESP_{respondent_counter:05d}",
                            'week_id': week_id,
                            'region_id': region_id,
                            'brand_id': brand_id,
                            'preference_score': preference_score
                        })
                        respondent_counter += 1
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} survey responses")
        return df
    
    def generate_price_schedule(self) -> pd.DataFrame:
        """Generate price schedule from aggregated data."""
        print("\nGenerating price schedule...")
        
        rows = []
        
        # Base prices from restaurant data if available
        base_prices = {}
        if self.restaurant_ratings is not None and 'price' in self.restaurant_ratings.columns:
            for brand_id in self.brands['brand_id']:
                brand_name = self.brand_id_to_name[brand_id]
                matching = self.restaurant_ratings[
                    self.restaurant_ratings['name'].str.contains(brand_name, case=False, na=False)
                ]
                if len(matching) > 0:
                    # Map price level to price index
                    price_levels = matching['price'].value_counts()
                    if 'high' in price_levels.index:
                        base_prices[brand_id] = 1.1
                    elif 'medium' in price_levels.index:
                        base_prices[brand_id] = 1.0
                    else:
                        base_prices[brand_id] = 0.9
                else:
                    base_prices[brand_id] = 1.0
        else:
            # Default base prices
            for brand_id in self.brands['brand_id']:
                base_prices[brand_id] = 1.0
        
        for week_id in range(self.start_week, self.start_week + self.num_weeks):
            # Seasonality
            seasonal_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (week_id - self.start_week) / 52.0)
            
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row['brand_id']
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row['region_id']
                    
                    # Base price with brand differentiation
                    price_index = base_prices[brand_id] * seasonal_factor
                    
                    # Region heterogeneity
                    region_multiplier = 1.0 + (hash(region_id) % 20) / 200.0
                    price_index *= region_multiplier
                    
                    # Add volatility
                    price_index *= (1.0 + self.rng_prices.normal(0, 0.05))
                    price_index = max(0.5, price_index)
                    
                    rows.append({
                        'week_id': week_id,
                        'brand_id': brand_id,
                        'region_id': region_id,
                        'price_index': price_index
                    })
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} price schedule entries")
        return df
    
    def generate_promo_schedule(self) -> pd.DataFrame:
        """Generate promo schedule."""
        print("\nGenerating promo schedule...")
        
        rows = []
        
        for week_id in range(self.start_week, self.start_week + self.num_weeks):
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row['brand_id']
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row['region_id']
                    
                    # Base promo intensity
                    promo_intensity = 0.3 + self.rng_promos.normal(0, 0.1)
                    promo_intensity = np.clip(promo_intensity, 0.0, 1.0)
                    
                    rows.append({
                        'week_id': week_id,
                        'brand_id': brand_id,
                        'region_id': region_id,
                        'promo_intensity': promo_intensity
                    })
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} promo schedule entries")
        return df
    
    def generate_menu_availability(self) -> pd.DataFrame:
        """Generate menu availability schedule."""
        print("\nGenerating menu availability schedule...")
        
        rows = []
        
        for week_id in range(self.start_week, self.start_week + self.num_weeks):
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row['brand_id']
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row['region_id']
                    
                    # Base availability
                    availability = 0.9 + self.rng_promos.normal(0, 0.05)
                    availability = np.clip(availability, 0.0, 1.0)
                    
                    rows.append({
                        'week_id': week_id,
                        'brand_id': brand_id,
                        'region_id': region_id,
                        'availability_score': availability
                    })
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} availability schedule entries")
        return df
    
    def generate_observed_metrics(self, price_schedule: pd.DataFrame, 
                                  promo_schedule: pd.DataFrame) -> pd.DataFrame:
        """Generate observed metrics from aggregated review data."""
        print("\nGenerating observed metrics...")
        
        rows = []
        
        # Aggregate review data by brand
        brand_review_counts = {}
        brand_avg_ratings = {}
        
        if self.restaurant_ratings is not None:
            for brand_id in self.brands['brand_id']:
                brand_name = self.brand_id_to_name[brand_id]
                matching = self.restaurant_ratings[
                    self.restaurant_ratings['name'].str.contains(brand_name, case=False, na=False)
                ]
                if len(matching) > 0:
                    brand_review_counts[brand_id] = matching['num_reviews'].sum()
                    brand_avg_ratings[brand_id] = matching['avg_rating'].mean()
        
        # Ensure all brands have reasonable base transaction counts
        # Use median of existing counts or a minimum threshold
        if brand_review_counts:
            median_count = np.median(list(brand_review_counts.values()))
            min_threshold = max(median_count * 0.3, 5000.0)  # At least 30% of median or 5000
        else:
            min_threshold = 5000.0
        
        # Set minimum base transactions for brands with low/no review counts
        for brand_id in self.brands['brand_id']:
            if brand_id not in brand_review_counts or brand_review_counts[brand_id] < min_threshold:
                brand_review_counts[brand_id] = min_threshold
                print(f"  Setting minimum base transactions for {self.brand_id_to_name[brand_id]}: {min_threshold:.0f}")
        
        # Merge price and promo schedules
        merged = price_schedule.merge(
            promo_schedule,
            on=['week_id', 'brand_id', 'region_id'],
            how='left'
        )
        
        for _, row in merged.iterrows():
            week_id = int(row['week_id'])
            brand_id = row['brand_id']
            region_id = row['region_id']
            price_index = row['price_index']
            promo_intensity = row['promo_intensity']
            
            # Base transactions from review counts
            base_transactions = brand_review_counts.get(brand_id, 1000.0)
            
            # Brand effect
            brand_multiplier = 1.0 + (hash(brand_id) % 100) / 200.0
            
            # Region effect
            region_multiplier = 1.0 + (hash(region_id) % 50) / 200.0
            
            # Price elasticity
            price_effect = np.exp(-0.5 * (price_index - 1.0))
            
            # Promo effect
            promo_effect = 1.0 + 0.5 * promo_intensity
            
            # Seasonality
            seasonal_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (week_id - self.start_week) / 52.0)
            
            # Compute transactions
            transactions = (base_transactions * brand_multiplier * region_multiplier *
                          price_effect * promo_effect * seasonal_factor)
            
            # Add noise
            transactions *= (1.0 + self.rng_aggregates.normal(0, 0.15))
            transactions = max(0, transactions)
            
            # Revenue = transactions * price
            revenue = transactions * price_index * self.rng_aggregates.uniform(0.9, 1.1)
            revenue *= (1.0 + self.rng_aggregates.normal(0, 0.2))
            revenue = max(0, revenue)
            
            # Confidence weight based on review count
            review_count = brand_review_counts.get(brand_id, 0)
            confidence_weight = min(1.0, 0.5 + review_count / 10000.0)
            confidence_weight += self.rng_aggregates.normal(0, 0.1)
            confidence_weight = np.clip(confidence_weight, 0.1, 1.0)
            
            rows.append({
                'week_id': week_id,
                'brand_id': brand_id,
                'region_id': region_id,
                'transactions_obs': transactions,
                'revenue_obs': revenue,
                'confidence_weight': confidence_weight
            })
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} observed metrics entries")
        return df
    
    def generate_taste_ratings(self) -> pd.DataFrame:
        """Generate taste ratings from review data."""
        print("\nGenerating taste ratings...")
        
        rows = []
        respondent_counter = 1
        
        # Create items from brands
        items = []
        for brand_id in self.brands['brand_id']:
            brand_name = self.brand_id_to_name[brand_id]
            items.append(f"{brand_name}_Burger")
            items.append(f"{brand_name}_Fries")
            items.append(f"{brand_name}_Drink")
        
        attributes = ["sweetness", "saltiness", "spiciness", "richness"]
        
        # Sample respondents
        num_respondents = min(500, len(self.brands) * 50)
        
        for i in range(num_respondents):
            respondent_id = f"RESP_{respondent_counter:05d}"
            num_items_rated = self.rng_surveys.integers(5, min(15, len(items)))
            items_rated = self.rng_surveys.choice(items, size=num_items_rated, replace=False)
            
            for item_id in items_rated:
                rating = self.rng_surveys.uniform(2.0, 5.0)
                
                row = {
                    'respondent_id': respondent_id,
                    'item_id': item_id,
                    'rating': rating
                }
                
                # Add attribute scores
                for attr in attributes:
                    row[attr] = self.rng_surveys.uniform(0.0, 1.0)
                
                rows.append(row)
            
            respondent_counter += 1
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} taste ratings")
        return df
    
    def generate_choice_experiments(self) -> pd.DataFrame:
        """Generate choice experiment data."""
        print("\nGenerating choice experiments...")
        
        rows = []
        respondent_counter = 1
        option_set_id = 0
        
        # Sample weeks
        survey_weeks = list(range(self.start_week, self.start_week + min(4, self.num_weeks)))
        
        num_respondents = min(300, len(self.brands) * 30)
        
        for i in range(num_respondents):
            respondent_id = f"RESP_{respondent_counter:05d}"
            
            for week_id in survey_weeks:
                option_set_id += 1
                
                # Create option set (2-4 brands)
                num_options = self.rng_surveys.integers(2, min(5, len(self.brands) + 1))
                options = self.rng_surveys.choice(
                    self.brands['brand_id'].values,
                    size=num_options,
                    replace=False
                )
                
                # Generate prices for each option
                prices = {}
                for brand_id in options:
                    prices[f"price_{brand_id}"] = self.rng_surveys.uniform(0.8, 1.5)
                
                # Choose one
                chosen_brand_id = self.rng_surveys.choice(options)
                
                row = {
                    'respondent_id': respondent_id,
                    'week_id': week_id,
                    'option_set_id': option_set_id,
                    'chosen_brand_id': chosen_brand_id,
                    **prices,
                    'context_time_of_day': self.rng_surveys.choice(['morning', 'afternoon', 'evening']),
                    'context_day_of_week': self.rng_surveys.choice(['weekday', 'weekend'])
                }
                
                rows.append(row)
            
            respondent_counter += 1
        
        df = pd.DataFrame(rows)
        print(f"  ✓ Generated {len(df)} choice experiments")
        return df
    
    def compile_all(self, output_dir: str) -> Dict[str, str]:
        """
        Compile all datasets and save to disk.
        
        Args:
            output_dir: Base directory to save output files
            
        Returns:
            Dictionary mapping table names to file paths
        """
        print(f"\n{'='*60}")
        print(f"Compiling datasets for LPM consumption")
        print(f"{'='*60}")
        print(f"Data version: {self.data_version}")
        print(f"Start week: {self.start_week}")
        print(f"Number of weeks: {self.num_weeks}")
        print(f"Seed: {self.seed}")
        
        # Load datasets
        self.load_datasets()
        
        # Extract entities
        self.extract_entities()
        
        # Create versioned subdirectory
        version_dir = Path(output_dir) / self.data_version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        
        # 1. Entity tables
        print("\n" + "="*60)
        print("Generating entity tables...")
        print("="*60)
        
        self.brands.to_csv(version_dir / "brands.csv", index=False)
        file_paths["brands"] = str(version_dir / "brands.csv")
        
        self.regions.to_csv(version_dir / "regions.csv", index=False)
        file_paths["regions"] = str(version_dir / "regions.csv")
        
        self.channels.to_csv(version_dir / "channels.csv", index=False)
        file_paths["channels"] = str(version_dir / "channels.csv")
        
        # 2. Environment schedules
        print("\n" + "="*60)
        print("Generating environment schedules...")
        print("="*60)
        
        price_schedule = self.generate_price_schedule()
        price_schedule.to_csv(version_dir / "brand_price_schedule.csv", index=False)
        file_paths["brand_price_schedule"] = str(version_dir / "brand_price_schedule.csv")
        
        promo_schedule = self.generate_promo_schedule()
        promo_schedule.to_csv(version_dir / "brand_promo_schedule.csv", index=False)
        file_paths["brand_promo_schedule"] = str(version_dir / "brand_promo_schedule.csv")
        
        availability = self.generate_menu_availability()
        availability.to_csv(version_dir / "brand_menu_availability.csv", index=False)
        file_paths["brand_menu_availability"] = str(version_dir / "brand_menu_availability.csv")
        
        # 3. Survey data
        print("\n" + "="*60)
        print("Generating survey data...")
        print("="*60)
        
        survey_responses = self.generate_survey_responses()
        survey_responses.to_csv(version_dir / "survey_responses.csv", index=False)
        file_paths["survey_responses"] = str(version_dir / "survey_responses.csv")
        
        taste_ratings = self.generate_taste_ratings()
        taste_ratings.to_csv(version_dir / "taste_ratings.csv", index=False)
        file_paths["taste_ratings"] = str(version_dir / "taste_ratings.csv")
        
        choice_experiments = self.generate_choice_experiments()
        choice_experiments.to_csv(version_dir / "choice_experiments.csv", index=False)
        file_paths["choice_experiments"] = str(version_dir / "choice_experiments.csv")
        
        # 4. Observed aggregates
        print("\n" + "="*60)
        print("Generating observed metrics...")
        print("="*60)
        
        observed_metrics = self.generate_observed_metrics(price_schedule, promo_schedule)
        observed_metrics.to_csv(version_dir / "observed_metrics_brand_week_region.csv", index=False)
        file_paths["observed_metrics_brand_week_region"] = str(version_dir / "observed_metrics_brand_week_region.csv")
        
        # Save metadata
        metadata = {
            "data_version": self.data_version,
            "start_week": self.start_week,
            "num_weeks": self.num_weeks,
            "seed": self.seed,
            "num_brands": len(self.brands),
            "num_regions": len(self.regions),
            "num_channels": len(self.channels),
            "generated_at": datetime.now().isoformat(),
            "source_datasets": {
                "mcdonalds_reviews": self.mcdonalds_reviews is not None,
                "english_tweets": self.english_tweets is not None,
                "restaurant_ratings": self.restaurant_ratings is not None
            }
        }
        
        with open(version_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n{'='*60}")
        print("Compilation complete!")
        print(f"{'='*60}")
        print(f"✓ Generated {len(file_paths)} tables")
        print(f"✓ Output directory: {version_dir}")
        print(f"\nTables generated:")
        for table_name, file_path in file_paths.items():
            print(f"  - {table_name}: {file_path}")
        
        return file_paths


def main():
    parser = argparse.ArgumentParser(
        description="Compile ingestion datasets into LPM-compatible schemas"
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=1,
        help="Starting week ID"
    )
    parser.add_argument(
        "--num-weeks",
        type=int,
        default=52,
        help="Number of weeks to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory for generated datasets"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        default=None,
        help="Optional data version ID (auto-generated if not provided)"
    )
    
    args = parser.parse_args()
    
    # Initialize compiler
    compiler = IngestionDataCompiler(
        start_week=args.start_week,
        num_weeks=args.num_weeks,
        seed=args.seed,
        data_version=args.data_version
    )
    
    # Compile all datasets
    try:
        file_paths = compiler.compile_all(args.output_dir)
        print(f"\n✓ Successfully compiled datasets!")
        print(f"  Data version: {compiler.data_version}")
        print(f"  Use this version ID in downstream layers.")
    except Exception as e:
        print(f"\n✗ Error during compilation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

