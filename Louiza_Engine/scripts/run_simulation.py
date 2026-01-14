#!/usr/bin/env python3
"""
CLI script for running LPM simulations.

Usage:
    python scripts/run_simulation.py \
        --persona-version PersonaSet_v1 \
        --data-version data_2026_01_08_run01 \
        --scenario configs/baseline_scenario.json \
        --seed 123 \
        --num-agents 200000 \
        --output-dir runs/baseline_001/
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lpm.simulator import LPMSimulator
from pme.pme_runner import PMERunner
from data_engine.loaders import DataLoader


def load_scenario(scenario_path: str) -> dict:
    """Load scenario configuration from JSON file."""
    with open(scenario_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Run LPM simulation for Louiza Engine"
    )
    parser.add_argument(
        "--persona-version",
        type=str,
        required=True,
        help="PersonaSet version (e.g., PersonaSet_v1) or path to PersonaSet JSON"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        required=True,
        help="Data version ID (e.g., data_2026_01_08_run01)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        required=True,
        help="Path to scenario configuration JSON file"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=10000,
        help="Number of agents to simulate"
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=1,
        help="Starting week ID"
    )
    parser.add_argument(
        "--num-weeks",
        type=int,
        default=None,
        help="Number of weeks to simulate (defaults to scenario time_horizon_weeks if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for simulation results"
    )
    
    args = parser.parse_args()
    
    # Load scenario first to get time_horizon_weeks
    try:
        scenario_config = load_scenario(args.scenario)
    except FileNotFoundError:
        print(f"Error: Scenario file not found: {args.scenario}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in scenario file: {e}")
        sys.exit(1)
    
    # Use scenario's time_horizon_weeks if --num-weeks not provided
    if args.num_weeks is None:
        args.num_weeks = scenario_config.get("time_horizon_weeks", 12)
    
    print(f"Running LPM simulation...")
    print(f"  Persona version: {args.persona_version}")
    print(f"  Data version: {args.data_version}")
    print(f"  Scenario: {args.scenario}")
    print(f"  Seed: {args.seed}")
    print(f"  Number of agents: {args.num_agents}")
    print(f"  Weeks: {args.start_week} to {args.start_week + args.num_weeks - 1}")
    if args.num_weeks == scenario_config.get("time_horizon_weeks", 12):
        print(f"  (Using scenario time_horizon_weeks: {args.num_weeks})")
    
    # Load PersonaSet
    try:
        pme_runner = PMERunner(data_version=args.data_version)
        if Path(args.persona_version).exists():
            personaset = pme_runner.load_personaset(args.persona_version)
        else:
            # Try to find PersonaSet file
            personaset_path = Path(args.persona_version)
            if not personaset_path.suffix:
                personaset_path = Path(f"{args.persona_version}.json")
            if personaset_path.exists():
                personaset = pme_runner.load_personaset(str(personaset_path))
            else:
                print(f"Error: PersonaSet file not found: {args.persona_version}")
                sys.exit(1)
    except Exception as e:
        print(f"Error loading PersonaSet: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Load data
    try:
        data_loader = DataLoader("data/synthetic", args.data_version)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Create and run simulator
    try:
        simulator = LPMSimulator(
            personaset=personaset,
            data_loader=data_loader,
            scenario_config=scenario_config,
            num_agents=args.num_agents,
            seed=args.seed
        )
        
        print(f"\n✓ Simulator initialized")
        print(f"  Brands: {len(simulator.brand_ids)}")
        print(f"  Regions: {len(simulator.regions)}")
        
        print(f"\nRunning simulation...")
        results = simulator.run(
            start_week=args.start_week,
            num_weeks=args.num_weeks,
            output_dir=args.output_dir
        )
        
        print(f"\n✓ Simulation complete!")
        print(f"  Simulated metrics: {len(results['simulated_metrics'])} rows")
        print(f"  Persona contributions: {len(results['persona_contributions'])} rows")
        print(f"  Output directory: {args.output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

