#!/usr/bin/env python3
"""
Validate custom data before using in simulations.

Usage:
    python scripts/validate_custom_data.py <data_version>
    
Example:
    python scripts/validate_custom_data.py data_2026_01_15_custom01
"""

import pandas as pd
import sys
from pathlib import Path


def validate_data_version(data_version: str):
    """Validate a data version."""
    data_path = Path("data/synthetic") / data_version
    
    if not data_path.exists():
        print(f"✗ Data version not found: {data_version}")
        print(f"  Expected path: {data_path}")
        return False
    
    print(f"Validating data version: {data_version}")
    print(f"Path: {data_path}\n")
    
    errors = []
    warnings = []
    
    # Check required files
    required_files = [
        "observed_metrics_brand_week_region.csv",
        "brand_price_schedule.csv",
        "brand_promo_schedule.csv",
        "brands.csv",
        "regions.csv"
    ]
    
    for file in required_files:
        if not (data_path / file).exists():
            errors.append(f"Missing required file: {file}")
        else:
            print(f"✓ Found: {file}")
    
    if errors:
        print("\n✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # Validate observed metrics
    print("\nValidating observed_metrics_brand_week_region.csv...")
    try:
        obs = pd.read_csv(data_path / "observed_metrics_brand_week_region.csv")
        required_cols = ["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs"]
        missing_cols = [col for col in required_cols if col not in obs.columns]
        if missing_cols:
            errors.append(f"observed_metrics missing columns: {missing_cols}")
        else:
            print(f"  ✓ All required columns present")
        
        # Check for negative values
        if (obs["transactions_obs"] < 0).any():
            warnings.append("Found negative transactions_obs values")
        else:
            print(f"  ✓ No negative transactions")
        
        if (obs["revenue_obs"] < 0).any():
            warnings.append("Found negative revenue_obs values")
        else:
            print(f"  ✓ No negative revenue")
        
        # Check confidence weights
        if "confidence_weight" in obs.columns:
            if (obs["confidence_weight"] < 0).any() or (obs["confidence_weight"] > 1).any():
                warnings.append("confidence_weight should be between 0 and 1")
            else:
                print(f"  ✓ Confidence weights in valid range")
        else:
            warnings.append("confidence_weight column missing (will default to 1.0)")
        
        # Check data coverage
        print(f"  ✓ Coverage: {len(obs)} rows, {obs['week_id'].nunique()} weeks, "
              f"{obs['brand_id'].nunique()} brands, {obs['region_id'].nunique()} regions")
        
    except Exception as e:
        errors.append(f"Error reading observed_metrics: {e}")
    
    # Validate price schedule
    print("\nValidating brand_price_schedule.csv...")
    try:
        prices = pd.read_csv(data_path / "brand_price_schedule.csv")
        if "price_index" not in prices.columns:
            errors.append("price_schedule missing price_index column")
        else:
            print(f"  ✓ price_index column present")
        
        if (prices["price_index"] <= 0).any():
            warnings.append("Found non-positive price_index values")
        else:
            print(f"  ✓ All price_index values positive")
        
        price_range = (prices["price_index"].min(), prices["price_index"].max())
        print(f"  ✓ Price index range: {price_range[0]:.3f} to {price_range[1]:.3f}")
        
    except Exception as e:
        errors.append(f"Error reading price_schedule: {e}")
    
    # Validate promo schedule
    print("\nValidating brand_promo_schedule.csv...")
    try:
        promos = pd.read_csv(data_path / "brand_promo_schedule.csv")
        if "promo_intensity" not in promos.columns:
            errors.append("promo_schedule missing promo_intensity column")
        else:
            print(f"  ✓ promo_intensity column present")
        
        if (promos["promo_intensity"] < 0).any() or (promos["promo_intensity"] > 1).any():
            warnings.append("promo_intensity should be between 0 and 1")
        else:
            print(f"  ✓ All promo_intensity values in valid range (0-1)")
        
        promo_range = (promos["promo_intensity"].min(), promos["promo_intensity"].max())
        print(f"  ✓ Promo intensity range: {promo_range[0]:.3f} to {promo_range[1]:.3f}")
        
    except Exception as e:
        errors.append(f"Error reading promo_schedule: {e}")
    
    # Check entity consistency
    print("\nValidating entity consistency...")
    try:
        obs = pd.read_csv(data_path / "observed_metrics_brand_week_region.csv")
        brands = pd.read_csv(data_path / "brands.csv")
        regions = pd.read_csv(data_path / "regions.csv")
        
        obs_brands = set(obs["brand_id"].unique())
        defined_brands = set(brands["brand_id"].unique())
        missing_brands = obs_brands - defined_brands
        if missing_brands:
            warnings.append(f"Brands in observed_metrics not in brands.csv: {missing_brands}")
        else:
            print(f"  ✓ All brands in observed_metrics are defined")
        
        obs_regions = set(obs["region_id"].unique())
        defined_regions = set(regions["region_id"].unique())
        missing_regions = obs_regions - defined_regions
        if missing_regions:
            warnings.append(f"Regions in observed_metrics not in regions.csv: {missing_regions}")
        else:
            print(f"  ✓ All regions in observed_metrics are defined")
        
        # Check for consistency across schedules
        obs_keys = set(zip(obs["week_id"], obs["brand_id"], obs["region_id"]))
        price_keys = set(zip(prices["week_id"], prices["brand_id"], prices["region_id"]))
        promo_keys = set(zip(promos["week_id"], promos["brand_id"], promos["region_id"]))
        
        if obs_keys != price_keys:
            warnings.append("Price schedule keys don't match observed_metrics keys")
        else:
            print(f"  ✓ Price schedule keys match observed_metrics")
        
        if obs_keys != promo_keys:
            warnings.append("Promo schedule keys don't match observed_metrics keys")
        else:
            print(f"  ✓ Promo schedule keys match observed_metrics")
        
    except Exception as e:
        warnings.append(f"Could not check entity consistency: {e}")
    
    # Report results
    print("\n" + "="*60)
    if errors:
        print("✗ Validation FAILED:")
        for error in errors:
            print(f"  ERROR: {error}")
        return False
    
    if warnings:
        print("⚠️  Validation passed with WARNINGS:")
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print("✓ Validation PASSED - No issues found!")
    
    print("="*60)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_custom_data.py <data_version>")
        print("\nExample:")
        print("  python scripts/validate_custom_data.py data_2026_01_15_custom01")
        sys.exit(1)
    
    success = validate_data_version(sys.argv[1])
    sys.exit(0 if success else 1)

