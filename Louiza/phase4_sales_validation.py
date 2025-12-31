"""
Phase 4.2: Sales/POS Validation
Validates that intent indices predict sales outcomes
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import json
import os


class SalesValidator:
    """
    Validates that intent indices predict sales outcomes
    """
    
    def __init__(self, 
                 intent_data: pd.DataFrame,
                 sales_data: pd.DataFrame,
                 category_col: str = 'product_category',
                 date_col: str = 'date'):
        """
        Args:
            intent_data: DataFrame with intent values (must have category, date, intent_value)
            sales_data: DataFrame with sales data (must have category, date, sales_value)
            category_col: Column name for category grouping
            date_col: Column name for date
        """
        self.intent_data = intent_data.copy()
        self.sales_data = sales_data.copy()
        self.category_col = category_col
        
        # Determine date column - check what's actually available
        if date_col in self.intent_data.columns:
            self.intent_date_col = date_col
        elif 'date' in self.intent_data.columns:
            self.intent_date_col = 'date'
        elif 'timestamp' in self.intent_data.columns:
            self.intent_date_col = 'timestamp'
        else:
            raise ValueError("Intent data must have 'date' or 'timestamp' column")
        
        if date_col in self.sales_data.columns:
            self.sales_date_col = date_col
        elif 'date' in self.sales_data.columns:
            self.sales_date_col = 'date'
        elif 'timestamp' in self.sales_data.columns:
            self.sales_date_col = 'timestamp'
        else:
            raise ValueError("Sales data must have 'date' or 'timestamp' column")
        
        # Ensure date columns are datetime
        if self.intent_date_col in self.intent_data.columns:
            self.intent_data[self.intent_date_col] = pd.to_datetime(self.intent_data[self.intent_date_col])
        if self.sales_date_col in self.sales_data.columns:
            self.sales_data[self.sales_date_col] = pd.to_datetime(self.sales_data[self.sales_date_col])
    
    def compute_intent_index(self) -> pd.DataFrame:
        """
        Compute intent index: Ic(t) = E[ŷt | category = c]
        Returns:
            DataFrame with intent index per category over time
        """
        intent_index = self.intent_data.groupby([self.intent_date_col, self.category_col])['intent_value'].agg([
            'mean', 'std', 'count'
        ]).reset_index()
        
        intent_index.columns = [self.intent_date_col, self.category_col, 'intent_mean', 'intent_std', 'intent_count']
        return intent_index
    
    def compute_lead_lag_correlation(self, 
                                    max_lag_days: int = 30,
                                    min_correlation: float = 0.3) -> Dict:
        """
        Compute lead-lag correlation: Does intent at time t predict sales at time t+k?
        
        Args:
            max_lag_days: Maximum lag to test (days)
            min_correlation: Minimum correlation threshold
            
        Returns:
            Dictionary with correlation results for each lag
        """
        intent_index = self.compute_intent_index()
        
        # Aggregate sales by category and date
        sales_agg = self.sales_data.groupby([self.sales_date_col, self.category_col])['sales_value'].sum().reset_index()
        sales_agg.columns = [self.sales_date_col, self.category_col, 'sales']
        
        # Rename date columns to match for merging
        intent_index_renamed = intent_index.rename(columns={self.intent_date_col: 'date'})
        sales_agg_renamed = sales_agg.rename(columns={self.sales_date_col: 'date'})
        
        # Merge intent and sales
        merged = pd.merge(intent_index_renamed, sales_agg_renamed, on=['date', self.category_col], how='inner')
        
        if len(merged) == 0:
            return {'error': 'No overlapping dates/categories between intent and sales'}
        
        results = {}
        best_lag = None
        best_correlation = -1
        
        for lag_days in range(1, max_lag_days + 1):
            # Shift sales forward by lag_days
            merged_lag = merged.copy()
            merged_lag['sales_lagged'] = merged_lag.groupby(self.category_col)['sales'].shift(-lag_days)
            
            # Remove rows with NaN (end of time series)
            merged_lag = merged_lag.dropna(subset=['intent_mean', 'sales_lagged'])
            
            if len(merged_lag) < 10:  # Need minimum data points
                continue
            
            # Compute correlation
            correlation = merged_lag['intent_mean'].corr(merged_lag['sales_lagged'])
            
            if not np.isnan(correlation):
                results[f'lag_{lag_days}d'] = {
                    'correlation': float(correlation),
                    'n_observations': len(merged_lag),
                    'p_value': self._compute_correlation_pvalue(merged_lag['intent_mean'], merged_lag['sales_lagged'])
                }
                
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_lag = lag_days
        
        results['best_lag'] = best_lag
        results['best_correlation'] = float(best_correlation) if best_correlation > -1 else None
        results['meets_threshold'] = best_correlation >= min_correlation if best_correlation > -1 else False
        
        return results
    
    def compute_variance_explained(self, lag_days: Optional[int] = None) -> Dict:
        """
        Compute how much variance in future sales is explained by intent
        
        Args:
            lag_days: Specific lag to use (if None, uses best lag from lead-lag analysis)
            
        Returns:
            Dictionary with R², coefficients, etc.
        """
        intent_index = self.compute_intent_index()
        
        # Aggregate sales by category and date
        sales_agg = self.sales_data.groupby([self.sales_date_col, self.category_col])['sales_value'].sum().reset_index()
        sales_agg.columns = [self.sales_date_col, self.category_col, 'sales']
        
        # Rename date columns to match for merging
        intent_index_renamed = intent_index.rename(columns={self.intent_date_col: 'date'})
        sales_agg_renamed = sales_agg.rename(columns={self.sales_date_col: 'date'})
        
        # Merge intent and sales
        merged = pd.merge(intent_index_renamed, sales_agg_renamed, on=['date', self.category_col], how='inner')
        
        if len(merged) == 0:
            return {'error': 'No overlapping dates/categories between intent and sales'}
        
        # Use best lag if not specified
        if lag_days is None:
            lead_lag = self.compute_lead_lag_correlation()
            lag_days = lead_lag.get('best_lag', 7)  # Default to 7 days
        
        # Shift sales forward
        merged['sales_future'] = merged.groupby(self.category_col)['sales'].shift(-lag_days)
        merged = merged.dropna(subset=['intent_mean', 'sales_future'])
        
        if len(merged) < 10:
            return {'error': 'Insufficient data for regression'}
        
        # Prepare features
        X = merged[['intent_mean']].values
        y = merged['sales_future'].values
        
        # Fit regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Predictions
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # Per-category R²
        category_r2 = {}
        for category in merged[self.category_col].unique():
            cat_data = merged[merged[self.category_col] == category]
            if len(cat_data) >= 5:  # Need minimum points
                X_cat = cat_data[['intent_mean']].values
                y_cat = cat_data['sales_future'].values
                y_pred_cat = model.predict(X_cat)
                r2_cat = r2_score(y_cat, y_pred_cat)
                category_r2[category] = float(r2_cat)
        
        return {
            'lag_days': lag_days,
            'r2_overall': float(r2),
            'r2_by_category': category_r2,
            'coefficient': float(model.coef_[0]),
            'intercept': float(model.intercept_),
            'n_observations': len(merged),
            'meets_threshold': r2 >= 0.2  # At least 20% variance explained
        }
    
    def compute_rank_correlation(self, lag_days: int = 7) -> Dict:
        """
        Compute rank correlation: Do products ranked by intent match products ranked by sales?
        
        Args:
            lag_days: Lag between intent and sales
            
        Returns:
            Dictionary with Spearman rank correlation
        """
        intent_index = self.compute_intent_index()
        
        # Aggregate sales by category and date
        sales_agg = self.sales_data.groupby([self.sales_date_col, self.category_col])['sales_value'].sum().reset_index()
        sales_agg.columns = [self.sales_date_col, self.category_col, 'sales']
        
        # Rename date columns to match for merging
        intent_index_renamed = intent_index.rename(columns={self.intent_date_col: 'date'})
        sales_agg_renamed = sales_agg.rename(columns={self.sales_date_col: 'date'})
        
        # Merge
        merged = pd.merge(intent_index_renamed, sales_agg_renamed, on=['date', self.category_col], how='inner')
        
        if len(merged) == 0:
            return {'error': 'No overlapping dates/categories'}
        
        # Shift sales forward
        merged['sales_future'] = merged.groupby(self.category_col)['sales'].shift(-lag_days)
        merged = merged.dropna(subset=['intent_mean', 'sales_future'])
        
        if len(merged) < 10:
            return {'error': 'Insufficient data'}
        
        # Compute rank correlation
        spearman_corr, p_value = stats.spearmanr(merged['intent_mean'], merged['sales_future'])
        
        return {
            'lag_days': lag_days,
            'spearman_correlation': float(spearman_corr) if not np.isnan(spearman_corr) else None,
            'p_value': float(p_value) if not np.isnan(p_value) else None,
            'n_observations': len(merged),
            'meets_threshold': abs(spearman_corr) >= 0.3 if not np.isnan(spearman_corr) else False
        }
    
    def validate_intent_predicts_sales(self, 
                                      min_r2: float = 0.2,
                                      min_correlation: float = 0.3) -> Dict:
        """
        Comprehensive validation that intent predicts sales
        
        Args:
            min_r2: Minimum R² threshold
            min_correlation: Minimum correlation threshold
            
        Returns:
            Dictionary with all validation results
        """
        results = {
            'lead_lag_analysis': self.compute_lead_lag_correlation(min_correlation=min_correlation),
            'variance_explained': self.compute_variance_explained(),
            'rank_correlation': self.compute_rank_correlation(),
            'validation_passed': False
        }
        
        # Determine if validation passes
        variance_ok = results['variance_explained'].get('r2_overall', 0) >= min_r2
        correlation_ok = results['lead_lag_analysis'].get('meets_threshold', False)
        rank_ok = results['rank_correlation'].get('meets_threshold', False)
        
        results['validation_passed'] = variance_ok and (correlation_ok or rank_ok)
        results['summary'] = {
            'variance_explained_ok': variance_ok,
            'lead_lag_ok': correlation_ok,
            'rank_correlation_ok': rank_ok
        }
        
        return results
    
    def _compute_correlation_pvalue(self, x: pd.Series, y: pd.Series) -> float:
        """Compute p-value for correlation"""
        try:
            _, p_value = stats.pearsonr(x, y)
            return float(p_value)
        except:
            return 1.0
    
    def generate_validation_report(self, output_path: str) -> str:
        """
        Generate a human-readable validation report
        
        Args:
            output_path: Path to save report
            
        Returns:
            Report text
        """
        validation_results = self.validate_intent_predicts_sales()
        
        report_lines = [
            "=" * 60,
            "Phase 4.2: Sales/POS Validation Report",
            "=" * 60,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Lead-Lag Correlation Analysis",
            "",
        ]
        
        lead_lag = validation_results['lead_lag_analysis']
        if 'error' in lead_lag:
            report_lines.append(f"  ⚠️  {lead_lag['error']}")
        else:
            best_lag = lead_lag.get('best_lag')
            best_corr = lead_lag.get('best_correlation')
            if best_lag and best_corr:
                report_lines.append(f"  Best Lag: {best_lag} days")
                report_lines.append(f"  Best Correlation: {best_corr:.4f}")
                report_lines.append(f"  Meets Threshold: {'✅' if lead_lag.get('meets_threshold') else '❌'}")
                report_lines.append("")
                report_lines.append("  Top 5 Lags:")
                lag_keys = [k for k in lead_lag.keys() if k.startswith('lag_')]
                lag_corrs = [(k, lead_lag[k]['correlation']) for k in lag_keys]
                lag_corrs.sort(key=lambda x: x[1], reverse=True)
                for lag_key, corr in lag_corrs[:5]:
                    lag_days = lag_key.replace('lag_', '').replace('d', '')
                    report_lines.append(f"    {lag_days} days: {corr:.4f}")
        
        report_lines.extend([
            "",
            "## Variance Explained",
            "",
        ])
        
        variance = validation_results['variance_explained']
        if 'error' in variance:
            report_lines.append(f"  ⚠️  {variance['error']}")
        else:
            r2 = variance.get('r2_overall', 0)
            report_lines.append(f"  Overall R²: {r2:.4f}")
            report_lines.append(f"  Coefficient: {variance.get('coefficient', 0):.4f}")
            report_lines.append(f"  Meets Threshold (R² >= 0.2): {'✅' if variance.get('meets_threshold') else '❌'}")
            report_lines.append("")
            report_lines.append("  R² by Category:")
            for cat, r2_cat in variance.get('r2_by_category', {}).items():
                report_lines.append(f"    {cat}: {r2_cat:.4f}")
        
        report_lines.extend([
            "",
            "## Rank Correlation",
            "",
        ])
        
        rank = validation_results['rank_correlation']
        if 'error' in rank:
            report_lines.append(f"  ⚠️  {rank['error']}")
        else:
            spearman = rank.get('spearman_correlation')
            if spearman is not None:
                report_lines.append(f"  Spearman Correlation: {spearman:.4f}")
                report_lines.append(f"  P-value: {rank.get('p_value', 0):.4f}")
                report_lines.append(f"  Meets Threshold: {'✅' if rank.get('meets_threshold') else '❌'}")
        
        report_lines.extend([
            "",
            "## Overall Validation",
            "",
            f"  Validation Passed: {'✅ YES' if validation_results['validation_passed'] else '❌ NO'}",
            "",
            "  Summary:",
        ])
        
        summary = validation_results['summary']
        report_lines.append(f"    Variance Explained OK: {'✅' if summary['variance_explained_ok'] else '❌'}")
        report_lines.append(f"    Lead-Lag Correlation OK: {'✅' if summary['lead_lag_ok'] else '❌'}")
        report_lines.append(f"    Rank Correlation OK: {'✅' if summary['rank_correlation_ok'] else '❌'}")
        
        report_text = "\n".join(report_lines)
        
        # Save to file
        with open(output_path, 'w') as f:
            f.write(report_text)
        
        return report_text

