#!/usr/bin/env python3
"""
CLI script for initializing seed personas.

Usage:
    python scripts/initialize_personas.py \
        --data-version data_2026_01_08_run01 \
        --output PersonaSet_v1.json \
        --num-personas 10
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pme.pme_runner import PMERunner
from common.versioning import generate_personaset_version


def main():
    parser = argparse.ArgumentParser(
        description="Initialize seed personas for Louiza Engine POC"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        required=True,
        help="Data version ID (e.g., data_2026_01_08_run01)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="PersonaSet_v1.json",
        help="Output file path for PersonaSet JSON"
    )
    parser.add_argument(
        "--num-personas",
        type=int,
        default=10,
        help="Number of seed personas to create (8-12 recommended)"
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Optional PersonaSet version (auto-generated if not provided)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.num_personas < 1 or args.num_personas > 20:
        print(f"Error: Number of personas must be between 1 and 20, got {args.num_personas}")
        sys.exit(1)
    
    print(f"Initializing seed personas...")
    print(f"  Data version: {args.data_version}")
    print(f"  Number of personas: {args.num_personas}")
    print(f"  Output file: {args.output}")
    
    # Initialize PME runner
    runner = PMERunner(data_version=args.data_version)
    
    # Create seed personas
    try:
        personaset = runner.initialize_seed_personas(
            num_personas=args.num_personas,
            version=args.version
        )
        
        print(f"\n✓ Created PersonaSet: {personaset.version}")
        print(f"  PME run ID: {runner.pme_run_id}")
        print(f"  Number of personas: {len(personaset.personas)}")
        
        # Validate
        validation = runner.validate_personaset(personaset)
        if not validation["valid"]:
            print(f"\n⚠ Validation warnings:")
            for error in validation["errors"]:
                print(f"  - {error}")
        else:
            print(f"  Total weight: {validation['total_weight']:.4f}")
            print(f"  Active personas: {validation['num_active']}")
        
        # Save
        runner.save_personaset(personaset, args.output)
        print(f"\n✓ Saved PersonaSet to: {args.output}")
        
        # Print persona summary
        print(f"\nPersonas:")
        for persona in personaset.personas:
            print(f"  - {persona.persona_id}: {persona.explainability.human_label}")
            print(f"    Weight: {persona.population_weight.global_weight:.4f}")
            print(f"    Price sensitivity: {persona.behavioral_params.price_sensitivity:.2f}")
            print(f"    Promo responsiveness: {persona.behavioral_params.promo_responsiveness:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n✓ Persona initialization complete!")
    print(f"  Use PersonaSet version '{personaset.version}' in downstream layers.")


if __name__ == "__main__":
    main()

