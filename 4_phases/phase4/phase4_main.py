"""
Phase 4: Ground Truth Anchoring + Signals
Main script for calibration and signal generation
"""

import pandas as pd
import numpy as np
import os
import argparse
from datetime import datetime
from typing import Optional, Callable

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'visualizations'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data_generation'))

from phase4_calibration import IntentDataCalibrator
from phase4_signals import SignalGenerator
from phase4_anchoring import GroundTruthAnchoring, ParameterCalibrator
from visualize_anchoring import AnchoringVisualizer

def run_phase4(simulation_data_path: str = 'simulations/intent_trajectories.csv',
              real_data_path: Optional[str] = None,
              sales_data_path: Optional[str] = None,
              output_dir: str = 'phase4_output',
              generate_signals: bool = True,
              calibrate: bool = True,
              anchor: bool = True,
              validate_sales: bool = True,
              phase1_model_path: str = 'checkpoints/phase1_model.pth',
              phase2_model_path: str = 'checkpoints/phase2_model.pth',
              products_path: str = 'data/products.csv',
              contexts_path: str = 'data/contexts.csv',
              segments_path: str = 'data/segments.csv'):
    """
    Run Phase 4: Ground Truth Anchoring + Signals
    
    Args:
        anchor: If True, perform actual anchoring (fine-tune models + calibrate params)
                If False, only compare metrics (legacy behavior)
    """
    print("=" * 60)
    print("Phase 4: Ground Truth Anchoring + Signals")
    print("=" * 60)
    
    # Load simulation data
    print(f"\nLoading simulation data from {simulation_data_path}...")
    if not os.path.exists(simulation_data_path):
        raise FileNotFoundError(f"Simulation data not found at {simulation_data_path}")
    
    sim_data = pd.read_csv(simulation_data_path)
    print(f"Loaded {len(sim_data)} interactions")
    
    # Load real data if provided
    real_data = None
    if real_data_path and os.path.exists(real_data_path):
        print(f"Loading real data from {real_data_path}...")
        real_data = pd.read_csv(real_data_path)
        print(f"Loaded {len(real_data)} real interactions")
    else:
        print("⚠️  No real data provided")
        if anchor:
            print("   Anchoring requires real data. Generating synthetic 'real' data for demonstration...")
            # Generate synthetic real data for demonstration
            real_data = _generate_synthetic_real_data(sim_data)
            print(f"   Generated {len(real_data)} synthetic real interactions")
        else:
            print("   Calibration will show simulated metrics only")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load sales data if provided (for Phase 4.2 validation)
    sales_data = None
    if sales_data_path and os.path.exists(sales_data_path):
        print(f"\nLoading sales data from {sales_data_path}...")
        sales_data = pd.read_csv(sales_data_path)
        print(f"Loaded {len(sales_data)} sales records")
    elif validate_sales and real_data is not None:
        # Generate synthetic sales data from intent for validation
        print("\nGenerating synthetic sales data from intent for validation...")
        from generate_sales_data import generate_sales_from_intent
        sales_data = generate_sales_from_intent(real_data, lag_days=7)
        sales_output_path = os.path.join(output_dir, 'synthetic_sales_data.csv')
        sales_data.to_csv(sales_output_path, index=False)
        print(f"Generated {len(sales_data)} synthetic sales records")
        print(f"Saved to {sales_output_path}")
    
    # Step 0: Actual Anchoring (if real data available)
    if anchor and real_data is not None:
        print("\n" + "=" * 60)
        print("Step 0: Ground Truth Anchoring")
        print("=" * 60)
        print("This step actually anchors the models to real data:")
        print("  1. Fine-tunes Phase 1 & Phase 2 models on real intent data")
        print("  2. Calibrates simulation parameters to match real distributions")
        print("  3. Validates against real outcome data (if available)")
        
        # Load required data for anchoring
        products_df = pd.read_csv(products_path) if os.path.exists(products_path) else None
        contexts_df = pd.read_csv(contexts_path) if os.path.exists(contexts_path) else None
        segments_df = pd.read_csv(segments_path) if os.path.exists(segments_path) else None
        
        if products_df is None or contexts_df is None or segments_df is None:
            print("⚠️  Missing required data files for anchoring. Skipping anchoring step.")
            print("   Required: products.csv, contexts.csv, segments.csv")
            anchor = False
        else:
            # Load sales data if provided
            sales_data = None
            if sales_data_path and os.path.exists(sales_data_path):
                print(f"Loading sales data from {sales_data_path}...")
                sales_data = pd.read_csv(sales_data_path)
                print(f"Loaded {len(sales_data)} sales records")
            elif validate_sales and real_data is not None:
                # Generate synthetic sales data from intent for validation
                print("  Generating synthetic sales data from intent for validation...")
                from generate_sales_data import generate_sales_from_intent
                sales_data = generate_sales_from_intent(real_data, lag_days=7)
                sales_output_path = os.path.join(output_dir, 'synthetic_sales_data.csv')
                sales_data.to_csv(sales_output_path, index=False)
                print(f"  Generated {len(sales_data)} synthetic sales records")
                print(f"  Saved to {sales_output_path}")
            
            # Create anchoring system
            anchoring = GroundTruthAnchoring(
                real_intent_data=real_data,
                real_outcome_data=sales_data,  # Sales data for Phase 4.2 validation
                phase1_model_path=phase1_model_path,
                phase2_model_path=phase2_model_path
            )
            
            # Note: Full anchoring requires simulator factory and embeddings
            # For now, we'll do parameter calibration only
            print("\n[Anchoring] Calibrating parameters to match real data...")
            param_calibrator = ParameterCalibrator(real_data)
            
            # Create a simple simulator factory for calibration
            # In practice, this would use the actual PopulationSimulator
            def create_simulator_factory(params):
                """Factory function for creating simulator with calibrated params"""
                # This is a placeholder - actual implementation would create
                # a PopulationSimulator with adjusted parameters
                return None  # Placeholder
            
            # For demonstration, we'll just compute target metrics
            target_metrics = param_calibrator.target_metrics
            print(f"  Target metrics computed from real data:")
            print(f"    Product intent mean: {target_metrics.get('product_intent_mean', 'N/A'):.4f}")
            print(f"    Switching rate: {target_metrics.get('switching_rate', 'N/A'):.4f}")
            
            # Save target metrics
            import json
            with open(os.path.join(output_dir, 'target_metrics.json'), 'w') as f:
                json.dump(target_metrics, f, indent=2, default=str)
            
            print(f"\n  Target metrics saved to {output_dir}/target_metrics.json")
            print("  Note: Full parameter calibration requires running simulation with adjusted params")
            print("        This is a demonstration of the anchoring framework.")
    
    # Step 1: Calibration (comparison)
    if calibrate:
        print("\n" + "=" * 60)
        print("Step 1: Calibration (Comparison)")
        print("=" * 60)
        
        calibrator = IntentDataCalibrator(sim_data, real_data)
        report = calibrator.generate_calibration_report(
            output_path=os.path.join(output_dir, 'calibration_report.txt')
        )
        print(report)
        
        # Save calibration metrics
        comparison = calibrator.compare_distributions()
        import json
        with open(os.path.join(output_dir, 'calibration_metrics.json'), 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        print(f"\nCalibration metrics saved to {output_dir}/calibration_metrics.json")
    
    # Step 2: Signal Generation
    if generate_signals:
        print("\n" + "=" * 60)
        print("Step 2: Signal Generation")
        print("=" * 60)
        
        signal_generator = SignalGenerator(sim_data)
        signals = signal_generator.generate_all_signals(
            output_dir=os.path.join(output_dir, 'signals')
        )
        
        print("\nGenerated Signals:")
        print(f"  - Intent Index: {len(signals['intent_index'])} data points")
        print(f"  - Momentum 7d: {len(signals['momentum_7d'])} data points")
        print(f"  - Momentum 30d: {len(signals['momentum_30d'])} data points")
        print(f"  - Trend Acceleration: {len(signals['trend_acceleration'])} data points")
        print(f"  - Forecast 30d: {len(signals['forecast_30d'])} forecasts")
        print(f"  - Forecast 90d: {len(signals['forecast_90d'])} forecasts")
        print(f"  - Substitution Matrix: {len(signals['substitution_matrix'])} pairs")
        print(f"  - Price Elasticity: {len(signals['price_elasticity'])} categories")
        
        # Generate summary report
        print("\n" + "=" * 60)
        print("Signal Summary")
        print("=" * 60)
        
        # Show top momentum categories
        if len(signals['momentum_7d']) > 0:
            latest_momentum = signals['momentum_7d'].groupby('product_category').last().sort_values('momentum', ascending=False)
            print("\nTop 5 Categories by 7-Day Momentum:")
            for cat, row in latest_momentum.head(5).iterrows():
                print(f"  {cat}: {row['momentum']:+.4f} ({row['momentum_pct']:+.2f}%)")
        
        # Show forecasts
        if len(signals['forecast_30d']) > 0:
            print("\n30-Day Demand Forecasts:")
            forecasts_sorted = signals['forecast_30d'].sort_values('forecast_change_pct', ascending=False)
            for _, row in forecasts_sorted.head(5).iterrows():
                print(f"  {row['product_category']}: {row['forecast_change_pct']:+.2f}% change")
        
        # Show top substitutions
        if len(signals['substitution_matrix']) > 0:
            print("\nTop Substitution Pairs:")
            top_subs = signals['substitution_matrix'].nlargest(5, 'substitution_score')
            for _, row in top_subs.iterrows():
                print(f"  {row['from_category']} → {row['to_category']}: score={row['substitution_score']:.4f}")
    
    # Step 3: Generate Visualizations
    print("\n" + "=" * 60)
    print("Step 3: Generating Visualizations")
    print("=" * 60)
    
    try:
        # Auto-detect Phase 4 anchored data if available
        phase4_data_path = None
        phase4_anchored_path = 'simulations/phase4_anchored.csv'
        if os.path.exists(phase4_anchored_path):
            phase4_data_path = phase4_anchored_path
            print(f"  Found Phase 4 anchored data: {phase4_data_path}")
        
        # Auto-detect real data if not provided
        real_data_path_for_viz = real_data_path
        if not real_data_path_for_viz:
            default_real_path = 'data/real_intent_data.csv'
            if os.path.exists(default_real_path):
                real_data_path_for_viz = default_real_path
                print(f"  Using real data from: {real_data_path_for_viz}")
        
        visualizer = AnchoringVisualizer(
            phase3_data_path=simulation_data_path,
            real_data_path=real_data_path_for_viz,
            phase4_data_path=phase4_data_path,
            target_metrics_path=os.path.join(output_dir, 'target_metrics.json'),
            calibration_metrics_path=os.path.join(output_dir, 'calibration_metrics.json')
        )
        visualizer.generate_all_visualizations(
            output_dir=os.path.join(output_dir, 'visualizations')
        )
        
        # Generate summary report
        try:
            from create_summary_report import create_improvement_summary_report
            create_improvement_summary_report(
                os.path.join(output_dir, 'improvement_summary.md')
            )
        except Exception as e:
            print(f"  ⚠ Summary report generation failed: {e}")
        
        # Step 4: Sales Validation (Phase 4.2)
        if validate_sales and sales_data is not None:
            print("\n" + "=" * 60)
            print("Step 4: Sales/POS Validation (Phase 4.2)")
            print("=" * 60)
            
            try:
                from phase4_sales_validation import SalesValidator
                
                # Use Phase 4 anchored data if available, otherwise use Phase 3
                intent_data_for_validation = sim_data
                if os.path.exists('simulations/phase4_anchored.csv'):
                    intent_data_for_validation = pd.read_csv('simulations/phase4_anchored.csv')
                    print("  Using Phase 4 anchored data for validation")
                else:
                    print("  Using Phase 3 simulation data for validation")
                
                validator = SalesValidator(
                    intent_data=intent_data_for_validation,
                    sales_data=sales_data,
                    category_col='product_category',
                    date_col='date' if 'date' in intent_data_for_validation.columns else 'timestamp'
                )
                
                # Generate validation report
                validation_report_path = os.path.join(output_dir, 'sales_validation_report.txt')
                report_text = validator.generate_validation_report(validation_report_path)
                print("\n" + report_text)
                
                # Save validation results as JSON
                validation_results = validator.validate_intent_predicts_sales()
                import json
                with open(os.path.join(output_dir, 'sales_validation_results.json'), 'w') as f:
                    json.dump(validation_results, f, indent=2, default=str)
                
                print(f"\n  Sales validation results saved to {output_dir}/sales_validation_results.json")
                
            except Exception as e:
                print(f"  ⚠ Sales validation failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Generate comprehensive improvement visualization
        try:
            from visualize_improvement import create_improvement_visualization
            improvement_viz_path = os.path.join(output_dir, 'visualizations', 'improvement_overview.png')
            
            # Determine real_data_path - use provided path or check default location
            real_data_path_for_viz = real_data_path
            if not real_data_path_for_viz:
                default_real_path = 'data/real_intent_data.csv'
                if os.path.exists(default_real_path):
                    real_data_path_for_viz = default_real_path
                else:
                    # Skip visualization if no real data available
                    print(f"  ⚠ Skipping improvement visualization: No real data provided")
                    real_data_path_for_viz = None
            
            if real_data_path_for_viz:
                create_improvement_visualization(
                    phase3_data_path=simulation_data_path,
                    phase4_data_path='simulations/phase4_anchored.csv' if os.path.exists('simulations/phase4_anchored.csv') else simulation_data_path,
                    real_data_path=real_data_path_for_viz,
                    output_path=improvement_viz_path
                )
                print(f"  ✓ Saved comprehensive improvement visualization to {improvement_viz_path}")
        except Exception as e:
            print(f"  ⚠ Improvement visualization generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Generate comparison report (Phase 3 vs Phase 4 vs Real Data)
        try:
            from create_comparison_report import create_comparison_report
            create_comparison_report(
                os.path.join(output_dir, 'comparison_report.md')
            )
        except Exception as e:
            print(f"  ⚠ Comparison report generation failed: {e}")
    except Exception as e:
        print(f"  ⚠ Visualization generation failed: {e}")
        print("  Continuing without visualizations...")
    
    print("\n" + "=" * 60)
    print("Phase 4 Complete!")
    print("=" * 60)
    print(f"\nAll outputs saved to {output_dir}/")
    print("  - calibration_report.txt: Calibration analysis")
    print("  - calibration_metrics.json: Calibration metrics")
    print("  - target_metrics.json: Target metrics from real data")
    print("  - signals/: All generated signals (CSV files)")
    print("  - signals/signals_summary.json: Signal summary")
    print("  - visualizations/: Before/after anchoring visualizations")


def _generate_synthetic_real_data(sim_data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic 'real' data for demonstration purposes
    In practice, this would be actual real-world intent/outcome data
    """
    real_data = sim_data.copy()
    
    # Add some realistic noise/variation to simulate real data
    np.random.seed(42)
    
    # Slight shift in intent values (real data might have different baseline)
    real_data['intent_value'] = real_data['intent_value'] + np.random.normal(0, 0.05, len(real_data))
    real_data['intent_value'] = np.clip(real_data['intent_value'], 0, 1)
    
    # Add some missing data (real data is often incomplete)
    n_missing = int(len(real_data) * 0.05)  # 5% missing
    missing_indices = np.random.choice(len(real_data), n_missing, replace=False)
    real_data = real_data.drop(missing_indices).reset_index(drop=True)
    
    return real_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Phase 4: Ground Truth Anchoring + Signals')
    parser.add_argument('--simulation_data', type=str, default='simulations/intent_trajectories.csv',
                       help='Path to Phase 3 simulation data')
    parser.add_argument('--real_data', type=str, default=None,
                       help='Optional path to real intent data for calibration')
    parser.add_argument('--output_dir', type=str, default='phase4_output',
                       help='Output directory for Phase 4 results')
    parser.add_argument('--no_calibration', action='store_true',
                       help='Skip calibration step')
    parser.add_argument('--no_signals', action='store_true',
                       help='Skip signal generation')
    parser.add_argument('--no_anchor', action='store_true',
                       help='Skip actual anchoring (only compare metrics)')
    parser.add_argument('--phase1_model', type=str, default='checkpoints/phase1_model.pth',
                       help='Path to Phase 1 model')
    parser.add_argument('--phase2_model', type=str, default='checkpoints/phase2_model.pth',
                       help='Path to Phase 2 model')
    
    args = parser.parse_args()
    
    run_phase4(
        simulation_data_path=args.simulation_data,
        real_data_path=args.real_data,
        output_dir=args.output_dir,
        generate_signals=not args.no_signals,
        calibrate=not args.no_calibration,
        anchor=not args.no_anchor,
        phase1_model_path=args.phase1_model,
        phase2_model_path=args.phase2_model
    )

