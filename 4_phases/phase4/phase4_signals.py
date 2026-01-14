"""
Phase 4: Signal Generation for Hedge Funds
Generates alpha-ready demand signals from intent data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os

class SignalGenerator:
    """
    Generates hedge-fund-usable signals from intent data
    """
    
    def __init__(self, intent_data: pd.DataFrame):
        """
        Args:
            intent_data: DataFrame with intent trajectories (from Phase 3 or real data)
        """
        self.data = intent_data.copy()
        
        # Ensure timestamp column
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            self.data['date'] = self.data['timestamp'].dt.date
    
    def compute_intent_index(self, 
                            groupby_col: str = 'product_category',
                            time_col: str = 'date') -> pd.DataFrame:
        """
        Compute intent index: I_c(t) = E[ŷ_t | category = c]
        Args:
            groupby_col: Column to group by (category, brand, product_id, etc.)
            time_col: Time column for aggregation
        Returns:
            DataFrame with intent index over time
        """
        if time_col not in self.data.columns:
            # Create date column if needed
            if 'timestamp' in self.data.columns:
                self.data['date'] = pd.to_datetime(self.data['timestamp']).dt.date
                time_col = 'date'
            else:
                raise ValueError("No time column found")
        
        # Aggregate intent by group and time
        intent_index = self.data.groupby([time_col, groupby_col])['intent_value'].agg([
            'mean', 'std', 'count'
        ]).reset_index()
        
        intent_index.columns = [time_col, groupby_col, 'intent_mean', 'intent_std', 'intent_count']
        
        return intent_index
    
    def compute_category_momentum_index(self, 
                                       window_days: int = 7,
                                       category: Optional[str] = None) -> pd.DataFrame:
        """
        Category Momentum Index: Δ in I_c(t) over window_days
        Args:
            window_days: Time window for momentum calculation
            category: Optional specific category, otherwise computes for all
        Returns:
            DataFrame with momentum index
        """
        # Compute intent index
        intent_index = self.compute_intent_index(groupby_col='product_category')
        
        if category:
            intent_index = intent_index[intent_index['product_category'] == category]
        
        # Sort by date
        intent_index = intent_index.sort_values('date')
        
        # Compute momentum (change over window)
        momentum_data = []
        for cat in intent_index['product_category'].unique():
            cat_data = intent_index[intent_index['product_category'] == cat].sort_values('date')
            
            for i in range(len(cat_data)):
                current_date = cat_data.iloc[i]['date']
                current_intent = cat_data.iloc[i]['intent_mean']
                
                # Find data window_days ago
                window_start = current_date - timedelta(days=window_days)
                window_data = cat_data[cat_data['date'] <= window_start]
                
                if len(window_data) > 0:
                    past_intent = window_data.iloc[-1]['intent_mean']
                    momentum = current_intent - past_intent
                    momentum_pct = (momentum / past_intent * 100) if past_intent > 0 else 0
                else:
                    momentum = 0
                    momentum_pct = 0
                
                momentum_data.append({
                    'date': current_date,
                    'product_category': cat,
                    'intent_index': current_intent,
                    'momentum': momentum,
                    'momentum_pct': momentum_pct,
                    'window_days': window_days
                })
        
        return pd.DataFrame(momentum_data)
    
    def compute_trend_acceleration_index(self, 
                                        category: Optional[str] = None,
                                        trend_type: str = 'zero_sugar') -> pd.DataFrame:
        """
        Trend Acceleration Index: second derivative / slope of intent for trends
        Args:
            category: Optional specific category
            trend_type: Type of trend to track (e.g., 'zero_sugar', 'probiotic', 'energy')
        Returns:
            DataFrame with trend acceleration
        """
        # Filter by trend type if specified (would need product metadata)
        # For now, compute for all categories or specified category
        
        intent_index = self.compute_intent_index(groupby_col='product_category')
        
        if category:
            intent_index = intent_index[intent_index['product_category'] == category]
        
        intent_index = intent_index.sort_values('date')
        
        acceleration_data = []
        for cat in intent_index['product_category'].unique():
            cat_data = intent_index[intent_index['product_category'] == cat].sort_values('date')
            
            if len(cat_data) < 3:
                continue
            
            # Compute first derivative (slope/velocity)
            dates = pd.to_datetime(cat_data['date'])
            intents = cat_data['intent_mean'].values
            
            # Use rolling window for smoother derivatives
            window = min(5, len(cat_data))
            velocities = []
            accelerations = []
            
            for i in range(len(cat_data)):
                start_idx = max(0, i - window // 2)
                end_idx = min(len(cat_data), i + window // 2 + 1)
                
                window_dates = dates.iloc[start_idx:end_idx]
                window_intents = intents[start_idx:end_idx]
                
                if len(window_dates) > 1:
                    # First derivative (velocity)
                    x = np.arange(len(window_dates))
                    y = window_intents
                    velocity = np.polyfit(x, y, 1)[0] if len(x) > 1 else 0
                    velocities.append(velocity)
                else:
                    velocities.append(0)
            
            # Second derivative (acceleration) from velocities
            for i in range(1, len(velocities)):
                acceleration = velocities[i] - velocities[i-1]
                accelerations.append(acceleration)
            
            # Pad first value
            if accelerations:
                accelerations.insert(0, accelerations[0])
            
            for i, row in cat_data.iterrows():
                acceleration_data.append({
                    'date': row['date'],
                    'product_category': cat,
                    'intent_index': row['intent_mean'],
                    'velocity': velocities[i] if i < len(velocities) else 0,
                    'acceleration': accelerations[i] if i < len(accelerations) else 0
                })
        
        return pd.DataFrame(acceleration_data)
    
    def compute_demand_forecast(self,
                               forecast_horizon_days: int = 30,
                               category: Optional[str] = None) -> pd.DataFrame:
        """
        Brand / SKU Demand Forecasts: forecasted adoption over next 30-90 days
        Args:
            forecast_horizon_days: Days ahead to forecast
            category: Optional specific category
        Returns:
            DataFrame with forecasts
        """
        intent_index = self.compute_intent_index(groupby_col='product_category')
        
        if category:
            intent_index = intent_index[intent_index['product_category'] == category]
        
        intent_index = intent_index.sort_values('date')
        
        forecasts = []
        for cat in intent_index['product_category'].unique():
            cat_data = intent_index[intent_index['product_category'] == cat].sort_values('date')
            
            if len(cat_data) < 3:
                continue
            
            # Use last N days for trend estimation
            lookback_days = min(14, len(cat_data))
            recent_data = cat_data.tail(lookback_days)
            
            # Fit trend
            dates = pd.to_datetime(recent_data['date'])
            intents = recent_data['intent_mean'].values
            x = np.arange(len(dates))
            
            # Linear trend
            coeffs = np.polyfit(x, intents, 1)
            trend_slope = coeffs[0]
            intercept = coeffs[1]
            
            # Forecast
            last_date = dates.iloc[-1]
            forecast_date = last_date + timedelta(days=forecast_horizon_days)
            
            # Extrapolate
            forecast_intent = intercept + trend_slope * (len(x) + forecast_horizon_days)
            
            forecasts.append({
                'product_category': cat,
                'current_date': last_date.date(),
                'forecast_date': forecast_date.date(),
                'current_intent': intents[-1],
                'forecast_intent': max(0, forecast_intent),  # Ensure non-negative
                'forecast_change': forecast_intent - intents[-1],
                'forecast_change_pct': ((forecast_intent - intents[-1]) / intents[-1] * 100) if intents[-1] > 0 else 0,
                'trend_slope': trend_slope,
                'forecast_horizon_days': forecast_horizon_days
            })
        
        return pd.DataFrame(forecasts)
    
    def compute_substitution_matrix(self, 
                                    time_window_days: int = 7) -> pd.DataFrame:
        """
        Substitution Matrix: predicted share shifts between brands/categories
        Args:
            time_window_days: Time window for computing shifts
        Returns:
            DataFrame with substitution probabilities
        """
        # Get unique categories
        categories = self.data['product_category'].unique()
        
        # Compute market share over time
        intent_index = self.compute_intent_index(groupby_col='product_category')
        intent_index = intent_index.sort_values('date')
        
        # Normalize to shares (intent as proxy for share)
        substitution_data = []
        
        for date in intent_index['date'].unique():
            date_data = intent_index[intent_index['date'] == date]
            total_intent = date_data['intent_mean'].sum()
            
            if total_intent > 0:
                shares = date_data['intent_mean'] / total_intent
                
                for _, row in date_data.iterrows():
                    substitution_data.append({
                        'date': date,
                        'product_category': row['product_category'],
                        'market_share': shares[row.name] if row.name in shares.index else 0
                    })
        
        shares_df = pd.DataFrame(substitution_data)
        
        # Compute share changes (substitution)
        # Align shares by date first
        shares_pivot = shares_df.pivot(index='date', columns='product_category', values='market_share').fillna(0)
        
        substitution_matrix = []
        for cat_from in categories:
            for cat_to in categories:
                if cat_from == cat_to:
                    continue
                
                if cat_from not in shares_pivot.columns or cat_to not in shares_pivot.columns:
                    continue
                
                cat_from_shares = shares_pivot[cat_from].values
                cat_to_shares = shares_pivot[cat_to].values
                
                if len(cat_from_shares) > 1 and len(cat_to_shares) > 1 and len(cat_from_shares) == len(cat_to_shares):
                    # Correlation suggests substitution
                    if np.std(cat_from_shares) > 0 and np.std(cat_to_shares) > 0:
                        correlation = np.corrcoef(cat_from_shares, cat_to_shares)[0, 1]
                        
                        # Negative correlation suggests substitution
                        substitution_score = -correlation if not np.isnan(correlation) else 0
                    else:
                        correlation = 0
                        substitution_score = 0
                    
                    substitution_matrix.append({
                        'from_category': cat_from,
                        'to_category': cat_to,
                        'substitution_score': substitution_score,
                        'correlation': correlation
                    })
        
        return pd.DataFrame(substitution_matrix)
    
    def compute_price_elasticity(self,
                                price_change_pct: float = 0.1,
                                category: Optional[str] = None) -> pd.DataFrame:
        """
        Price Elasticity / Scenario Outputs: how I_c(t) changes under ±price simulations
        Args:
            price_change_pct: Percentage price change to simulate (e.g., 0.1 for 10%)
            category: Optional specific category
        Returns:
            DataFrame with price elasticity estimates
        """
        # Get current intent index
        intent_index = self.compute_intent_index(groupby_col='product_category')
        
        if category:
            intent_index = intent_index[intent_index['product_category'] == category]
        
        # For price elasticity, we need product-level data with prices
        # Since we don't have price in intent data, we'll estimate based on category patterns
        # In real implementation, this would use product prices from product catalog
        
        elasticity_data = []
        
        # Estimate elasticity based on intent sensitivity to context price
        if 'context_id' in self.data.columns:
            # Group by category and compute average intent
            category_intent = self.data.groupby('product_category')['intent_value'].mean()
            
            # Estimate: categories with lower average intent might be more price-sensitive
            # (This is a simplified heuristic - real implementation would use actual price data)
            
            for cat in category_intent.index:
                base_intent = category_intent[cat]
                
                # Simulate price increase effect (negative relationship)
                # Higher price -> lower intent (negative elasticity)
                estimated_elasticity = -0.5  # Base assumption: -0.5 elasticity
                
                # Adjust based on category characteristics
                if 'water' in cat.lower() or 'enhanced' in cat.lower():
                    # More price-sensitive
                    estimated_elasticity = -0.8
                elif 'premium' in cat.lower() or 'energy' in cat.lower():
                    # Less price-sensitive
                    estimated_elasticity = -0.3
                
                # Compute expected change
                price_change = price_change_pct
                expected_intent_change = base_intent * estimated_elasticity * price_change
                expected_new_intent = base_intent + expected_intent_change
                
                elasticity_data.append({
                    'product_category': cat,
                    'base_intent': base_intent,
                    'price_change_pct': price_change_pct * 100,
                    'estimated_elasticity': estimated_elasticity,
                    'expected_intent_change': expected_intent_change,
                    'expected_new_intent': max(0, expected_new_intent),
                    'intent_change_pct': (expected_intent_change / base_intent * 100) if base_intent > 0 else 0
                })
        
        return pd.DataFrame(elasticity_data)
    
    def generate_all_signals(self, output_dir: str = 'signals') -> Dict[str, pd.DataFrame]:
        """Generate all signals and save to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        signals = {}
        
        print("Generating signals...")
        
        # 1. Intent Index
        print("  Computing intent index...")
        intent_index = self.compute_intent_index()
        signals['intent_index'] = intent_index
        intent_index.to_csv(os.path.join(output_dir, 'intent_index.csv'), index=False)
        
        # 2. Category Momentum Index (7d and 30d)
        print("  Computing momentum indices...")
        momentum_7d = self.compute_category_momentum_index(window_days=7)
        momentum_30d = self.compute_category_momentum_index(window_days=30)
        signals['momentum_7d'] = momentum_7d
        signals['momentum_30d'] = momentum_30d
        momentum_7d.to_csv(os.path.join(output_dir, 'momentum_7d.csv'), index=False)
        momentum_30d.to_csv(os.path.join(output_dir, 'momentum_30d.csv'), index=False)
        
        # 3. Trend Acceleration Index
        print("  Computing trend acceleration...")
        acceleration = self.compute_trend_acceleration_index()
        signals['trend_acceleration'] = acceleration
        acceleration.to_csv(os.path.join(output_dir, 'trend_acceleration.csv'), index=False)
        
        # 4. Demand Forecasts (30d and 90d)
        print("  Computing demand forecasts...")
        forecast_30d = self.compute_demand_forecast(forecast_horizon_days=30)
        forecast_90d = self.compute_demand_forecast(forecast_horizon_days=90)
        signals['forecast_30d'] = forecast_30d
        signals['forecast_90d'] = forecast_90d
        forecast_30d.to_csv(os.path.join(output_dir, 'forecast_30d.csv'), index=False)
        forecast_90d.to_csv(os.path.join(output_dir, 'forecast_90d.csv'), index=False)
        
        # 5. Substitution Matrix
        print("  Computing substitution matrix...")
        substitution = self.compute_substitution_matrix()
        signals['substitution_matrix'] = substitution
        substitution.to_csv(os.path.join(output_dir, 'substitution_matrix.csv'), index=False)
        
        # 6. Price Elasticity
        print("  Computing price elasticity...")
        price_elasticity = self.compute_price_elasticity(price_change_pct=0.1)
        signals['price_elasticity'] = price_elasticity
        price_elasticity.to_csv(os.path.join(output_dir, 'price_elasticity.csv'), index=False)
        
        # Generate summary JSON
        summary = {
            'signals_generated': list(signals.keys()),
            'date_range': {
                'start': str(intent_index['date'].min()),
                'end': str(intent_index['date'].max())
            },
            'categories': sorted(intent_index['product_category'].unique().tolist()),
            'total_data_points': len(intent_index)
        }
        
        with open(os.path.join(output_dir, 'signals_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nAll signals saved to {output_dir}/")
        
        return signals

