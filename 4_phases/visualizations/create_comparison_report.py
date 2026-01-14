"""
Create a comprehensive comparison report showing Phase 3 vs Phase 4 vs Real Data
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def compute_metrics(data: pd.DataFrame, label: str = "") -> dict:
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
        metrics['product_coverage'] = len(product_intent)
    
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
        data_sorted['date'] = pd.to_datetime(data_sorted['timestamp']).dt.date
        daily_intent = data_sorted.groupby('date')['intent_value'].mean()
        if len(daily_intent) > 1:
            x = np.arange(len(daily_intent))
            y = daily_intent.values
            metrics['daily_trend'] = np.polyfit(x, y, 1)[0]
            metrics['daily_mean'] = daily_intent.mean()
            metrics['daily_std'] = daily_intent.std()
    
    return metrics

def create_comparison_report(output_path: str = 'phase4_output/comparison_report.md'):
    """Create comprehensive comparison report"""
    
    print("Creating comparison report...")
    
    # Load data
    phase3_path = 'simulations/intent_trajectories.csv'
    phase4_path = 'simulations/phase4_anchored.csv'
    real_path = 'data/real_intent_data.csv'
    
    phase3_data = None
    phase4_data = None
    real_data = None
    
    if os.path.exists(phase3_path):
        phase3_data = pd.read_csv(phase3_path)
        phase3_data['timestamp'] = pd.to_datetime(phase3_data['timestamp'])
        print(f"  ✓ Loaded Phase 3: {len(phase3_data)} interactions")
    
    if os.path.exists(phase4_path):
        phase4_data = pd.read_csv(phase4_path)
        phase4_data['timestamp'] = pd.to_datetime(phase4_data['timestamp'])
        print(f"  ✓ Loaded Phase 4: {len(phase4_data)} interactions")
    
    if os.path.exists(real_path):
        real_data = pd.read_csv(real_path)
        real_data['timestamp'] = pd.to_datetime(real_data['timestamp'])
        print(f"  ✓ Loaded Real Data: {len(real_data)} interactions")
    
    if phase3_data is None:
        print("  ⚠ Phase 3 data not found")
        return
    
    # Compute metrics
    phase3_metrics = compute_metrics(phase3_data, "Phase 3")
    phase4_metrics = compute_metrics(phase4_data, "Phase 4") if phase4_data is not None else None
    real_metrics = compute_metrics(real_data, "Real") if real_data is not None else None
    
    # Load target metrics if real data not available
    if real_metrics is None:
        target_path = 'phase4_output/target_metrics.json'
        if os.path.exists(target_path):
            with open(target_path, 'r') as f:
                target_data = json.load(f)
                real_metrics = {
                    'product_intent_mean': target_data.get('product_intent_mean'),
                    'switching_rate': target_data.get('switching_rate'),
                    'category_intent_means': target_data.get('category_intent_means', {}),
                    'segment_intent_means': target_data.get('segment_intent_means', {}),
                    'daily_trend': target_data.get('daily_trend')
                }
                print("  ✓ Using target metrics from file")
    
    # Create report
    report_lines = []
    report_lines.append("# Phase 3 vs Phase 4 vs Real Data Comparison")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Overview")
    report_lines.append("")
    report_lines.append("This report compares Phase 3 (Initial Approximation), Phase 4 (Ground Truth Anchored), and Real Data (Ground Truth) to demonstrate improvement.")
    report_lines.append("")
    
    # Key Metrics Table
    report_lines.append("## Key Metrics Comparison")
    report_lines.append("")
    report_lines.append("| Metric | Phase 3 (Initial) | Real Data (Target) | Phase 4 (Anchored) | Phase 3 Error | Phase 4 Error | Improvement |")
    report_lines.append("|--------|-------------------|---------------------|---------------------|---------------|---------------|-------------|")
    
    if real_metrics:
        # Product Intent Mean
        phase3_val = phase3_metrics.get('product_intent_mean', 'N/A')
        real_val = real_metrics.get('product_intent_mean', 'N/A')
        phase4_val = phase4_metrics.get('product_intent_mean', 'N/A') if phase4_metrics else 'N/A'
        
        if phase3_val != 'N/A' and real_val != 'N/A':
            phase3_error = abs(phase3_val - real_val)
            if phase4_val != 'N/A':
                phase4_error = abs(phase4_val - real_val)
                improvement = phase3_error - phase4_error
                improvement_pct = (improvement / phase3_error * 100) if phase3_error > 0 else 0
                improvement_str = f"{improvement:.4f} ({improvement_pct:+.1f}%)"
                phase4_val_str = f"{phase4_val:.4f}"
                phase4_error_str = f"{phase4_error:.4f}"
            else:
                phase4_error = 'N/A'
                improvement_str = 'N/A'
                phase4_val_str = 'N/A'
                phase4_error_str = 'N/A'
            
            report_lines.append(f"| Product Intent Mean | {phase3_val:.4f} | {real_val:.4f} | {phase4_val_str} | {phase3_error:.4f} | {phase4_error_str} | {improvement_str} |")
        
        # Switching Rate
        phase3_val = phase3_metrics.get('switching_rate', 'N/A')
        real_val = real_metrics.get('switching_rate', 'N/A')
        phase4_val = phase4_metrics.get('switching_rate', 'N/A') if phase4_metrics else 'N/A'
        
        if phase3_val != 'N/A' and real_val != 'N/A':
            phase3_error = abs(phase3_val - real_val)
            if phase4_val != 'N/A':
                phase4_error = abs(phase4_val - real_val)
                improvement = phase3_error - phase4_error
                improvement_pct = (improvement / phase3_error * 100) if phase3_error > 0 else 0
                improvement_str = f"{improvement:.4f} ({improvement_pct:+.1f}%)"
                phase4_val_str = f"{phase4_val:.4f}"
                phase4_error_str = f"{phase4_error:.4f}"
            else:
                phase4_error = 'N/A'
                improvement_str = 'N/A'
                phase4_val_str = 'N/A'
                phase4_error_str = 'N/A'
            
            report_lines.append(f"| Switching Rate | {phase3_val:.4f} | {real_val:.4f} | {phase4_val_str} | {phase3_error:.4f} | {phase4_error_str} | {improvement_str} |")
        
        # Daily Trend
        phase3_val = phase3_metrics.get('daily_trend', 'N/A')
        real_val = real_metrics.get('daily_trend', 'N/A')
        phase4_val = phase4_metrics.get('daily_trend', 'N/A') if phase4_metrics else 'N/A'
        
        if phase3_val != 'N/A' and real_val != 'N/A':
            phase3_error = abs(phase3_val - real_val)
            if phase4_val != 'N/A':
                phase4_error = abs(phase4_val - real_val)
                improvement = phase3_error - phase4_error
                improvement_pct = (improvement / phase3_error * 100) if phase3_error > 0 else 0
                improvement_str = f"{improvement:.6f} ({improvement_pct:+.1f}%)"
                phase4_val_str = f"{phase4_val:.6f}"
                phase4_error_str = f"{phase4_error:.6f}"
            else:
                phase4_error = 'N/A'
                improvement_str = 'N/A'
                phase4_val_str = 'N/A'
                phase4_error_str = 'N/A'
            
            report_lines.append(f"| Daily Trend | {phase3_val:.6f} | {real_val:.6f} | {phase4_val_str} | {phase3_error:.6f} | {phase4_error_str} | {improvement_str} |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Category-Level Comparison
    if real_metrics and real_metrics.get('category_intent_means'):
        report_lines.append("## Category-Level Comparison")
        report_lines.append("")
        report_lines.append("| Category | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |")
        report_lines.append("|----------|---------|-----------|---------|---------------|---------------|-------------|")
        
        phase3_cats = phase3_metrics.get('category_intent_means', {})
        phase4_cats = phase4_metrics.get('category_intent_means', {}) if phase4_metrics else {}
        real_cats = real_metrics.get('category_intent_means', {})
        
        for cat in sorted(real_cats.keys()):
            phase3_val = phase3_cats.get(cat, 'N/A')
            real_val = real_cats.get(cat, 'N/A')
            phase4_val = phase4_cats.get(cat, 'N/A') if phase4_cats else 'N/A'
            
            if phase3_val != 'N/A' and real_val != 'N/A':
                phase3_error = abs(phase3_val - real_val)
                if phase4_val != 'N/A':
                    phase4_error = abs(phase4_val - real_val)
                    improvement = phase3_error - phase4_error
                    improvement_pct = (improvement / phase3_error * 100) if phase3_error > 0 else 0
                    status = "✅" if improvement > 0 else "⚠️"
                    improvement_str = f"{improvement:.4f} ({improvement_pct:+.1f}%) {status}"
                    phase4_val_str = f"{phase4_val:.4f}"
                    phase4_error_str = f"{phase4_error:.4f}"
                else:
                    phase4_error = 'N/A'
                    improvement_str = 'N/A'
                    phase4_val_str = 'N/A'
                    phase4_error_str = 'N/A'
                
                report_lines.append(f"| {cat} | {phase3_val:.4f} | {real_val:.4f} | {phase4_val_str} | {phase3_error:.4f} | {phase4_error_str} | {improvement_str} |")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
    
    # Segment-Level Comparison
    if real_metrics and real_metrics.get('segment_intent_means'):
        report_lines.append("## Segment-Level Comparison")
        report_lines.append("")
        report_lines.append("| Segment | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |")
        report_lines.append("|---------|---------|-----------|---------|---------------|---------------|-------------|")
        
        phase3_segs = phase3_metrics.get('segment_intent_means', {})
        phase4_segs = phase4_metrics.get('segment_intent_means', {}) if phase4_metrics else {}
        real_segs = real_metrics.get('segment_intent_means', {})
        
        for seg in sorted(real_segs.keys()):
            phase3_val = phase3_segs.get(seg, 'N/A')
            real_val = real_segs.get(seg, 'N/A')
            phase4_val = phase4_segs.get(seg, 'N/A') if phase4_segs else 'N/A'
            
            if phase3_val != 'N/A' and real_val != 'N/A':
                phase3_error = abs(phase3_val - real_val)
                if phase4_val != 'N/A':
                    phase4_error = abs(phase4_val - real_val)
                    improvement = phase3_error - phase4_error
                    improvement_pct = (improvement / phase3_error * 100) if phase3_error > 0 else 0
                    status = "✅" if improvement > 0 else "⚠️"
                    improvement_str = f"{improvement:.4f} ({improvement_pct:+.1f}%) {status}"
                    phase4_val_str = f"{phase4_val:.4f}"
                    phase4_error_str = f"{phase4_error:.4f}"
                else:
                    phase4_error = 'N/A'
                    improvement_str = 'N/A'
                    phase4_val_str = 'N/A'
                    phase4_error_str = 'N/A'
                
                report_lines.append(f"| {seg} | {phase3_val:.4f} | {real_val:.4f} | {phase4_val_str} | {phase3_error:.4f} | {phase4_error_str} | {improvement_str} |")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append("")
    
    if phase4_metrics and real_metrics:
        # Calculate overall improvement
        total_phase3_error = 0
        total_phase4_error = 0
        n_metrics = 0
        
        # Product intent mean
        if phase3_metrics.get('product_intent_mean') and real_metrics.get('product_intent_mean'):
            total_phase3_error += abs(phase3_metrics['product_intent_mean'] - real_metrics['product_intent_mean'])
            if phase4_metrics.get('product_intent_mean'):
                total_phase4_error += abs(phase4_metrics['product_intent_mean'] - real_metrics['product_intent_mean'])
                n_metrics += 1
        
        # Switching rate
        if phase3_metrics.get('switching_rate') and real_metrics.get('switching_rate'):
            total_phase3_error += abs(phase3_metrics['switching_rate'] - real_metrics['switching_rate'])
            if phase4_metrics.get('switching_rate'):
                total_phase4_error += abs(phase4_metrics['switching_rate'] - real_metrics['switching_rate'])
                n_metrics += 1
        
        if n_metrics > 0:
            avg_phase3_error = total_phase3_error / n_metrics
            avg_phase4_error = total_phase4_error / n_metrics
            overall_improvement = avg_phase3_error - avg_phase4_error
            improvement_pct = (overall_improvement / avg_phase3_error * 100) if avg_phase3_error > 0 else 0
            
            report_lines.append(f"### Overall Error Reduction")
            report_lines.append("")
            report_lines.append(f"- **Phase 3 Average Error:** {avg_phase3_error:.4f}")
            report_lines.append(f"- **Phase 4 Average Error:** {avg_phase4_error:.4f}")
            report_lines.append(f"- **Overall Improvement:** {overall_improvement:.4f} ({improvement_pct:+.1f}% better)")
            report_lines.append("")
            
            if improvement_pct > 0:
                report_lines.append("✅ **Phase 4 successfully reduces error compared to Phase 3**")
            else:
                report_lines.append("⚠️ **Phase 4 error similar to Phase 3 - may need more calibration**")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## File Locations")
    report_lines.append("")
    report_lines.append("- **Phase 3 Data:** `simulations/intent_trajectories.csv`")
    report_lines.append("- **Phase 4 Data:** `simulations/phase4_anchored.csv`")
    report_lines.append("- **Real Data:** `data/real_intent_data.csv`")
    report_lines.append("- **Visualizations:** `phase4_output/visualizations/`")
    report_lines.append("- **Calibration Metrics:** `phase4_output/calibration_metrics.json`")
    report_lines.append("")
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"  ✓ Saved: {output_path}")
    
    # Also create JSON version
    json_path = output_path.replace('.md', '.json')
    comparison_data = {
        'phase3_metrics': phase3_metrics,
        'phase4_metrics': phase4_metrics,
        'real_metrics': real_metrics,
        'generated': datetime.now().isoformat()
    }
    
    with open(json_path, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=str)
    
    print(f"  ✓ Saved: {json_path}")

if __name__ == '__main__':
    create_comparison_report()

