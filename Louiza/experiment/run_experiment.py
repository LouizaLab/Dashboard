"""
PART F: Main Experiment Runner
Runs the complete entropy reduction experiment end-to-end
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Optional

# Import experiment components
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_synthetic_revenue import SyntheticRevenueGenerator
from models.baseline import BaselineRevenueModel
from models.phase3_unanchored import Phase3UnanchoredModel
from models.phase4_anchored import Phase4AnchoredModel
from metrics.entropy import EntropyMetrics
from plots.visualizations import ExperimentVisualizer


def run_full_experiment(
    output_dir: str = 'experiment/results',
    revenue_data_path: Optional[str] = None,
    latents_data_path: Optional[str] = None,
    phase3_intent_path: str = 'simulations/intent_trajectories.csv',
    phase4_intent_path: Optional[str] = None,
    generate_revenue: bool = True
):
    """
    Run the complete entropy reduction experiment
    
    Args:
        output_dir: Output directory for results
        revenue_data_path: Path to existing revenue data (if None, generates new)
        latents_data_path: Path to existing latents data (if None, generates new)
        phase3_intent_path: Path to Phase 3 simulation outputs
        phase4_intent_path: Path to Phase 4 anchored simulation outputs (if None, uses Phase 3 with anchoring)
        generate_revenue: If True, generate new synthetic revenue data
    """
    print("=" * 80)
    print("ENTROPY REDUCTION EXPERIMENT")
    print("=" * 80)
    print("\nDemonstrating that Phase 4 (anchored) models produce:")
    print("  - Lower entropy")
    print("  - More stable forecasts")
    print("  - Better calibration")
    print("=" * 80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # PART A: Generate or load revenue data
    print("\n" + "=" * 80)
    print("PART A: Synthetic Revenue Dataset")
    print("=" * 80)
    
    if generate_revenue or revenue_data_path is None:
        print("Generating synthetic revenue data...")
        generator = SyntheticRevenueGenerator()
        revenue_df, latents_df = generator.generate_revenue()
        
        revenue_path = os.path.join(output_dir, 'revenue.csv')
        latents_path = os.path.join(output_dir, 'ground_truth_latents.csv')
        generator.save(revenue_df, latents_df, output_dir)
    else:
        print(f"Loading revenue data from {revenue_data_path}...")
        revenue_df = pd.read_csv(revenue_data_path)
        if latents_data_path:
            latents_df = pd.read_csv(latents_data_path)
        else:
            latents_df = None
    
    print(f"Revenue data shape: {revenue_df.shape}")
    print(f"Date range: {revenue_df['date'].min()} to {revenue_df['date'].max()}")
    
    # PART B: Load intent data
    print("\n" + "=" * 80)
    print("PART B: Loading Intent Data")
    print("=" * 80)
    
    print(f"Loading Phase 3 intent data from {phase3_intent_path}...")
    if os.path.exists(phase3_intent_path):
        phase3_intent = pd.read_csv(phase3_intent_path)
        print(f"Phase 3 intent shape: {phase3_intent.shape}")
    else:
        print(f"Warning: Phase 3 intent data not found at {phase3_intent_path}")
        print("Creating synthetic intent data for demonstration...")
        phase3_intent = _create_synthetic_intent_data(revenue_df)
    
    if phase4_intent_path and os.path.exists(phase4_intent_path):
        print(f"Loading Phase 4 intent data from {phase4_intent_path}...")
        phase4_intent = pd.read_csv(phase4_intent_path)
        print(f"Phase 4 intent shape: {phase4_intent.shape}")
    else:
        print("Phase 4 intent data not found. Using Phase 3 data with anchoring applied...")
        phase4_intent = phase3_intent.copy()  # Will be anchored in model
    
    # PART B: Fit Models
    print("\n" + "=" * 80)
    print("PART B: Fitting Forecast Models")
    print("=" * 80)
    
    # M0: Baseline
    print("\nFitting M0: Baseline Revenue Model...")
    model_m0 = BaselineRevenueModel(method='arima')
    model_m0.fit(revenue_df)
    
    # M1: Phase 3 Unanchored
    print("\nFitting M1: Phase 3 Unanchored LPM Model...")
    model_m1 = Phase3UnanchoredModel(phase3_intent)
    model_m1.fit(revenue_df)
    
    # M2: Phase 4 Anchored
    print("\nFitting M2: Phase 4 Anchored LPM Model...")
    # Create anchoring constraints from historical data
    anchoring_constraints = _create_anchoring_constraints(revenue_df)
    model_m2 = Phase4AnchoredModel(phase4_intent, anchoring_constraints)
    model_m2.fit(revenue_df)
    
    # Generate predictions
    print("\nGenerating predictions...")
    predictions_m0 = model_m0.predict(revenue_df)
    predictions_m1 = model_m1.predict(revenue_df)
    predictions_m2 = model_m2.predict(revenue_df)
    
    print(f"M0 predictions: {len(predictions_m0)}")
    print(f"M1 predictions: {len(predictions_m1)}")
    print(f"M2 predictions: {len(predictions_m2)}")
    
    # Filter to 2024 (prediction period)
    revenue_2024 = revenue_df[pd.to_datetime(revenue_df['date']) >= '2024-01-01'].copy()
    
    # PART C: Compute Metrics
    print("\n" + "=" * 80)
    print("PART C: Computing Entropy & Signal Quality Metrics")
    print("=" * 80)
    
    metrics_m0 = EntropyMetrics(predictions_m0, revenue_2024)
    metrics_m1 = EntropyMetrics(predictions_m1, revenue_2024)
    metrics_m2 = EntropyMetrics(predictions_m2, revenue_2024)
    
    all_metrics_m0 = metrics_m0.compute_all_metrics(latents_df)
    all_metrics_m1 = metrics_m1.compute_all_metrics(latents_df)
    all_metrics_m2 = metrics_m2.compute_all_metrics(latents_df)
    
    # Compute entropy DataFrames
    entropy_m0 = metrics_m0.compute_predictive_entropy()
    entropy_m1 = metrics_m1.compute_predictive_entropy()
    entropy_m2 = metrics_m2.compute_predictive_entropy()
    
    # Save metrics
    print("\nSaving metrics...")
    metrics_summary = {
        'M0_Baseline': all_metrics_m0,
        'M1_Phase3_Unanchored': all_metrics_m1,
        'M2_Phase4_Anchored': all_metrics_m2,
        'comparison': {
            'entropy_reduction_m2_vs_m0': (all_metrics_m0['mean_entropy'] - all_metrics_m2['mean_entropy']) / all_metrics_m0['mean_entropy'],
            'entropy_reduction_m2_vs_m1': (all_metrics_m1['mean_entropy'] - all_metrics_m2['mean_entropy']) / all_metrics_m1['mean_entropy'],
            'calibration_improvement_m2': all_metrics_m2['calibration']['calibration_error_80'] < all_metrics_m0['calibration']['calibration_error_80'],
            'stability_improvement_m2': all_metrics_m2['stability']['stability_score'] > all_metrics_m0['stability']['stability_score']
        }
    }
    
    def json_serializer(obj):
        """Custom JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer, np.int_)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float_)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(os.path.join(output_dir, 'metrics_summary.json'), 'w') as f:
        json.dump(metrics_summary, f, indent=2, default=json_serializer)
    
    # Print summary
    print("\n" + "=" * 80)
    print("METRICS SUMMARY")
    print("=" * 80)
    print(f"\nMean Predictive Entropy:")
    print(f"  M0 (Baseline):           {all_metrics_m0['mean_entropy']:.3f} nats")
    print(f"  M1 (Phase 3 Unanchored): {all_metrics_m1['mean_entropy']:.3f} nats")
    print(f"  M2 (Phase 4 Anchored):   {all_metrics_m2['mean_entropy']:.3f} nats")
    print(f"\nEntropy Reduction:")
    print(f"  M2 vs M0: {metrics_summary['comparison']['entropy_reduction_m2_vs_m0']*100:.1f}%")
    print(f"  M2 vs M1: {metrics_summary['comparison']['entropy_reduction_m2_vs_m1']*100:.1f}%")
    print(f"\nCalibration (80% Interval):")
    print(f"  M0: Coverage = {all_metrics_m0['calibration']['coverage_80']:.3f}, Error = {all_metrics_m0['calibration']['calibration_error_80']:.3f}")
    print(f"  M1: Coverage = {all_metrics_m1['calibration']['coverage_80']:.3f}, Error = {all_metrics_m1['calibration']['calibration_error_80']:.3f}")
    print(f"  M2: Coverage = {all_metrics_m2['calibration']['coverage_80']:.3f}, Error = {all_metrics_m2['calibration']['calibration_error_80']:.3f}")
    print(f"\nStability Score:")
    print(f"  M0: {all_metrics_m0['stability']['stability_score']:.3f}")
    print(f"  M1: {all_metrics_m1['stability']['stability_score']:.3f}")
    print(f"  M2: {all_metrics_m2['stability']['stability_score']:.3f}")
    
    # PART D: Generate Visualizations
    print("\n" + "=" * 80)
    print("PART D: Generating Visualizations")
    print("=" * 80)
    
    viz = ExperimentVisualizer(output_dir=os.path.join(output_dir, 'plots'))
    
    print("Generating fan charts...")
    viz.plot_revenue_forecast_fan_charts(
        predictions_m0, predictions_m1, predictions_m2, revenue_2024
    )
    
    print("Generating entropy over time plot...")
    viz.plot_predictive_entropy_over_time(entropy_m0, entropy_m1, entropy_m2)
    
    print("Generating entropy vs volatility plot...")
    viz.plot_preference_entropy_vs_revenue_volatility(entropy_m2, revenue_2024)
    
    print("Generating shock response plot...")
    shock_dates = _identify_shock_dates(revenue_df)
    viz.plot_shock_response_comparison(predictions_m1, predictions_m2, revenue_2024, shock_dates)
    
    print("Generating signal-to-noise ratio plot...")
    viz.plot_signal_to_noise_ratio(all_metrics_m0, all_metrics_m1, all_metrics_m2)
    
    print("Generating metrics comparison plot...")
    viz.plot_metrics_comparison(all_metrics_m0, all_metrics_m1, all_metrics_m2)
    
    print("Generating actual vs predicted Phase 4 plot...")
    viz.plot_actual_vs_predicted_phase4(predictions_m2, revenue_2024)
    
    # Save predictions
    predictions_m0.to_csv(os.path.join(output_dir, 'predictions_m0.csv'), index=False)
    predictions_m1.to_csv(os.path.join(output_dir, 'predictions_m1.csv'), index=False)
    predictions_m2.to_csv(os.path.join(output_dir, 'predictions_m2.csv'), index=False)
    
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved to: {output_dir}/")
    print("  - metrics_summary.json: All computed metrics")
    print("  - predictions_m0.csv: Baseline predictions")
    print("  - predictions_m1.csv: Phase 3 predictions")
    print("  - predictions_m2.csv: Phase 4 predictions")
    print("  - plots/: All visualizations")
    print("    - actual_vs_predicted_phase4.png: Actual vs Phase 4 predicted revenue")
    
    return {
        'metrics': metrics_summary,
        'predictions': {
            'm0': predictions_m0,
            'm1': predictions_m1,
            'm2': predictions_m2
        }
    }


def _create_anchoring_constraints(revenue_df: pd.DataFrame) -> Dict:
    """Create anchoring constraints from historical revenue data"""
    revenue_df['date'] = pd.to_datetime(revenue_df['date'])
    train_revenue = revenue_df[revenue_df['date'] < '2024-01-01'].copy()
    
    # Compute market shares
    total_by_brand = train_revenue.groupby('brand')['revenue'].sum()
    total_revenue = total_by_brand.sum()
    market_shares = total_by_brand / total_revenue
    
    # Create ranges (±5% around mean)
    market_share_ranges = {}
    for brand, share in market_shares.items():
        market_share_ranges[brand] = (max(0.05, share - 0.05), min(0.95, share + 0.05))
    
    # Demographic mix (by region)
    demographic_mix = {}
    for region in train_revenue['region'].unique():
        region_data = train_revenue[train_revenue['region'] == region]
        region_total = region_data.groupby('brand')['revenue'].sum()
        region_shares = region_total / region_total.sum()
        demographic_mix[region] = region_shares.to_dict()
    
    return {
        'market_share_ranges': market_share_ranges,
        'preference_stability_prior': 0.7,
        'demographic_mix': demographic_mix,
        'elasticity_bounds': {}  # Would be set from external data
    }


def _create_synthetic_intent_data(revenue_df: pd.DataFrame) -> pd.DataFrame:
    """Create synthetic intent data for demonstration"""
    intent_records = []
    
    revenue_df['date'] = pd.to_datetime(revenue_df['date'])
    
    for _, row in revenue_df.iterrows():
        # Create synthetic intent proportional to revenue (with noise)
        base_intent = np.random.uniform(0.3, 0.8)
        revenue_factor = row['revenue'] / revenue_df['revenue'].mean()
        intent_value = np.clip(base_intent * revenue_factor + np.random.normal(0, 0.1), 0, 1)
        
        intent_records.append({
            'timestamp': row['date'],
            'date': row['date'],
            'product_category': f"category_{hash(row['brand']) % 5}",
            'brand': row['brand'],
            'region': row['region'],
            'intent_value': intent_value,
            'product_id': f"prod_{hash(row['brand']) % 10}",
            'agent_id': f"agent_{hash((row['brand'], row['region'])) % 100}",
            'segment_id': f"seg_{hash(row['region']) % 5}"
        })
    
    return pd.DataFrame(intent_records)


def _identify_shock_dates(revenue_df: pd.DataFrame) -> list:
    """Identify shock dates (large revenue changes)"""
    revenue_df['date'] = pd.to_datetime(revenue_df['date'])
    revenue_df = revenue_df.sort_values(['brand', 'region', 'date'])
    revenue_df['revenue_change'] = revenue_df.groupby(['brand', 'region'])['revenue'].pct_change()
    
    # Find dates with large changes (>20%)
    shocks = revenue_df[abs(revenue_df['revenue_change']) > 0.20]
    shock_dates = shocks['date'].unique().tolist()
    
    return [pd.to_datetime(d) for d in shock_dates[:5]]  # Top 5 shocks


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run entropy reduction experiment')
    parser.add_argument('--output_dir', type=str, default='experiment/results',
                       help='Output directory')
    parser.add_argument('--revenue_data', type=str, default=None,
                       help='Path to existing revenue data')
    parser.add_argument('--phase3_intent', type=str, default='simulations/intent_trajectories.csv',
                       help='Path to Phase 3 intent data')
    parser.add_argument('--phase4_intent', type=str, default=None,
                       help='Path to Phase 4 intent data')
    parser.add_argument('--no_generate_revenue', action='store_true',
                       help='Skip revenue generation')
    
    args = parser.parse_args()
    
    run_full_experiment(
        output_dir=args.output_dir,
        revenue_data_path=args.revenue_data,
        phase3_intent_path=args.phase3_intent,
        phase4_intent_path=args.phase4_intent,
        generate_revenue=not args.no_generate_revenue
    )

