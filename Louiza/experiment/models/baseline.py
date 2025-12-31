"""
Model M0: Baseline Revenue Model
Uses only past revenue and seasonality features
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
except ImportError:
    print("Warning: statsmodels not available. Using simple moving average fallback.")
    ARIMA = None

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Warning: Prophet not available. Using ARIMA fallback.")


class BaselineRevenueModel:
    """
    Baseline model using only historical revenue
    Methods: ARIMA or Prophet
    """
    
    def __init__(self, method: str = 'arima', confidence_levels: Tuple[float, float] = (0.80, 0.95)):
        """
        Args:
            method: 'arima' or 'prophet'
            confidence_levels: Tuple of (lower, upper) confidence levels
        """
        self.method = method
        self.confidence_levels = confidence_levels
        self.models = {}  # One model per brand-region combination
        self.fitted = False
    
    def _prepare_features(self, revenue_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare time-series features"""
        df = revenue_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['brand', 'region', 'date'])
        
        # Time features
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['year'] = df['date'].dt.year
        
        # Lag features
        df['revenue_lag1'] = df.groupby(['brand', 'region'])['revenue'].shift(1)
        df['revenue_lag4'] = df.groupby(['brand', 'region'])['revenue'].shift(4)  # Monthly
        df['revenue_lag52'] = df.groupby(['brand', 'region'])['revenue'].shift(52)  # Yearly
        
        return df
    
    def fit(self, revenue_df: pd.DataFrame):
        """Fit models for each brand-region combination"""
        df = self._prepare_features(revenue_df)
        
        for (brand, region), group in df.groupby(['brand', 'region']):
            # Filter to training period (2022-2023)
            train_data = group[group['date'] < '2024-01-01'].copy()
            
            if len(train_data) < 20:  # Need minimum data
                continue
            
            # Create time series
            ts = train_data.set_index('date')['revenue'].sort_index()
            
            if self.method == 'prophet' and PROPHET_AVAILABLE:
                model = self._fit_prophet(ts)
                method_used = 'prophet'
            elif self.method == 'arima' and ARIMA is not None:
                model = self._fit_arima(ts)
                method_used = 'arima' if model is not None else 'simple'
            else:
                # Fallback: simple moving average
                model = None
                method_used = 'simple'
            
            # If model fitting failed, use simple MA
            if model is None:
                method_used = 'simple'
            
            self.models[(brand, region)] = {
                'model': model,
                'method': method_used,
                'mean_revenue': ts.mean(),
                'std_revenue': ts.std()
            }
        
        self.fitted = True
        print(f"Fitted {len(self.models)} models")
    
    def _fit_prophet(self, ts: pd.Series):
        """Fit Prophet model"""
        df_prophet = pd.DataFrame({
            'ds': ts.index,
            'y': ts.values
        })
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        model.fit(df_prophet)
        return model
    
    def _fit_arima(self, ts: pd.Series):
        """Fit ARIMA model"""
        # Auto-select order (simplified)
        try:
            model = ARIMA(ts, order=(2, 1, 2), seasonal_order=(1, 1, 1, 52))
            fitted = model.fit()
            return fitted
        except:
            # Fallback to simpler model
            try:
                model = ARIMA(ts, order=(1, 1, 1))
                fitted = model.fit()
                return fitted
            except:
                # Return None to indicate fallback needed
                return None
    
    def _fit_simple_ma(self, ts: pd.Series):
        """Fallback: Simple moving average"""
        # Return None to indicate simple MA (will use mean/std from model_info)
        return None
    
    def predict(self, revenue_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate predictions with uncertainty intervals
        
        Returns:
            DataFrame with columns [date, brand, region, revenue_pred, 
                                   revenue_lower_80, revenue_upper_80,
                                   revenue_lower_95, revenue_upper_95]
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        df = self._prepare_features(revenue_df)
        predictions = []
        
        for (brand, region), group in df.groupby(['brand', 'region']):
            if (brand, region) not in self.models:
                # Use mean if no model
                model_info = {'mean_revenue': group['revenue'].mean(), 'std_revenue': group['revenue'].std()}
                method = 'simple'
            else:
                model_info = self.models[(brand, region)]
                method = model_info['method']
            
            model = model_info['model']
            
            # Filter to prediction period (2024)
            pred_data = group[group['date'] >= '2024-01-01'].copy()
            
            for _, row in pred_data.iterrows():
                date = row['date']
                
                if method == 'prophet' and hasattr(model, 'predict'):
                    pred_df = pd.DataFrame({'ds': [date]})
                    forecast = model.predict(pred_df)
                    pred_mean = forecast['yhat'].iloc[0]
                    pred_lower_80 = forecast['yhat_lower'].iloc[0]
                    pred_upper_80 = forecast['yhat_upper'].iloc[0]
                    pred_lower_95 = forecast['yhat_lower'].iloc[0]  # Prophet doesn't give 95% directly
                    pred_upper_95 = forecast['yhat_upper'].iloc[0]
                elif method == 'arima' and hasattr(model, 'get_forecast'):
                    # Get forecast
                    forecast = model.get_forecast(steps=1)
                    pred_mean = forecast.predicted_mean.iloc[0]
                    conf_int = forecast.conf_int()
                    pred_lower_80 = conf_int.iloc[0, 0]
                    pred_upper_80 = conf_int.iloc[0, 1]
                    pred_lower_95 = pred_lower_80  # Approximate
                    pred_upper_95 = pred_upper_80
                else:
                    # Simple MA (fallback for dict models or when ARIMA/Prophet unavailable)
                    pred_mean = model_info.get('mean_revenue', group['revenue'].mean())
                    std = model_info.get('std_revenue', group['revenue'].std())
                    pred_lower_80 = pred_mean - 1.28 * std
                    pred_upper_80 = pred_mean + 1.28 * std
                    pred_lower_95 = pred_mean - 1.96 * std
                    pred_upper_95 = pred_mean + 1.96 * std
                
                predictions.append({
                    'date': date,
                    'brand': brand,
                    'region': region,
                    'revenue_pred': pred_mean,
                    'revenue_lower_80': pred_lower_80,
                    'revenue_upper_80': pred_upper_80,
                    'revenue_lower_95': pred_lower_95,
                    'revenue_upper_95': pred_upper_95
                })
        
        return pd.DataFrame(predictions)

