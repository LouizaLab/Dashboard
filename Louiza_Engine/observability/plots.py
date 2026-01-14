"""
Visualization functions for Louiza Engine observability.

All plots are derived from logged artifacts - no numbers are invented.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json


class PlotGenerator:
    """
    Generator for all Louiza Engine visualizations.
    
    All plots load from saved artifacts and correspond to system invariants.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize plot generator.
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_data_engine_sanity(self, observed_metrics: pd.DataFrame, price_schedule: pd.DataFrame, promo_schedule: pd.DataFrame):
        """
        Plot Data Engine sanity checks.
        
        Shows transactions/revenue over time and price/promo schedules.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Data Engine: Synthetic Data Sanity Checks', fontsize=16)
        
        # Transactions over time by brand
        ax = axes[0, 0]
        for brand_id in observed_metrics['brand_id'].unique()[:5]:  # Limit to 5 brands
            brand_data = observed_metrics[observed_metrics['brand_id'] == brand_id]
            brand_data = brand_data.groupby('week_id')['transactions_obs'].sum().reset_index()
            ax.plot(brand_data['week_id'], brand_data['transactions_obs'], label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Transactions')
        ax.set_title('Transactions Over Time (by Brand)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Revenue over time
        ax = axes[0, 1]
        revenue_by_week = observed_metrics.groupby('week_id')['revenue_obs'].sum().reset_index()
        ax.plot(revenue_by_week['week_id'], revenue_by_week['revenue_obs'], marker='o', color='green')
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Revenue')
        ax.set_title('Total Revenue Over Time')
        ax.grid(True, alpha=0.3)
        
        # Price schedule
        ax = axes[1, 0]
        for brand_id in price_schedule['brand_id'].unique()[:5]:
            brand_prices = price_schedule[price_schedule['brand_id'] == brand_id]
            brand_prices = brand_prices.groupby('week_id')['price_index'].mean().reset_index()
            ax.plot(brand_prices['week_id'], brand_prices['price_index'], label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Price Index')
        ax.set_title('Price Schedule (by Brand)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Promo schedule
        ax = axes[1, 1]
        for brand_id in promo_schedule['brand_id'].unique()[:5]:
            brand_promos = promo_schedule[promo_schedule['brand_id'] == brand_id]
            brand_promos = brand_promos.groupby('week_id')['promo_intensity'].mean().reset_index()
            ax.plot(brand_promos['week_id'], brand_promos['promo_intensity'], label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Promo Intensity')
        ax.set_title('Promotion Schedule (by Brand)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'data_engine_sanity_checks.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_data_coverage(self, observed_metrics: pd.DataFrame):
        """Plot data coverage heatmap."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('Data Engine: Data Coverage', fontsize=16)
        
        # Week × Region availability heatmap
        ax = axes[0]
        coverage = observed_metrics.groupby(['week_id', 'region_id']).size().reset_index(name='count')
        pivot = coverage.pivot(index='week_id', columns='region_id', values='count')
        im = ax.imshow(pivot.values, aspect='auto', cmap='YlGn', interpolation='nearest')
        ax.set_xlabel('Region')
        ax.set_ylabel('Week ID')
        ax.set_title('Data Availability Heatmap (Week × Region)')
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
        plt.colorbar(im, ax=ax)
        
        # Confidence weight distribution
        ax = axes[1]
        if 'confidence_weight' in observed_metrics.columns:
            ax.hist(observed_metrics['confidence_weight'], bins=20, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Confidence Weight')
            ax.set_ylabel('Frequency')
            ax.set_title('Confidence Weight Distribution')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'data_coverage.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_persona_overview(self, personaset_path: str):
        """Plot persona overview panel."""
        import json
        with open(personaset_path, 'r') as f:
            personaset_data = json.load(f)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('PME: Persona Overview', fontsize=16)
        
        # Persona population weights
        ax = axes[0]
        personas = personaset_data['personas']
        active_personas = [p for p in personas if p['status'] == 'active']
        persona_ids = [p['persona_id'] for p in active_personas]
        weights = [p['population_weight']['global_weight'] for p in active_personas]
        
        bars = ax.bar(range(len(persona_ids)), weights, color=plt.cm.viridis(np.linspace(0, 1, len(persona_ids))))
        ax.set_xlabel('Persona')
        ax.set_ylabel('Population Weight')
        ax.set_title('Persona Population Weights')
        ax.set_xticks(range(len(persona_ids)))
        ax.set_xticklabels([pid.split('_')[-1][:15] for pid in persona_ids], rotation=45, ha='right')
        ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Sum = 1.0')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (bar, weight) in enumerate(zip(bars, weights)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{weight:.3f}', ha='center', va='bottom', fontsize=8)
        
        # Persona behavioral parameters comparison
        ax = axes[1]
        price_sens = [p['behavioral_params']['price_sensitivity'] for p in active_personas]
        promo_resp = [p['behavioral_params']['promo_responsiveness'] for p in active_personas]
        
        x = np.arange(len(persona_ids))
        width = 0.35
        ax.bar(x - width/2, price_sens, width, label='Price Sensitivity', alpha=0.8)
        ax.bar(x + width/2, promo_resp, width, label='Promo Responsiveness', alpha=0.8)
        ax.set_xlabel('Persona')
        ax.set_ylabel('Parameter Value')
        ax.set_title('Behavioral Parameters Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([pid.split('_')[-1][:15] for pid in persona_ids], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'persona_overview.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_lpm_outcomes(self, simulated_metrics: pd.DataFrame):
        """Plot LPM population outcomes."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('LPM: Population Outcome Dashboard', fontsize=16)
        
        # Transactions by brand over time
        ax = axes[0, 0]
        for brand_id in simulated_metrics['brand_id'].unique()[:5]:
            brand_data = simulated_metrics[simulated_metrics['brand_id'] == brand_id]
            brand_data = brand_data.groupby('week_id')['transactions_sim'].sum().reset_index()
            ax.plot(brand_data['week_id'], brand_data['transactions_sim'], label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Transactions')
        ax.set_title('Transactions by Brand Over Time')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Revenue by brand over time
        ax = axes[0, 1]
        for brand_id in simulated_metrics['brand_id'].unique()[:5]:
            brand_data = simulated_metrics[simulated_metrics['brand_id'] == brand_id]
            brand_data = brand_data.groupby('week_id')['revenue_sim'].sum().reset_index()
            ax.plot(brand_data['week_id'], brand_data['revenue_sim'], label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Revenue')
        ax.set_title('Revenue by Brand Over Time')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Market share evolution
        ax = axes[1, 0]
        total_by_week = simulated_metrics.groupby('week_id')['transactions_sim'].sum().reset_index()
        for brand_id in simulated_metrics['brand_id'].unique()[:5]:
            brand_data = simulated_metrics[simulated_metrics['brand_id'] == brand_id]
            brand_data = brand_data.groupby('week_id')['transactions_sim'].sum().reset_index()
            merged = pd.merge(brand_data, total_by_week, on='week_id', suffixes=('_brand', '_total'))
            market_share = (merged['transactions_sim_brand'] / merged['transactions_sim_total']) * 100
            ax.plot(brand_data['week_id'], market_share, label=brand_id, marker='o', markersize=3)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Market Share (%)')
        ax.set_title('Market Share Evolution')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Total transactions over time
        ax = axes[1, 1]
        total_transactions = simulated_metrics.groupby('week_id')['transactions_sim'].sum().reset_index()
        ax.plot(total_transactions['week_id'], total_transactions['transactions_sim'], marker='o', color='purple', linewidth=2)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Total Transactions')
        ax.set_title('Total Transactions Over Time')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'lpm_outcomes.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_persona_contributions(self, persona_contributions: pd.DataFrame):
        """Plot persona contribution breakdown."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('LPM: Persona Contribution Breakdown', fontsize=16)
        
        # Stacked area: persona contribution to transactions over time
        ax = axes[0]
        persona_by_week = persona_contributions.groupby(['week_id', 'persona_id'])['transactions_sim'].sum().reset_index()
        pivot = persona_by_week.pivot(index='week_id', columns='persona_id', values='transactions_sim').fillna(0)
        
        ax.stackplot(pivot.index, *[pivot[col] for col in pivot.columns], labels=pivot.columns, alpha=0.7)
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Transactions')
        ax.set_title('Persona Contribution to Transactions (Stacked)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Persona × Brand heatmap
        ax = axes[1]
        persona_brand = persona_contributions.groupby(['persona_id', 'brand_id'])['transactions_sim'].sum().reset_index()
        pivot_heatmap = persona_brand.pivot(index='persona_id', columns='brand_id', values='transactions_sim').fillna(0)
        
        im = ax.imshow(pivot_heatmap.values, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        ax.set_xlabel('Brand')
        ax.set_ylabel('Persona')
        ax.set_title('Persona × Brand Heatmap (Transactions)')
        ax.set_xticks(range(len(pivot_heatmap.columns)))
        ax.set_xticklabels(pivot_heatmap.columns, rotation=45, ha='right')
        ax.set_yticks(range(len(pivot_heatmap.index)))
        ax.set_yticklabels([pid.split('_')[-1][:15] for pid in pivot_heatmap.index])
        plt.colorbar(im, ax=ax)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'persona_contributions.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_anchoring_before_after(
        self,
        observed_metrics: pd.DataFrame,
        simulated_before: pd.DataFrame,
        simulated_after: pd.DataFrame
    ):
        """Plot before/after anchoring comparison."""
        # First, create aggregated view (original 2x2 grid)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Anchoring: Before vs After Calibration (Aggregated)', fontsize=16)
        
        # Transactions: Observed vs Simulated (Before)
        ax = axes[0, 0]
        obs_tx = observed_metrics.groupby('week_id')['transactions_obs'].sum().reset_index()
        sim_before_tx = simulated_before.groupby('week_id')['transactions_sim'].sum().reset_index()
        
        ax.plot(obs_tx['week_id'], obs_tx['transactions_obs'], label='Observed', marker='o', linewidth=2, color='blue')
        ax.plot(sim_before_tx['week_id'], sim_before_tx['transactions_sim'], label='Simulated (Before)', marker='s', linestyle='--', color='red')
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Transactions')
        ax.set_title('Transactions: Observed vs Simulated (Before)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Transactions: Observed vs Simulated (After)
        ax = axes[0, 1]
        sim_after_tx = simulated_after.groupby('week_id')['transactions_sim'].sum().reset_index()
        
        ax.plot(obs_tx['week_id'], obs_tx['transactions_obs'], label='Observed', marker='o', linewidth=2, color='blue')
        ax.plot(sim_after_tx['week_id'], sim_after_tx['transactions_sim'], label='Simulated (After)', marker='s', linestyle='--', color='green')
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Transactions')
        ax.set_title('Transactions: Observed vs Simulated (After)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Revenue: Observed vs Simulated (Before)
        ax = axes[1, 0]
        obs_rev = observed_metrics.groupby('week_id')['revenue_obs'].sum().reset_index()
        sim_before_rev = simulated_before.groupby('week_id')['revenue_sim'].sum().reset_index()
        
        ax.plot(obs_rev['week_id'], obs_rev['revenue_obs'], label='Observed', marker='o', linewidth=2, color='blue')
        ax.plot(sim_before_rev['week_id'], sim_before_rev['revenue_sim'], label='Simulated (Before)', marker='s', linestyle='--', color='red')
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Revenue')
        ax.set_title('Revenue: Observed vs Simulated (Before)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Revenue: Observed vs Simulated (After)
        ax = axes[1, 1]
        sim_after_rev = simulated_after.groupby('week_id')['revenue_sim'].sum().reset_index()
        
        ax.plot(obs_rev['week_id'], obs_rev['revenue_obs'], label='Observed', marker='o', linewidth=2, color='blue')
        ax.plot(sim_after_rev['week_id'], sim_after_rev['revenue_sim'], label='Simulated (After)', marker='s', linestyle='--', color='green')
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Revenue')
        ax.set_title('Revenue: Observed vs Simulated (After)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'anchoring_before_after.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Now create brand-by-brand visualization
        # Get top brands by total observed transactions
        brand_totals = observed_metrics.groupby('brand_id')['transactions_obs'].sum().sort_values(ascending=False)
        top_brands = brand_totals.head(9).index.tolist()  # Top 9 brands for 3x3 grid
        
        if len(top_brands) == 0:
            return
        
        # Create brand-by-brand transactions plot
        n_brands = len(top_brands)
        n_cols = 3
        n_rows = (n_brands + n_cols - 1) // n_cols  # Ceiling division
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        fig.suptitle('Anchoring: Transactions by Brand (Before vs After)', fontsize=16)
        
        for idx, brand_id in enumerate(top_brands):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            
            # Get brand-specific data
            brand_obs = observed_metrics[observed_metrics['brand_id'] == brand_id]
            brand_obs_tx = brand_obs.groupby('week_id')['transactions_obs'].sum().reset_index()
            
            brand_sim_before = simulated_before[simulated_before['brand_id'] == brand_id]
            brand_sim_before_tx = brand_sim_before.groupby('week_id')['transactions_sim'].sum().reset_index()
            
            brand_sim_after = simulated_after[simulated_after['brand_id'] == brand_id]
            brand_sim_after_tx = brand_sim_after.groupby('week_id')['transactions_sim'].sum().reset_index()
            
            # Plot
            ax.plot(brand_obs_tx['week_id'], brand_obs_tx['transactions_obs'], 
                   label='Observed', marker='o', linewidth=2, color='blue', markersize=4)
            ax.plot(brand_sim_before_tx['week_id'], brand_sim_before_tx['transactions_sim'], 
                   label='Sim (Before)', marker='s', linestyle='--', color='red', markersize=3)
            ax.plot(brand_sim_after_tx['week_id'], brand_sim_after_tx['transactions_sim'], 
                   label='Sim (After)', marker='^', linestyle='--', color='green', markersize=3)
            
            ax.set_xlabel('Week ID')
            ax.set_ylabel('Transactions')
            ax.set_title(f'{brand_id}', fontsize=10)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_brands, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'anchoring_before_after_by_brand_transactions.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Create brand-by-brand revenue plot
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        fig.suptitle('Anchoring: Revenue by Brand (Before vs After)', fontsize=16)
        
        for idx, brand_id in enumerate(top_brands):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            
            # Get brand-specific data
            brand_obs = observed_metrics[observed_metrics['brand_id'] == brand_id]
            brand_obs_rev = brand_obs.groupby('week_id')['revenue_obs'].sum().reset_index()
            
            brand_sim_before = simulated_before[simulated_before['brand_id'] == brand_id]
            brand_sim_before_rev = brand_sim_before.groupby('week_id')['revenue_sim'].sum().reset_index()
            
            brand_sim_after = simulated_after[simulated_after['brand_id'] == brand_id]
            brand_sim_after_rev = brand_sim_after.groupby('week_id')['revenue_sim'].sum().reset_index()
            
            # Plot
            ax.plot(brand_obs_rev['week_id'], brand_obs_rev['revenue_obs'], 
                   label='Observed', marker='o', linewidth=2, color='blue', markersize=4)
            ax.plot(brand_sim_before_rev['week_id'], brand_sim_before_rev['revenue_sim'], 
                   label='Sim (Before)', marker='s', linestyle='--', color='red', markersize=3)
            ax.plot(brand_sim_after_rev['week_id'], brand_sim_after_rev['revenue_sim'], 
                   label='Sim (After)', marker='^', linestyle='--', color='green', markersize=3)
            
            ax.set_xlabel('Week ID')
            ax.set_ylabel('Revenue')
            ax.set_title(f'{brand_id}', fontsize=10)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_brands, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'anchoring_before_after_by_brand_revenue.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_anchoring_error_reduction(self, anchoring_report_path: str):
        """Plot error reduction metrics."""
        import json
        with open(anchoring_report_path, 'r') as f:
            report = json.load(f)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('Anchoring: Error Reduction Metrics', fontsize=16)
        
        # Loss comparison
        ax = axes[0]
        categories = ['Baseline', 'After Anchoring']
        train_losses = [report['baseline']['train_loss'], report['after_anchoring']['train_loss']]
        holdout_losses = [report['baseline']['holdout_loss'], report['after_anchoring']['holdout_loss']]
        
        x = np.arange(len(categories))
        width = 0.35
        ax.bar(x - width/2, train_losses, width, label='Train Loss', alpha=0.8)
        ax.bar(x + width/2, holdout_losses, width, label='Holdout Loss', alpha=0.8)
        ax.set_ylabel('Loss')
        ax.set_title('Loss Before vs After Anchoring')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Improvement percentage
        ax = axes[1]
        improvements = [
            report['improvement']['train_loss_reduction'],
            report['improvement']['holdout_loss_reduction']
        ]
        colors = ['green' if imp > 0 else 'red' for imp in improvements]
        bars = ax.bar(['Train', 'Holdout'], improvements, color=colors, alpha=0.7)
        ax.set_ylabel('Loss Reduction (%)')
        ax.set_title('Loss Reduction Percentage')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, imp in zip(bars, improvements):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (1 if imp > 0 else -3),
                   f'{imp:.1f}%', ha='center', va='bottom' if imp > 0 else 'top', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'anchoring_error_reduction.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_persona_weight_adjustments(self, anchoring_patch_path: str, base_personaset_path: str):
        """Plot persona weight adjustments."""
        import json
        with open(anchoring_patch_path, 'r') as f:
            patch = json.load(f)
        
        with open(base_personaset_path, 'r') as f:
            personaset = json.load(f)
        
        # Get base weights
        base_weights = {}
        for persona in personaset['personas']:
            if persona['status'] == 'active':
                base_weights[persona['persona_id']] = persona['population_weight']['global_weight']
        
        # Get updated weights
        updated_weights = {}
        for persona_id, updates in patch['parameter_updates'].items():
            if 'population_weight.global' in updates:
                updated_weights[persona_id] = updates['population_weight.global']
        
        # Compute deltas
        deltas = {}
        for persona_id in updated_weights:
            if persona_id in base_weights:
                deltas[persona_id] = updated_weights[persona_id] - base_weights[persona_id]
        
        if not deltas:
            return  # No weight changes to plot
        
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('Anchoring: Persona Weight Adjustments', fontsize=16)
        
        persona_ids = list(deltas.keys())
        delta_values = [deltas[pid] for pid in persona_ids]
        colors = ['green' if d > 0 else 'red' for d in delta_values]
        
        bars = ax.bar(range(len(persona_ids)), delta_values, color=colors, alpha=0.7)
        ax.set_xlabel('Persona')
        ax.set_ylabel('Weight Delta')
        ax.set_title('Persona Weight Changes (After - Before)')
        ax.set_xticks(range(len(persona_ids)))
        ax.set_xticklabels([pid.split('_')[-1][:15] for pid in persona_ids], rotation=45, ha='right')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, delta in zip(bars, delta_values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.001 if delta > 0 else -0.002),
                   f'{delta:+.4f}', ha='center', va='bottom' if delta > 0 else 'top', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'persona_weight_adjustments.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_scenario_comparison(
        self,
        baseline_metrics: pd.DataFrame,
        scenario_metrics: pd.DataFrame,
        scenario_name: str = "Scenario"
    ):
        """Plot scenario comparison view."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f'LPM: Scenario Comparison ({scenario_name} vs Baseline)', fontsize=16)
        
        # Transactions delta
        ax = axes[0]
        baseline_tx = baseline_metrics.groupby(['week_id', 'brand_id'])['transactions_sim'].sum().reset_index()
        scenario_tx = scenario_metrics.groupby(['week_id', 'brand_id'])['transactions_sim'].sum().reset_index()
        
        merged = pd.merge(baseline_tx, scenario_tx, on=['week_id', 'brand_id'], suffixes=('_base', '_scenario'))
        merged['delta_pct'] = ((merged['transactions_sim_scenario'] - merged['transactions_sim_base']) / merged['transactions_sim_base']) * 100
        
        for brand_id in merged['brand_id'].unique()[:5]:
            brand_data = merged[merged['brand_id'] == brand_id]
            ax.plot(brand_data['week_id'], brand_data['delta_pct'], label=brand_id, marker='o', markersize=3)
        
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Delta (%)')
        ax.set_title('Transactions: % Change vs Baseline')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Revenue delta
        ax = axes[1]
        baseline_rev = baseline_metrics.groupby(['week_id', 'brand_id'])['revenue_sim'].sum().reset_index()
        scenario_rev = scenario_metrics.groupby(['week_id', 'brand_id'])['revenue_sim'].sum().reset_index()
        
        merged_rev = pd.merge(baseline_rev, scenario_rev, on=['week_id', 'brand_id'], suffixes=('_base', '_scenario'))
        merged_rev['delta_pct'] = ((merged_rev['revenue_sim_scenario'] - merged_rev['revenue_sim_base']) / merged_rev['revenue_sim_base']) * 100
        
        for brand_id in merged_rev['brand_id'].unique()[:5]:
            brand_data = merged_rev[merged_rev['brand_id'] == brand_id]
            ax.plot(brand_data['week_id'], brand_data['delta_pct'], label=brand_id, marker='o', markersize=3)
        
        ax.set_xlabel('Week ID')
        ax.set_ylabel('Delta (%)')
        ax.set_title('Revenue: % Change vs Baseline')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f'scenario_comparison_{scenario_name.lower().replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        plt.close()

