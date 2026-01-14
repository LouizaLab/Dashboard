#!/usr/bin/env python3
"""
Script to prepare and validate custom data for Louiza Engine.

Usage:
    python scripts/prepare_custom_data.py <your_data_dir> <output_version>
    
Example:
    python scripts/prepare_custom_data.py data/my_raw_data data_2026_01_15_custom01
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime


def create_data_version(your_data_dir: str, output_version: str):
    """
    Transform your data into Louiza Engine format.
    
    Args:
        your_data_dir: Directory containing your raw data files
        output_version: Version ID for the output (e.g., "data_2026_01_15_custom01")
    """
    your_data_path = Path(your_data_dir)
    output_path = Path("data/synthetic") / output_version
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from: {your_data_path}")
    print(f"Output version: {output_version}")
    
    # ============================================================================
    # STEP 1: Define your mappings
    # ============================================================================
    # TODO: Customize these mappings to match your data
    
    brand_mapping = {
        # "Your Brand Name": "BRAND_01",
        # "Another Brand": "BRAND_02",
        # Add your brand mappings here
    }
    
    region_mapping = {
        # "Your Region Name": "REGION_01",
        # "Another Region": "REGION_02",
        # Add your region mappings here
    }
    
    if not brand_mapping or not region_mapping:
        print("\n⚠️  WARNING: You need to define brand_mapping and region_mapping!")
        print("   Edit this script and add your mappings in the create_data_version function.")
        print("\n   Example:")
        print('   brand_mapping = {"Burger King": "BRAND_01", "McDonald\'s": "BRAND_02"}')
        return False
    
    # ============================================================================
    # STEP 2: Load your data files
    # ============================================================================
    # Adjust file names to match your actual files
    
    try:
        # Expected files (adjust names as needed)
        revenue_file = your_data_path / "revenue_data.csv"
        price_file = your_data_path / "price_data.csv"
        promo_file = your_data_path / "promo_data.csv"
        
        # Load data
        if revenue_file.exists():
            your_revenue = pd.read_csv(revenue_file)
            print(f"✓ Loaded revenue data: {len(your_revenue)} rows")
        else:
            print(f"✗ Revenue file not found: {revenue_file}")
            print("  Expected: revenue_data.csv")
            return False
        
        if price_file.exists():
            your_prices = pd.read_csv(price_file)
            print(f"✓ Loaded price data: {len(your_prices)} rows")
        else:
            print(f"⚠️  Price file not found: {price_file}")
            print("  Will create default price schedule")
            your_prices = None
        
        if promo_file.exists():
            your_promos = pd.read_csv(promo_file)
            print(f"✓ Loaded promo data: {len(your_promos)} rows")
        else:
            print(f"⚠️  Promo file not found: {promo_file}")
            print("  Will create default promo schedule")
            your_promos = None
            
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False
    
    # ============================================================================
    # STEP 3: Transform observed metrics
    # ============================================================================
    # Adjust column names to match your data
    
    try:
        # Map your column names to required columns
        # TODO: Adjust these mappings to match your actual column names
        observed_metrics = pd.DataFrame({
            "week_id": your_revenue["week"],  # Adjust column name
            "brand_id": your_revenue["brand"].map(brand_mapping),  # Adjust column name
            "region_id": your_revenue["region"].map(region_mapping),  # Adjust column name
            "transactions_obs": your_revenue["transactions"],  # Adjust column name
            "revenue_obs": your_revenue["revenue"],  # Adjust column name
            "confidence_weight": 1.0  # Or calculate from your data quality metrics
        })
        
        # Check for missing mappings
        missing_brands = observed_metrics[observed_metrics["brand_id"].isna()]["brand"].unique() if "brand" in your_revenue.columns else []
        missing_regions = observed_metrics[observed_metrics["region_id"].isna()]["region"].unique() if "region" in your_revenue.columns else []
        
        if len(missing_brands) > 0:
            print(f"⚠️  WARNING: Unmapped brands: {missing_brands}")
        if len(missing_regions) > 0:
            print(f"⚠️  WARNING: Unmapped regions: {missing_regions}")
        
        # Drop rows with missing mappings
        observed_metrics = observed_metrics.dropna(subset=["brand_id", "region_id"])
        
        print(f"✓ Created observed_metrics: {len(observed_metrics)} rows")
        
    except KeyError as e:
        print(f"✗ Error: Column not found in your data: {e}")
        print("  Please adjust column mappings in the script")
        return False
    
    # ============================================================================
    # STEP 4: Transform price schedule
    # ============================================================================
    
    if your_prices is not None:
        try:
            baseline_price = your_prices["price"].mean()  # Or use specific baseline
            
            price_schedule = pd.DataFrame({
                "week_id": your_prices["week"],  # Adjust column name
                "brand_id": your_prices["brand"].map(brand_mapping),  # Adjust column name
                "region_id": your_prices["region"].map(region_mapping),  # Adjust column name
                "price_index": your_prices["price"] / baseline_price  # Normalize to index
            })
            
            price_schedule = price_schedule.dropna(subset=["brand_id", "region_id"])
            print(f"✓ Created price_schedule: {len(price_schedule)} rows")
            
        except Exception as e:
            print(f"⚠️  Error creating price schedule: {e}")
            print("  Will create default price schedule")
            your_prices = None
    
    if your_prices is None:
        # Create default price schedule from observed metrics
        price_schedule = observed_metrics[["week_id", "brand_id", "region_id"]].copy()
        price_schedule["price_index"] = 1.0  # Default baseline
        print("✓ Created default price_schedule")
    
    # ============================================================================
    # STEP 5: Transform promo schedule
    # ============================================================================
    
    if your_promos is not None:
        try:
            promo_schedule = pd.DataFrame({
                "week_id": your_promos["week"],  # Adjust column name
                "brand_id": your_promos["brand"].map(brand_mapping),  # Adjust column name
                "region_id": your_promos["region"].map(region_mapping),  # Adjust column name
                "promo_intensity": your_promos["promo_intensity"]  # Should be 0-1, adjust if needed
            })
            
            # If promo data is in percentage (0-100), normalize
            if "promo_intensity" in your_promos.columns:
                if your_promos["promo_intensity"].max() > 1.0:
                    promo_schedule["promo_intensity"] = promo_schedule["promo_intensity"] / 100.0
            
            promo_schedule = promo_schedule.dropna(subset=["brand_id", "region_id"])
            print(f"✓ Created promo_schedule: {len(promo_schedule)} rows")
            
        except Exception as e:
            print(f"⚠️  Error creating promo schedule: {e}")
            print("  Will create default promo schedule")
            your_promos = None
    
    if your_promos is None:
        # Create default promo schedule from observed metrics
        promo_schedule = observed_metrics[["week_id", "brand_id", "region_id"]].copy()
        promo_schedule["promo_intensity"] = 0.0  # Default no promo
        print("✓ Created default promo_schedule")
    
    # ============================================================================
    # STEP 6: Create entity tables
    # ============================================================================
    
    brands = pd.DataFrame({
        "brand_id": list(brand_mapping.values()),
        "name": list(brand_mapping.keys()),
        "category": "Fast Food"  # TODO: Customize categories
    })
    
    regions = pd.DataFrame({
        "region_id": list(region_mapping.values()),
        "name": list(region_mapping.keys())
    })
    
    # ============================================================================
    # STEP 7: Save all files
    # ============================================================================
    
    observed_metrics.to_csv(output_path / "observed_metrics_brand_week_region.csv", index=False)
    price_schedule.to_csv(output_path / "brand_price_schedule.csv", index=False)
    promo_schedule.to_csv(output_path / "brand_promo_schedule.csv", index=False)
    brands.to_csv(output_path / "brands.csv", index=False)
    regions.to_csv(output_path / "regions.csv", index=False)
    
    print(f"\n✓ Data version created: {output_version}")
    print(f"  Location: {output_path}")
    print(f"  Files created:")
    for file in output_path.glob("*.csv"):
        print(f"    - {file.name}")
    
    print(f"\n📋 Next steps:")
    print(f"  1. Validate: python3 scripts/validate_custom_data.py {output_version}")
    print(f"  2. Test simulation: python3 scripts/run_simulation.py --data-version {output_version} ...")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/prepare_custom_data.py <your_data_dir> <output_version>")
        print("\nExample:")
        print("  python scripts/prepare_custom_data.py data/my_raw_data data_2026_01_15_custom01")
        sys.exit(1)
    
    success = create_data_version(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)

