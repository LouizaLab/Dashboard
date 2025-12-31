"""
Phase 4 Dashboard: Correlation Analysis & Behavioral Pattern Detection
Interactive dashboard for analyzing signals, correlations, and behavioral trends
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

class Phase4Dashboard:
    """
    Interactive dashboard for Phase 4 signal analysis
    """
    
    def __init__(self, 
                 signals_dir: str = 'phase4_output/signals',
                 phase3_data_path: str = 'simulations/intent_trajectories.csv',
                 phase4_data_path: str = 'simulations/phase4_anchored.csv',
                 real_data_path: str = 'data/real_intent_data.csv'):
        """
        Initialize dashboard with signal data
        
        Args:
            signals_dir: Directory containing Phase 4 signals
            phase3_data_path: Path to Phase 3 simulation data
            phase4_data_path: Path to Phase 4 anchored data
            real_data_path: Path to real data
        """
        self.signals_dir = signals_dir
        self.phase3_data_path = phase3_data_path
        self.phase4_data_path = phase4_data_path
        self.real_data_path = real_data_path
        
        # Load all signals
        self.signals = self._load_signals()
        
        # Load intent data
        self.phase3_data = self._load_data(phase3_data_path) if os.path.exists(phase3_data_path) else None
        self.phase4_data = self._load_data(phase4_data_path) if os.path.exists(phase4_data_path) else None
        self.real_data = self._load_data(real_data_path) if os.path.exists(real_data_path) else None
        
        # Compute correlations and patterns
        self.correlations = self._compute_correlations()
        self.patterns = self._detect_patterns()
        self.behavioral_insights = self._compute_behavioral_insights()
        
    def _load_signals(self) -> Dict[str, pd.DataFrame]:
        """Load all signal files"""
        signals = {}
        
        signal_files = {
            'intent_index': 'intent_index.csv',
            'momentum_7d': 'momentum_7d.csv',
            'momentum_30d': 'momentum_30d.csv',
            'trend_acceleration': 'trend_acceleration.csv',
            'forecast_30d': 'forecast_30d.csv',
            'forecast_90d': 'forecast_90d.csv',
            'substitution_matrix': 'substitution_matrix.csv',
            'price_elasticity': 'price_elasticity.csv'
        }
        
        for signal_name, filename in signal_files.items():
            filepath = os.path.join(self.signals_dir, filename)
            if os.path.exists(filepath):
                signals[signal_name] = pd.read_csv(filepath)
                # Ensure date columns are datetime
                if 'date' in signals[signal_name].columns:
                    signals[signal_name]['date'] = pd.to_datetime(signals[signal_name]['date'])
        
        return signals
    
    def _load_data(self, path: str) -> Optional[pd.DataFrame]:
        """Load intent data"""
        if not os.path.exists(path):
            return None
        
        df = pd.read_csv(path)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def _compute_correlations(self) -> pd.DataFrame:
        """Compute correlation matrix between signals"""
        # Merge signals on date and category
        merged = None
        
        # Start with intent_index as base
        if 'intent_index' in self.signals:
            merged = self.signals['intent_index'].copy()
            
            # Merge momentum signals
            if 'momentum_7d' in self.signals:
                momentum_7d = self.signals['momentum_7d'][['date', 'product_category', 'momentum']].rename(
                    columns={'momentum': 'momentum_7d'}
                )
                merged = merged.merge(momentum_7d, on=['date', 'product_category'], how='left')
            
            if 'momentum_30d' in self.signals:
                momentum_30d = self.signals['momentum_30d'][['date', 'product_category', 'momentum']].rename(
                    columns={'momentum': 'momentum_30d'}
                )
                merged = merged.merge(momentum_30d, on=['date', 'product_category'], how='left')
            
            # Merge trend acceleration
            if 'trend_acceleration' in self.signals:
                accel = self.signals['trend_acceleration'][['date', 'product_category', 'acceleration', 'velocity']]
                merged = merged.merge(accel, on=['date', 'product_category'], how='left')
        
        if merged is None or len(merged) == 0:
            return pd.DataFrame()
        
        # Compute correlation matrix
        numeric_cols = merged.select_dtypes(include=[np.number]).columns
        correlation_matrix = merged[numeric_cols].corr()
        
        return correlation_matrix
    
    def _detect_patterns(self) -> Dict:
        """Detect patterns and trends in signals"""
        patterns = {
            'strong_momentum': [],
            'trend_reversals': [],
            'acceleration_spikes': [],
            'substitution_patterns': [],
            'price_sensitivity': []
        }
        
        # Strong momentum patterns
        if 'momentum_7d' in self.signals:
            momentum = self.signals['momentum_7d']
            # Find categories with consistently strong momentum
            for cat in momentum['product_category'].unique():
                cat_momentum = momentum[momentum['product_category'] == cat]['momentum']
                if len(cat_momentum) > 0:
                    avg_momentum = cat_momentum.mean()
                    if abs(avg_momentum) > 0.01:  # Threshold
                        patterns['strong_momentum'].append({
                            'category': cat,
                            'avg_momentum': avg_momentum,
                            'trend': 'positive' if avg_momentum > 0 else 'negative'
                        })
        
        # Trend reversals (acceleration changes sign)
        if 'trend_acceleration' in self.signals:
            accel = self.signals['trend_acceleration']
            for cat in accel['product_category'].unique():
                cat_accel = accel[accel['product_category'] == cat].sort_values('date')
                if len(cat_accel) > 1:
                    accel_values = cat_accel['acceleration'].values
                    # Find sign changes
                    sign_changes = np.where(np.diff(np.sign(accel_values)) != 0)[0]
                    if len(sign_changes) > 0:
                        patterns['trend_reversals'].append({
                            'category': cat,
                            'reversal_count': len(sign_changes),
                            'dates': cat_accel.iloc[sign_changes]['date'].tolist()
                        })
        
        # Substitution patterns
        if 'substitution_matrix' in self.signals:
            sub_matrix = self.signals['substitution_matrix']
            # Find strong substitution relationships
            # Check what columns exist
            prob_col = None
            for col in ['substitution_probability', 'correlation', 'substitution_strength']:
                if col in sub_matrix.columns:
                    prob_col = col
                    break
            
            if prob_col and 'from_category' in sub_matrix.columns and 'to_category' in sub_matrix.columns:
                strong_subs = sub_matrix[
                    (sub_matrix[prob_col] > 0.3) & 
                    (sub_matrix['from_category'] != sub_matrix['to_category'])
                ]
                patterns['substitution_patterns'] = strong_subs.to_dict('records')
            elif len(sub_matrix) > 0:
                # Use all substitution pairs if no probability column
                patterns['substitution_patterns'] = sub_matrix.to_dict('records')
        
        # Price sensitivity
        if 'price_elasticity' in self.signals:
            elasticity = self.signals['price_elasticity']
            # Find highly price-sensitive categories
            # Check what columns exist
            elastic_col = None
            for col in ['elasticity', 'price_elasticity', 'elasticity_coefficient']:
                if col in elasticity.columns:
                    elastic_col = col
                    break
            
            if elastic_col:
                sensitive = elasticity[elasticity[elastic_col] < -1.0]  # Elastic
                patterns['price_sensitivity'] = sensitive.to_dict('records')
            elif len(elasticity) > 0:
                # Use all elasticity data if column name doesn't match
                patterns['price_sensitivity'] = elasticity.to_dict('records')
        
        return patterns
    
    def _compute_behavioral_insights(self) -> Dict:
        """Compute behavioral insights from calibrated data"""
        insights = {
            'segment_preferences': {},
            'category_switching': {},
            'temporal_patterns': {},
            'calibration_impact': {},
            'signal_strength': {},
            'predictive_power': {}
        }
        
        # Segment preferences (from Phase 4 data)
        if self.phase4_data is not None and 'segment_id' in self.phase4_data.columns:
            segment_prefs = self.phase4_data.groupby(['segment_id', 'product_category'])['intent_value'].mean().reset_index()
            insights['segment_preferences'] = segment_prefs.to_dict('records')
        
        # Category switching behavior
        if self.phase4_data is not None and 'agent_id' in self.phase4_data.columns:
            # Compute switching rates by category
            agent_switches = []
            for agent_id in self.phase4_data['agent_id'].unique()[:100]:  # Sample
                agent_data = self.phase4_data[
                    self.phase4_data['agent_id'] == agent_id
                ].sort_values('timestamp')
                
                if len(agent_data) > 1:
                    categories = agent_data['product_category'].values
                    switches = sum(1 for i in range(1, len(categories)) if categories[i] != categories[i-1])
                    switch_rate = switches / (len(categories) - 1) if len(categories) > 1 else 0
                    
                    agent_switches.append({
                        'agent_id': agent_id,
                        'switch_rate': switch_rate,
                        'preferred_category': agent_data['product_category'].mode()[0] if len(agent_data) > 0 else None
                    })
            
            insights['category_switching'] = pd.DataFrame(agent_switches).to_dict('records')
        
        # Temporal patterns
        if self.phase4_data is not None and 'timestamp' in self.phase4_data.columns:
            self.phase4_data['hour'] = pd.to_datetime(self.phase4_data['timestamp']).dt.hour
            hourly_intent = self.phase4_data.groupby('hour')['intent_value'].mean()
            insights['temporal_patterns'] = {
                'peak_hour': hourly_intent.idxmax(),
                'low_hour': hourly_intent.idxmin(),
                'hourly_distribution': hourly_intent.to_dict()
            }
        
        # Calibration impact (Phase 3 vs Phase 4)
        if self.phase3_data is not None and self.phase4_data is not None:
            p3_mean = self.phase3_data['intent_value'].mean()
            p4_mean = self.phase4_data['intent_value'].mean()
            real_mean = self.real_data['intent_value'].mean() if self.real_data is not None else None
            
            insights['calibration_impact'] = {
                'phase3_error': abs(p3_mean - real_mean) if real_mean else None,
                'phase4_error': abs(p4_mean - real_mean) if real_mean else None,
                'improvement_pct': ((abs(p3_mean - real_mean) - abs(p4_mean - real_mean)) / abs(p3_mean - real_mean) * 100) if real_mean and abs(p3_mean - real_mean) > 0 else None
            }
        
        # Signal strength metrics
        insights['signal_strength'] = self._compute_signal_strength()
        
        # Predictive power analysis
        insights['predictive_power'] = self._compute_predictive_power()
        
        return insights
    
    def _compute_signal_strength(self) -> Dict:
        """Compute signal strength metrics"""
        strength = {}
        
        # Momentum signal strength (volatility-normalized)
        if 'momentum_7d' in self.signals:
            momentum = self.signals['momentum_7d']
            for cat in momentum['product_category'].unique():
                cat_mom = momentum[momentum['product_category'] == cat]['momentum']
                if len(cat_mom) > 0:
                    # Signal strength = mean / std (signal-to-noise ratio)
                    signal_strength = abs(cat_mom.mean()) / cat_mom.std() if cat_mom.std() > 0 else 0
                    strength[f'momentum_7d_{cat}'] = signal_strength
        
        # Trend acceleration strength
        if 'trend_acceleration' in self.signals:
            accel = self.signals['trend_acceleration']
            for cat in accel['product_category'].unique():
                cat_accel = accel[accel['product_category'] == cat]['acceleration']
                if len(cat_accel) > 0:
                    signal_strength = abs(cat_accel.mean()) / cat_accel.std() if cat_accel.std() > 0 else 0
                    strength[f'acceleration_{cat}'] = signal_strength
        
        return strength
    
    def _compute_predictive_power(self) -> Dict:
        """Compute predictive power of signals (lead-lag correlation)"""
        power = {}
        
        # If we have sales/outcome data, compute predictive power
        if self.phase4_data is not None and 'outcome' in self.phase4_data.columns:
            # Merge signals with outcomes
            if 'intent_index' in self.signals and 'momentum_7d' in self.signals:
                intent_index = self.signals['intent_index']
                momentum = self.signals['momentum_7d']
                
                # Compute correlation between signals and future outcomes
                merged = intent_index.merge(
                    momentum[['date', 'product_category', 'momentum']],
                    on=['date', 'product_category'],
                    how='left'
                )
                
                # Merge with outcomes (shifted forward for lead-lag)
                outcomes = self.phase4_data.groupby(['date', 'product_category'])['outcome'].mean().reset_index()
                outcomes['date'] = pd.to_datetime(outcomes['date'])
                
                # Try different lags
                for lag_days in [1, 3, 7]:
                    outcomes_lagged = outcomes.copy()
                    outcomes_lagged['date'] = outcomes_lagged['date'] - timedelta(days=lag_days)
                    outcomes_lagged = outcomes_lagged.rename(columns={'outcome': f'outcome_lag_{lag_days}'})
                    
                    merged_lag = merged.merge(
                        outcomes_lagged[['date', 'product_category', f'outcome_lag_{lag_days}']],
                        on=['date', 'product_category'],
                        how='inner'
                    )
                    
                    if len(merged_lag) > 10:
                        # Correlation between intent and future outcome
                        intent_corr = merged_lag['intent_mean'].corr(merged_lag[f'outcome_lag_{lag_days}'])
                        momentum_corr = merged_lag['momentum'].corr(merged_lag[f'outcome_lag_{lag_days}']) if 'momentum' in merged_lag.columns else None
                        
                        power[f'intent_predictive_power_{lag_days}d'] = intent_corr
                        if momentum_corr is not None:
                            power[f'momentum_predictive_power_{lag_days}d'] = momentum_corr
        
        return power
    
    def create_correlation_heatmap(self) -> go.Figure:
        """Create correlation heatmap of signals"""
        if len(self.correlations) == 0:
            return go.Figure()
        
        fig = go.Figure(data=go.Heatmap(
            z=self.correlations.values,
            x=self.correlations.columns,
            y=self.correlations.index,
            colorscale='RdBu',
            zmid=0,
            text=np.round(self.correlations.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title='Signal Correlation Matrix',
            xaxis_title='Signal',
            yaxis_title='Signal',
            height=600,
            width=800
        )
        
        return fig
    
    def create_pattern_detection_chart(self) -> go.Figure:
        """Create chart showing detected patterns"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Strong Momentum', 'Trend Reversals', 'Substitution Patterns', 'Price Sensitivity'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Strong momentum
        if self.patterns['strong_momentum']:
            momentum_df = pd.DataFrame(self.patterns['strong_momentum'])
            fig.add_trace(
                go.Bar(
                    x=momentum_df['category'],
                    y=momentum_df['avg_momentum'],
                    marker_color=['green' if m > 0 else 'red' for m in momentum_df['avg_momentum']],
                    name='Momentum'
                ),
                row=1, col=1
            )
        
        # Trend reversals
        if self.patterns['trend_reversals']:
            reversals_df = pd.DataFrame(self.patterns['trend_reversals'])
            fig.add_trace(
                go.Bar(
                    x=reversals_df['category'],
                    y=reversals_df['reversal_count'],
                    marker_color='orange',
                    name='Reversals'
                ),
                row=1, col=2
            )
        
        # Substitution patterns (top 10)
        if self.patterns['substitution_patterns']:
            sub_df = pd.DataFrame(self.patterns['substitution_patterns'])
            # Find probability/correlation column
            prob_col = None
            for col in ['substitution_probability', 'correlation', 'substitution_strength']:
                if col in sub_df.columns:
                    prob_col = col
                    break
            
            if prob_col:
                top_subs = sub_df.nlargest(10, prob_col)
                label_cols = ['from_category', 'to_category']
                if all(col in sub_df.columns for col in label_cols):
                    fig.add_trace(
                        go.Bar(
                            x=[f"{row['from_category']} → {row['to_category']}" for _, row in top_subs.iterrows()],
                            y=top_subs[prob_col],
                            marker_color='blue',
                            name='Substitution'
                        ),
                        row=2, col=1
                    )
        
        # Price sensitivity
        if self.patterns['price_sensitivity']:
            price_df = pd.DataFrame(self.patterns['price_sensitivity'])
            # Find elasticity column
            elastic_col = None
            for col in ['elasticity', 'price_elasticity', 'elasticity_coefficient']:
                if col in price_df.columns:
                    elastic_col = col
                    break
            
            if elastic_col and 'product_category' in price_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=price_df['product_category'],
                        y=price_df[elastic_col],
                        marker_color='purple',
                        name='Elasticity'
                    ),
                    row=2, col=2
                )
        
        fig.update_layout(
            title='Detected Patterns & Trends',
            height=800,
            showlegend=False
        )
        
        return fig
    
    def create_behavioral_insights_chart(self) -> go.Figure:
        """Create behavioral insights visualization"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Segment Preferences', 'Category Switching Rates', 'Temporal Patterns', 'Calibration Impact', 'Signal Strength', 'Predictive Power'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Segment preferences
        if self.behavioral_insights['segment_preferences']:
            seg_prefs = pd.DataFrame(self.behavioral_insights['segment_preferences'])
            top_cats = seg_prefs.groupby('product_category')['intent_value'].mean().nlargest(7)
            fig.add_trace(
                go.Bar(
                    x=top_cats.index,
                    y=top_cats.values,
                    marker_color='steelblue',
                    name='Avg Intent'
                ),
                row=1, col=1
            )
        
        # Category switching rates
        if self.behavioral_insights['category_switching']:
            switch_df = pd.DataFrame(self.behavioral_insights['category_switching'])
            fig.add_trace(
                go.Histogram(
                    x=switch_df['switch_rate'],
                    nbinsx=20,
                    marker_color='coral',
                    name='Switch Rate'
                ),
                row=1, col=2
            )
        
        # Temporal patterns
        if self.behavioral_insights['temporal_patterns'] and 'hourly_distribution' in self.behavioral_insights['temporal_patterns']:
            hourly = self.behavioral_insights['temporal_patterns']['hourly_distribution']
            fig.add_trace(
                go.Bar(
                    x=list(hourly.keys()),
                    y=list(hourly.values()),
                    marker_color='lightgreen',
                    name='Hourly Intent'
                ),
                row=2, col=1
            )
        
        # Calibration impact
        if self.behavioral_insights['calibration_impact']:
            calib = self.behavioral_insights['calibration_impact']
            if calib['phase3_error'] and calib['phase4_error']:
                fig.add_trace(
                    go.Bar(
                        x=['Phase 3 Error', 'Phase 4 Error'],
                        y=[calib['phase3_error'], calib['phase4_error']],
                        marker_color=['red', 'green'],
                        name='Error'
                    ),
                    row=2, col=2
                )
        
        # Signal strength
        if self.behavioral_insights['signal_strength']:
            strength = self.behavioral_insights['signal_strength']
            if strength:
                strength_df = pd.DataFrame([{'signal': k, 'strength': v} for k, v in strength.items()])
                top_strength = strength_df.nlargest(10, 'strength')
                fig.add_trace(
                    go.Bar(
                        x=top_strength['signal'],
                        y=top_strength['strength'],
                        marker_color='purple',
                        name='Signal Strength'
                    ),
                    row=3, col=1
                )
        
        # Predictive power
        if self.behavioral_insights['predictive_power']:
            power = self.behavioral_insights['predictive_power']
            if power:
                power_df = pd.DataFrame([{'metric': k, 'correlation': v} for k, v in power.items()])
                fig.add_trace(
                    go.Bar(
                        x=power_df['metric'],
                        y=power_df['correlation'],
                        marker_color='orange',
                        name='Predictive Power'
                    ),
                    row=3, col=2
                )
        
        fig.update_layout(
            title='Behavioral Insights After Calibration',
            height=1200,
            showlegend=False
        )
        
        return fig
    
    def create_signal_timeseries(self, category: Optional[str] = None) -> go.Figure:
        """Create time series of signals for a category"""
        if 'intent_index' not in self.signals:
            return go.Figure()
        
        intent_data = self.signals['intent_index']
        if category:
            intent_data = intent_data[intent_data['product_category'] == category]
        
        fig = go.Figure()
        
        # Intent index
        for cat in intent_data['product_category'].unique():
            cat_data = intent_data[intent_data['product_category'] == cat].sort_values('date')
            fig.add_trace(go.Scatter(
                x=cat_data['date'],
                y=cat_data['intent_mean'],
                mode='lines+markers',
                name=f'{cat} - Intent',
                line=dict(width=2)
            ))
        
        # Add momentum overlay if available
        if 'momentum_7d' in self.signals:
            momentum = self.signals['momentum_7d']
            if category:
                momentum = momentum[momentum['product_category'] == category]
            
            for cat in momentum['product_category'].unique():
                cat_mom = momentum[momentum['product_category'] == cat].sort_values('date')
                fig.add_trace(go.Scatter(
                    x=cat_mom['date'],
                    y=cat_mom['momentum'] * 10 + 0.5,  # Scale for visibility
                    mode='lines',
                    name=f'{cat} - Momentum (scaled)',
                    line=dict(dash='dash', width=1),
                    yaxis='y2'
                ))
        
        fig.update_layout(
            title=f'Signal Time Series{" - " + category if category else ""}',
            xaxis_title='Date',
            yaxis_title='Intent Index',
            yaxis2=dict(title='Momentum (scaled)', overlaying='y', side='right'),
            height=600,
            hovermode='x unified'
        )
        
        return fig
    
    def generate_dashboard_html(self, output_path: str = 'phase4_output/dashboard.html'):
        """Generate standalone HTML dashboard"""
        # Create all visualizations
        corr_fig = self.create_correlation_heatmap()
        pattern_fig = self.create_pattern_detection_chart()
        behavioral_fig = self.create_behavioral_insights_chart()
        timeseries_fig = self.create_signal_timeseries()
        
        # Combine into HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phase 4 Behavioral Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .section {{
                    background-color: white;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1, h2 {{
                    margin-top: 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Phase 4 Behavioral Dashboard</h1>
                <p>Signal Correlation Analysis & Pattern Detection</p>
            </div>
            
            <div class="section">
                <h2>Signal Correlations</h2>
                <div id="correlation-chart"></div>
            </div>
            
            <div class="section">
                <h2>Detected Patterns & Trends</h2>
                <div id="pattern-chart"></div>
            </div>
            
            <div class="section">
                <h2>Behavioral Insights</h2>
                <div id="behavioral-chart"></div>
            </div>
            
            <div class="section">
                <h2>Signal Time Series</h2>
                <div id="timeseries-chart"></div>
            </div>
            
            <script>
                var corrData = {corr_fig.to_json()};
                var patternData = {pattern_fig.to_json()};
                var behavioralData = {behavioral_fig.to_json()};
                var timeseriesData = {timeseries_fig.to_json()};
                
                Plotly.newPlot('correlation-chart', corrData.data, corrData.layout);
                Plotly.newPlot('pattern-chart', patternData.data, patternData.layout);
                Plotly.newPlot('behavioral-chart', behavioralData.data, behavioralData.layout);
                Plotly.newPlot('timeseries-chart', timeseriesData.data, timeseriesData.layout);
            </script>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Dashboard saved to {output_path}")


def create_interactive_dashboard():
    """Create interactive Dash dashboard"""
    app = dash.Dash(__name__)
    
    # Initialize dashboard
    dashboard = Phase4Dashboard()
    
    app.layout = html.Div([
        html.H1("Phase 4 Behavioral Dashboard", style={'textAlign': 'center'}),
        html.Hr(),
        
        html.Div([
            html.H2("Signal Correlations"),
            dcc.Graph(figure=dashboard.create_correlation_heatmap())
        ]),
        
        html.Div([
            html.H2("Detected Patterns & Trends"),
            dcc.Graph(figure=dashboard.create_pattern_detection_chart())
        ]),
        
        html.Div([
            html.H2("Behavioral Insights"),
            dcc.Graph(figure=dashboard.create_behavioral_insights_chart())
        ]),
        
        html.Div([
            html.H2("Signal Time Series"),
            dcc.Dropdown(
                id='category-selector',
                options=[{'label': 'All Categories', 'value': None}] + 
                        [{'label': cat, 'value': cat} for cat in dashboard.signals.get('intent_index', pd.DataFrame())['product_category'].unique() if pd.notna(cat)],
                value=None,
                style={'width': '300px', 'margin': '10px'}
            ),
            dcc.Graph(id='timeseries-graph')
        ])
    ])
    
    @app.callback(
        Output('timeseries-graph', 'figure'),
        Input('category-selector', 'value')
    )
    def update_timeseries(category):
        return dashboard.create_signal_timeseries(category)
    
    return app


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        # Launch interactive Dash app
        app = create_interactive_dashboard()
        app.run_server(debug=True, port=8050)
    else:
        # Generate static HTML dashboard
        dashboard = Phase4Dashboard()
        dashboard.generate_dashboard_html()
        print("\n✅ Dashboard generated!")
        print("   Open phase4_output/dashboard.html in your browser")
        print("\n   For interactive dashboard, run:")
        print("   python phase4_dashboard.py interactive")

