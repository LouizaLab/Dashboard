"""
Helper script to generate synthetic sales data for Phase 4.2 validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sales_from_intent(intent_data: pd.DataFrame,
                               base_sales_per_intent: float = 1000.0,
                               noise_level: float = 0.2,
                               lag_days: int = 7) -> pd.DataFrame:
    """
    Generate synthetic sales data from intent data
    
    Args:
        intent_data: DataFrame with intent values (must have product_category, date/timestamp, intent_value)
        base_sales_per_intent: Base sales multiplier
        noise_level: Noise level (0-1)
        lag_days: Days between intent and sales (intent leads sales)
        
    Returns:
        DataFrame with sales data
    """
    sales_data = intent_data.copy()
    
    # Ensure date column
    if 'date' not in sales_data.columns and 'timestamp' in sales_data.columns:
        sales_data['date'] = pd.to_datetime(sales_data['timestamp']).dt.date
    elif 'timestamp' in sales_data.columns:
        sales_data['date'] = pd.to_datetime(sales_data['timestamp']).dt.date
    
    # Aggregate intent by category and date
    if 'product_category' in sales_data.columns:
        intent_agg = sales_data.groupby(['date', 'product_category'])['intent_value'].mean().reset_index()
    else:
        intent_agg = sales_data.groupby('date')['intent_value'].mean().reset_index()
        intent_agg['product_category'] = 'all'
    
    # Shift dates forward by lag_days (intent leads sales)
    intent_agg['sales_date'] = pd.to_datetime(intent_agg['date']) + timedelta(days=lag_days)
    intent_agg['sales_date'] = intent_agg['sales_date'].dt.date
    
    # Generate sales from intent
    # Sales = base * intent * (1 + noise)
    sales_values = []
    for _, row in intent_agg.iterrows():
        base_sales = base_sales_per_intent * row['intent_value']
        noise = np.random.normal(1.0, noise_level)
        sales = max(0, base_sales * noise)  # Ensure non-negative
        sales_values.append(sales)
    
    intent_agg['sales_value'] = sales_values
    
    # Create sales DataFrame
    sales_df = pd.DataFrame({
        'date': intent_agg['sales_date'],
        'product_category': intent_agg['product_category'],
        'sales_value': intent_agg['sales_value']
    })
    
    return sales_df


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_sales_data.py <intent_data.csv> [output.csv]")
        sys.exit(1)
    
    intent_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'data/sales_data.csv'
    
    print(f"Loading intent data from {intent_path}...")
    intent_data = pd.read_csv(intent_path)
    
    print("Generating sales data...")
    sales_data = generate_sales_from_intent(intent_data, lag_days=7)
    
    print(f"Saving sales data to {output_path}...")
    sales_data.to_csv(output_path, index=False)
    print(f"Generated {len(sales_data)} sales records")


