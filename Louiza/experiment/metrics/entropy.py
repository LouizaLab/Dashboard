"""
PART C: Entropy and Signal Quality Metrics
Computes predictive entropy, calibration, mutual information, stability
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from scipy import stats
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')


class EntropyMetrics:
    """
    Computes entropy-based metrics for forecast quality
    """
    
    def __init__(self, predictions: pd.DataFrame, actuals: pd.DataFrame):
        """
        Args:
            predictions: DataFrame with columns [date, brand, region, revenue_pred, 
                                                 revenue_lower_80, revenue_upper_80,
                                                 revenue_lower_95, revenue_upper_95]
            actuals: DataFrame with columns [date, brand, region, revenue]
        """
        self.predictions = predictions.copy()
        self.actuals = actuals.copy()
        
        # Merge predictions and actuals
        self.predictions['date'] = pd.to_datetime(self.predictions['date'])
        self.actuals['date'] = pd.to_datetime(self.actuals['date'])
        
        self.merged = pd.merge(
            self.predictions,
            self.actuals,
            on=['date', 'brand', 'region'],
            how='inner'
        )
    
    def compute_predictive_entropy(self) -> pd.DataFrame:
        """
        Compute predictive entropy H(Y_t+1 | X_t)
        
        For a normal distribution: H = 0.5 * log(2 * pi * e * sigma^2)
        
        Returns:
            DataFrame with entropy per prediction
        """
        entropy_records = []
        
        for _, row in self.merged.iterrows():
            # Estimate sigma from prediction intervals
            # For 80% interval: mean ± 1.28*sigma
            interval_80_width = row['revenue_upper_80'] - row['revenue_lower_80']
            sigma_80 = interval_80_width / (2 * 1.28)
            
            # For 95% interval: mean ± 1.96*sigma
            interval_95_width = row['revenue_upper_95'] - row['revenue_lower_95']
            sigma_95 = interval_95_width / (2 * 1.96)
            
            # Use average sigma
            sigma = (sigma_80 + sigma_95) / 2
            
            # Ensure positive
            sigma = max(sigma, 1.0)
            
            # Entropy for normal distribution
            entropy = 0.5 * np.log(2 * np.pi * np.e * sigma**2)
            
            entropy_records.append({
                'date': row['date'],
                'brand': row['brand'],
                'region': row['region'],
                'entropy': entropy,
                'sigma': sigma,
                'interval_width_80': interval_80_width,
                'interval_width_95': interval_95_width
            })
        
        return pd.DataFrame(entropy_records)
    
    def compute_calibration_error(self) -> Dict:
        """
        Compute calibration error: How often true revenue falls inside predicted intervals
        
        Returns:
            Dict with calibration metrics
        """
        # 80% interval calibration
        in_80 = (
            (self.merged['revenue'] >= self.merged['revenue_lower_80']) &
            (self.merged['revenue'] <= self.merged['revenue_upper_80'])
        )
        coverage_80 = in_80.mean()
        calibration_error_80 = abs(coverage_80 - 0.80)
        
        # 95% interval calibration
        in_95 = (
            (self.merged['revenue'] >= self.merged['revenue_lower_95']) &
            (self.merged['revenue'] <= self.merged['revenue_upper_95'])
        )
        coverage_95 = in_95.mean()
        calibration_error_95 = abs(coverage_95 - 0.95)
        
        return {
            'coverage_80': coverage_80,
            'coverage_95': coverage_95,
            'calibration_error_80': calibration_error_80,
            'calibration_error_95': calibration_error_95,
            'n_predictions': len(self.merged)
        }
    
    def compute_prediction_interval_width(self) -> pd.DataFrame:
        """
        Compute prediction interval widths
        
        Returns:
            DataFrame with interval widths
        """
        self.merged['interval_width_80'] = (
            self.merged['revenue_upper_80'] - self.merged['revenue_lower_80']
        )
        self.merged['interval_width_95'] = (
            self.merged['revenue_upper_95'] - self.merged['revenue_lower_95']
        )
        
        return self.merged[['date', 'brand', 'region', 
                           'interval_width_80', 'interval_width_95']].copy()
    
    def compute_mutual_information(self, latent_signals: Optional[pd.DataFrame] = None) -> Dict:
        """
        Compute mutual information I(latent_signals; future_revenue)
        
        Args:
            latent_signals: Optional DataFrame with latent preference signals
        
        Returns:
            Dict with mutual information metrics
        """
        if latent_signals is None:
            # Use prediction mean as proxy for signal
            signal = self.merged['revenue_pred']
        else:
            # Merge latent signals
            latent_signals['date'] = pd.to_datetime(latent_signals['date'])
            merged_with_latents = pd.merge(
                self.merged,
                latent_signals,
                on=['date', 'brand', 'region'],
                how='inner'
            )
            
            if len(merged_with_latents) == 0:
                return {'mutual_information': 0.0, 'n_observations': 0}
            
            # Use latent preference as signal
            signal = merged_with_latents.get('latent_preference', merged_with_latents['revenue_pred'])
            target = merged_with_latents['revenue']
        target = self.merged['revenue']
        
        # Discretize for mutual information computation
        n_bins = min(10, len(signal) // 10)
        if n_bins < 2:
            return {'mutual_information': 0.0, 'n_observations': len(signal)}
        
        signal_binned = pd.cut(signal, bins=n_bins, labels=False)
        target_binned = pd.cut(target, bins=n_bins, labels=False)
        
        # Compute mutual information
        try:
            mi = stats.mutual_info_score(signal_binned, target_binned)
        except:
            mi = 0.0
        
        # Normalize by entropy of target
        target_entropy = stats.entropy(pd.Series(target_binned).value_counts())
        normalized_mi = mi / max(target_entropy, 1e-10)
        
        return {
            'mutual_information': mi,
            'normalized_mutual_information': normalized_mi,
            'n_observations': len(signal)
        }
    
    def compute_stability_metrics(self) -> Dict:
        """
        Compute stability metrics:
        - Week-to-week variance of predictions
        - Sensitivity to shocks
        """
        # Sort by date
        sorted_preds = self.merged.sort_values(['brand', 'region', 'date'])
        
        # Week-to-week changes
        sorted_preds['pred_change'] = sorted_preds.groupby(['brand', 'region'])['revenue_pred'].diff()
        sorted_preds['actual_change'] = sorted_preds.groupby(['brand', 'region'])['revenue'].diff()
        
        # Prediction variance
        pred_variance = sorted_preds.groupby(['brand', 'region'])['revenue_pred'].var().mean()
        actual_variance = sorted_preds.groupby(['brand', 'region'])['revenue'].var().mean()
        
        # Prediction change variance (stability)
        pred_change_variance = sorted_preds['pred_change'].var()
        actual_change_variance = sorted_preds['actual_change'].var()
        
        # Over-reaction metric (how much predictions change vs actuals)
        over_reaction_ratio = pred_change_variance / max(actual_change_variance, 1e-10)
        
        return {
            'prediction_variance': pred_variance,
            'actual_variance': actual_variance,
            'prediction_change_variance': pred_change_variance,
            'actual_change_variance': actual_change_variance,
            'over_reaction_ratio': over_reaction_ratio,
            'stability_score': 1.0 / (1.0 + over_reaction_ratio)  # Higher = more stable
        }
    
    def compute_accuracy_metrics(self) -> Dict:
        """
        Compute accuracy metrics (secondary to entropy)
        """
        rmse = np.sqrt(((self.merged['revenue'] - self.merged['revenue_pred'])**2).mean())
        mae = np.abs(self.merged['revenue'] - self.merged['revenue_pred']).mean()
        
        # R²
        r2 = r2_score(self.merged['revenue'], self.merged['revenue_pred'])
        
        # Mean absolute percentage error
        mape = np.abs((self.merged['revenue'] - self.merged['revenue_pred']) / 
                     self.merged['revenue']).mean() * 100
        
        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape
        }
    
    def compute_all_metrics(self, latent_signals: Optional[pd.DataFrame] = None) -> Dict:
        """
        Compute all metrics
        
        Returns:
            Dict with all computed metrics
        """
        entropy_df = self.compute_predictive_entropy()
        calibration = self.compute_calibration_error()
        stability = self.compute_stability_metrics()
        accuracy = self.compute_accuracy_metrics()
        mi = self.compute_mutual_information(latent_signals)
        
        return {
            'mean_entropy': entropy_df['entropy'].mean(),
            'std_entropy': entropy_df['entropy'].std(),
            'mean_interval_width_80': entropy_df['interval_width_80'].mean(),
            'mean_interval_width_95': entropy_df['interval_width_95'].mean(),
            'calibration': calibration,
            'stability': stability,
            'accuracy': accuracy,
            'mutual_information': mi,
            'entropy_by_time': {str(k): float(v) for k, v in entropy_df.groupby('date')['entropy'].mean().to_dict().items()}
        }

