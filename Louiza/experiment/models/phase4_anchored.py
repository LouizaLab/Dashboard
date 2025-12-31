"""
Model M2: Phase 4 Anchored Preference Model
Uses Phase 3 outputs + anchoring constraints to reduce entropy
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
import warnings
warnings.filterwarnings('ignore')


class Phase4AnchoredModel:
    """
    Forecasts revenue from Phase 4 (anchored) LPM outputs
    Applies anchoring constraints to reduce entropy
    """
    
    def __init__(self,
                 intent_data: pd.DataFrame,
                 anchoring_constraints: Optional[Dict] = None,
                 confidence_levels: Tuple[float, float] = (0.80, 0.95)):
        """
        Args:
            intent_data: Phase 4 anchored simulation outputs
            anchoring_constraints: Dict with constraints:
                - market_share_ranges: Dict[brand] -> (min, max) share
                - preference_stability_prior: float (how much to penalize large changes)
                - elasticity_bounds: Dict[brand] -> (min, max) elasticity
                - demographic_mix: Dict[region] -> Dict[brand] -> share
            confidence_levels: Tuple of (lower, upper) confidence levels
        """
        self.intent_data = intent_data.copy()
        self.confidence_levels = confidence_levels
        self.models = {}
        self.fitted = False
        
        # Default anchoring constraints
        self.anchoring_constraints = anchoring_constraints or {
            'market_share_ranges': {},  # Will be inferred from data
            'preference_stability_prior': 0.7,  # Higher = more stable
            'elasticity_bounds': {},
            'demographic_mix': {}
        }
        
        # Map categories to brands
        self.category_to_brand = self._create_category_mapping()
    
    def _create_category_mapping(self) -> Dict[str, str]:
        """Map product categories to brands"""
        categories = self.intent_data['product_category'].unique() if 'product_category' in self.intent_data.columns else []
        brands = ['McDonalds', 'BurgerKing', 'Wendys', 'TacoBell', 
                 'Subway', 'KFC', 'Dominos', 'PizzaHut']
        
        mapping = {}
        for i, cat in enumerate(categories):
            mapping[cat] = brands[i % len(brands)]
        return mapping
    
    def _apply_anchoring(self, intent_signals: pd.DataFrame, 
                        historical_revenue: pd.DataFrame) -> pd.DataFrame:
        """
        Apply anchoring constraints to intent signals
        
        This is the key difference from Phase 3:
        - Reweights signals based on market share constraints
        - Smooths preference trajectories (stability prior)
        - Applies demographic mix constraints
        """
        anchored = intent_signals.copy()
        
        # 1. Market share reweighting
        if 'market_share_ranges' in self.anchoring_constraints:
            anchored = self._reweight_by_market_share(anchored, historical_revenue)
        
        # 2. Preference stability smoothing
        stability_prior = self.anchoring_constraints.get('preference_stability_prior', 0.7)
        anchored['intent_mean'] = self._smooth_preferences(
            anchored['intent_mean'], 
            alpha=stability_prior
        )
        
        # 3. Demographic mix constraints
        if 'demographic_mix' in self.anchoring_constraints:
            anchored = self._apply_demographic_mix(anchored)
        
        # 4. Elasticity bounds (if provided)
        if 'elasticity_bounds' in self.anchoring_constraints:
            anchored = self._apply_elasticity_bounds(anchored)
        
        return anchored
    
    def _reweight_by_market_share(self, signals: pd.DataFrame, 
                                  revenue: pd.DataFrame) -> pd.DataFrame:
        """Reweight intent signals to match market share constraints"""
        anchored = signals.copy()
        
        # Compute historical market shares
        revenue['date'] = pd.to_datetime(revenue['date'])
        revenue['week'] = (revenue['date'] - revenue['date'].min()).dt.days // 7
        
        for week in signals['date'].unique():
            week_signals = anchored[anchored['date'] == week]
            week_revenue = revenue[revenue['week'] == (pd.to_datetime(week) - revenue['date'].min()).days // 7]
            
            if len(week_revenue) == 0:
                continue
            
            # Compute market shares
            total_revenue = week_revenue.groupby('brand')['revenue'].sum()
            market_shares = total_revenue / total_revenue.sum()
            
            # Apply constraints if available
            for brand in week_signals['brand'].unique():
                if brand in self.anchoring_constraints['market_share_ranges']:
                    min_share, max_share = self.anchoring_constraints['market_share_ranges'][brand]
                    current_share = market_shares.get(brand, 0)
                    
                    # Adjust intent proportionally
                    if current_share < min_share:
                        multiplier = min_share / max(current_share, 0.01)
                    elif current_share > max_share:
                        multiplier = max_share / current_share
                    else:
                        multiplier = 1.0
                    
                    mask = (anchored['date'] == week) & (anchored['brand'] == brand)
                    anchored.loc[mask, 'intent_mean'] *= multiplier
        
        return anchored
    
    def _smooth_preferences(self, preferences: pd.Series, alpha: float = 0.7) -> pd.Series:
        """
        Apply exponential smoothing to preferences (stability prior)
        Higher alpha = more stable (less reactive to changes)
        """
        smoothed = preferences.copy()
        
        # Exponential moving average
        for i in range(1, len(smoothed)):
            smoothed.iloc[i] = alpha * smoothed.iloc[i-1] + (1 - alpha) * smoothed.iloc[i]
        
        return smoothed
    
    def _apply_demographic_mix(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Apply demographic mix constraints"""
        anchored = signals.copy()
        
        if 'demographic_mix' not in self.anchoring_constraints:
            return anchored
        
        # Adjust intent by region-brand mix
        for region in anchored['region'].unique():
            if region in self.anchoring_constraints['demographic_mix']:
                region_mix = self.anchoring_constraints['demographic_mix'][region]
                
                for brand in anchored['brand'].unique():
                    if brand in region_mix:
                        target_share = region_mix[brand]
                        
                        # Compute current share
                        region_brand = anchored[
                            (anchored['region'] == region) & 
                            (anchored['brand'] == brand)
                        ]
                        if len(region_brand) > 0:
                            current_intent = region_brand['intent_mean'].mean()
                            total_intent = anchored[anchored['region'] == region]['intent_mean'].sum()
                            current_share = current_intent / max(total_intent, 0.01)
                            
                            # Adjust to target
                            if current_share > 0:
                                multiplier = target_share / current_share
                                mask = (anchored['region'] == region) & (anchored['brand'] == brand)
                                anchored.loc[mask, 'intent_mean'] *= multiplier
        
        return anchored
    
    def _apply_elasticity_bounds(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Apply price elasticity bounds"""
        # This would constrain how much intent changes with price
        # For now, just return as-is (placeholder)
        return signals
    
    def _aggregate_intent_signals(self, intent_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate Phase 4 intent outputs (same as Phase 3 but with anchoring)"""
        df = intent_df.copy()
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        if 'product_category' in df.columns:
            df['brand'] = df['product_category'].map(self.category_to_brand)
        else:
            df['brand'] = 'Unknown'
        
        if 'segment_id' in df.columns:
            regions = ['Northeast', 'South', 'Midwest', 'West', 'Southwest']
            df['region'] = df['segment_id'].apply(lambda x: regions[hash(str(x)) % len(regions)])
        else:
            df['region'] = 'Unknown'
        
        weekly_signals = []
        
        for (brand, region), group in df.groupby(['brand', 'region']):
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
            
            weekly['intent_momentum_7d'] = weekly['intent_mean'].diff(1)
            weekly['intent_momentum_30d'] = weekly['intent_mean'].diff(4)
            weekly['intent_volatility'] = weekly['intent_mean'].rolling(4).std()
            
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
        """Fit models with anchored signals"""
        # Aggregate intent signals
        intent_signals = self._aggregate_intent_signals(self.intent_data)
        
        if len(intent_signals) == 0:
            print("Warning: No intent signals generated.")
            self.fitted = True
            return
        
        # Apply anchoring
        train_revenue = revenue_df[revenue_df['date'] < '2024-01-01'].copy()
        anchored_signals = self._apply_anchoring(intent_signals, train_revenue)
        
        # Merge with revenue
        revenue_df['date'] = pd.to_datetime(revenue_df['date'])
        anchored_signals['date'] = pd.to_datetime(anchored_signals['date'])
        
        # Fit models per brand-region
        for (brand, region), revenue_group in train_revenue.groupby(['brand', 'region']):
            intent_group = anchored_signals[
                (anchored_signals['brand'] == brand) & 
                (anchored_signals['region'] == region)
            ].copy()
            
            if len(intent_group) < 10:
                continue
            
            merged = pd.merge_asof(
                revenue_group.sort_values('date'),
                intent_group.sort_values('date'),
                on='date',
                direction='nearest',
                tolerance=pd.Timedelta(days=7)
            )
            
            if len(merged) < 10:
                continue
            
            feature_cols = ['intent_mean', 'intent_std', 'intent_momentum_7d', 
                          'intent_momentum_30d', 'intent_volatility', 'switching_rate',
                          'n_products', 'n_agents']
            feature_cols = [col for col in feature_cols if col in merged.columns]
            
            X = merged[feature_cols].fillna(0)
            y = merged['revenue']
            
            mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
            X = X[mask]
            y = y[mask]
            
            if len(X) < 5:
                continue
            
            # Use Bayesian Ridge for uncertainty
            model = BayesianRidge(compute_score=True)
            model.fit(X, y)
            
            self.models[(brand, region)] = {
                'model': model,
                'feature_cols': feature_cols,
                'mean_revenue': y.mean(),
                'std_revenue': y.std()
            }
        
        self.fitted = True
        print(f"Fitted {len(self.models)} Phase 4 anchored models")
    
    def predict(self, revenue_df: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions with anchored signals"""
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        intent_signals = self._aggregate_intent_signals(self.intent_data)
        
        if len(intent_signals) == 0:
            # Fallback
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
        
        # Apply anchoring
        historical_revenue = revenue_df[revenue_df['date'] < '2024-01-01'].copy()
        anchored_signals = self._apply_anchoring(intent_signals, historical_revenue)
        
        anchored_signals['date'] = pd.to_datetime(anchored_signals['date'])
        revenue_df['date'] = pd.to_datetime(revenue_df['date'])
        
        predictions = []
        pred_revenue = revenue_df[revenue_df['date'] >= '2024-01-01'].copy()
        
        for (brand, region), revenue_group in pred_revenue.groupby(['brand', 'region']):
            if (brand, region) not in self.models:
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
            
            intent_group = anchored_signals[
                (anchored_signals['brand'] == brand) & 
                (anchored_signals['region'] == region)
            ].copy()
            
            for _, row in revenue_group.iterrows():
                date = row['date']
                
                intent_match = intent_group.iloc[
                    (intent_group['date'] - date).abs().argsort()[:1]
                ]
                
                if len(intent_match) == 0:
                    pred_mean = model_info['mean_revenue']
                    pred_std = model_info['std_revenue']
                else:
                    X = intent_match[feature_cols].fillna(0)
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

