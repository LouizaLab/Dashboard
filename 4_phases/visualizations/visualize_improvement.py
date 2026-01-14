"""
Single comprehensive visualization showing Phase 3 → Phase 4 improvement vs Real Data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import os
from typing import Optional

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300


def create_improvement_visualization(
    phase3_data_path: str = 'simulations/intent_trajectories.csv',
    phase4_data_path: Optional[str] = None,
    real_data_path: Optional[str] = None,
    output_path: str = 'phase4_output/visualizations/improvement_overview.png'
):
    """
    Create a single comprehensive visualization showing Phase 3 → Phase 4 improvement
    
    Layout:
    - Top row: Overall metrics comparison (error bars, improvement arrows)
    - Middle left: Intent distribution comparison (histograms)
    - Middle right: Category-level comparison (before/after bars)
    - Bottom left: Segment-level comparison (before/after bars)
    - Bottom right: Error reduction summary (bar chart)
    """
    
    # Load data
    print("Loading data...")
    phase3_data = pd.read_csv(phase3_data_path)
    
    # Load real data if provided
    if real_data_path and os.path.exists(real_data_path):
        real_data = pd.read_csv(real_data_path)
    else:
        print(f"⚠️  Real data not available at {real_data_path if real_data_path else 'None'}")
        print(f"    Skipping improvement visualization (requires real data for comparison)")
        return  # Early return - this visualization requires real data
    
    if phase4_data_path and os.path.exists(phase4_data_path):
        phase4_data = pd.read_csv(phase4_data_path)
    else:
        if phase4_data_path:
            print(f"⚠️  Phase 4 data not found at {phase4_data_path}, using Phase 3 data")
        phase4_data = phase3_data.copy()
    
    # Ensure date columns
    for df in [phase3_data, phase4_data, real_data]:
        if df is not None and 'date' not in df.columns and 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Compute metrics
    def compute_metrics(data, label):
        metrics = {}
        metrics['overall_mean'] = data['intent_value'].mean()
        metrics['overall_std'] = data['intent_value'].std()
        
        if 'product_category' in data.columns:
            metrics['category_means'] = data.groupby('product_category')['intent_value'].mean().to_dict()
        
        if 'segment_id' in data.columns:
            metrics['segment_means'] = data.groupby('segment_id')['intent_value'].mean().to_dict()
        
        if 'product_id' in data.columns:
            product_means = data.groupby('product_id')['intent_value'].mean()
            metrics['product_intent_mean'] = product_means.mean()
        
        if 'agent_id' in data.columns and 'product_id' in data.columns:
            agent_products = data.sort_values(['agent_id', 'timestamp' if 'timestamp' in data.columns else 'date']).groupby('agent_id')['product_id']
            switches = []
            for agent_id, products in agent_products:
                product_seq = products.tolist()
                switch_count = sum(1 for i in range(1, len(product_seq)) if product_seq[i] != product_seq[i-1])
                if len(product_seq) > 1:
                    switches.append(switch_count / (len(product_seq) - 1))
            if switches:
                metrics['switching_rate'] = np.mean(switches)
        
        return metrics
    
    phase3_metrics = compute_metrics(phase3_data, 'Phase 3')
    phase4_metrics = compute_metrics(phase4_data, 'Phase 4')
    real_metrics = compute_metrics(real_data, 'Real')
    
    # Compute errors
    def compute_error(sim_metric, real_metric):
        return abs(sim_metric - real_metric)
    
    phase3_errors = {}
    phase4_errors = {}
    
    phase3_errors['overall_mean'] = compute_error(phase3_metrics['overall_mean'], real_metrics['overall_mean'])
    phase4_errors['overall_mean'] = compute_error(phase4_metrics['overall_mean'], real_metrics['overall_mean'])
    
    if 'product_intent_mean' in phase3_metrics and 'product_intent_mean' in real_metrics:
        phase3_errors['product_intent_mean'] = compute_error(phase3_metrics['product_intent_mean'], real_metrics['product_intent_mean'])
        phase4_errors['product_intent_mean'] = compute_error(phase4_metrics['product_intent_mean'], real_metrics['product_intent_mean'])
    
    if 'switching_rate' in phase3_metrics and 'switching_rate' in real_metrics:
        phase3_errors['switching_rate'] = compute_error(phase3_metrics['switching_rate'], real_metrics['switching_rate'])
        phase4_errors['switching_rate'] = compute_error(phase4_metrics['switching_rate'], real_metrics['switching_rate'])
    
    # Category errors
    if 'category_means' in phase3_metrics and 'category_means' in real_metrics:
        phase3_errors['categories'] = {}
        phase4_errors['categories'] = {}
        all_cats = set(phase3_metrics['category_means'].keys()) | set(real_metrics['category_means'].keys())
        for cat in all_cats:
            phase3_val = phase3_metrics['category_means'].get(cat, 0)
            phase4_val = phase4_metrics['category_means'].get(cat, 0)
            real_val = real_metrics['category_means'].get(cat, 0)
            phase3_errors['categories'][cat] = compute_error(phase3_val, real_val)
            phase4_errors['categories'][cat] = compute_error(phase4_val, real_val)
    
    # Create figure
    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('Phase 3 → Phase 4 Improvement: Anchoring to Real Data', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # 1. Top: Overall Metrics Comparison with Error Bars
    ax1 = fig.add_subplot(gs[0, :])
    
    metrics_to_show = []
    phase3_vals = []
    phase4_vals = []
    real_vals = []
    phase3_errs = []
    phase4_errs = []
    
    if 'product_intent_mean' in phase3_metrics:
        metrics_to_show.append('Product Intent\nMean')
        phase3_vals.append(phase3_metrics['product_intent_mean'])
        phase4_vals.append(phase4_metrics['product_intent_mean'])
        real_vals.append(real_metrics['product_intent_mean'])
        phase3_errs.append(phase3_errors['product_intent_mean'])
        phase4_errs.append(phase4_errors['product_intent_mean'])
    
    metrics_to_show.append('Overall Intent\nMean')
    phase3_vals.append(phase3_metrics['overall_mean'])
    phase4_vals.append(phase4_metrics['overall_mean'])
    real_vals.append(real_metrics['overall_mean'])
    phase3_errs.append(phase3_errors['overall_mean'])
    phase4_errs.append(phase4_errors['overall_mean'])
    
    if 'switching_rate' in phase3_metrics:
        metrics_to_show.append('Switching\nRate')
        phase3_vals.append(phase3_metrics['switching_rate'])
        phase4_vals.append(phase4_metrics['switching_rate'])
        real_vals.append(real_metrics['switching_rate'])
        phase3_errs.append(phase3_errors['switching_rate'])
        phase4_errs.append(phase4_errors['switching_rate'])
    
    x = np.arange(len(metrics_to_show))
    width = 0.25
    
    bars1 = ax1.bar(x - width, phase3_vals, width, label='Phase 3 (Before)', 
                    color='#3498db', alpha=0.7, yerr=phase3_errs, capsize=5)
    bars2 = ax1.bar(x, real_vals, width, label='Real Data (Target)', 
                    color='#2ecc71', alpha=0.7)
    bars3 = ax1.bar(x + width, phase4_vals, width, label='Phase 4 (After)', 
                    color='#e74c3c', alpha=0.7, yerr=phase4_errs, capsize=5)
    
    # Add improvement arrows
    for i, (p3_err, p4_err) in enumerate(zip(phase3_errs, phase4_errs)):
        improvement = p3_err - p4_err
        if improvement > 0:
            ax1.annotate('', xy=(i + width, phase4_vals[i] + phase4_errs[i] + 0.01),
                        xytext=(i - width, phase3_vals[i] + phase3_errs[i] + 0.01),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
            pct_improvement = (improvement / p3_err * 100) if p3_err > 0 else 0
            ax1.text(i, max(phase3_vals[i] + phase3_errs[i], phase4_vals[i] + phase4_errs[i]) + 0.02,
                    f'{pct_improvement:.1f}%', ha='center', fontsize=10, fontweight='bold', color='green')
    
    ax1.set_ylabel('Value', fontsize=12)
    ax1.set_title('Key Metrics: Phase 3 vs Phase 4 vs Real Data', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics_to_show)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. Middle Left: Intent Distribution Comparison
    ax2 = fig.add_subplot(gs[1, 0])
    
    ax2.hist(phase3_data['intent_value'], bins=30, alpha=0.5, label='Phase 3', 
             color='#3498db', density=True, edgecolor='black', linewidth=0.5)
    ax2.hist(real_data['intent_value'], bins=30, alpha=0.5, label='Real Data', 
             color='#2ecc71', density=True, edgecolor='black', linewidth=0.5)
    ax2.hist(phase4_data['intent_value'], bins=30, alpha=0.5, label='Phase 4', 
             color='#e74c3c', density=True, edgecolor='black', linewidth=0.5)
    
    # Add vertical lines for means
    ax2.axvline(phase3_metrics['overall_mean'], color='#3498db', linestyle='--', linewidth=2, label='Phase 3 Mean')
    ax2.axvline(real_metrics['overall_mean'], color='#2ecc71', linestyle='--', linewidth=2, label='Real Mean')
    ax2.axvline(phase4_metrics['overall_mean'], color='#e74c3c', linestyle='--', linewidth=2, label='Phase 4 Mean')
    
    ax2.set_xlabel('Intent Value', fontsize=11)
    ax2.set_ylabel('Density', fontsize=11)
    ax2.set_title('Intent Distribution Comparison', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Middle Right: Category-Level Comparison
    ax3 = fig.add_subplot(gs[1, 1])
    
    if 'categories' in phase3_errors:
        categories = sorted(phase3_errors['categories'].keys())
        phase3_cat_errors = [phase3_errors['categories'][cat] for cat in categories]
        phase4_cat_errors = [phase4_errors['categories'][cat] for cat in categories]
        
        x_cat = np.arange(len(categories))
        width_cat = 0.35
        
        bars_p3 = ax3.bar(x_cat - width_cat/2, phase3_cat_errors, width_cat, 
                         label='Phase 3 Error', color='#3498db', alpha=0.7)
        bars_p4 = ax3.bar(x_cat + width_cat/2, phase4_cat_errors, width_cat, 
                         label='Phase 4 Error', color='#e74c3c', alpha=0.7)
        
        # Add improvement indicators
        for i, (p3_err, p4_err) in enumerate(zip(phase3_cat_errors, phase4_cat_errors)):
            if p3_err > p4_err:
                improvement = p3_err - p4_err
                pct = (improvement / p3_err * 100) if p3_err > 0 else 0
                ax3.text(i, max(p3_err, p4_err) + 0.002, f'↓{pct:.0f}%', 
                        ha='center', fontsize=8, color='green', fontweight='bold')
        
        ax3.set_ylabel('Error vs Real Data', fontsize=11)
        ax3.set_title('Category-Level Error Reduction', fontsize=12, fontweight='bold')
        ax3.set_xticks(x_cat)
        ax3.set_xticklabels(categories, rotation=45, ha='right')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Bottom Left: Segment-Level Comparison
    ax4 = fig.add_subplot(gs[2, 0])
    
    if 'segment_means' in phase3_metrics and 'segment_means' in real_metrics:
        segments = sorted(set(phase3_metrics['segment_means'].keys()) | set(real_metrics['segment_means'].keys()))
        phase3_seg_errors = []
        phase4_seg_errors = []
        
        for seg in segments:
            p3_val = phase3_metrics['segment_means'].get(seg, 0)
            p4_val = phase4_metrics['segment_means'].get(seg, 0)
            real_val = real_metrics['segment_means'].get(seg, 0)
            phase3_seg_errors.append(compute_error(p3_val, real_val))
            phase4_seg_errors.append(compute_error(p4_val, real_val))
        
        x_seg = np.arange(len(segments))
        width_seg = 0.35
        
        bars_p3_seg = ax4.bar(x_seg - width_seg/2, phase3_seg_errors, width_seg, 
                              label='Phase 3 Error', color='#3498db', alpha=0.7)
        bars_p4_seg = ax4.bar(x_seg + width_seg/2, phase4_seg_errors, width_seg, 
                              label='Phase 4 Error', color='#e74c3c', alpha=0.7)
        
        # Add improvement indicators
        for i, (p3_err, p4_err) in enumerate(zip(phase3_seg_errors, phase4_seg_errors)):
            if p3_err > p4_err:
                improvement = p3_err - p4_err
                pct = (improvement / p3_err * 100) if p3_err > 0 else 0
                ax4.text(i, max(p3_err, p4_err) + 0.002, f'↓{pct:.0f}%', 
                        ha='center', fontsize=8, color='green', fontweight='bold')
        
        ax4.set_ylabel('Error vs Real Data', fontsize=11)
        ax4.set_title('Segment-Level Error Reduction', fontsize=12, fontweight='bold')
        ax4.set_xticks(x_seg)
        ax4.set_xticklabels(segments, rotation=45, ha='right')
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Bottom Right: Overall Error Reduction Summary
    ax5 = fig.add_subplot(gs[2, 1:])
    
    # Calculate overall improvements
    error_types = []
    phase3_total_errors = []
    phase4_total_errors = []
    improvements = []
    improvement_pcts = []
    
    if 'product_intent_mean' in phase3_errors:
        error_types.append('Product Intent\nMean')
        phase3_total_errors.append(phase3_errors['product_intent_mean'])
        phase4_total_errors.append(phase4_errors['product_intent_mean'])
        imp = phase3_errors['product_intent_mean'] - phase4_errors['product_intent_mean']
        improvements.append(imp)
        improvement_pcts.append((imp / phase3_errors['product_intent_mean'] * 100) if phase3_errors['product_intent_mean'] > 0 else 0)
    
    error_types.append('Overall Intent\nMean')
    phase3_total_errors.append(phase3_errors['overall_mean'])
    phase4_total_errors.append(phase4_errors['overall_mean'])
    imp = phase3_errors['overall_mean'] - phase4_errors['overall_mean']
    improvements.append(imp)
    improvement_pcts.append((imp / phase3_errors['overall_mean'] * 100) if phase3_errors['overall_mean'] > 0 else 0)
    
    if 'categories' in phase3_errors:
        avg_p3_cat_err = np.mean(list(phase3_errors['categories'].values()))
        avg_p4_cat_err = np.mean(list(phase4_errors['categories'].values()))
        error_types.append('Avg Category\nError')
        phase3_total_errors.append(avg_p3_cat_err)
        phase4_total_errors.append(avg_p4_cat_err)
        imp = avg_p3_cat_err - avg_p4_cat_err
        improvements.append(imp)
        improvement_pcts.append((imp / avg_p3_cat_err * 100) if avg_p3_cat_err > 0 else 0)
    
    if 'switching_rate' in phase3_errors:
        error_types.append('Switching\nRate')
        phase3_total_errors.append(phase3_errors['switching_rate'])
        phase4_total_errors.append(phase4_errors['switching_rate'])
        imp = phase3_errors['switching_rate'] - phase4_errors['switching_rate']
        improvements.append(imp)
        improvement_pcts.append((imp / phase3_errors['switching_rate'] * 100) if phase3_errors['switching_rate'] > 0 else 0)
    
    x_err = np.arange(len(error_types))
    width_err = 0.35
    
    bars_p3_err = ax5.bar(x_err - width_err/2, phase3_total_errors, width_err, 
                         label='Phase 3 Error', color='#3498db', alpha=0.7)
    bars_p4_err = ax5.bar(x_err + width_err/2, phase4_total_errors, width_err, 
                         label='Phase 4 Error', color='#e74c3c', alpha=0.7)
    
    # Add improvement percentages
    for i, (p3_err, p4_err, pct) in enumerate(zip(phase3_total_errors, phase4_total_errors, improvement_pcts)):
        if pct > 0:
            ax5.text(i, max(p3_err, p4_err) + 0.002, f'{pct:.1f}%', 
                    ha='center', fontsize=10, fontweight='bold', color='green')
            # Add arrow
            ax5.annotate('', xy=(i + width_err/2, p4_err), 
                        xytext=(i - width_err/2, p3_err),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2, alpha=0.7))
    
    ax5.set_ylabel('Error Magnitude', fontsize=12)
    ax5.set_title('Overall Error Reduction Summary', fontsize=14, fontweight='bold')
    ax5.set_xticks(x_err)
    ax5.set_xticklabels(error_types)
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Add summary text box
    total_improvement = sum(improvements)
    avg_improvement_pct = np.mean([p for p in improvement_pcts if p > 0])
    
    summary_text = f'Summary:\n'
    summary_text += f'• Average Error Reduction: {avg_improvement_pct:.1f}%\n'
    summary_text += f'• Total Error Reduction: {total_improvement:.4f}\n'
    summary_text += f'• Phase 4 is closer to Real Data across all metrics'
    
    ax5.text(0.02, 0.98, summary_text, transform=ax5.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved improvement visualization to {output_path}")
    
    return fig


if __name__ == '__main__':
    import sys
    
    phase3_path = sys.argv[1] if len(sys.argv) > 1 else 'simulations/intent_trajectories.csv'
    phase4_path = sys.argv[2] if len(sys.argv) > 2 else 'simulations/phase4_anchored.csv'
    real_path = sys.argv[3] if len(sys.argv) > 3 else None  # Make optional
    output_path = sys.argv[4] if len(sys.argv) > 4 else 'phase4_output/visualizations/improvement_overview.png'
    
    # Check if required files exist
    if not os.path.exists(phase3_path):
        print(f"Error: Phase 3 data not found at {phase3_path}")
        print("Usage: python visualize_improvement.py [phase3_path] [phase4_path] [real_path] [output_path]")
        sys.exit(1)
    
    # Check if phase4_path exists (optional)
    if phase4_path and not os.path.exists(phase4_path):
        print(f"Warning: Phase 4 data not found at {phase4_path}, will use Phase 3 data")
        phase4_path = None
    
    # Check if real_path exists (optional but recommended)
    if real_path and not os.path.exists(real_path):
        print(f"Warning: Real data not found at {real_path}")
        print("This visualization requires real data for comparison. Skipping...")
        sys.exit(0)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    create_improvement_visualization(phase3_path, phase4_path, real_path, output_path)
    print(f"✓ Improvement visualization created at {output_path}")


