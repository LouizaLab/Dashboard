"""
Insight generation for dashboard
Auto-generates insight cards from data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


def generate_insights(trajectories_df: pd.DataFrame,
                     intent_logs_df: pd.DataFrame,
                     intent_index_df: pd.DataFrame,
                     momentum_df: pd.DataFrame,
                     selected_segments: List[str],
                     selected_contexts: List[str],
                     time_range: Tuple[int, int]) -> List[Dict]:
    """
    Generate 5-10 insight cards automatically
    Returns list of insight dictionaries
    """
    insights = []
    
    # Filter data
    filtered_traj = trajectories_df[
        trajectories_df['segment_id'].isin(selected_segments)
    ].copy() if not trajectories_df.empty else pd.DataFrame()
    
    # Insight 1: Biggest week-over-week change
    if not intent_index_df.empty and 'date' in intent_index_df.columns:
        intent_index_df['date'] = pd.to_datetime(intent_index_df['date'])
        intent_index_df = intent_index_df.sort_values('date')
        
        # Handle both 'category' and 'product_category' column names
        cat_col = 'product_category' if 'product_category' in intent_index_df.columns else 'category'
        
        if cat_col in intent_index_df.columns:
            # Compute week-over-week change
            intent_index_df['week'] = intent_index_df['date'].dt.isocalendar().week
            weekly_avg = intent_index_df.groupby(['week', cat_col])['intent_mean'].mean().reset_index()
        
            if len(weekly_avg) > 1:
                weekly_pivot = weekly_avg.pivot(index='week', columns=cat_col, values='intent_mean')
                wow_changes = weekly_pivot.diff().iloc[-1] if len(weekly_pivot) > 1 else pd.Series()
                
                if len(wow_changes) > 0:
                    biggest_change = wow_changes.abs().idxmax()
                    change_value = wow_changes[biggest_change]
                    
                    insights.append({
                        'title': f'Biggest Week-over-Week Change',
                        'value': f'{change_value:+.3f}',
                        'description': f'{biggest_change} intent changed by {change_value:+.3f} points',
                        'type': 'delta',
                        'category': biggest_change
                    })
    
    # Insight 2: Segment-context interaction strength
    if not filtered_traj.empty and 'context_id' in filtered_traj.columns:
        seg_context = filtered_traj.groupby(['segment_id', 'context_id'])['intent_value'].mean().reset_index()
        
        if len(seg_context) > 0:
            # Compute variance across contexts per segment (higher = context matters more)
            context_variance = seg_context.groupby('segment_id')['intent_value'].std()
            
            if len(context_variance) > 0:
                max_variance_seg = context_variance.idxmax()
                max_variance = context_variance.max()
                
                insights.append({
                    'title': 'Context Matters More Than Segment',
                    'value': f'{max_variance:.3f}',
                    'description': f'Segment {max_variance_seg} shows {max_variance:.3f} std dev across contexts',
                    'type': 'interaction',
                    'segment': max_variance_seg
                })
    
    # Insight 3: Price sensitivity breakpoint
    if not filtered_traj.empty and 'price' in filtered_traj.columns:
        # Find price threshold where intent drops significantly
        price_bins = pd.cut(filtered_traj['price'], bins=5)
        price_intent = filtered_traj.groupby(price_bins)['intent_value'].mean()
        
        if len(price_intent) > 1:
            price_drops = price_intent.diff()
            biggest_drop = price_drops.idxmin()
            
            insights.append({
                'title': 'Price Sensitivity Breakpoint',
                'value': f'{biggest_drop}',
                'description': f'Intent drops most at price range {biggest_drop}',
                'type': 'price',
                'breakpoint': str(biggest_drop)
            })
    
    # Insight 4: Repeat purchase lift after N exposures
    if not filtered_traj.empty and 'agent_id' in filtered_traj.columns:
        # Compute repeat rate by exposure count
        agent_exposures = filtered_traj.groupby('agent_id').size()
        agent_repeats = []
        
        for agent_id in filtered_traj['agent_id'].unique()[:100]:  # Sample
            agent_data = filtered_traj[filtered_traj['agent_id'] == agent_id].sort_values('timestamp' if 'timestamp' in filtered_traj.columns else 'date')
            if len(agent_data) > 1:
                products = agent_data['product_id'].values
                repeats = sum(1 for i in range(1, len(products)) if products[i] == products[i-1])
                agent_repeats.append({
                    'agent_id': agent_id,
                    'exposures': len(agent_data),
                    'repeats': repeats,
                    'repeat_rate': repeats / (len(products) - 1) if len(products) > 1 else 0
                })
        
        if agent_repeats:
            repeat_df = pd.DataFrame(agent_repeats)
            repeat_df['exposure_bin'] = pd.cut(repeat_df['exposures'], bins=3, labels=['Low', 'Mid', 'High'])
            exposure_lift = repeat_df.groupby('exposure_bin')['repeat_rate'].mean()
            
            if len(exposure_lift) > 1:
                lift = exposure_lift['High'] - exposure_lift['Low']
                
                insights.append({
                    'title': 'Repeat Purchase Lift',
                    'value': f'{lift:+.1%}',
                    'description': f'High exposure shows {lift:+.1%} higher repeat rate vs low exposure',
                    'type': 'repeat',
                    'lift': lift
                })
    
    # Insight 5: Momentum trend
    if not momentum_df.empty and 'momentum' in momentum_df.columns:
        # Handle both 'category' and 'product_category' column names
        cat_col_mom = 'product_category' if 'product_category' in momentum_df.columns else 'category'
        
        if cat_col_mom in momentum_df.columns:
            latest_momentum = momentum_df.groupby(cat_col_mom)['momentum'].last()
            
            if len(latest_momentum) > 0:
                strongest_momentum = latest_momentum.abs().idxmax()
                momentum_value = latest_momentum[strongest_momentum]
                
                insights.append({
                    'title': 'Strongest Momentum Trend',
                    'value': f'{momentum_value:+.3f}',
                    'description': f'{strongest_momentum} shows strongest momentum ({momentum_value:+.3f})',
                    'type': 'momentum',
                    'category': strongest_momentum
                })
    
    # Insight 6: Category switching pattern
    # Handle both 'category' and 'product_category' column names
    cat_col_traj = 'product_category' if 'product_category' in filtered_traj.columns else 'category'
    if not filtered_traj.empty and cat_col_traj in filtered_traj.columns:
        # Find most common category switches
        switches = []
        for agent_id in filtered_traj['agent_id'].unique()[:100]:
            agent_data = filtered_traj[filtered_traj['agent_id'] == agent_id].sort_values('timestamp' if 'timestamp' in filtered_traj.columns else 'date')
            if len(agent_data) > 1:
                categories = agent_data[cat_col_traj].values
                for i in range(1, len(categories)):
                    if categories[i] != categories[i-1]:
                        switches.append({
                            'from': categories[i-1],
                            'to': categories[i]
                        })
        
        if switches:
            switch_df = pd.DataFrame(switches)
            top_switch = switch_df.groupby(['from', 'to']).size().idxmax()
            switch_count = switch_df.groupby(['from', 'to']).size().max()
            
            insights.append({
                'title': 'Most Common Category Switch',
                'value': f'{switch_count}',
                'description': f'{top_switch[0]} → {top_switch[1]} ({switch_count} switches)',
                'type': 'switching',
                'from': top_switch[0],
                'to': top_switch[1]
            })
    
    # Insight 7: Temporal pattern
    if not filtered_traj.empty and 'timestamp' in filtered_traj.columns:
        filtered_traj['hour'] = pd.to_datetime(filtered_traj['timestamp']).dt.hour
        hourly_intent = filtered_traj.groupby('hour')['intent_value'].mean()
        
        if len(hourly_intent) > 0:
            peak_hour = hourly_intent.idxmax()
            peak_value = hourly_intent.max()
            
            insights.append({
                'title': 'Peak Consumption Hour',
                'value': f'{peak_hour}:00',
                'description': f'Hour {peak_hour} shows highest intent ({peak_value:.3f})',
                'type': 'temporal',
                'hour': peak_hour
            })
    
    # Insight 8: Segment preference divergence
    if not filtered_traj.empty:
        seg_prefs = filtered_traj.groupby('segment_id')['intent_value'].mean()
        
        if len(seg_prefs) > 1:
            max_pref = seg_prefs.max()
            min_pref = seg_prefs.min()
            divergence = max_pref - min_pref
            
            insights.append({
                'title': 'Segment Preference Divergence',
                'value': f'{divergence:.3f}',
                'description': f'Segments differ by {divergence:.3f} points in average intent',
                'type': 'divergence',
                'range': divergence
            })
    
    # Return top 10 insights
    return insights[:10]

