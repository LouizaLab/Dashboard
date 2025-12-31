"""
Metrics computation for dashboard
Aggregates behavioral metrics from data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def compute_taste_profile(products_df: pd.DataFrame, 
                         segments_df: pd.DataFrame,
                         intent_logs_df: pd.DataFrame,
                         selected_segments: List[str]) -> pd.DataFrame:
    """
    Compute baseline taste/preference metrics per segment
    Returns DataFrame with segment preferences
    """
    if intent_logs_df.empty or segments_df.empty:
        return pd.DataFrame()
    
    # Filter by selected segments
    filtered_logs = intent_logs_df[
        intent_logs_df['segment_id'].isin(selected_segments)
    ].copy()
    
    if filtered_logs.empty:
        return pd.DataFrame()
    
    # Merge with products to get product attributes
    if not products_df.empty and 'product_id' in filtered_logs.columns:
        # Handle both 'category' and 'product_category' column names
        product_cols = ['product_id', 'sugar_g', 'caffeine_mg', 'price']
        if 'product_category' in products_df.columns:
            product_cols.append('product_category')
        elif 'category' in products_df.columns:
            product_cols.append('category')
            # Rename to product_category for consistency
            products_df = products_df.rename(columns={'category': 'product_category'})
        
        # Only include columns that exist
        available_cols = [col for col in product_cols if col in products_df.columns]
        filtered_logs = filtered_logs.merge(
            products_df[available_cols],
            on='product_id',
            how='left'
        )
    
    # Aggregate by segment
    metrics = []
    for seg_id in selected_segments:
        seg_data = filtered_logs[filtered_logs['segment_id'] == seg_id]
        
        if seg_data.empty:
            continue
        
        # Compute preference metrics
        avg_intent = seg_data['preference_value'].mean() if 'preference_value' in seg_data.columns else seg_data['intent_value'].mean() if 'intent_value' in seg_data.columns else 0
        
        # Sugar preference (weighted by intent)
        if 'sugar_g' in seg_data.columns:
            sugar_pref = (seg_data['sugar_g'] * seg_data.get('preference_value', seg_data.get('intent_value', 1))).sum() / seg_data.get('preference_value', seg_data.get('intent_value', 1)).sum() if seg_data.get('preference_value', seg_data.get('intent_value', 1)).sum() > 0 else 0
        else:
            sugar_pref = 0
        
        # Caffeine tolerance
        if 'caffeine_mg' in seg_data.columns:
            caffeine_pref = (seg_data['caffeine_mg'] * seg_data.get('preference_value', seg_data.get('intent_value', 1))).sum() / seg_data.get('preference_value', seg_data.get('intent_value', 1)).sum() if seg_data.get('preference_value', seg_data.get('intent_value', 1)).sum() > 0 else 0
        else:
            caffeine_pref = 0
        
        # Price sensitivity (inverse of avg price preference)
        if 'price' in seg_data.columns:
            price_pref = seg_data['price'].mean()
            price_sensitivity = 1 / (price_pref + 1)  # Higher price = lower sensitivity
        else:
            price_sensitivity = 0.5
        
        # Category preferences (handle both 'category' and 'product_category')
        cat_col = None
        if 'product_category' in seg_data.columns:
            cat_col = 'product_category'
        elif 'category' in seg_data.columns:
            cat_col = 'category'
        
        top_category = None
        if cat_col:
            pref_col = 'preference_value' if 'preference_value' in seg_data.columns else ('intent_value' if 'intent_value' in seg_data.columns else None)
            if pref_col:
                cat_prefs = seg_data.groupby(cat_col)[pref_col].mean()
                top_category = cat_prefs.idxmax() if len(cat_prefs) > 0 else None
        
        metrics.append({
            'segment_id': seg_id,
            'avg_intent': avg_intent,
            'sugar_preference': sugar_pref,
            'caffeine_tolerance': caffeine_pref,
            'price_sensitivity': price_sensitivity,
            'top_category': top_category
        })
    
    return pd.DataFrame(metrics)


def compute_behavioral_dynamics(trajectories_df: pd.DataFrame,
                               selected_segments: List[str],
                               selected_contexts: Optional[List[str]] = None,
                               time_range: Tuple[int, int] = (0, 90)) -> pd.DataFrame:
    """
    Compute behavioral metrics over time
    Returns time series of metrics
    """
    if trajectories_df.empty:
        return pd.DataFrame()
    
    # Filter by segments
    filtered = trajectories_df[
        trajectories_df['segment_id'].isin(selected_segments)
    ].copy()
    
    if filtered.empty:
        return pd.DataFrame()
    
    # Filter by time range (if time_step or date available)
    if 'time_step' in filtered.columns:
        filtered = filtered[
            (filtered['time_step'] >= time_range[0]) & 
            (filtered['time_step'] <= time_range[1])
        ]
    elif 'date' in filtered.columns:
        # Convert date range to dates
        start_date = pd.to_datetime('2024-01-01') + pd.Timedelta(days=time_range[0])
        end_date = pd.to_datetime('2024-01-01') + pd.Timedelta(days=time_range[1])
        filtered['date'] = pd.to_datetime(filtered['date'])
        filtered = filtered[
            (filtered['date'] >= start_date) & 
            (filtered['date'] <= end_date)
        ]
    
    # Filter by contexts if provided
    if selected_contexts and 'context_id' in filtered.columns:
        # Map context IDs if needed
        filtered = filtered[filtered['context_id'].isin(selected_contexts)]
    
    # Group by time and compute metrics
    time_col = 'time_step' if 'time_step' in filtered.columns else 'date'
    
    metrics = []
    for time_val in sorted(filtered[time_col].unique()):
        time_data = filtered[filtered[time_col] == time_val]
        
        # Purchase probability (intent value)
        purchase_prob = time_data['intent_value'].mean() if 'intent_value' in time_data.columns else 0
        
        # Repeat rate (same product as previous)
        if 'agent_id' in time_data.columns and 'product_id' in time_data.columns:
            # For each agent, check if they repeated
            repeats = 0
            total = 0
            for agent_id in time_data['agent_id'].unique():
                agent_data = time_data[time_data['agent_id'] == agent_id].sort_values('timestamp' if 'timestamp' in time_data.columns else time_col)
                if len(agent_data) > 1:
                    products = agent_data['product_id'].values
                    for i in range(1, len(products)):
                        if products[i] == products[i-1]:
                            repeats += 1
                        total += 1
            repeat_rate = repeats / total if total > 0 else 0
        else:
            repeat_rate = 0
        
        # Churn (low intent)
        churn_rate = (time_data['intent_value'] < 0.3).mean() if 'intent_value' in time_data.columns else 0
        
        # Adoption (new product trial)
        if 'agent_id' in time_data.columns and 'product_id' in time_data.columns:
            # Count unique products per agent (proxy for adoption)
            adoption_rate = time_data.groupby('agent_id')['product_id'].nunique().mean() if len(time_data) > 0 else 0
        else:
            adoption_rate = 0
        
        metrics.append({
            time_col: time_val,
            'purchase_probability': purchase_prob,
            'repeat_rate': repeat_rate,
            'churn_rate': churn_rate,
            'adoption_rate': adoption_rate
        })
    
    return pd.DataFrame(metrics)


def compute_segment_context_interaction(intent_logs_df: pd.DataFrame,
                                       trajectories_df: pd.DataFrame,
                                       selected_segments: List[str]) -> pd.DataFrame:
    """
    Compute segment-context interaction effects
    """
    # Use trajectories if available, otherwise intent_logs
    data = trajectories_df if not trajectories_df.empty else intent_logs_df
    
    if data.empty:
        return pd.DataFrame()
    
    filtered = data[data['segment_id'].isin(selected_segments)].copy()
    
    if filtered.empty or 'context_id' not in filtered.columns:
        return pd.DataFrame()
    
    # Group by segment and context
    interaction = filtered.groupby(['segment_id', 'context_id']).agg({
        'intent_value': 'mean' if 'intent_value' in filtered.columns else 'preference_value'
    }).reset_index()
    
    return interaction

