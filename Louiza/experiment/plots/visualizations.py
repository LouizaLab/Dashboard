"""
PART D: Investor-Ready Visualizations
Generates plots showing entropy reduction and signal quality
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime

# Set style
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    try:
        plt.style.use('seaborn-darkgrid')
    except:
        plt.style.use('default')
sns.set_palette("husl")


class ExperimentVisualizer:
    """
    Generates visualizations for the entropy experiment
    """
    
    def __init__(self, output_dir: str = 'experiment/plots'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def plot_revenue_forecast_fan_charts(self,
                                       predictions_m0: pd.DataFrame,
                                       predictions_m1: pd.DataFrame,
                                       predictions_m2: pd.DataFrame,
                                       actuals: pd.DataFrame,
                                       brand: str = None,
                                       region: str = None):
        """
        Plot fan charts comparing M0, M1, M2 forecasts
        
        Args:
            predictions_m0: Baseline model predictions
            predictions_m1: Phase 3 unanchored predictions
            predictions_m2: Phase 4 anchored predictions
            actuals: Actual revenue
            brand: Optional brand filter
            region: Optional region filter
        """
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        models = [
            ('M0: Baseline', predictions_m0, 'blue'),
            ('M1: Phase 3 Unanchored', predictions_m1, 'orange'),
            ('M2: Phase 4 Anchored', predictions_m2, 'green')
        ]
        
        for idx, (model_name, preds, color) in enumerate(models):
            ax = axes[idx]
            
            # Filter if needed
            if brand:
                preds = preds[preds['brand'] == brand]
                actuals_filtered = actuals[actuals['brand'] == brand]
            else:
                actuals_filtered = actuals
            
            if region:
                preds = preds[preds['region'] == region]
                actuals_filtered = actuals_filtered[actuals_filtered['region'] == region]
            
            # Aggregate by date if multiple brands/regions
            if brand is None or region is None:
                preds_agg = preds.groupby('date').agg({
                    'revenue_pred': 'mean',
                    'revenue_lower_80': 'mean',
                    'revenue_upper_80': 'mean',
                    'revenue_lower_95': 'mean',
                    'revenue_upper_95': 'mean'
                }).reset_index()
                actuals_agg = actuals_filtered.groupby('date')['revenue'].mean().reset_index()
            else:
                preds_agg = preds.sort_values('date')
                actuals_agg = actuals_filtered.sort_values('date')
            
            # Merge
            merged = pd.merge(preds_agg, actuals_agg, on='date', how='inner')
            merged = merged.sort_values('date')
            
            # Plot fan chart
            dates = pd.to_datetime(merged['date'])
            
            # 95% interval (lighter)
            ax.fill_between(dates, merged['revenue_lower_95'], merged['revenue_upper_95'],
                           alpha=0.2, color=color, label='95% Interval')
            
            # 80% interval (darker)
            ax.fill_between(dates, merged['revenue_lower_80'], merged['revenue_upper_80'],
                           alpha=0.4, color=color, label='80% Interval')
            
            # Prediction mean
            ax.plot(dates, merged['revenue_pred'], color=color, linewidth=2, 
                   label=f'{model_name} Forecast')
            
            # Actuals
            ax.plot(dates, merged['revenue'], color='red', linewidth=2, 
                   linestyle='--', marker='o', markersize=4, label='Actual Revenue')
            
            ax.set_title(f'{model_name} - Revenue Forecasts', fontsize=12, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Revenue ($)')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        filename = f'fan_charts'
        if brand:
            filename += f'_{brand}'
        if region:
            filename += f'_{region}'
        filename += '.png'
        
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved fan charts to {filename}")
    
    def plot_predictive_entropy_over_time(self,
                                        entropy_m0: pd.DataFrame,
                                        entropy_m1: pd.DataFrame,
                                        entropy_m2: pd.DataFrame):
        """Plot predictive entropy over time for all models"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Aggregate by date
        entropy_m0_agg = entropy_m0.groupby('date')['entropy'].mean()
        entropy_m1_agg = entropy_m1.groupby('date')['entropy'].mean()
        entropy_m2_agg = entropy_m2.groupby('date')['entropy'].mean()
        
        dates = pd.to_datetime(entropy_m0_agg.index)
        
        ax.plot(dates, entropy_m0_agg, label='M0: Baseline', color='blue', linewidth=2)
        ax.plot(dates, entropy_m1_agg, label='M1: Phase 3 Unanchored', color='orange', linewidth=2)
        ax.plot(dates, entropy_m2_agg, label='M2: Phase 4 Anchored', color='green', linewidth=2)
        
        ax.set_title('Predictive Entropy Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Predictive Entropy (nats)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'entropy_over_time.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved entropy over time plot")
    
    def plot_preference_entropy_vs_revenue_volatility(self,
                                                    entropy_df: pd.DataFrame,
                                                    actuals: pd.DataFrame):
        """Plot relationship between preference entropy and revenue volatility"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Compute revenue volatility by brand-region
        actuals['date'] = pd.to_datetime(actuals['date'])
        revenue_volatility = actuals.groupby(['brand', 'region'])['revenue'].std()
        
        # Compute mean entropy by brand-region
        entropy_df['date'] = pd.to_datetime(entropy_df['date'])
        mean_entropy = entropy_df.groupby(['brand', 'region'])['entropy'].mean()
        
        # Merge
        merged = pd.DataFrame({
            'entropy': mean_entropy,
            'revenue_volatility': revenue_volatility
        }).dropna()
        
        # Scatter plot
        ax.scatter(merged['entropy'], merged['revenue_volatility'], 
                  s=100, alpha=0.6, edgecolors='black')
        
        # Add labels
        for idx, row in merged.iterrows():
            brand, region = idx
            ax.annotate(f'{brand[:3]}-{region[:3]}', 
                       (row['entropy'], row['revenue_volatility']),
                       fontsize=8)
        
        ax.set_xlabel('Mean Predictive Entropy (nats)')
        ax.set_ylabel('Revenue Volatility ($)')
        ax.set_title('Preference Entropy vs Revenue Volatility', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'entropy_vs_volatility.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved entropy vs volatility plot")
    
    def plot_shock_response_comparison(self,
                                      predictions_m1: pd.DataFrame,
                                      predictions_m2: pd.DataFrame,
                                      actuals: pd.DataFrame,
                                      shock_dates: List[datetime] = None):
        """
        Plot how unanchored vs anchored models respond to shocks
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Aggregate by date
        pred_m1_agg = predictions_m1.groupby('date')['revenue_pred'].mean()
        pred_m2_agg = predictions_m2.groupby('date')['revenue_pred'].mean()
        actuals_agg = actuals.groupby('date')['revenue'].mean()
        
        dates = pd.to_datetime(pred_m1_agg.index)
        
        ax.plot(dates, pred_m1_agg, label='M1: Unanchored', color='orange', linewidth=2)
        ax.plot(dates, pred_m2_agg, label='M2: Anchored', color='green', linewidth=2)
        ax.plot(dates, actuals_agg, label='Actual', color='red', linewidth=2, linestyle='--')
        
        # Mark shocks if provided
        if shock_dates:
            for shock_date in shock_dates:
                ax.axvline(pd.to_datetime(shock_date), color='red', linestyle=':', 
                          alpha=0.5, label='Shock' if shock_date == shock_dates[0] else '')
        
        ax.set_title('Shock Response: Unanchored vs Anchored Models', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Revenue ($)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'shock_response.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved shock response plot")
    
    def plot_signal_to_noise_ratio(self,
                                  metrics_m0: Dict,
                                  metrics_m1: Dict,
                                  metrics_m2: Dict):
        """Plot signal-to-noise ratio comparison"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        models = ['M0: Baseline', 'M1: Phase 3\nUnanchored', 'M2: Phase 4\nAnchored']
        
        # Compute signal-to-noise as inverse of entropy (normalized)
        entropy_m0 = metrics_m0.get('mean_entropy', 10)
        entropy_m1 = metrics_m1.get('mean_entropy', 10)
        entropy_m2 = metrics_m2.get('mean_entropy', 10)
        
        # Normalize (higher entropy = lower SNR)
        max_entropy = max(entropy_m0, entropy_m1, entropy_m2)
        snr_m0 = 1.0 / (1.0 + entropy_m0 / max_entropy)
        snr_m1 = 1.0 / (1.0 + entropy_m1 / max_entropy)
        snr_m2 = 1.0 / (1.0 + entropy_m2 / max_entropy)
        
        snr_values = [snr_m0, snr_m1, snr_m2]
        colors = ['blue', 'orange', 'green']
        
        bars = ax.bar(models, snr_values, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels
        for bar, val in zip(bars, snr_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.3f}',
                   ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Signal-to-Noise Ratio (Normalized)')
        ax.set_title('Signal-to-Noise Ratio Comparison', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(snr_values) * 1.2)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'signal_to_noise.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved signal-to-noise ratio plot")
    
    def plot_metrics_comparison(self,
                               metrics_m0: Dict,
                               metrics_m1: Dict,
                               metrics_m2: Dict):
        """Plot comprehensive metrics comparison"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        models = ['M0', 'M1', 'M2']
        
        # 1. Mean Entropy
        ax = axes[0, 0]
        entropies = [
            metrics_m0.get('mean_entropy', 0),
            metrics_m1.get('mean_entropy', 0),
            metrics_m2.get('mean_entropy', 0)
        ]
        ax.bar(models, entropies, color=['blue', 'orange', 'green'], alpha=0.7)
        ax.set_ylabel('Mean Predictive Entropy (nats)')
        ax.set_title('Mean Predictive Entropy', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 2. Calibration Error (80%)
        ax = axes[0, 1]
        cal_errors = [
            metrics_m0.get('calibration', {}).get('calibration_error_80', 0),
            metrics_m1.get('calibration', {}).get('calibration_error_80', 0),
            metrics_m2.get('calibration', {}).get('calibration_error_80', 0)
        ]
        ax.bar(models, cal_errors, color=['blue', 'orange', 'green'], alpha=0.7)
        ax.set_ylabel('Calibration Error (80% Interval)')
        ax.set_title('Calibration Error', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 3. Stability Score
        ax = axes[1, 0]
        stability_scores = [
            metrics_m0.get('stability', {}).get('stability_score', 0),
            metrics_m1.get('stability', {}).get('stability_score', 0),
            metrics_m2.get('stability', {}).get('stability_score', 0)
        ]
        ax.bar(models, stability_scores, color=['blue', 'orange', 'green'], alpha=0.7)
        ax.set_ylabel('Stability Score')
        ax.set_title('Prediction Stability', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. Interval Width (80%)
        ax = axes[1, 1]
        interval_widths = [
            metrics_m0.get('mean_interval_width_80', 0),
            metrics_m1.get('mean_interval_width_80', 0),
            metrics_m2.get('mean_interval_width_80', 0)
        ]
        ax.bar(models, interval_widths, color=['blue', 'orange', 'green'], alpha=0.7)
        ax.set_ylabel('Mean Interval Width (80%)')
        ax.set_title('Prediction Interval Width', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'metrics_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved metrics comparison plot")
    
    def plot_actual_vs_predicted_phase4(self,
                                       predictions_m2: pd.DataFrame,
                                       actuals: pd.DataFrame,
                                       brand: str = None,
                                       region: str = None):
        """
        Plot actual revenue vs Phase 4 predicted revenue
        
        Args:
            predictions_m2: Phase 4 predictions DataFrame
            actuals: Actual revenue DataFrame
            brand: Optional brand filter
            region: Optional region filter
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Filter if needed
        preds = predictions_m2.copy()
        actuals_filtered = actuals.copy()
        
        if brand:
            preds = preds[preds['brand'] == brand]
            actuals_filtered = actuals_filtered[actuals_filtered['brand'] == brand]
        
        if region:
            preds = preds[preds['region'] == region]
            actuals_filtered = actuals_filtered[actuals_filtered['region'] == region]
        
        # Aggregate by date if multiple brands/regions
        if brand is None or region is None:
            preds_agg = preds.groupby('date').agg({
                'revenue_pred': 'mean',
                'revenue_lower_80': 'mean',
                'revenue_upper_80': 'mean',
                'revenue_lower_95': 'mean',
                'revenue_upper_95': 'mean'
            }).reset_index()
            actuals_agg = actuals_filtered.groupby('date')['revenue'].mean().reset_index()
        else:
            preds_agg = preds.sort_values('date')
            actuals_agg = actuals_filtered.sort_values('date')
        
        # Merge on date
        merged = pd.merge(preds_agg, actuals_agg, on='date', how='inner')
        merged = merged.sort_values('date')
        merged['date'] = pd.to_datetime(merged['date'])
        
        dates = merged['date']
        
        # Plot prediction intervals
        # 95% interval (lighter)
        ax.fill_between(dates, merged['revenue_lower_95'], merged['revenue_upper_95'],
                        alpha=0.15, color='green', label='95% Prediction Interval')
        
        # 80% interval (darker)
        ax.fill_between(dates, merged['revenue_lower_80'], merged['revenue_upper_80'],
                        alpha=0.3, color='green', label='80% Prediction Interval')
        
        # Predicted revenue (Phase 4)
        ax.plot(dates, merged['revenue_pred'], color='green', linewidth=2.5,
               label='Phase 4 Predicted Revenue', marker='o', markersize=4, alpha=0.8)
        
        # Actual revenue
        ax.plot(dates, merged['revenue'], color='red', linewidth=2.5,
               label='Actual Revenue', marker='s', markersize=4, alpha=0.8, linestyle='--')
        
        # Compute and display metrics
        rmse = np.sqrt(((merged['revenue'] - merged['revenue_pred'])**2).mean())
        mae = np.abs(merged['revenue'] - merged['revenue_pred']).mean()
        mape = np.abs((merged['revenue'] - merged['revenue_pred']) / merged['revenue']).mean() * 100
        
        # Add text box with metrics
        textstr = f'RMSE: ${rmse:,.0f}\nMAE: ${mae:,.0f}\nMAPE: {mape:.2f}%'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
               verticalalignment='top', bbox=props)
        
        # Title
        title = 'Phase 4: Actual vs Predicted Revenue'
        if brand:
            title += f' - {brand}'
        if region:
            title += f' ({region})'
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Revenue ($)', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        filename = 'actual_vs_predicted_phase4'
        if brand:
            filename += f'_{brand}'
        if region:
            filename += f'_{region}'
        filename += '.png'
        
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved actual vs predicted plot to {filename}")

