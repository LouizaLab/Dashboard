"""
Model M1: Phase 3 Unanchored LPM Forecast Model
Uses aggregated outputs from Phase 3 population simulation
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
import warnings
warnings.filterwarnings('ignore')


class Phase3UnanchoredModel:
    """
    Forecasts revenue from Phase 3 (unanchored) LPM outputs
    No anchoring constraints applied
    """
    
    def __init__(self, 
                 intent_data: pd.DataFrame,
                 confidence_levels: Tuple[float, float] = (0.80, 0.95)):
        """
        Args:
            intent_data: Phase 3 simulation outputs (intent trajectories)
            confidence_levels: Tuple of (lower, upper) confidence levels
        """
        self.intent_data = intent_data.copy()
        self.confidence_levels = confidence_levels
        self.models = {}  # One model per brand-region
        self.fitted = False
        
        # Map product categories to brands (simplified mapping)
        self.category_to_brand = self._create_category_mapping()
    
    def _create_category_mapping(self) -> Dict[str, str]:
        """Map product categories to brands (simplified)"""
        # This is a placeholder - in practice would use actual product data
        categories = self.intent_data['product_category'].unique() if 'product_category' in self.intent_data.columns else []
        brands = ['McDonalds', 'BurgerKing', 'Wendys', 'TacoBell', 
                 'Subway', 'KFC', 'Dominos', 'PizzaHut']
        
        # Simple round-robin mapping
        mapping = {}
        for i, cat in enumerate(categories):
            mapping[cat] = brands[i % len(brands)]
        return mapping
    
    def _aggregate_intent_signals(self, intent_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate Phase 3 intent outputs into weekly signals
        
        Returns:
            DataFrame with weekly aggregated signals per brand-region
        """
        df = intent_df.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Map categories to brands
        if 'product_category' in df.columns:
            df['brand'] = df['product_category'].map(self.category_to_brand)
        else:
            df['brand'] = 'Unknown'
        
        # Infer region from segment if available
        if 'segment_id' in df.columns:
            # Simple mapping: use segment_id hash to assign regions
            regions = ['Northeast', 'South', 'Midwest', 'West', 'Southwest']
            df['region'] = df['segment_id'].apply(lambda x: regions[hash(str(x)) % len(regions)])
        else:
            df['region'] = 'Unknown'
        
        # Aggregate to weekly level
        weekly_signals = []
        
        for (brand, region), group in df.groupby(['brand', 'region']):
            # Group by week
            group['week_start'] = pd.to_datetime(group['date']) - pd.to_timedelta(
                pd.to_datetime(group['date']).dt.dayofweek, unit='d'
            )
            
            weekly = group.groupby('week_start').agg({
                'intent_value': ['mean', 'std', 'count'],
                'product_id': 'nunique',
                'agent_id': 'nunique'
            }).reset_index()
            
            weekly.columns = ['date', 'intent_mean', 'intent_std', 'intent_count', 
                            'n_products', 'n_agents']
            
            # Compute additional signals
            weekly['intent_momentum_7d'] = weekly['intent_mean'].diff(1)
            weekly['intent_momentum_30d'] = weekly['intent_mean'].diff(4)
            weekly['intent_volatility'] = weekly['intent_mean'].rolling(4).std()
            
            # Switching rate (how often agents change products)
            if 'product_id' in group.columns and 'agent_id' in group.columns:
                agent_switches = []
                for agent_id, agent_group in group.groupby('agent_id'):
                    products = agent_group.sort_values('date')['product_id'].tolist()
                    switches = sum(1 for i in range(1, len(products)) if products[i] != products[i-1])
                    if len(products) > 1:
                        agent_switches.append(switches / (len(products) - 1))
                weekly['switching_rate'] = np.mean(agent_switches) if agent_switches else 0.0
            else:
                weekly['switching_rate'] = 0.0
            
            weekly['brand'] = brand
            weekly['region'] = region
            
            weekly_signals.append(weekly)
        
        if not weekly_signals:
            return pd.DataFrame()
        
        return pd.concat(weekly_signals, ignore_index=True)
    
    def fit(self, revenue_df: pd.DataFrame):
        """
        Fit regression models mapping Phase 3 signals → revenue
        
        Args:
            revenue_df: Historical revenue data (2022-2023 for training)
        """
        # Aggregate intent signals
        intent_signals = self._aggregate_intent_signals(self.intent_data)
        
        if len(intent_signals) == 0:
            print("Warning: No intent signals generated. Using fallback model.")
            self.fitted = True
            return
        
        # Merge with revenue
        revenue_df['date'] = pd.to_datetime(revenue_df['date'])
        intent_signals['date'] = pd.to_datetime(intent_signals['date'])
        
        # Filter to training period
        train_revenue = revenue_df[revenue_df['date'] < '2024-01-01'].copy()
        
        # Fit models per brand-region
        for (brand, region), revenue_group in train_revenue.groupby(['brand', 'region']):
            # Get corresponding intent signals
            intent_group = intent_signals[
                (intent_signals['brand'] == brand) & 
                (intent_signals['region'] == region)
            ].copy()
            
            if len(intent_group) < 10:  # Need minimum data
                continue
            
            # Merge on date (nearest match)
            merged = pd.merge_asof(
                revenue_group.sort_values('date'),
                intent_group.sort_values('date'),
                on='date',
                direction='nearest',
                tolerance=pd.Timedelta(days=7)
            )
            
            if len(merged) < 10:
                continue
            
            # Prepare features
            feature_cols = ['intent_mean', 'intent_std', 'intent_momentum_7d', 
                          'intent_momentum_30d', 'intent_volatility', 'switching_rate',
                          'n_products', 'n_agents']
            feature_cols = [col for col in feature_cols if col in merged.columns]
            
            X = merged[feature_cols].fillna(0)
            y = merged['revenue']
            
            # Remove infinite values
            mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
            X = X[mask]
            y = y[mask]
            
            if len(X) < 5:
                continue
            
            # Fit Bayesian Ridge for uncertainty quantification
            model = BayesianRidge(compute_score=True)
            model.fit(X, y)
            
            self.models[(brand, region)] = {
                'model': model,
                'feature_cols': feature_cols,
                'mean_revenue': y.mean(),
                'std_revenue': y.std()
            }
        
        self.fitted = True
        print(f"Fitted {len(self.models)} Phase 3 models")
    
    def predict(self, revenue_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate predictions from Phase 3 signals
        
        Returns:
            DataFrame with predictions and uncertainty intervals
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        # Aggregate intent signals
        intent_signals = self._aggregate_intent_signals(self.intent_data)
        
        if len(intent_signals) == 0:
            # Fallback: use mean
            predictions = []
            for (brand, region), group in revenue_df.groupby(['brand', 'region']):
                mean_rev = group['revenue'].mean()
                std_rev = group['revenue'].std()
                for _, row in group.iterrows():
                    predictions.append({
                        'date': row['date'],
                        'brand': brand,
                        'region': region,
                        'revenue_pred': mean_rev,
                        'revenue_lower_80': mean_rev - 1.28 * std_rev,
                        'revenue_upper_80': mean_rev + 1.28 * std_rev,
                        'revenue_lower_95': mean_rev - 1.96 * std_rev,
                        'revenue_upper_95': mean_rev + 1.96 * std_rev
                    })
            return pd.DataFrame(predictions)
        
        intent_signals['date'] = pd.to_datetime(intent_signals['date'])
        revenue_df['date'] = pd.to_datetime(revenue_df['date'])
        
        predictions = []
        
        # Filter to prediction period
        pred_revenue = revenue_df[revenue_df['date'] >= '2024-01-01'].copy()
        
        for (brand, region), revenue_group in pred_revenue.groupby(['brand', 'region']):
            if (brand, region) not in self.models:
                # Use mean if no model
                mean_rev = revenue_group['revenue'].mean() if len(revenue_group) > 0 else 0
                std_rev = revenue_group['revenue'].std() if len(revenue_group) > 0 else 1000
                for _, row in revenue_group.iterrows():
                    predictions.append({
                        'date': row['date'],
                        'brand': brand,
                        'region': region,
                        'revenue_pred': mean_rev,
                        'revenue_lower_80': mean_rev - 1.28 * std_rev,
                        'revenue_upper_80': mean_rev + 1.28 * std_rev,
                        'revenue_lower_95': mean_rev - 1.96 * std_rev,
                        'revenue_upper_95': mean_rev + 1.96 * std_rev
                    })
                continue
            
            model_info = self.models[(brand, region)]
            model = model_info['model']
            feature_cols = model_info['feature_cols']
            
            # Get intent signals
            intent_group = intent_signals[
                (intent_signals['brand'] == brand) & 
                (intent_signals['region'] == region)
            ].copy()
            
            for _, row in revenue_group.iterrows():
                date = row['date']
                
                # Find nearest intent signal
                intent_match = intent_group.iloc[
                    (intent_group['date'] - date).abs().argsort()[:1]
                ]
                
                if len(intent_match) == 0:
                    # Use mean
                    pred_mean = model_info['mean_revenue']
                    pred_std = model_info['std_revenue']
                else:
                    # Prepare features
                    X = intent_match[feature_cols].fillna(0)
                    
                    # Predict
                    pred_mean, pred_std = model.predict(X, return_std=True)
                    # Handle both numpy array and pandas Series
                    if hasattr(pred_mean, 'iloc'):
                        pred_mean = pred_mean.iloc[0]
                    else:
                        pred_mean = float(pred_mean[0] if len(pred_mean) > 0 else pred_mean)
                    if hasattr(pred_std, 'iloc'):
                        pred_std = pred_std.iloc[0]
                    else:
                        pred_std = float(pred_std[0] if len(pred_std) > 0 else pred_std)
                
                # Generate intervals
                predictions.append({
                    'date': date,
                    'brand': brand,
                    'region': region,
                    'revenue_pred': pred_mean,
                    'revenue_lower_80': pred_mean - 1.28 * pred_std,
                    'revenue_upper_80': pred_mean + 1.28 * pred_std,
                    'revenue_lower_95': pred_mean - 1.96 * pred_std,
                    'revenue_upper_95': pred_mean + 1.96 * pred_std
                })
        
        return pd.DataFrame(predictions)

