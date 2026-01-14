#!/usr/bin/env python3
"""
CLI script for running anchoring calibration.

Usage:
    python scripts/run_anchoring.py \
        --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
        --simulated-data runs/baseline_001/simulated_metrics_brand_week_region.csv \
        --persona-contributions runs/baseline_001/persona_contributions.csv \
        --persona-version PersonaSet_v1.json \
        --output-dir runs/anchored_001/
"""

import argparse
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from anchoring.anchoring_runner import AnchoringRunner
from pme.pme_runner import PMERunner


def main():
    parser = argparse.ArgumentParser(
        description="Run anchoring calibration for Louiza Engine"
    )
    parser.add_argument(
        "--observed-data",
        type=str,
        required=True,
        help="Path to observed metrics CSV"
    )
    parser.add_argument(
        "--simulated-data",
        type=str,
        required=True,
        help="Path to simulated metrics CSV"
    )
    parser.add_argument(
        "--persona-contributions",
        type=str,
        required=True,
        help="Path to persona contributions CSV"
    )
    parser.add_argument(
        "--persona-version",
        type=str,
        required=True,
        help="Path to PersonaSet JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for anchoring results"
    )
    parser.add_argument(
        "--train-weeks",
        type=str,
        default=None,
        help="Comma-separated list of training weeks (e.g., '1,2,3,4,5,6,7,8')"
    )
    parser.add_argument(
        "--holdout-weeks",
        type=str,
        default=None,
        help="Comma-separated list of holdout weeks (e.g., '9,10')"
    )
    parser.add_argument(
        "--optimize-behavioral-param",
        type=str,
        default=None,
        help="Optional behavioral parameter to optimize (e.g., 'price_sensitivity')"
    )
    parser.add_argument(
        "--behavioral-persona-id",
        type=str,
        default=None,
        help="Optional persona ID for behavioral parameter optimization"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Weight for transactions error"
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=0.5,
        help="Weight for revenue error"
    )
    parser.add_argument(
        "--lambda-reg",
        type=float,
        default=0.01,
        help="Regularization strength (default: 0.01, lower = more aggressive, higher = more conservative)"
    )
    parser.add_argument(
        "--use-relative-error",
        action="store_true",
        default=True,
        help="Use relative error instead of absolute error (default: True, recommended)"
    )
    parser.add_argument(
        "--use-absolute-error",
        action="store_true",
        help="Use absolute error instead of relative error (overrides --use-relative-error)"
    )
    
    args = parser.parse_args()
    
    print(f"Running anchoring calibration...")
    print(f"  Observed data: {args.observed_data}")
    print(f"  Simulated data: {args.simulated_data}")
    print(f"  Persona contributions: {args.persona_contributions}")
    print(f"  Persona version: {args.persona_version}")
    
    # Load data
    try:
        observed_metrics = pd.read_csv(args.observed_data)
        simulated_metrics = pd.read_csv(args.simulated_data)
        persona_contributions = pd.read_csv(args.persona_contributions)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Load PersonaSet
    try:
        pme_runner = PMERunner(data_version="dummy")  # Data version not needed for loading
        personaset = pme_runner.load_personaset(args.persona_version)
    except Exception as e:
        print(f"Error loading PersonaSet: {e}")
        sys.exit(1)
    
    # Parse train/holdout weeks
    train_weeks = None
    holdout_weeks = None
    if args.train_weeks:
        train_weeks = [int(w) for w in args.train_weeks.split(",")]
    if args.holdout_weeks:
        holdout_weeks = [int(w) for w in args.holdout_weeks.split(",")]
    
    # Determine error type
    use_relative_error = args.use_relative_error and not args.use_absolute_error
    
    # Create and run anchoring
    try:
        runner = AnchoringRunner(
            personaset=personaset,
            observed_metrics=observed_metrics,
            simulated_metrics=simulated_metrics,
            persona_contributions=persona_contributions,
            alpha=args.alpha,
            beta=args.beta,
            lambda_reg=args.lambda_reg,
            use_relative_error=use_relative_error
        )
        
        results = runner.run(
            train_weeks=train_weeks,
            holdout_weeks=holdout_weeks,
            optimize_behavioral_param=args.optimize_behavioral_param,
            behavioral_persona_id=args.behavioral_persona_id
        )
        
        # Save results
        runner.save_results(results, args.output_dir)
        
        print(f"\n✓ Anchoring complete!")
        print(f"  Baseline train loss: {results['report']['baseline']['train_loss']:.2f}")
        print(f"  Final train loss: {results['report']['after_anchoring']['train_loss']:.2f}")
        print(f"  Improvement: {results['report']['improvement']['train_loss_reduction']:.1f}%")
        print(f"  Holdout loss: {results['report']['after_anchoring']['holdout_loss']:.2f}")
        print(f"  Output directory: {args.output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error during anchoring: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

