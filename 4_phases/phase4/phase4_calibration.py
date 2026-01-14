"""
Phase 4: Ground Truth Anchoring + Calibration
Calibrates simulation to match real intent data patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os

class IntentDataCalibrator:
    """
    Calibrates simulation to match real intent data patterns
    """
    
    def __init__(self, simulated_data: pd.DataFrame, real_data: Optional[pd.DataFrame] = None):
        """
        Args:
            simulated_data: DataFrame from Phase 3 simulation
            real_data: Optional real intent data for calibration
        """
        self.simulated_data = simulated_data.copy()
        self.real_data = real_data.copy() if real_data is not None else None
        
        # Ensure timestamp column
        if 'timestamp' in self.simulated_data.columns:
            self.simulated_data['timestamp'] = pd.to_datetime(self.simulated_data['timestamp'])
        if self.real_data is not None and 'timestamp' in self.real_data.columns:
            self.real_data['timestamp'] = pd.to_datetime(self.real_data['timestamp'])
    
    def compute_distribution_metrics(self, data: pd.DataFrame) -> Dict:
        """Compute distribution metrics for calibration"""
        metrics = {}
        
        # Product-level intent distribution
        if 'product_id' in data.columns and 'intent_value' in data.columns:
            product_intent = data.groupby('product_id')['intent_value'].agg(['mean', 'std', 'count'])
            metrics['product_intent_mean'] = product_intent['mean'].mean()
            metrics['product_intent_std'] = product_intent['std'].mean()
            metrics['product_coverage'] = len(product_intent)
        
        # Segment-level patterns
        if 'segment_id' in data.columns:
            segment_intent = data.groupby('segment_id')['intent_value'].agg(['mean', 'std'])
            metrics['segment_intent_means'] = segment_intent['mean'].to_dict()
            metrics['segment_intent_stds'] = segment_intent['std'].to_dict()
        
        # Category-level patterns
        if 'product_category' in data.columns:
            category_intent = data.groupby('product_category')['intent_value'].agg(['mean', 'std', 'count'])
            metrics['category_intent_means'] = category_intent['mean'].to_dict()
            metrics['category_intent_stds'] = category_intent['std'].to_dict()
            metrics['category_counts'] = category_intent['count'].to_dict()
        
        # Time-series drift
        if 'timestamp' in data.columns:
            data_sorted = data.sort_values('timestamp')
            data_sorted['date'] = data_sorted['timestamp'].dt.date
            daily_intent = data_sorted.groupby('date')['intent_value'].mean()
            
            if len(daily_intent) > 1:
                # Trend (slope)
                x = np.arange(len(daily_intent))
                y = daily_intent.values
                slope = np.polyfit(x, y, 1)[0]
                metrics['daily_trend'] = slope
                metrics['daily_mean'] = daily_intent.mean()
                metrics['daily_std'] = daily_intent.std()
        
        # Switching rates (how often agents change products)
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
        
        return metrics
    
    def compare_distributions(self) -> Dict:
        """Compare simulated vs real distributions"""
        sim_metrics = self.compute_distribution_metrics(self.simulated_data)
        
        if self.real_data is None:
            return {
                'simulated_metrics': sim_metrics,
                'calibration_needed': False,
                'message': 'No real data provided for calibration'
            }
        
        real_metrics = self.compute_distribution_metrics(self.real_data)
        
        # Compute differences
        differences = {}
        
        # Product-level differences
        if 'product_intent_mean' in sim_metrics and 'product_intent_mean' in real_metrics:
            differences['product_intent_mean_diff'] = (
                sim_metrics['product_intent_mean'] - real_metrics['product_intent_mean']
            )
        
        # Segment-level differences
        if 'segment_intent_means' in sim_metrics and 'segment_intent_means' in real_metrics:
            segment_diffs = {}
            all_segments = set(sim_metrics['segment_intent_means'].keys()) | set(real_metrics['segment_intent_means'].keys())
            for seg in all_segments:
                sim_mean = sim_metrics['segment_intent_means'].get(seg, 0)
                real_mean = real_metrics['segment_intent_means'].get(seg, 0)
                segment_diffs[seg] = sim_mean - real_mean
            differences['segment_differences'] = segment_diffs
        
        # Category-level differences
        if 'category_intent_means' in sim_metrics and 'category_intent_means' in real_metrics:
            category_diffs = {}
            all_categories = set(sim_metrics['category_intent_means'].keys()) | set(real_metrics['category_intent_means'].keys())
            for cat in all_categories:
                sim_mean = sim_metrics['category_intent_means'].get(cat, 0)
                real_mean = real_metrics['category_intent_means'].get(cat, 0)
                category_diffs[cat] = sim_mean - real_mean
            differences['category_differences'] = category_diffs
        
        # Trend differences
        if 'daily_trend' in sim_metrics and 'daily_trend' in real_metrics:
            differences['trend_difference'] = sim_metrics['daily_trend'] - real_metrics['daily_trend']
        
        return {
            'simulated_metrics': sim_metrics,
            'real_metrics': real_metrics,
            'differences': differences,
            'calibration_needed': True
        }
    
    def generate_calibration_report(self, output_path: Optional[str] = None) -> str:
        """Generate calibration report"""
        comparison = self.compare_distributions()
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Phase 4: Calibration Report")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        if not comparison['calibration_needed']:
            report_lines.append("No real data provided - showing simulated metrics only")
            report_lines.append("")
            sim_metrics = comparison['simulated_metrics']
            report_lines.append("Simulated Data Metrics:")
            report_lines.append(f"  Product intent mean: {sim_metrics.get('product_intent_mean', 'N/A'):.4f}")
            report_lines.append(f"  Switching rate: {sim_metrics.get('switching_rate', 'N/A'):.4f}")
            if 'category_intent_means' in sim_metrics:
                report_lines.append("  Category intent means:")
                for cat, mean in sim_metrics['category_intent_means'].items():
                    report_lines.append(f"    {cat}: {mean:.4f}")
        else:
            report_lines.append("Comparison: Simulated vs Real Data")
            report_lines.append("")
            
            diffs = comparison['differences']
            
            if 'product_intent_mean_diff' in diffs:
                report_lines.append(f"Product Intent Mean Difference: {diffs['product_intent_mean_diff']:.4f}")
            
            if 'category_differences' in diffs:
                report_lines.append("Category Intent Differences:")
                for cat, diff in diffs['category_differences'].items():
                    report_lines.append(f"  {cat}: {diff:+.4f}")
            
            if 'trend_difference' in diffs:
                report_lines.append(f"Trend Difference: {diffs['trend_difference']:.6f}")
            
            report_lines.append("")
            report_lines.append("Calibration Recommendations:")
            report_lines.append("  - Adjust segment state initialization if segment differences are large")
            report_lines.append("  - Adjust transition model parameters if switching rates differ")
            report_lines.append("  - Add macro context if trend differences are significant")
        
        report = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"Calibration report saved to {output_path}")
        
        return report

