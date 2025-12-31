"""
PART A: Synthetic Revenue Dataset Generator
Creates realistic weekly revenue data (2022-2024) with ground truth latents
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json


class SyntheticRevenueGenerator:
    """
    Generates synthetic but realistic revenue data from latent preferences
    """
    
    def __init__(self, 
                 brands: List[str] = None,
                 regions: List[str] = None,
                 start_date: str = '2022-01-03',  # First Monday of 2022
                 end_date: str = '2024-12-30',
                 seed: int = 42):
        """
        Args:
            brands: List of brand names (default: fast food brands)
            regions: List of regions (default: US regions)
            start_date: Start date (should be a Monday)
            end_date: End date
            seed: Random seed
        """
        np.random.seed(seed)
        
        self.brands = brands or [
            'McDonalds', 'BurgerKing', 'Wendys', 'TacoBell', 
            'Subway', 'KFC', 'Dominos', 'PizzaHut'
        ]
        self.regions = regions or ['Northeast', 'South', 'Midwest', 'West', 'Southwest']
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate weekly dates (Mondays)
        self.weekly_dates = self._generate_weekly_dates()
        
        # Ground truth latent parameters (hidden from models)
        self.latent_params = self._initialize_latent_params()
    
    def _generate_weekly_dates(self) -> List[datetime]:
        """Generate list of weekly dates (Mondays)"""
        dates = []
        current = self.start_date
        while current <= self.end_date:
            dates.append(current)
            current += timedelta(days=7)
        return dates
    
    def _initialize_latent_params(self) -> Dict:
        """Initialize ground truth latent preference parameters"""
        n_brands = len(self.brands)
        n_regions = len(self.regions)
        n_weeks = len(self.weekly_dates)
        
        # Base preference levels per brand-region (0-1 scale)
        base_preferences = np.random.beta(2, 2, size=(n_brands, n_regions))
        
        # Preference drift over time (slow random walk)
        preference_drift = np.zeros((n_weeks, n_brands, n_regions))
        for t in range(1, n_weeks):
            drift = np.random.normal(0, 0.01, size=(n_brands, n_regions))
            preference_drift[t] = preference_drift[t-1] + drift
        
        # Brand-level seasonality (some brands peak in summer, others in winter)
        seasonality_strength = np.random.uniform(0.05, 0.15, size=n_brands)
        seasonality_phase = np.random.uniform(0, 2*np.pi, size=n_brands)
        
        # Price elasticity per brand-region (negative, typically -0.5 to -2.0)
        price_elasticity = np.random.uniform(-2.0, -0.5, size=(n_brands, n_regions))
        
        # Market share targets (should sum to ~1 per region)
        market_shares = np.random.dirichlet([2] * n_brands, size=n_regions).T
        
        # Brand switching propensity (how often consumers switch brands)
        switching_rate = np.random.beta(2, 5, size=(n_brands, n_regions))
        
        return {
            'base_preferences': base_preferences,
            'preference_drift': preference_drift,
            'seasonality_strength': seasonality_strength,
            'seasonality_phase': seasonality_phase,
            'price_elasticity': price_elasticity,
            'market_shares': market_shares,
            'switching_rate': switching_rate,
            'base_revenue_per_preference': np.random.uniform(50000, 200000, size=(n_brands, n_regions))
        }
    
    def _compute_preference(self, brand_idx: int, region_idx: int, week_idx: int) -> float:
        """Compute latent preference at given time"""
        base = self.latent_params['base_preferences'][brand_idx, region_idx]
        drift = self.latent_params['preference_drift'][week_idx, brand_idx, region_idx]
        
        # Add seasonality
        week_of_year = self.weekly_dates[week_idx].timetuple().tm_yday / 365.0 * 2 * np.pi
        seasonality = self.latent_params['seasonality_strength'][brand_idx] * \
                     np.sin(week_of_year + self.latent_params['seasonality_phase'][brand_idx])
        
        preference = base + drift + seasonality
        return np.clip(preference, 0.01, 0.99)  # Keep in valid range
    
    def _apply_price_shock(self, brand_idx: int, region_idx: int, week_idx: int, 
                          base_price: float) -> float:
        """Apply price changes (shocks)"""
        # Occasional price changes (5% chance per week)
        if np.random.random() < 0.05:
            change_pct = np.random.normal(0, 0.1)  # ±10% change
            return base_price * (1 + change_pct)
        return base_price
    
    def _apply_promotion_shock(self, brand_idx: int, week_idx: int) -> float:
        """Apply promotion effects (temporary boosts)"""
        # 10% chance of promotion per week
        if np.random.random() < 0.10:
            return np.random.uniform(1.1, 1.3)  # 10-30% boost
        return 1.0
    
    def _apply_holiday_effect(self, week_idx: int) -> float:
        """Apply holiday effects (Thanksgiving, Christmas, etc.)"""
        date = self.weekly_dates[week_idx]
        month = date.month
        day = date.day
        
        # Thanksgiving week (late November)
        if month == 11 and day >= 20:
            return 1.2
        
        # Christmas/New Year (late Dec - early Jan)
        if (month == 12 and day >= 20) or (month == 1 and day <= 7):
            return 1.15
        
        # Summer peak (June-August)
        if month in [6, 7, 8]:
            return 1.05
        
        return 1.0
    
    def generate_revenue(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate revenue dataset and ground truth latents
        
        Returns:
            revenue_df: DataFrame with columns [date, brand, region, revenue, price, promotion]
            latents_df: DataFrame with ground truth latent variables
        """
        revenue_records = []
        latents_records = []
        
        # Base prices per brand (will vary by region slightly)
        base_prices = np.random.uniform(8.0, 15.0, size=len(self.brands))
        
        for week_idx, date in enumerate(self.weekly_dates):
            for brand_idx, brand in enumerate(self.brands):
                for region_idx, region in enumerate(self.regions):
                    # Compute latent preference
                    preference = self._compute_preference(brand_idx, region_idx, week_idx)
                    
                    # Base revenue (proportional to preference)
                    base_revenue = self.latent_params['base_revenue_per_preference'][brand_idx, region_idx] * preference
                    
                    # Apply price effects
                    price = self._apply_price_shock(brand_idx, region_idx, week_idx, base_prices[brand_idx])
                    price_multiplier = (price / base_prices[brand_idx]) ** self.latent_params['price_elasticity'][brand_idx, region_idx]
                    
                    # Apply promotions
                    promotion_multiplier = self._apply_promotion_shock(brand_idx, week_idx)
                    
                    # Apply holiday effects
                    holiday_multiplier = self._apply_holiday_effect(week_idx)
                    
                    # Add noise (multiplicative log-normal)
                    noise = np.random.lognormal(0, 0.1)
                    
                    # Final revenue
                    revenue = base_revenue * price_multiplier * promotion_multiplier * holiday_multiplier * noise
                    
                    # Ensure non-negative
                    revenue = max(0, revenue)
                    
                    # Record revenue
                    revenue_records.append({
                        'date': date,
                        'week': week_idx,
                        'brand': brand,
                        'region': region,
                        'revenue': revenue,
                        'price': price,
                        'promotion': promotion_multiplier > 1.0,
                        'holiday': holiday_multiplier > 1.0
                    })
                    
                    # Record latents (for evaluation only, not training)
                    latents_records.append({
                        'date': date,
                        'week': week_idx,
                        'brand': brand,
                        'region': region,
                        'latent_preference': preference,
                        'preference_drift': self.latent_params['preference_drift'][week_idx, brand_idx, region_idx],
                        'market_share_target': self.latent_params['market_shares'][brand_idx, region_idx],
                        'switching_rate': self.latent_params['switching_rate'][brand_idx, region_idx],
                        'price_elasticity': self.latent_params['price_elasticity'][brand_idx, region_idx]
                    })
        
        revenue_df = pd.DataFrame(revenue_records)
        latents_df = pd.DataFrame(latents_records)
        
        return revenue_df, latents_df
    
    def save(self, revenue_df: pd.DataFrame, latents_df: pd.DataFrame, output_dir: str):
        """Save datasets to CSV"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        revenue_path = os.path.join(output_dir, 'revenue.csv')
        latents_path = os.path.join(output_dir, 'ground_truth_latents.csv')
        
        revenue_df.to_csv(revenue_path, index=False)
        latents_df.to_csv(latents_path, index=False)
        
        print(f"Saved revenue data to {revenue_path}")
        print(f"Saved ground truth latents to {latents_path}")
        print(f"Revenue shape: {revenue_df.shape}")
        print(f"Latents shape: {latents_df.shape}")


if __name__ == '__main__':
    generator = SyntheticRevenueGenerator()
    revenue_df, latents_df = generator.generate_revenue()
    
    # Save to data directory
    generator.save(revenue_df, latents_df, 'data')
    
    # Print summary
    print("\n=== Revenue Summary ===")
    print(f"Date range: {revenue_df['date'].min()} to {revenue_df['date'].max()}")
    print(f"Total weeks: {revenue_df['week'].nunique()}")
    print(f"Brands: {revenue_df['brand'].nunique()}")
    print(f"Regions: {revenue_df['region'].nunique()}")
    print(f"\nRevenue statistics:")
    print(revenue_df.groupby('brand')['revenue'].agg(['mean', 'std', 'sum']))
    print(f"\nTotal revenue: ${revenue_df['revenue'].sum():,.2f}")

