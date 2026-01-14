#!/usr/bin/env python3
"""
CLI script for generating all visualizations.

Usage:
    python scripts/generate_all_plots.py \
        --run-id baseline_001 \
        --artifacts-dir runs/baseline_001/ \
        --output-dir plots/baseline_001/
"""

import argparse
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.plots import PlotGenerator
from data_engine.loaders import DataLoader


def main():
    parser = argparse.ArgumentParser(
        description="Generate all visualizations for Louiza Engine POC"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Run ID for plot naming"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        required=True,
        help="Directory containing simulation artifacts"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for plots"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        default=None,
        help="Data version for loading observed metrics (optional)"
    )
    parser.add_argument(
        "--personaset-path",
        type=str,
        default=None,
        help="Path to PersonaSet JSON (optional)"
    )
    parser.add_argument(
        "--anchoring-dir",
        type=str,
        default=None,
        help="Directory containing anchoring results (optional)"
    )
    parser.add_argument(
        "--baseline-dir",
        type=str,
        default=None,
        help="Directory containing baseline simulation results (for scenario comparison)"
    )
    
    args = parser.parse_args()
    
    print(f"Generating visualizations...")
    print(f"  Run ID: {args.run_id}")
    print(f"  Artifacts directory: {args.artifacts_dir}")
    print(f"  Output directory: {args.output_dir}")
    
    artifacts_path = Path(args.artifacts_dir)
    output_path = Path(args.output_dir)
    
    # Initialize plot generator
    generator = PlotGenerator(str(output_path))
    
    try:
        # Load simulation artifacts
        simulated_metrics = pd.read_csv(artifacts_path / "simulated_metrics_brand_week_region.csv")
        persona_contributions = pd.read_csv(artifacts_path / "persona_contributions.csv")
        
        print(f"\n✓ Loaded simulation artifacts")
        
        # 1. LPM Visualizations
        print("Generating LPM visualizations...")
        generator.plot_lpm_outcomes(simulated_metrics)
        generator.plot_persona_contributions(persona_contributions)
        print("  ✓ LPM plots generated")
        
        # 2. Data Engine Visualizations (if data version provided)
        if args.data_version:
            print("Generating Data Engine visualizations...")
            try:
                data_loader = DataLoader("data/synthetic", args.data_version)
                observed_metrics = data_loader.load_observed_metrics()
                price_schedule = data_loader.load_price_schedule()
                promo_schedule = data_loader.load_promo_schedule()
                
                generator.plot_data_engine_sanity(observed_metrics, price_schedule, promo_schedule)
                generator.plot_data_coverage(observed_metrics)
                print("  ✓ Data Engine plots generated")
            except Exception as e:
                print(f"  ⚠ Warning: Could not generate Data Engine plots: {e}")
        
        # 3. PME Visualizations (if PersonaSet provided)
        if args.personaset_path:
            print("Generating PME visualizations...")
            try:
                generator.plot_persona_overview(args.personaset_path)
                print("  ✓ PME plots generated")
            except Exception as e:
                print(f"  ⚠ Warning: Could not generate PME plots: {e}")
        
        # 4. Anchoring Visualizations (if anchoring directory provided)
        if args.anchoring_dir:
            print("Generating Anchoring visualizations...")
            try:
                anchoring_path = Path(args.anchoring_dir)
                anchored_metrics = pd.read_csv(anchoring_path / "anchored_metrics_brand_week_region.csv")
                anchoring_report = str(anchoring_path / "anchoring_report.json")
                anchoring_patch = str(anchoring_path / "anchoring_patch.json")
                
                # Before/after comparison
                if args.data_version:
                    data_loader = DataLoader("data/synthetic", args.data_version)
                    observed_metrics = data_loader.load_observed_metrics()
                    generator.plot_anchoring_before_after(
                        observed_metrics,
                        simulated_metrics,
                        anchored_metrics
                    )
                
                # Error reduction
                generator.plot_anchoring_error_reduction(anchoring_report)
                
                # Weight adjustments
                if args.personaset_path:
                    generator.plot_persona_weight_adjustments(
                        anchoring_patch,
                        args.personaset_path
                    )
                
                print("  ✓ Anchoring plots generated")
            except Exception as e:
                print(f"  ⚠ Warning: Could not generate Anchoring plots: {e}")
        
        # 5. Scenario Comparison (if baseline directory provided)
        if args.baseline_dir:
            print("Generating Scenario Comparison visualizations...")
            try:
                baseline_path = Path(args.baseline_dir)
                baseline_metrics = pd.read_csv(baseline_path / "simulated_metrics_brand_week_region.csv")
                
                generator.plot_scenario_comparison(
                    baseline_metrics,
                    simulated_metrics,
                    scenario_name=args.run_id
                )
                print("  ✓ Scenario comparison plots generated")
            except Exception as e:
                print(f"  ⚠ Warning: Could not generate Scenario Comparison plots: {e}")
        
        print(f"\n✓ All visualizations generated!")
        print(f"  Output directory: {args.output_dir}")
        print(f"  Plots saved with run ID: {args.run_id}")
        
    except Exception as e:
        print(f"\n✗ Error during plot generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

