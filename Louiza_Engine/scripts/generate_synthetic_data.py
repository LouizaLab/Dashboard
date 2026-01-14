#!/usr/bin/env python3
"""
CLI script for generating synthetic datasets.

Usage:
    python scripts/generate_synthetic_data.py \
        --config configs/synthetic_config.json \
        --seed 42 \
        --output-dir data/synthetic/
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_engine.config import SyntheticDataConfig
from data_engine.generator import SyntheticDataGenerator
from data_engine.catalog import DataCatalog
from common.versioning import generate_data_version


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic datasets for Louiza Engine POC"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to synthetic data configuration JSON file"
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory for generated datasets"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        default=None,
        help="Optional data version ID (auto-generated if not provided)"
    )
    parser.add_argument(
        "--catalog-file",
        type=str,
        default="data/catalog.json",
        help="Path to catalog file for metadata tracking"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config_dict = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    
    # Create config object
    try:
        config = SyntheticDataConfig(**config_dict)
        config.seed = args.seed
    except Exception as e:
        print(f"Error: Invalid configuration: {e}")
        sys.exit(1)
    
    # Generate data version ID
    data_version = args.data_version or generate_data_version()
    
    # Output directory (generator will create version subdirectory)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating synthetic data...")
    print(f"  Data version: {data_version}")
    print(f"  Seed: {args.seed}")
    print(f"  Output directory: {output_dir / data_version}")
    print(f"  Configuration: {config_dict}")
    
    # Initialize generator
    generator = SyntheticDataGenerator(
        config=config,
        seed=args.seed,
        data_version=data_version
    )
    
    # Generate all datasets
    try:
        file_paths = generator.generate_all(str(output_dir))
        print(f"\n✓ Generated {len(file_paths)} tables:")
        for table_name, file_path in file_paths.items():
            print(f"  - {table_name}: {file_path}")
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Register in catalog
    try:
        catalog = DataCatalog(args.catalog_file)
        catalog.register_dataset(
            version_id=data_version,
            generation_config=config.model_dump(),
            random_seed=args.seed,
            file_paths=file_paths,
            metadata={
                "output_dir": str(output_dir),
                "num_tables": len(file_paths)
            }
        )
        print(f"\n✓ Registered in catalog: {args.catalog_file}")
    except Exception as e:
        print(f"\n⚠ Warning: Failed to register in catalog: {e}")
    
    print(f"\n✓ Synthetic data generation complete!")
    print(f"  Data version: {data_version}")
    print(f"  Use this version ID in downstream layers.")


if __name__ == "__main__":
    main()

