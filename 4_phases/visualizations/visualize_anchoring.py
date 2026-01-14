"""
Visualize Phase 3 vs Phase 4: Before and After Anchoring
Shows how simulation improves after ground truth anchoring
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json
from typing import Optional, Dict, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)


class AnchoringVisualizer:
    """Visualize before/after anchoring comparison"""
    
    def __init__(self, 
                 phase3_data_path: str = 'simulations/intent_trajectories.csv',
                 real_data_path: Optional[str] = None,
                 phase4_data_path: Optional[str] = None,
                 target_metrics_path: str = 'phase4_output/target_metrics.json',
                 calibration_metrics_path: str = 'phase4_output/calibration_metrics.json'):
        """
        Args:
            phase3_data_path: Path to Phase 3 simulation data (before anchoring)
            real_data_path: Path to real/ground truth data
            phase4_data_path: Path to Phase 4 anchored simulation (if available)
            target_metrics_path: Path to target metrics from real data
            calibration_metrics_path: Path to calibration comparison metrics
        """
        self.phase3_data_path = phase3_data_path
        self.real_data_path = real_data_path
        self.phase4_data_path = phase4_data_path
        self.target_metrics_path = target_metrics_path
        self.calibration_metrics_path = calibration_metrics_path
        
        # Load data
        self.phase3_data = None
        self.real_data = None
        self.phase4_data = None
        self.target_metrics = None
        self.calibration_metrics = None
        
        self._load_data()
    
    def _load_data(self):
        """Load all data files"""
        print("Loading data...")
        
        # Phase 3 data (before anchoring)
        if os.path.exists(self.phase3_data_path):
            self.phase3_data = pd.read_csv(self.phase3_data_path)
            self.phase3_data['timestamp'] = pd.to_datetime(self.phase3_data['timestamp'])
            print(f"  ✓ Loaded Phase 3 data: {len(self.phase3_data)} interactions")
        else:
            raise FileNotFoundError(f"Phase 3 data not found: {self.phase3_data_path}")
        
        # Real data (ground truth)
        if self.real_data_path and os.path.exists(self.real_data_path):
            self.real_data = pd.read_csv(self.real_data_path)
            self.real_data['timestamp'] = pd.to_datetime(self.real_data['timestamp'])
            print(f"  ✓ Loaded real data: {len(self.real_data)} interactions")
        else:
            print("  ⚠ No real data provided - will use target metrics only")
        
        # Phase 4 data (after anchoring) - if available
        if self.phase4_data_path and os.path.exists(self.phase4_data_path):
            self.phase4_data = pd.read_csv(self.phase4_data_path)
            self.phase4_data['timestamp'] = pd.to_datetime(self.phase4_data['timestamp'])
            print(f"  ✓ Loaded Phase 4 anchored data: {len(self.phase4_data)} interactions")
        else:
            print("  ⚠ No Phase 4 anchored data - will show Phase 3 vs Real only")
        
        # Target metrics
        if os.path.exists(self.target_metrics_path):
            with open(self.target_metrics_path, 'r') as f:
                self.target_metrics = json.load(f)
            print(f"  ✓ Loaded target metrics")
        
        # Calibration metrics
        if os.path.exists(self.calibration_metrics_path):
            with open(self.calibration_metrics_path, 'r') as f:
                self.calibration_metrics = json.load(f)
            print(f"  ✓ Loaded calibration metrics")
    
    def compute_metrics(self, data: pd.DataFrame, label: str = "") -> Dict:
        """Compute metrics for a dataset"""
        metrics = {}
        
        if 'intent_value' in data.columns:
            metrics['intent_mean'] = data['intent_value'].mean()
            metrics['intent_std'] = data['intent_value'].std()
            metrics['intent_median'] = data['intent_value'].median()
        
        if 'product_id' in data.columns and 'intent_value' in data.columns:
            product_intent = data.groupby('product_id')['intent_value'].mean()
            metrics['product_intent_mean'] = product_intent.mean()
            metrics['product_intent_std'] = product_intent.std()
        
        if 'segment_id' in data.columns and 'intent_value' in data.columns:
            segment_intent = data.groupby('segment_id')['intent_value'].mean()
            metrics['segment_intent_means'] = segment_intent.to_dict()
        
        if 'product_category' in data.columns and 'intent_value' in data.columns:
            category_intent = data.groupby('product_category')['intent_value'].mean()
            metrics['category_intent_means'] = category_intent.to_dict()
        
        if 'agent_id' in data.columns and 'product_id' in data.columns:
            agent_products = data.sort_values(['agent_id', 'timestamp']).groupby('agent_id')['product_id']
            switches = []
            for agent_id, products in agent_products:
                product_seq = products.tolist()
                switch_count = sum(1 for i in range(1, len(product_seq)) if product_seq[i] != product_seq[i-1])
                if len(product_seq) > 1:
                    switches.append(switch_count / (len(product_seq) - 1))
            if switches:
                metrics['switching_rate'] = np.mean(switches)
        
        if 'timestamp' in data.columns:
            data_sorted = data.sort_values('timestamp')
            data_sorted['date'] = data_sorted['timestamp'].dt.date
            daily_intent = data_sorted.groupby('date')['intent_value'].mean()
            if len(daily_intent) > 1:
                x = np.arange(len(daily_intent))
                y = daily_intent.values
                metrics['daily_trend'] = np.polyfit(x, y, 1)[0]
                metrics['daily_mean'] = daily_intent.mean()
                metrics['daily_std'] = daily_intent.std()
        
        return metrics
    
    def plot_intent_distribution_comparison(self, output_path: str = 'phase4_output/visualizations/intent_distribution.png'):
        """Compare intent value distributions"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Intent Distribution: Phase 3 (Initial Approximation) vs Phase 4 (Ground Truth Anchored)', 
                     fontsize=16, fontweight='bold')
        
        # 1. Overall intent distribution
        ax = axes[0, 0]
        if self.phase3_data is not None:
            ax.hist(self.phase3_data['intent_value'], bins=30, alpha=0.6, label='Phase 3 (Before)', color='blue', density=True)
        if self.real_data is not None:
            ax.hist(self.real_data['intent_value'], bins=30, alpha=0.6, label='Real Data', color='green', density=True)
        if self.phase4_data is not None:
            ax.hist(self.phase4_data['intent_value'], bins=30, alpha=0.6, label='Phase 4 (After)', color='red', density=True)
        ax.set_xlabel('Intent Value')
        ax.set_ylabel('Density')
        ax.set_title('Overall Intent Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Category-level intent means
        ax = axes[0, 1]
        # Get all categories
        all_cats = set()
        if self.phase3_data is not None and 'product_category' in self.phase3_data.columns:
            all_cats.update(self.phase3_data['product_category'].unique())
        if self.real_data is not None and 'product_category' in self.real_data.columns:
            all_cats.update(self.real_data['product_category'].unique())
        if self.phase4_data is not None and 'product_category' in self.phase4_data.columns:
            all_cats.update(self.phase4_data['product_category'].unique())
        all_cats = sorted(all_cats)
        
        # Prepare data
        x = np.arange(len(all_cats))
        width = 0.25
        
        phase3_vals = []
        real_vals = []
        phase4_vals = []
        
        if self.phase3_data is not None and 'product_category' in self.phase3_data.columns:
            phase3_cat = self.phase3_data.groupby('product_category')['intent_value'].mean()
            phase3_vals = [phase3_cat.get(cat, 0) for cat in all_cats]
        if self.real_data is not None and 'product_category' in self.real_data.columns:
            real_cat = self.real_data.groupby('product_category')['intent_value'].mean()
            real_vals = [real_cat.get(cat, 0) for cat in all_cats]
        elif self.target_metrics and 'category_intent_means' in self.target_metrics:
            real_vals = [self.target_metrics['category_intent_means'].get(cat, 0) for cat in all_cats]
        if self.phase4_data is not None and 'product_category' in self.phase4_data.columns:
            phase4_cat = self.phase4_data.groupby('product_category')['intent_value'].mean()
            phase4_vals = [phase4_cat.get(cat, 0) for cat in all_cats]
        
        # Plot bars
        if phase3_vals:
            ax.bar(x - width, phase3_vals, width, alpha=0.6, label='Phase 3', color='blue')
        if real_vals:
            ax.bar(x, real_vals, width, alpha=0.6, label='Real', color='green')
        if phase4_vals:
            ax.bar(x + width, phase4_vals, width, alpha=0.6, label='Phase 4', color='red')
        
        ax.set_xticks(x)
        ax.set_xticklabels(all_cats, rotation=45, ha='right')
        ax.set_xlabel('Mean Intent Value')
        ax.set_title('Category-Level Intent Means')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. Segment-level intent means
        ax = axes[1, 0]
        if self.phase3_data is not None and 'segment_id' in self.phase3_data.columns:
            phase3_seg = self.phase3_data.groupby('segment_id')['intent_value'].mean().sort_values()
            x_pos = np.arange(len(phase3_seg))
            ax.bar(x_pos - 0.2, phase3_seg.values, width=0.4, alpha=0.6, label='Phase 3', color='blue')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(phase3_seg.index, rotation=45)
        if self.real_data is not None and 'segment_id' in self.real_data.columns:
            real_seg = self.real_data.groupby('segment_id')['intent_value'].mean().sort_index()
            if self.phase3_data is not None:
                x_pos = np.arange(len(real_seg))
                ax.bar(x_pos, real_seg.values, width=0.4, alpha=0.6, label='Real', color='green')
            else:
                x_pos = np.arange(len(real_seg))
                ax.bar(x_pos, real_seg.values, width=0.4, alpha=0.6, label='Real', color='green')
                ax.set_xticks(x_pos)
                ax.set_xticklabels(real_seg.index, rotation=45)
        if self.phase4_data is not None and 'segment_id' in self.phase4_data.columns:
            phase4_seg = self.phase4_data.groupby('segment_id')['intent_value'].mean().sort_index()
            if self.phase3_data is not None:
                x_pos = np.arange(len(phase4_seg))
                ax.bar(x_pos + 0.2, phase4_seg.values, width=0.4, alpha=0.6, label='Phase 4', color='red')
        ax.set_ylabel('Mean Intent Value')
        ax.set_title('Segment-Level Intent Means')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. Time series trend
        ax = axes[1, 1]
        if self.phase3_data is not None and 'timestamp' in self.phase3_data.columns:
            phase3_daily = self.phase3_data.groupby(self.phase3_data['timestamp'].dt.date)['intent_value'].mean()
            ax.plot(phase3_daily.index, phase3_daily.values, label='Phase 3', color='blue', alpha=0.7, marker='o', markersize=4)
        if self.real_data is not None and 'timestamp' in self.real_data.columns:
            real_daily = self.real_data.groupby(self.real_data['timestamp'].dt.date)['intent_value'].mean()
            ax.plot(real_daily.index, real_daily.values, label='Real', color='green', alpha=0.7, marker='s', markersize=4)
        if self.phase4_data is not None and 'timestamp' in self.phase4_data.columns:
            phase4_daily = self.phase4_data.groupby(self.phase4_data['timestamp'].dt.date)['intent_value'].mean()
            ax.plot(phase4_daily.index, phase4_daily.values, label='Phase 4', color='red', alpha=0.7, marker='^', markersize=4)
        ax.set_xlabel('Date')
        ax.set_ylabel('Mean Intent Value')
        ax.set_title('Daily Intent Trend Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def compute_accuracy_improvement(self, phase3_metrics: Dict, phase4_metrics: Optional[Dict], real_metrics: Dict) -> Dict:
        """Compute accuracy improvement from Phase 3 to Phase 4"""
        improvements = {}
        
        if not real_metrics:
            return improvements
        
        # Product intent mean improvement
        if phase3_metrics.get('product_intent_mean') is not None:
            phase3_error = abs(phase3_metrics['product_intent_mean'] - real_metrics.get('product_intent_mean', 0))
            if phase4_metrics and phase4_metrics.get('product_intent_mean') is not None:
                phase4_error = abs(phase4_metrics['product_intent_mean'] - real_metrics.get('product_intent_mean', 0))
                improvements['product_intent'] = {
                    'phase3_error': phase3_error,
                    'phase4_error': phase4_error,
                    'improvement': phase3_error - phase4_error,
                    'improvement_pct': ((phase3_error - phase4_error) / phase3_error * 100) if phase3_error > 0 else 0
                }
        
        # Switching rate improvement
        if phase3_metrics.get('switching_rate') is not None:
            phase3_error = abs(phase3_metrics['switching_rate'] - real_metrics.get('switching_rate', 0))
            if phase4_metrics and phase4_metrics.get('switching_rate') is not None:
                phase4_error = abs(phase4_metrics['switching_rate'] - real_metrics.get('switching_rate', 0))
                improvements['switching_rate'] = {
                    'phase3_error': phase3_error,
                    'phase4_error': phase4_error,
                    'improvement': phase3_error - phase4_error,
                    'improvement_pct': ((phase3_error - phase4_error) / phase3_error * 100) if phase3_error > 0 else 0
                }
        
        # Category-level improvements
        if phase3_metrics.get('category_intent_means') and real_metrics.get('category_intent_means'):
            category_improvements = {}
            for cat in real_metrics['category_intent_means'].keys():
                phase3_val = phase3_metrics['category_intent_means'].get(cat, 0)
                real_val = real_metrics['category_intent_means'].get(cat, 0)
                phase3_error = abs(phase3_val - real_val)
                
                if phase4_metrics and phase4_metrics.get('category_intent_means'):
                    phase4_val = phase4_metrics['category_intent_means'].get(cat, 0)
                    phase4_error = abs(phase4_val - real_val)
                    category_improvements[cat] = {
                        'phase3_error': phase3_error,
                        'phase4_error': phase4_error,
                        'improvement': phase3_error - phase4_error,
                        'improvement_pct': ((phase3_error - phase4_error) / phase3_error * 100) if phase3_error > 0 else 0
                    }
            
            if category_improvements:
                improvements['categories'] = category_improvements
        
        return improvements
    
    def plot_metrics_comparison(self, output_path: str = 'phase4_output/visualizations/metrics_comparison.png'):
        """Compare key metrics side-by-side"""
        # Compute metrics for each dataset
        phase3_metrics = self.compute_metrics(self.phase3_data, "Phase 3")
        real_metrics = self.compute_metrics(self.real_data, "Real") if self.real_data is not None else None
        phase4_metrics = self.compute_metrics(self.phase4_data, "Phase 4") if self.phase4_data is not None else None
        
        # Use target metrics if real data not available
        if real_metrics is None and self.target_metrics is not None:
            real_metrics = {
                'product_intent_mean': self.target_metrics.get('product_intent_mean'),
                'switching_rate': self.target_metrics.get('switching_rate'),
                'daily_trend': self.target_metrics.get('daily_trend'),
                'category_intent_means': self.target_metrics.get('category_intent_means', {})
            }
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Accuracy Improvement: Phase 3 (Approximation) → Phase 4 (Ground Truth Anchored)', 
                     fontsize=16, fontweight='bold')
        
        # Compute improvements
        improvements = self.compute_accuracy_improvement(phase3_metrics, phase4_metrics, real_metrics or {})
        
        # 1. Product Intent Mean
        ax = axes[0, 0]
        metrics_to_plot = []
        labels = []
        colors = []
        if phase3_metrics.get('product_intent_mean') is not None:
            metrics_to_plot.append(phase3_metrics['product_intent_mean'])
            labels.append('Phase 3\n(Before)')
            colors.append('blue')
        if real_metrics and real_metrics.get('product_intent_mean') is not None:
            metrics_to_plot.append(real_metrics['product_intent_mean'])
            labels.append('Real Data\n(Ground Truth)')
            colors.append('green')
        if phase4_metrics and phase4_metrics.get('product_intent_mean') is not None:
            metrics_to_plot.append(phase4_metrics['product_intent_mean'])
            labels.append('Phase 4\n(After)')
            colors.append('red')
        
        bars = ax.bar(labels, metrics_to_plot, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_ylabel('Product Intent Mean')
        ax.set_title('Product Intent Mean Comparison')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.4f}',
                   ha='center', va='bottom', fontweight='bold')
        
        # Add improvement annotation if Phase 4 exists
        if phase4_metrics and real_metrics and 'product_intent' in improvements:
            imp = improvements['product_intent']
            phase3_val = phase3_metrics.get('product_intent_mean', 0)
            phase4_val = phase4_metrics.get('product_intent_mean', 0)
            real_val = real_metrics.get('product_intent_mean', 0)
            
            if imp['improvement'] > 0:
                # Arrow showing convergence
                ax.annotate('', xy=(2, real_val), xytext=(0, phase3_val),
                           arrowprops=dict(arrowstyle='->', color='green', lw=3, alpha=0.7))
                # Improvement text
                ax.text(1, max(phase3_val, real_val) + 0.01, 
                       f'✓ Improved by {imp["improvement"]:.4f}\n({imp["improvement_pct"]:.1f}% better)', 
                       ha='center', va='bottom', fontsize=11, color='green', fontweight='bold',
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8, edgecolor='green', linewidth=2))
            elif imp['improvement'] < 0:
                ax.text(1, max(phase3_val, real_val) + 0.01, 
                       f'⚠ Degraded by {abs(imp["improvement"]):.4f}', 
                       ha='center', va='bottom', fontsize=10, color='red', fontweight='bold',
                       bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
        
        # 2. Switching Rate
        ax = axes[0, 1]
        metrics_to_plot = []
        labels = []
        colors = []
        if phase3_metrics.get('switching_rate') is not None:
            metrics_to_plot.append(phase3_metrics['switching_rate'])
            labels.append('Phase 3\n(Before)')
            colors.append('blue')
        if real_metrics and real_metrics.get('switching_rate') is not None:
            metrics_to_plot.append(real_metrics['switching_rate'])
            labels.append('Real Data\n(Ground Truth)')
            colors.append('green')
        if phase4_metrics and phase4_metrics.get('switching_rate') is not None:
            metrics_to_plot.append(phase4_metrics['switching_rate'])
            labels.append('Phase 4\n(After)')
            colors.append('red')
        
        bars = ax.bar(labels, metrics_to_plot, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_ylabel('Switching Rate')
        ax.set_title('Switching Rate Comparison')
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.4f}',
                   ha='center', va='bottom', fontweight='bold')
        
        # 3. Daily Trend
        ax = axes[1, 0]
        metrics_to_plot = []
        labels = []
        colors = []
        if phase3_metrics.get('daily_trend') is not None:
            metrics_to_plot.append(phase3_metrics['daily_trend'])
            labels.append('Phase 3\n(Before)')
            colors.append('blue')
        if real_metrics and real_metrics.get('daily_trend') is not None:
            metrics_to_plot.append(real_metrics['daily_trend'])
            labels.append('Real Data\n(Ground Truth)')
            colors.append('green')
        if phase4_metrics and phase4_metrics.get('daily_trend') is not None:
            metrics_to_plot.append(phase4_metrics['daily_trend'])
            labels.append('Phase 4\n(After)')
            colors.append('red')
        
        bars = ax.bar(labels, metrics_to_plot, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_ylabel('Daily Trend (Slope)')
        ax.set_title('Time-Series Trend Comparison')
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.6f}',
                   ha='center', va='bottom' if height >= 0 else 'top', fontweight='bold')
        
        # 4. Accuracy Improvement Summary
        ax = axes[1, 1]
        if improvements:
            improvement_data = []
            labels = []
            colors_list = []
            
            for metric_name, imp_data in improvements.items():
                if metric_name != 'categories' and isinstance(imp_data, dict):
                    improvement = imp_data.get('improvement', 0)
                    improvement_pct = imp_data.get('improvement_pct', 0)
                    
                    if improvement != 0:
                        improvement_data.append(improvement)
                        labels.append(f'{metric_name.replace("_", " ").title()}\n({improvement_pct:+.1f}%)')
                        colors_list.append('green' if improvement > 0 else 'red')
            
            if improvement_data:
                bars = ax.barh(labels, improvement_data, color=colors_list, alpha=0.7, edgecolor='black', linewidth=2)
                ax.set_xlabel('Error Reduction (Phase 3 Error - Phase 4 Error)')
                ax.set_title('Accuracy Improvement Summary\n(Ground Truth Anchoring Impact)')
                ax.axvline(x=0, color='black', linestyle='-', linewidth=2)
                ax.grid(True, alpha=0.3, axis='x')
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2.,
                           f'{width:+.4f}',
                           ha='left' if width >= 0 else 'right', va='center', fontweight='bold', fontsize=10)
                
                # Add overall improvement score
                total_improvement = sum([imp for imp in improvement_data if imp > 0])
                if total_improvement > 0:
                    ax.text(0.98, 0.02, f'Total Improvement: {total_improvement:.4f}',
                           transform=ax.transAxes, ha='right', va='bottom',
                           fontsize=12, fontweight='bold', color='green',
                           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'No Phase 4 data available\nfor improvement calculation', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title('Accuracy Improvement Summary')
        else:
            ax.text(0.5, 0.5, 'Real data required\nfor improvement calculation', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Accuracy Improvement Summary')
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def plot_category_comparison(self, output_path: str = 'phase4_output/visualizations/category_comparison.png'):
        """Compare category-level intent across datasets"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get category means
        phase3_cat = {}
        real_cat = {}
        phase4_cat = {}
        
        if self.phase3_data is not None and 'product_category' in self.phase3_data.columns:
            phase3_cat = self.phase3_data.groupby('product_category')['intent_value'].mean().to_dict()
        
        if self.real_data is not None and 'product_category' in self.real_data.columns:
            real_cat = self.real_data.groupby('product_category')['intent_value'].mean().to_dict()
        elif self.target_metrics and 'category_intent_means' in self.target_metrics:
            real_cat = self.target_metrics['category_intent_means']
        
        if self.phase4_data is not None and 'product_category' in self.phase4_data.columns:
            phase4_cat = self.phase4_data.groupby('product_category')['intent_value'].mean().to_dict()
        
        # Get all categories
        all_categories = set(list(phase3_cat.keys()) + list(real_cat.keys()) + list(phase4_cat.keys()))
        all_categories = sorted(all_categories)
        
        # Prepare data
        x = np.arange(len(all_categories))
        width = 0.25
        
        phase3_vals = [phase3_cat.get(cat, 0) for cat in all_categories]
        real_vals = [real_cat.get(cat, 0) for cat in all_categories]
        phase4_vals = [phase4_cat.get(cat, 0) for cat in all_categories]
        
        # Plot bars
        bars1 = ax.bar(x - width, phase3_vals, width, label='Phase 3 (Before)', color='blue', alpha=0.7)
        bars2 = ax.bar(x, real_vals, width, label='Real Data (Ground Truth)', color='green', alpha=0.7)
        if any(phase4_vals):
            bars3 = ax.bar(x + width, phase4_vals, width, label='Phase 4 (After)', color='red', alpha=0.7)
        
        ax.set_xlabel('Product Category', fontsize=12, fontweight='bold')
        ax.set_ylabel('Mean Intent Value', fontsize=12, fontweight='bold')
        ax.set_title('Category-Level Intent: Phase 3 (Initial) → Phase 4 (Ground Truth Anchored)', 
                     fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(all_categories, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add improvement indicators
        if real_cat and phase3_cat and phase4_cat:
            improvements_count = 0
            for i, cat in enumerate(all_categories):
                if cat in phase3_cat and cat in real_cat and cat in phase4_cat:
                    phase3_error = abs(phase3_cat[cat] - real_cat[cat])
                    phase4_error = abs(phase4_cat[cat] - real_cat[cat])
                    if phase4_error < phase3_error:
                        improvements_count += 1
                        # Improvement arrow
                        ax.annotate('', xy=(i + width, real_cat[cat]), 
                                   xytext=(i - width, phase3_cat[cat]),
                                   arrowprops=dict(arrowstyle='->', color='green', lw=2, alpha=0.7))
                        # Improvement percentage
                        improvement_pct = ((phase3_error - phase4_error) / phase3_error * 100) if phase3_error > 0 else 0
                        ax.text(i, max(phase3_cat[cat], real_cat[cat], phase4_cat[cat]) + 0.02,
                               f'{improvement_pct:.0f}%',
                               ha='center', va='bottom', fontsize=8, color='green', fontweight='bold')
            
            # Add summary text
            if improvements_count > 0:
                ax.text(0.02, 0.98, f'{improvements_count}/{len(all_categories)} categories improved',
                       transform=ax.transAxes, ha='left', va='top',
                       fontsize=11, fontweight='bold', color='green',
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def plot_convergence_path(self, output_path: str = 'phase4_output/visualizations/convergence_path.png'):
        """Show the path from Phase 3 to Phase 4 (convergence visualization)"""
        if not self.target_metrics:
            print("  ⚠ Target metrics not available - skipping convergence plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Convergence Path: Phase 3 (Initial Approximation) → Phase 4 (Ground Truth Anchored)', 
                     fontsize=16, fontweight='bold')
        
        # Compute improvements for annotations
        phase3_metrics = self.compute_metrics(self.phase3_data, "Phase 3")
        phase4_metrics = self.compute_metrics(self.phase4_data, "Phase 4") if self.phase4_data is not None else None
        real_metrics = self.compute_metrics(self.real_data, "Real") if self.real_data is not None else {}
        if not real_metrics and self.target_metrics:
            real_metrics = {
                'product_intent_mean': self.target_metrics.get('product_intent_mean'),
                'switching_rate': self.target_metrics.get('switching_rate'),
                'category_intent_means': self.target_metrics.get('category_intent_means', {})
            }
        improvements = self.compute_accuracy_improvement(phase3_metrics, phase4_metrics, real_metrics)
        
        # 1. Product Intent Mean convergence
        ax = axes[0, 0]
        target = self.target_metrics.get('product_intent_mean', 0)
        phase3_val = phase3_metrics.get('product_intent_mean', 0)
        
        # Plot Phase 3 (initial approximation)
        ax.scatter([0], [phase3_val], s=300, color='blue', marker='o', 
                  label='Phase 3\n(Initial Approximation)', zorder=3, edgecolors='black', linewidth=3)
        
        # Plot target (ground truth)
        ax.axhline(y=target, color='green', linestyle='--', linewidth=3, 
                  label='Ground Truth Target', alpha=0.8)
        ax.text(0.5, target, f'Target: {target:.4f}', ha='left', va='bottom', 
               fontsize=10, color='green', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        # Plot Phase 4 (ground truth anchored)
        if phase4_metrics:
            phase4_val = phase4_metrics.get('product_intent_mean', 0)
            ax.scatter([1], [phase4_val], s=300, color='red', marker='s', 
                      label='Phase 4\n(Ground Truth Anchored)', zorder=3, edgecolors='black', linewidth=3)
            
            # Convergence path with arrow
            ax.plot([0, 1], [phase3_val, phase4_val], 'r-', linewidth=3, alpha=0.6, label='Convergence Path')
            ax.annotate('', xy=(1, phase4_val), xytext=(0, phase3_val),
                       arrowprops=dict(arrowstyle='->', color='red', lw=3, alpha=0.8))
            
            # Show improvement
            if 'product_intent' in improvements:
                imp = improvements['product_intent']
                if imp['improvement'] > 0:
                    ax.text(0.5, (phase3_val + phase4_val)/2, 
                           f'✓ {imp["improvement_pct"]:.1f}% Better',
                           ha='center', va='center', fontsize=11, fontweight='bold', color='green',
                           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8, edgecolor='green', linewidth=2))
        
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylabel('Product Intent Mean', fontsize=12, fontweight='bold')
        ax.set_title('Product Intent Mean: Convergence to Ground Truth', fontsize=13, fontweight='bold')
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Phase 3\n(Initial)', 'Phase 4\n(Anchored)'], fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 2. Switching Rate convergence
        ax = axes[0, 1]
        target = self.target_metrics.get('switching_rate', 0)
        phase3_val = phase3_metrics.get('switching_rate', 0)
        
        ax.scatter([0], [phase3_val], s=200, color='blue', marker='o', label='Phase 3', zorder=3, edgecolors='black', linewidth=2)
        ax.axhline(y=target, color='green', linestyle='--', linewidth=2, label='Target (Real Data)', alpha=0.7)
        
        if phase4_metrics:
            phase4_val = phase4_metrics.get('switching_rate', 0)
            ax.scatter([1], [phase4_val], s=200, color='red', marker='s', label='Phase 4', zorder=3, edgecolors='black', linewidth=2)
            ax.plot([0, 1], [phase3_val, phase4_val], 'r--', linewidth=2, alpha=0.5)
            ax.annotate('', xy=(1, phase4_val), xytext=(0, phase3_val),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2))
        
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylabel('Switching Rate')
        ax.set_title('Switching Rate Convergence')
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Phase 3\n(Before)', 'Phase 4\n(After)'])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. Category-level convergence (scatter)
        ax = axes[1, 0]
        if self.target_metrics.get('category_intent_means'):
            categories = list(self.target_metrics['category_intent_means'].keys())
            target_vals = [self.target_metrics['category_intent_means'][cat] for cat in categories]
            phase3_vals = [phase3_metrics.get('category_intent_means', {}).get(cat, 0) for cat in categories]
            phase4_vals = [phase4_metrics.get('category_intent_means', {}).get(cat, 0) for cat in categories] if phase4_metrics else None
            
            ax.scatter(target_vals, phase3_vals, s=100, color='blue', alpha=0.6, label='Phase 3', marker='o')
            if phase4_vals:
                ax.scatter(target_vals, phase4_vals, s=100, color='red', alpha=0.6, label='Phase 4', marker='s')
            
            # Perfect match line
            min_val = min(min(target_vals), min(phase3_vals))
            max_val = max(max(target_vals), max(phase3_vals))
            ax.plot([min_val, max_val], [min_val, max_val], 'g--', linewidth=2, label='Perfect Match', alpha=0.7)
            
            ax.set_xlabel('Target (Real Data) Intent')
            ax.set_ylabel('Simulated Intent')
            ax.set_title('Category Intent: Phase 3 vs Phase 4')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 4. Overall Accuracy Score
        ax = axes[1, 1]
        if improvements:
            # Calculate overall accuracy scores
            phase3_total_error = 0
            phase4_total_error = 0
            n_metrics = 0
            
            for metric_name, imp_data in improvements.items():
                if metric_name != 'categories' and isinstance(imp_data, dict):
                    phase3_total_error += imp_data.get('phase3_error', 0)
                    phase4_total_error += imp_data.get('phase4_error', 0)
                    n_metrics += 1
            
            if n_metrics > 0:
                phase3_accuracy = 100 * (1 - phase3_total_error / n_metrics) if n_metrics > 0 else 0
                phase4_accuracy = 100 * (1 - phase4_total_error / n_metrics) if n_metrics > 0 else 0
                accuracy_gain = phase4_accuracy - phase3_accuracy
                
                # Plot accuracy scores
                scores = [phase3_accuracy, phase4_accuracy]
                labels_acc = ['Phase 3\n(Initial)', 'Phase 4\n(Anchored)']
                colors_acc = ['blue', 'red']
                
                bars = ax.bar(labels_acc, scores, color=colors_acc, alpha=0.7, edgecolor='black', linewidth=3)
                ax.set_ylabel('Accuracy Score (%)', fontsize=12, fontweight='bold')
                ax.set_title('Overall Accuracy: Ground Truth Anchoring Impact', fontsize=13, fontweight='bold')
                ax.set_ylim([0, 105])
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%',
                           ha='center', va='bottom', fontweight='bold', fontsize=12)
                
                # Add improvement annotation
                if accuracy_gain > 0:
                    ax.annotate('', xy=(1, phase4_accuracy), xytext=(0, phase3_accuracy),
                               arrowprops=dict(arrowstyle='->', color='green', lw=3))
                    ax.text(0.5, (phase3_accuracy + phase4_accuracy)/2,
                           f'✓ +{accuracy_gain:.1f}% Accuracy Gain',
                           ha='center', va='center', fontsize=12, fontweight='bold', color='green',
                           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9, edgecolor='green', linewidth=2))
                
                # Add explanation text
                ax.text(0.5, -5, 'Higher = Better (closer to ground truth)',
                       ha='center', va='top', transform=ax.transAxes, fontsize=10, style='italic')
            else:
                ax.text(0.5, 0.5, 'Phase 4 data required\nfor accuracy calculation', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title('Overall Accuracy Score')
        else:
            ax.text(0.5, 0.5, 'Real data required\nfor accuracy calculation', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Overall Accuracy Score')
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {output_path}")
        plt.close()
    
    def create_interactive_dashboard(self, output_path: str = 'phase4_output/visualizations/anchoring_dashboard.html'):
        """Create interactive HTML dashboard using Plotly"""
        print("\nCreating interactive dashboard...")
        
        # Compute metrics
        phase3_metrics = self.compute_metrics(self.phase3_data, "Phase 3")
        phase4_metrics = self.compute_metrics(self.phase4_data, "Phase 4") if self.phase4_data is not None else None
        real_metrics = self.compute_metrics(self.real_data, "Real") if self.real_data is not None else {}
        
        if not real_metrics and self.target_metrics:
            real_metrics = {
                'product_intent_mean': self.target_metrics.get('product_intent_mean'),
                'switching_rate': self.target_metrics.get('switching_rate'),
                'category_intent_means': self.target_metrics.get('category_intent_means', {})
            }
        
        improvements = self.compute_accuracy_improvement(phase3_metrics, phase4_metrics, real_metrics)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Product Intent Mean: Convergence Path',
                'Switching Rate: Convergence Path',
                'Category-Level Intent Comparison',
                'Accuracy Improvement Summary',
                'Time Series: Daily Intent Trend',
                'Overall Accuracy Score'
            ),
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.15
        )
        
        # 1. Product Intent Mean Convergence
        target = real_metrics.get('product_intent_mean', self.target_metrics.get('product_intent_mean', 0))
        phase3_val = phase3_metrics.get('product_intent_mean', 0)
        
        fig.add_trace(
            go.Scatter(x=[0], y=[phase3_val], mode='markers',
                      marker=dict(size=15, color='blue', line=dict(width=2, color='black')),
                      name='Phase 3 (Initial)', showlegend=True),
            row=1, col=1
        )
        
        fig.add_hline(y=target, line_dash="dash", line_color="green", 
                     annotation_text=f"Target: {target:.4f}",
                     row=1, col=1)
        
        if phase4_metrics:
            phase4_val = phase4_metrics.get('product_intent_mean', 0)
            fig.add_trace(
                go.Scatter(x=[1], y=[phase4_val], mode='markers',
                          marker=dict(size=15, color='red', symbol='square', line=dict(width=2, color='black')),
                          name='Phase 4 (Anchored)', showlegend=True),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=[0, 1], y=[phase3_val, phase4_val], mode='lines+markers',
                          line=dict(color='red', width=3), marker=dict(size=10),
                          name='Convergence Path', showlegend=False),
                row=1, col=1
            )
            if 'product_intent' in improvements:
                imp = improvements['product_intent']
                fig.add_annotation(
                    x=0.5, y=max(phase3_val, phase4_val) + 0.01,
                    text=f"✓ {imp['improvement_pct']:.1f}% Better",
                    showarrow=False, font=dict(color='green', size=12, family='Arial Black'),
                    bgcolor='yellow', bordercolor='green', borderwidth=2,
                    row=1, col=1
                )
        
        fig.update_xaxes(title_text="", range=[-0.5, 1.5], tickvals=[0, 1],
                        ticktext=['Phase 3<br>(Initial)', 'Phase 4<br>(Anchored)'], row=1, col=1)
        fig.update_yaxes(title_text="Product Intent Mean", row=1, col=1)
        
        # 2. Switching Rate Convergence
        target_switch = real_metrics.get('switching_rate', self.target_metrics.get('switching_rate', 0))
        phase3_switch = phase3_metrics.get('switching_rate', 0)
        
        fig.add_trace(
            go.Scatter(x=[0], y=[phase3_switch], mode='markers',
                      marker=dict(size=15, color='blue', line=dict(width=2, color='black')),
                      name='Phase 3 (Initial)', showlegend=False),
            row=1, col=2
        )
        
        fig.add_hline(y=target_switch, line_dash="dash", line_color="green",
                     annotation_text=f"Target: {target_switch:.4f}",
                     row=1, col=2)
        
        if phase4_metrics:
            phase4_switch = phase4_metrics.get('switching_rate', 0)
            fig.add_trace(
                go.Scatter(x=[1], y=[phase4_switch], mode='markers',
                          marker=dict(size=15, color='red', symbol='square', line=dict(width=2, color='black')),
                          name='Phase 4 (Anchored)', showlegend=False),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=[0, 1], y=[phase3_switch, phase4_switch], mode='lines+markers',
                          line=dict(color='red', width=3), marker=dict(size=10),
                          showlegend=False),
                row=1, col=2
            )
        
        fig.update_xaxes(title_text="", range=[-0.5, 1.5], tickvals=[0, 1],
                        ticktext=['Phase 3<br>(Initial)', 'Phase 4<br>(Anchored)'], row=1, col=2)
        fig.update_yaxes(title_text="Switching Rate", row=1, col=2)
        
        # 3. Category Comparison
        if real_metrics.get('category_intent_means'):
            categories = list(real_metrics['category_intent_means'].keys())
            phase3_cats = phase3_metrics.get('category_intent_means', {})
            phase4_cats = phase4_metrics.get('category_intent_means', {}) if phase4_metrics else {}
            
            phase3_vals = [phase3_cats.get(cat, 0) for cat in categories]
            real_vals = [real_metrics['category_intent_means'][cat] for cat in categories]
            phase4_vals = [phase4_cats.get(cat, 0) for cat in categories] if phase4_cats else []
            
            fig.add_trace(
                go.Bar(x=categories, y=phase3_vals, name='Phase 3', marker_color='blue', opacity=0.7),
                row=2, col=1
            )
            fig.add_trace(
                go.Bar(x=categories, y=real_vals, name='Real (Target)', marker_color='green', opacity=0.7),
                row=2, col=1
            )
            if phase4_vals:
                fig.add_trace(
                    go.Bar(x=categories, y=phase4_vals, name='Phase 4', marker_color='red', opacity=0.7),
                    row=2, col=1
                )
        
        fig.update_xaxes(title_text="Category", tickangle=-45, row=2, col=1)
        fig.update_yaxes(title_text="Mean Intent", row=2, col=1)
        
        # 4. Accuracy Improvement Summary
        if improvements:
            improvement_data = []
            labels = []
            colors_list = []
            
            for metric_name, imp_data in improvements.items():
                if metric_name != 'categories' and isinstance(imp_data, dict):
                    improvement = imp_data.get('improvement', 0)
                    improvement_pct = imp_data.get('improvement_pct', 0)
                    if improvement != 0:
                        improvement_data.append(improvement)
                        labels.append(f'{metric_name.replace("_", " ").title()}<br>({improvement_pct:+.1f}%)')
                        colors_list.append('green' if improvement > 0 else 'red')
            
            if improvement_data:
                fig.add_trace(
                    go.Bar(x=improvement_data, y=labels, orientation='h',
                          marker_color=colors_list, opacity=0.7,
                          name='Improvement', showlegend=False),
                    row=2, col=2
                )
        
        fig.update_xaxes(title_text="Error Reduction", row=2, col=2)
        fig.update_yaxes(title_text="", row=2, col=2)
        
        # 5. Time Series Trend
        if self.phase3_data is not None and 'timestamp' in self.phase3_data.columns:
            phase3_daily = self.phase3_data.groupby(self.phase3_data['timestamp'].dt.date)['intent_value'].mean()
            fig.add_trace(
                go.Scatter(x=list(phase3_daily.index), y=phase3_daily.values,
                          mode='lines+markers', name='Phase 3', line=dict(color='blue', width=2),
                          marker=dict(size=6)),
                row=3, col=1
            )
        
        if self.real_data is not None and 'timestamp' in self.real_data.columns:
            real_daily = self.real_data.groupby(self.real_data['timestamp'].dt.date)['intent_value'].mean()
            fig.add_trace(
                go.Scatter(x=list(real_daily.index), y=real_daily.values,
                          mode='lines+markers', name='Real', line=dict(color='green', width=2, dash='dash'),
                          marker=dict(size=6)),
                row=3, col=1
            )
        
        if self.phase4_data is not None and 'timestamp' in self.phase4_data.columns:
            phase4_daily = self.phase4_data.groupby(self.phase4_data['timestamp'].dt.date)['intent_value'].mean()
            fig.add_trace(
                go.Scatter(x=list(phase4_daily.index), y=phase4_daily.values,
                          mode='lines+markers', name='Phase 4', line=dict(color='red', width=2),
                          marker=dict(size=6, symbol='square')),
                row=3, col=1
            )
        
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Mean Intent", row=3, col=1)
        
        # 6. Overall Accuracy Score
        if improvements:
            phase3_total_error = sum([imp.get('phase3_error', 0) for imp in improvements.values() 
                                     if isinstance(imp, dict) and 'phase3_error' in imp])
            phase4_total_error = sum([imp.get('phase4_error', 0) for imp in improvements.values() 
                                     if isinstance(imp, dict) and 'phase4_error' in imp])
            n_metrics = len([imp for imp in improvements.values() if isinstance(imp, dict) and 'phase3_error' in imp])
            
            if n_metrics > 0:
                phase3_accuracy = 100 * (1 - phase3_total_error / n_metrics) if n_metrics > 0 else 0
                phase4_accuracy = 100 * (1 - phase4_total_error / n_metrics) if n_metrics > 0 else 0
                
                fig.add_trace(
                    go.Bar(x=['Phase 3<br>(Initial)', 'Phase 4<br>(Anchored)'],
                          y=[phase3_accuracy, phase4_accuracy],
                          marker_color=['blue', 'red'], opacity=0.7,
                          text=[f'{phase3_accuracy:.1f}%', f'{phase4_accuracy:.1f}%'],
                          textposition='outside', showlegend=False),
                    row=3, col=2
                )
                
                if phase4_accuracy > phase3_accuracy:
                    fig.add_annotation(
                        x=0.5, y=max(phase3_accuracy, phase4_accuracy) + 5,
                        text=f"✓ +{phase4_accuracy - phase3_accuracy:.1f}% Accuracy Gain",
                        showarrow=False, font=dict(color='green', size=12, family='Arial Black'),
                        bgcolor='lightgreen', bordercolor='green', borderwidth=2,
                        row=3, col=2
                    )
        
        fig.update_xaxes(title_text="", row=3, col=2)
        fig.update_yaxes(title_text="Accuracy (%)", range=[0, 105], row=3, col=2)
        
        # Update layout
        fig.update_layout(
            height=1400,
            title_text="<b>Ground Truth Anchoring: Phase 3 → Phase 4 Improvement Dashboard</b><br>" +
                      "<i>Showing how anchoring to real data improves simulation accuracy</i>",
            title_x=0.5,
            title_font_size=16,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)
        print(f"  ✓ Saved: {output_path}")
    
    def generate_all_visualizations(self, output_dir: str = 'phase4_output/visualizations'):
        """Generate all visualization plots"""
        print("\n" + "=" * 60)
        print("Generating Anchoring Visualizations")
        print("=" * 60)
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.plot_intent_distribution_comparison(
            os.path.join(output_dir, 'intent_distribution.png')
        )
        
        self.plot_metrics_comparison(
            os.path.join(output_dir, 'metrics_comparison.png')
        )
        
        self.plot_category_comparison(
            os.path.join(output_dir, 'category_comparison.png')
        )
        
        self.plot_convergence_path(
            os.path.join(output_dir, 'convergence_path.png')
        )
        
        # Create interactive dashboard
        self.create_interactive_dashboard(
            os.path.join(output_dir, 'anchoring_dashboard.html')
        )
        
        print("\n" + "=" * 60)
        print("All visualizations generated!")
        print("=" * 60)
        print(f"\nVisualizations saved to: {output_dir}/")
        print("  - intent_distribution.png: Distribution comparisons")
        print("  - metrics_comparison.png: Key metrics side-by-side")
        print("  - category_comparison.png: Category-level comparison")
        print("  - convergence_path.png: Convergence visualization")
        print("  - anchoring_dashboard.html: Interactive HTML dashboard")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize Phase 3 vs Phase 4 anchoring')
    parser.add_argument('--phase3_data', type=str, default='simulations/intent_trajectories.csv',
                       help='Path to Phase 3 simulation data')
    parser.add_argument('--real_data', type=str, default=None,
                       help='Path to real/ground truth data')
    parser.add_argument('--phase4_data', type=str, default=None,
                       help='Path to Phase 4 anchored simulation data')
    parser.add_argument('--output_dir', type=str, default='phase4_output/visualizations',
                       help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    visualizer = AnchoringVisualizer(
        phase3_data_path=args.phase3_data,
        real_data_path=args.real_data,
        phase4_data_path=args.phase4_data
    )
    
    visualizer.generate_all_visualizations(output_dir=args.output_dir)

