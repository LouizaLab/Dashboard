"""
Synthetic Data Factory for POC mode.

Generates deterministic, versioned datasets that match production schemas.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import os

from common.versioning import generate_data_version
from common.seeds import SeedManager
from data_engine.config import SyntheticDataConfig


class SyntheticDataGenerator:
    """
    Generates synthetic datasets with deterministic, reproducible outputs.
    
    All randomness is seeded and reproducible given the same config + seed.
    """
    
    def __init__(self, config: SyntheticDataConfig, seed: int, data_version: Optional[str] = None):
        """
        Initialize generator.
        
        Args:
            config: Configuration for data generation
            seed: Random seed for reproducibility
            data_version: Optional data version ID (auto-generated if None)
        """
        self.config = config
        self.seed = seed
        self.seed_manager = SeedManager(base_seed=seed)
        self.data_version = data_version or generate_data_version()
        
        # Initialize RNGs for different components
        self.rng_entities = self.seed_manager.get_rng("entities")
        self.rng_prices = self.seed_manager.get_rng("prices")
        self.rng_promos = self.seed_manager.get_rng("promos")
        self.rng_surveys = self.seed_manager.get_rng("surveys")
        self.rng_aggregates = self.seed_manager.get_rng("aggregates")
        
        # Generate canonical entity lists
        self.brands = self._generate_brands()
        self.regions = self._generate_regions()
        self.channels = self._generate_channels()
    
    def _generate_brands(self) -> pd.DataFrame:
        """Generate brand entity table."""
        brand_ids = [f"BRAND_{i:02d}" for i in range(1, self.config.num_brands + 1)]
        categories = ["Fast Food", "Casual Dining", "Quick Service"]
        
        brands = []
        for i, brand_id in enumerate(brand_ids):
            category = categories[i % len(categories)]
            name = f"{category} Brand {i+1}"
            brands.append({
                "brand_id": brand_id,
                "name": name,
                "category": category
            })
        
        return pd.DataFrame(brands)
    
    def _generate_regions(self) -> pd.DataFrame:
        """Generate region entity table."""
        region_ids = [f"REGION_{i:02d}" for i in range(1, self.config.num_regions + 1)]
        region_names = ["US_North", "US_South", "US_West", "US_East", "US_Central"]
        
        regions = []
        for i, region_id in enumerate(region_ids):
            name = region_names[i % len(region_names)]
            regions.append({
                "region_id": region_id,
                "name": name
            })
        
        return pd.DataFrame(regions)
    
    def _generate_channels(self) -> pd.DataFrame:
        """Generate channel entity table."""
        channel_ids = [f"CHANNEL_{i:02d}" for i in range(1, self.config.num_channels + 1)]
        channel_names = ["drive_thru", "dine_in", "delivery", "mobile"]
        
        channels = []
        for i, channel_id in enumerate(channel_ids):
            name = channel_names[i % len(channel_names)]
            channels.append({
                "channel_id": channel_id,
                "name": name
            })
        
        return pd.DataFrame(channels)
    
    def generate_price_schedule(self) -> pd.DataFrame:
        """
        Generate brand price schedule with seasonality and shocks.
        
        Returns:
            DataFrame with columns: week_id, brand_id, region_id, price_index
        """
        rows = []
        
        for week_id in range(self.config.start_week, self.config.start_week + self.config.num_weeks):
            # Seasonality: higher prices in certain weeks
            seasonal_factor = 1.0 + self.config.seasonality_strength * np.sin(
                2 * np.pi * (week_id - self.config.start_week) / 52.0
            )
            
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row["brand_id"]
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row["region_id"]
                    
                    # Base price with brand differentiation
                    brand_base = self.config.price_base * (1.0 + (hash(brand_id) % 100) / 500.0)
                    
                    # Region heterogeneity
                    region_multiplier = 1.0 + (hash(region_id) % 50) / 500.0
                    
                    # Random walk with volatility
                    price_index = brand_base * region_multiplier * seasonal_factor
                    price_index *= (1.0 + self.rng_prices.normal(0, self.config.price_volatility))
                    
                    # Apply interventions
                    for intervention in self.config.interventions:
                        if (intervention.get("type") == "price_change" and
                            intervention.get("brand_id") == brand_id and
                            intervention.get("region_id") == region_id and
                            intervention.get("start_week", -1) <= week_id <= intervention.get("end_week", 9999)):
                            delta_pct = intervention.get("delta_pct", 0.0)
                            price_index *= (1.0 + delta_pct)
                    
                    rows.append({
                        "week_id": week_id,
                        "brand_id": brand_id,
                        "region_id": region_id,
                        "price_index": max(0.1, price_index)  # Ensure positive
                    })
        
        return pd.DataFrame(rows)
    
    def generate_promo_schedule(self) -> pd.DataFrame:
        """
        Generate brand promotion schedule.
        
        Returns:
            DataFrame with columns: week_id, brand_id, region_id, promo_intensity
        """
        rows = []
        
        for week_id in range(self.config.start_week, self.config.start_week + self.config.num_weeks):
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row["brand_id"]
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row["region_id"]
                    
                    # Base promo intensity
                    promo_intensity = self.config.promo_base_intensity
                    
                    # Add randomness
                    promo_intensity += self.rng_promos.normal(0, 0.1)
                    promo_intensity = np.clip(promo_intensity, 0.0, 1.0)
                    
                    # Apply interventions
                    for intervention in self.config.interventions:
                        if (intervention.get("type") == "promo" and
                            intervention.get("brand_id") == brand_id and
                            intervention.get("region_id") == region_id and
                            intervention.get("start_week", -1) <= week_id <= intervention.get("end_week", 9999)):
                            promo_intensity = intervention.get("intensity", promo_intensity)
                    
                    rows.append({
                        "week_id": week_id,
                        "brand_id": brand_id,
                        "region_id": region_id,
                        "promo_intensity": promo_intensity
                    })
        
        return pd.DataFrame(rows)
    
    def generate_menu_availability(self) -> pd.DataFrame:
        """
        Generate brand menu availability schedule.
        
        Returns:
            DataFrame with columns: week_id, brand_id, region_id, availability_score
        """
        rows = []
        
        for week_id in range(self.config.start_week, self.config.start_week + self.config.num_weeks):
            for _, brand_row in self.brands.iterrows():
                brand_id = brand_row["brand_id"]
                
                for _, region_row in self.regions.iterrows():
                    region_id = region_row["region_id"]
                    
                    # Base availability with small noise
                    availability = self.config.availability_base
                    availability += self.rng_promos.normal(0, 0.05)
                    availability = np.clip(availability, 0.0, 1.0)
                    
                    rows.append({
                        "week_id": week_id,
                        "brand_id": brand_id,
                        "region_id": region_id,
                        "availability_score": availability
                    })
        
        return pd.DataFrame(rows)
    
    def generate_survey_responses(self) -> pd.DataFrame:
        """
        Generate survey response data for PME.
        
        Returns:
            DataFrame with columns: respondent_id, week_id, region_id, brand_id, preference_score
        """
        rows = []
        
        respondent_ids = [f"RESP_{i:05d}" for i in range(1, self.config.num_respondents + 1)]
        
        # Sample weeks for surveys (not all weeks)
        survey_weeks = list(range(
            self.config.start_week,
            self.config.start_week + self.config.num_weeks,
            2  # Every other week
        ))
        
        for respondent_id in respondent_ids:
            # Each respondent has preferences for some brands
            num_brands_rated = self.rng_surveys.integers(2, self.config.num_brands + 1)
            brands_rated = self.rng_surveys.choice(
                self.brands["brand_id"].values,
                size=num_brands_rated,
                replace=False
            )
            
            for week_id in survey_weeks[:3]:  # Limit to first 3 survey weeks
                region_id = self.rng_surveys.choice(self.regions["region_id"].values)
                
                for brand_id in brands_rated:
                    # Generate preference score
                    preference_score = self.rng_surveys.uniform(0.0, 1.0)
                    
                    rows.append({
                        "respondent_id": respondent_id,
                        "week_id": week_id,
                        "region_id": region_id,
                        "brand_id": brand_id,
                        "preference_score": preference_score
                    })
        
        return pd.DataFrame(rows)
    
    def generate_taste_ratings(self) -> pd.DataFrame:
        """
        Generate taste ratings data.
        
        Returns:
            DataFrame with columns: respondent_id, item_id, rating, attributes...
        """
        rows = []
        
        respondent_ids = [f"RESP_{i:05d}" for i in range(1, min(500, self.config.num_respondents) + 1)]
        items = [f"ITEM_{i:03d}" for i in range(1, 21)]  # 20 items
        
        attributes = ["sweetness", "saltiness", "spiciness", "richness"]
        
        for respondent_id in respondent_ids:
            num_items_rated = self.rng_surveys.integers(5, 15)
            items_rated = self.rng_surveys.choice(items, size=num_items_rated, replace=False)
            
            for item_id in items_rated:
                rating = self.rng_surveys.uniform(1.0, 5.0)
                
                row = {
                    "respondent_id": respondent_id,
                    "item_id": item_id,
                    "rating": rating
                }
                
                # Add attribute scores
                for attr in attributes:
                    row[attr] = self.rng_surveys.uniform(0.0, 1.0)
                
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def generate_choice_experiments(self) -> pd.DataFrame:
        """
        Generate choice experiment data.
        
        Returns:
            DataFrame with columns: respondent_id, week_id, option_set_id, chosen_brand_id, prices..., context...
        """
        rows = []
        
        respondent_ids = [f"RESP_{i:05d}" for i in range(1, min(300, self.config.num_respondents) + 1)]
        
        survey_weeks = list(range(
            self.config.start_week,
            self.config.start_week + min(4, self.config.num_weeks)
        ))
        
        option_set_id = 0
        
        for respondent_id in respondent_ids:
            for week_id in survey_weeks:
                option_set_id += 1
                
                # Create option set (2-4 brands)
                num_options = self.rng_surveys.integers(2, min(5, self.config.num_brands + 1))
                options = self.rng_surveys.choice(
                    self.brands["brand_id"].values,
                    size=num_options,
                    replace=False
                )
                
                # Generate prices for each option
                prices = {}
                for brand_id in options:
                    prices[f"price_{brand_id}"] = self.rng_surveys.uniform(0.8, 1.5)
                
                # Choose one (simplified choice model)
                chosen_brand_id = self.rng_surveys.choice(options)
                
                row = {
                    "respondent_id": respondent_id,
                    "week_id": week_id,
                    "option_set_id": option_set_id,
                    "chosen_brand_id": chosen_brand_id,
                    **prices,
                    "context_time_of_day": self.rng_surveys.choice(["morning", "afternoon", "evening"]),
                    "context_day_of_week": self.rng_surveys.choice(["weekday", "weekend"])
                }
                
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def generate_observed_metrics(self) -> pd.DataFrame:
        """
        Generate observed market aggregates (ground truth for anchoring).
        
        Uses a hidden generative process to create realistic transaction/revenue patterns.
        
        Returns:
            DataFrame with columns: week_id, brand_id, region_id, transactions_obs, revenue_obs, confidence_weight
        """
        rows = []
        
        # Load price and promo schedules to inform observed metrics
        price_schedule = self.generate_price_schedule()
        promo_schedule = self.generate_promo_schedule()
        
        # Merge for convenience
        merged = price_schedule.merge(
            promo_schedule,
            on=["week_id", "brand_id", "region_id"],
            how="left"
        )
        
        for _, row in merged.iterrows():
            week_id = int(row["week_id"])
            brand_id = row["brand_id"]
            region_id = row["region_id"]
            price_index = row["price_index"]
            promo_intensity = row["promo_intensity"]
            
            # Hidden generative process: transactions depend on price and promo
            base_transactions = 1000.0
            
            # Brand effect
            brand_multiplier = 1.0 + (hash(brand_id) % 100) / 200.0
            
            # Region effect
            region_multiplier = 1.0 + (hash(region_id) % 50) / 200.0
            
            # Price elasticity (negative)
            price_effect = np.exp(-0.5 * (price_index - 1.0))
            
            # Promo effect (positive)
            promo_effect = 1.0 + 0.5 * promo_intensity
            
            # Seasonality
            seasonal_factor = 1.0 + self.config.seasonality_strength * np.sin(
                2 * np.pi * (week_id - self.config.start_week) / 52.0
            )
            
            # Compute transactions
            transactions = (base_transactions * brand_multiplier * region_multiplier *
                          price_effect * promo_effect * seasonal_factor)
            
            # Add noise
            transactions *= (1.0 + self.rng_aggregates.normal(0, self.config.transaction_noise_level))
            transactions = max(0, transactions)
            
            # Revenue = transactions * price (simplified)
            revenue = transactions * price_index * self.rng_aggregates.uniform(0.9, 1.1)
            revenue *= (1.0 + self.rng_aggregates.normal(0, self.config.revenue_noise_level))
            revenue = max(0, revenue)
            
            # Confidence weight (simulate measurement uncertainty)
            confidence_weight = self.config.confidence_weight_base
            confidence_weight += self.rng_aggregates.normal(0, self.config.confidence_weight_noise)
            confidence_weight = np.clip(confidence_weight, 0.1, 1.0)
            
            rows.append({
                "week_id": week_id,
                "brand_id": brand_id,
                "region_id": region_id,
                "transactions_obs": transactions,
                "revenue_obs": revenue,
                "confidence_weight": confidence_weight
            })
        
        return pd.DataFrame(rows)
    
    def generate_all(self, output_dir: str) -> Dict[str, str]:
        """
        Generate all datasets and save to disk.
        
        Args:
            output_dir: Base directory to save output files (version subdirectory will be created)
            
        Returns:
            Dictionary mapping table names to file paths
        """
        # Create versioned subdirectory
        version_dir = os.path.join(output_dir, self.data_version)
        os.makedirs(version_dir, exist_ok=True)
        
        file_paths = {}
        
        # 1. Entity tables
        self.brands.to_csv(os.path.join(version_dir, "brands.csv"), index=False)
        file_paths["brands"] = os.path.join(version_dir, "brands.csv")
        
        self.regions.to_csv(os.path.join(version_dir, "regions.csv"), index=False)
        file_paths["regions"] = os.path.join(version_dir, "regions.csv")
        
        self.channels.to_csv(os.path.join(version_dir, "channels.csv"), index=False)
        file_paths["channels"] = os.path.join(version_dir, "channels.csv")
        
        # 2. Environment schedules
        price_schedule = self.generate_price_schedule()
        price_schedule.to_csv(os.path.join(version_dir, "brand_price_schedule.csv"), index=False)
        file_paths["brand_price_schedule"] = os.path.join(version_dir, "brand_price_schedule.csv")
        
        promo_schedule = self.generate_promo_schedule()
        promo_schedule.to_csv(os.path.join(version_dir, "brand_promo_schedule.csv"), index=False)
        file_paths["brand_promo_schedule"] = os.path.join(version_dir, "brand_promo_schedule.csv")
        
        availability = self.generate_menu_availability()
        availability.to_csv(os.path.join(version_dir, "brand_menu_availability.csv"), index=False)
        file_paths["brand_menu_availability"] = os.path.join(version_dir, "brand_menu_availability.csv")
        
        # 3. Survey data
        survey_responses = self.generate_survey_responses()
        survey_responses.to_csv(os.path.join(version_dir, "survey_responses.csv"), index=False)
        file_paths["survey_responses"] = os.path.join(version_dir, "survey_responses.csv")
        
        taste_ratings = self.generate_taste_ratings()
        taste_ratings.to_csv(os.path.join(version_dir, "taste_ratings.csv"), index=False)
        file_paths["taste_ratings"] = os.path.join(version_dir, "taste_ratings.csv")
        
        choice_experiments = self.generate_choice_experiments()
        choice_experiments.to_csv(os.path.join(version_dir, "choice_experiments.csv"), index=False)
        file_paths["choice_experiments"] = os.path.join(version_dir, "choice_experiments.csv")
        
        # 4. Observed aggregates
        observed_metrics = self.generate_observed_metrics()
        observed_metrics.to_csv(os.path.join(version_dir, "observed_metrics_brand_week_region.csv"), index=False)
        file_paths["observed_metrics_brand_week_region"] = os.path.join(version_dir, "observed_metrics_brand_week_region.csv")
        
        return file_paths

