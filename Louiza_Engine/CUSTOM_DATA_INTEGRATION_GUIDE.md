# Custom Data Integration Guide

Complete guide for integrating your own datasets (revenue, preferences, etc.) into the Louiza Engine pipeline.

---

## Table of Contents

1. [Overview](#overview)
2. [Required Data Schemas](#required-data-schemas)
3. [Data Preparation Steps](#data-preparation-steps)
4. [Creating Your Data Version](#creating-your-data-version)
5. [Validation & Quality Checks](#validation--quality-checks)
6. [Running Simulations with Your Data](#running-simulations-with-your-data)
7. [Troubleshooting](#troubleshooting)
8. [Example: Complete Integration](#example-complete-integration)

---

## Overview

The Louiza Engine expects data in specific CSV formats organized by version. This guide shows you how to:

1. **Format your data** to match required schemas
2. **Create a versioned data directory** 
3. **Validate your data** before running simulations
4. **Use your data** in the simulation pipeline

### Key Concepts

- **Data Version**: Each dataset gets a unique version ID (e.g., `data_2026_01_08_run01`)
- **Versioned Directory**: All CSV files for a version live in `data/synthetic/<version_id>/`
- **Schema Compliance**: Your data must match exact column names and types
- **Entity Consistency**: Brand/region IDs must be consistent across all tables

---

## Required Data Schemas

### 1. Observed Metrics (Required for Anchoring)

**File**: `observed_metrics_brand_week_region.csv`

**Purpose**: Ground truth transaction and revenue data for anchoring calibration.

**Required Columns**:
- `week_id` (int): Week identifier (1, 2, 3, ...)
- `brand_id` (string): Brand identifier (e.g., "BRAND_01", "BK", "MCD")
- `region_id` (string): Region identifier (e.g., "REGION_01", "US_South")
- `transactions_obs` (float): Observed transaction count
- `revenue_obs` (float): Observed revenue
- `confidence_weight` (float, optional): Data quality/confidence score (0.0-1.0)

**Example**:
```csv
week_id,brand_id,region_id,transactions_obs,revenue_obs,confidence_weight
1,BRAND_01,REGION_01,1250.5,12500.75,0.95
1,BRAND_01,REGION_02,980.2,9800.50,0.92
1,BRAND_02,REGION_01,2100.3,21000.25,0.98
```

**Notes**:
- Must have at least one row per (week_id, brand_id, region_id) combination
- `confidence_weight` defaults to 1.0 if missing
- Values should be aggregated (not individual transactions)

### 2. Price Schedule (Required for LPM)

**File**: `brand_price_schedule.csv`

**Purpose**: Historical price data by brand, region, and week.

**Required Columns**:
- `week_id` (int): Week identifier
- `brand_id` (string): Brand identifier
- `region_id` (string): Region identifier
- `price_index` (float): Price index (normalized, typically 0.8-1.2)

**Example**:
```csv
week_id,brand_id,region_id,price_index
1,BRAND_01,REGION_01,1.0
1,BRAND_01,REGION_02,0.95
1,BRAND_02,REGION_01,1.1
```

**Notes**:
- `price_index` is relative (1.0 = baseline, 0.9 = 10% discount, 1.1 = 10% increase)
- Must cover all weeks and brand/region combinations in observed metrics

### 3. Promo Schedule (Required for LPM)

**File**: `brand_promo_schedule.csv`

**Purpose**: Promotion intensity by brand, region, and week.

**Required Columns**:
- `week_id` (int): Week identifier
- `brand_id` (string): Brand identifier
- `region_id` (string): Region identifier
- `promo_intensity` (float): Promotion intensity (0.0-1.0, where 1.0 = maximum promo)

**Example**:
```csv
week_id,brand_id,region_id,promo_intensity
1,BRAND_01,REGION_01,0.0
1,BRAND_01,REGION_02,0.5
1,BRAND_02,REGION_01,0.7
```

**Notes**:
- `promo_intensity` ranges from 0.0 (no promo) to 1.0 (maximum promo)
- Must cover all weeks and brand/region combinations

### 4. Menu Availability (Optional but Recommended)

**File**: `brand_menu_availability.csv`

**Purpose**: Product availability scores.

**Required Columns**:
- `week_id` (int)
- `brand_id` (string)
- `region_id` (string)
- `availability_score` (float): 0.0-1.0 (1.0 = fully available)

**Example**:
```csv
week_id,brand_id,region_id,availability_score
1,BRAND_01,REGION_01,0.95
1,BRAND_01,REGION_02,0.90
```

### 5. Entity Tables (Required)

**File**: `brands.csv`

**Required Columns**:
- `brand_id` (string): Unique brand identifier
- `name` (string): Brand name
- `category` (string, optional): Brand category

**Example**:
```csv
brand_id,name,category
BRAND_01,Burger King,Fast Food
BRAND_02,McDonald's,Fast Food
BRAND_03,Wendy's,Fast Food
```

**File**: `regions.csv`

**Required Columns**:
- `region_id` (string): Unique region identifier
- `name` (string): Region name

**Example**:
```csv
region_id,name
REGION_01,US_North
REGION_02,US_South
REGION_03,US_West
```

### 6. Survey/Preference Data (Optional, for PME)

**File**: `survey_responses.csv`

**Purpose**: Consumer preference data for persona discovery.

**Required Columns**:
- `respondent_id` (string): Unique respondent identifier
- `week_id` (int): Week of survey
- `region_id` (string): Region
- `brand_id` (string): Brand
- `preference_score` (float): Preference rating (typically 0.0-1.0 or 1-5 scale)

**File**: `taste_ratings.csv`

**Required Columns**:
- `respondent_id` (string)
- `item_id` (string): Menu item identifier
- `rating` (float): Taste rating

**File**: `choice_experiments.csv`

**Required Columns**:
- `respondent_id` (string)
- `week_id` (int)
- `option_set_id` (string): Experiment identifier
- `chosen_brand_id` (string): Selected brand
- Additional context columns (prices, promotions, etc.)

---

## Data Preparation Steps

### Step 1: Gather Your Data

Collect your data sources:
- **Revenue/Transaction data**: Sales, transactions, revenue by brand/region/week
- **Price data**: Historical prices or price indices
- **Promotion data**: Promo calendars, discount schedules
- **Preference data** (optional): Survey responses, ratings, choice experiments

### Step 2: Map to Required Schemas

Create mapping documents:

```python
# Example mapping
YOUR_DATA_MAPPING = {
    "observed_metrics": {
        "your_column": "required_column",
        "sales": "transactions_obs",
        "revenue": "revenue_obs",
        "week": "week_id",
        "brand": "brand_id",
        "region": "region_id"
    },
    "price_schedule": {
        "price": "price_index",  # May need normalization
        "week": "week_id",
        "brand": "brand_id"
    }
}
```

### Step 3: Transform Your Data

Create transformation scripts:

```python
import pandas as pd

# Load your data
your_revenue_data = pd.read_csv("your_revenue_data.csv")

# Transform to required schema
observed_metrics = pd.DataFrame({
    "week_id": your_revenue_data["week"],
    "brand_id": your_revenue_data["brand"].map(brand_mapping),  # Map to canonical IDs
    "region_id": your_revenue_data["region"].map(region_mapping),
    "transactions_obs": your_revenue_data["transactions"],
    "revenue_obs": your_revenue_data["revenue"],
    "confidence_weight": 1.0  # Or calculate from your data quality metrics
})

# Normalize price data
price_schedule = pd.DataFrame({
    "week_id": your_price_data["week"],
    "brand_id": your_price_data["brand"].map(brand_mapping),
    "region_id": your_price_data["region"].map(region_mapping),
    "price_index": your_price_data["price"] / baseline_price  # Normalize to index
})
```

### Step 4: Create Entity Mappings

Ensure consistent IDs across all tables:

```python
# Create brand mapping
brand_mapping = {
    "Burger King": "BRAND_01",
    "McDonald's": "BRAND_02",
    "Wendy's": "BRAND_03",
    # ... your brands
}

# Create region mapping
region_mapping = {
    "North": "REGION_01",
    "South": "REGION_02",
    "West": "REGION_03",
    # ... your regions
}
```

---

## Creating Your Data Version

### Step 1: Create Version Directory

```bash
# Generate version ID (or use your own)
VERSION_ID="data_2026_01_15_custom01"

# Create directory
mkdir -p data/synthetic/$VERSION_ID
```

### Step 2: Save Your CSV Files

```bash
# Save all required files
cd data/synthetic/$VERSION_ID

# Required files
cp your_observed_metrics.csv observed_metrics_brand_week_region.csv
cp your_price_schedule.csv brand_price_schedule.csv
cp your_promo_schedule.csv brand_promo_schedule.csv
cp your_brands.csv brands.csv
cp your_regions.csv regions.csv

# Optional files
cp your_menu_availability.csv brand_menu_availability.csv  # Optional
cp your_survey_responses.csv survey_responses.csv  # Optional
```

### Step 3: Create Data Preparation Script

Create `scripts/prepare_custom_data.py`:

```python
#!/usr/bin/env python3
"""
Script to prepare and validate custom data for Louiza Engine.
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
    
    # Load your data
    your_revenue = pd.read_csv(your_data_path / "revenue_data.csv")
    your_prices = pd.read_csv(your_data_path / "price_data.csv")
    your_promos = pd.read_csv(your_data_path / "promo_data.csv")
    
    # Define mappings (customize these!)
    brand_mapping = {
        "Burger King": "BRAND_01",
        "McDonald's": "BRAND_02",
        # Add your brand mappings
    }
    
    region_mapping = {
        "North": "REGION_01",
        "South": "REGION_02",
        # Add your region mappings
    }
    
    # Transform observed metrics
    observed_metrics = pd.DataFrame({
        "week_id": your_revenue["week"],
        "brand_id": your_revenue["brand"].map(brand_mapping),
        "region_id": your_revenue["region"].map(region_mapping),
        "transactions_obs": your_revenue["transactions"],
        "revenue_obs": your_revenue["revenue"],
        "confidence_weight": 1.0  # Or calculate from your data
    })
    
    # Transform price schedule
    baseline_price = your_prices["price"].mean()  # Or use specific baseline
    price_schedule = pd.DataFrame({
        "week_id": your_prices["week"],
        "brand_id": your_prices["brand"].map(brand_mapping),
        "region_id": your_prices["region"].map(region_mapping),
        "price_index": your_prices["price"] / baseline_price
    })
    
    # Transform promo schedule
    promo_schedule = pd.DataFrame({
        "week_id": your_promos["week"],
        "brand_id": your_promos["brand"].map(brand_mapping),
        "region_id": your_promos["region"].map(region_mapping),
        "promo_intensity": your_promos["promo_intensity"]  # Should be 0-1
    })
    
    # Create entity tables
    brands = pd.DataFrame({
        "brand_id": list(brand_mapping.values()),
        "name": list(brand_mapping.keys()),
        "category": "Fast Food"  # Customize
    })
    
    regions = pd.DataFrame({
        "region_id": list(region_mapping.values()),
        "name": list(region_mapping.keys())
    })
    
    # Save all files
    observed_metrics.to_csv(output_path / "observed_metrics_brand_week_region.csv", index=False)
    price_schedule.to_csv(output_path / "brand_price_schedule.csv", index=False)
    promo_schedule.to_csv(output_path / "brand_promo_schedule.csv", index=False)
    brands.to_csv(output_path / "brands.csv", index=False)
    regions.to_csv(output_path / "regions.csv", index=False)
    
    print(f"✓ Data version created: {output_version}")
    print(f"  Location: {output_path}")
    print(f"  Files: {len(list(output_path.glob('*.csv')))} CSV files")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/prepare_custom_data.py <your_data_dir> <output_version>")
        sys.exit(1)
    
    create_data_version(sys.argv[1], sys.argv[2])
```

---

## Validation & Quality Checks

### Step 1: Schema Validation

Create `scripts/validate_custom_data.py`:

```python
#!/usr/bin/env python3
"""
Validate custom data before using in simulations.
"""

import pandas as pd
import sys
from pathlib import Path

def validate_data_version(data_version: str):
    """Validate a data version."""
    data_path = Path("data/synthetic") / data_version
    
    if not data_path.exists():
        print(f"✗ Data version not found: {data_version}")
        return False
    
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
    
    if errors:
        print("✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # Validate observed metrics
    try:
        obs = pd.read_csv(data_path / "observed_metrics_brand_week_region.csv")
        required_cols = ["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs"]
        missing_cols = [col for col in required_cols if col not in obs.columns]
        if missing_cols:
            errors.append(f"observed_metrics missing columns: {missing_cols}")
        
        # Check for negative values
        if (obs["transactions_obs"] < 0).any():
            warnings.append("Found negative transactions_obs values")
        if (obs["revenue_obs"] < 0).any():
            warnings.append("Found negative revenue_obs values")
        
        # Check confidence weights
        if "confidence_weight" in obs.columns:
            if (obs["confidence_weight"] < 0).any() or (obs["confidence_weight"] > 1).any():
                warnings.append("confidence_weight should be between 0 and 1")
    except Exception as e:
        errors.append(f"Error reading observed_metrics: {e}")
    
    # Validate price schedule
    try:
        prices = pd.read_csv(data_path / "brand_price_schedule.csv")
        if "price_index" not in prices.columns:
            errors.append("price_schedule missing price_index column")
        if (prices["price_index"] <= 0).any():
            warnings.append("Found non-positive price_index values")
    except Exception as e:
        errors.append(f"Error reading price_schedule: {e}")
    
    # Validate promo schedule
    try:
        promos = pd.read_csv(data_path / "brand_promo_schedule.csv")
        if "promo_intensity" not in promos.columns:
            errors.append("promo_schedule missing promo_intensity column")
        if (promos["promo_intensity"] < 0).any() or (promos["promo_intensity"] > 1).any():
            warnings.append("promo_intensity should be between 0 and 1")
    except Exception as e:
        errors.append(f"Error reading promo_schedule: {e}")
    
    # Check entity consistency
    try:
        obs = pd.read_csv(data_path / "observed_metrics_brand_week_region.csv")
        brands = pd.read_csv(data_path / "brands.csv")
        regions = pd.read_csv(data_path / "regions.csv")
        
        obs_brands = set(obs["brand_id"].unique())
        defined_brands = set(brands["brand_id"].unique())
        missing_brands = obs_brands - defined_brands
        if missing_brands:
            warnings.append(f"Brands in observed_metrics not in brands.csv: {missing_brands}")
        
        obs_regions = set(obs["region_id"].unique())
        defined_regions = set(regions["region_id"].unique())
        missing_regions = obs_regions - defined_regions
        if missing_regions:
            warnings.append(f"Regions in observed_metrics not in regions.csv: {missing_regions}")
    except Exception as e:
        warnings.append(f"Could not check entity consistency: {e}")
    
    # Report results
    if errors:
        print("✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print("⚠ Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("✓ Validation passed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_custom_data.py <data_version>")
        sys.exit(1)
    
    success = validate_data_version(sys.argv[1])
    sys.exit(0 if success else 1)
```

### Step 2: Run Validation

```bash
python3 scripts/validate_custom_data.py data_2026_01_15_custom01
```

### Step 3: Check Data Coverage

```python
import pandas as pd
from data_engine.loaders import DataLoader

loader = DataLoader("data/synthetic", "data_2026_01_15_custom01")

# Check coverage
obs = loader.load_observed_metrics()
print(f"Weeks: {sorted(obs['week_id'].unique())}")
print(f"Brands: {sorted(obs['brand_id'].unique())}")
print(f"Regions: {sorted(obs['region_id'].unique())}")
print(f"Total rows: {len(obs)}")
print(f"Date range: {obs['week_id'].min()} to {obs['week_id'].max()}")
```

---

## Running Simulations with Your Data

### Step 1: Use Your Data Version

```bash
# Run simulation with your data
python3 scripts/run_simulation.py \
    --persona-version PersonaSet_v1.json \
    --scenario configs/baseline_scenario.json \
    --data-version data_2026_01_15_custom01 \
    --num-agents 10000 \
    --output-dir runs/custom_baseline/
```

### Step 2: Run Anchoring

```bash
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_15_custom01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/custom_baseline/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/custom_baseline/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --output-dir runs/custom_anchored/
```

### Step 3: Run Prompt Workflow

```bash
python3 scripts/run_from_prompt.py \
    "What happens if we launch a promo campaign?" \
    --data-version data_2026_01_15_custom01 \
    --persona-version PersonaSet_v1.json \
    --enable-anchoring
```

---

## Troubleshooting

### Problem: "Data version directory not found"

**Solution**: 
- Check the version ID is correct
- Ensure directory exists: `ls data/synthetic/<version_id>`
- Verify path: `data/synthetic/` not `data/` directly

### Problem: "Missing required columns"

**Solution**:
- Check column names match exactly (case-sensitive)
- Use validation script: `python3 scripts/validate_custom_data.py <version>`
- Review schema requirements above

### Problem: "Brand/Region IDs not matching"

**Solution**:
- Ensure entity tables (`brands.csv`, `regions.csv`) include all IDs used in other tables
- Check for typos or inconsistent naming
- Use consistent ID format (e.g., all "BRAND_01" not mix of "BRAND_01" and "brand_01")

### Problem: "Negative values in transactions/revenue"

**Solution**:
- Check your source data for errors
- Ensure aggregation is correct (sum, not difference)
- Filter out invalid rows before saving

### Problem: "Price index values seem wrong"

**Solution**:
- Price index should be normalized (1.0 = baseline)
- Calculate: `price_index = actual_price / baseline_price`
- Typical range: 0.5-2.0 (50% discount to 100% increase)

### Problem: "Promo intensity out of range"

**Solution**:
- Promo intensity must be 0.0-1.0
- If your data uses percentages (0-100), divide by 100
- If your data uses discount amounts, normalize to 0-1 scale

---

## Example: Complete Integration

### Scenario: You have sales data from your POS system

**Your Data**:
- `sales_data.csv`: Week, Brand, Region, Transactions, Revenue
- `pricing_data.csv`: Week, Brand, Region, Price
- `promo_calendar.csv`: Week, Brand, Region, Discount_Percent

**Step 1: Create transformation script**

```python
# transform_my_data.py
import pandas as pd

# Load your data
sales = pd.read_csv("sales_data.csv")
pricing = pd.read_csv("pricing_data.csv")
promos = pd.read_csv("promo_calendar.csv")

# Define mappings
brand_map = {"BK": "BRAND_01", "MCD": "BRAND_02", "WEN": "BRAND_03"}
region_map = {"North": "REGION_01", "South": "REGION_02"}

# Transform observed metrics
obs_metrics = pd.DataFrame({
    "week_id": sales["Week"],
    "brand_id": sales["Brand"].map(brand_map),
    "region_id": sales["Region"].map(region_map),
    "transactions_obs": sales["Transactions"],
    "revenue_obs": sales["Revenue"],
    "confidence_weight": 1.0
})

# Transform price schedule (normalize to index)
baseline_price = pricing["Price"].median()
price_sched = pd.DataFrame({
    "week_id": pricing["Week"],
    "brand_id": pricing["Brand"].map(brand_map),
    "region_id": pricing["Region"].map(region_map),
    "price_index": pricing["Price"] / baseline_price
})

# Transform promo schedule (convert discount % to intensity 0-1)
promo_sched = pd.DataFrame({
    "week_id": promos["Week"],
    "brand_id": promos["Brand"].map(brand_map),
    "region_id": promos["Region"].map(region_map),
    "promo_intensity": promos["Discount_Percent"] / 100.0
})

# Create entity tables
brands = pd.DataFrame({
    "brand_id": list(brand_map.values()),
    "name": ["Burger King", "McDonald's", "Wendy's"],
    "category": "Fast Food"
})

regions = pd.DataFrame({
    "region_id": list(region_map.values()),
    "name": ["US_North", "US_South"]
})

# Save to versioned directory
version = "data_2026_01_15_pos01"
output_dir = f"data/synthetic/{version}"
import os
os.makedirs(output_dir, exist_ok=True)

obs_metrics.to_csv(f"{output_dir}/observed_metrics_brand_week_region.csv", index=False)
price_sched.to_csv(f"{output_dir}/brand_price_schedule.csv", index=False)
promo_sched.to_csv(f"{output_dir}/brand_promo_schedule.csv", index=False)
brands.to_csv(f"{output_dir}/brands.csv", index=False)
regions.to_csv(f"{output_dir}/regions.csv", index=False)

print(f"✓ Data version created: {version}")
```

**Step 2: Validate**

```bash
python3 scripts/validate_custom_data.py data_2026_01_15_pos01
```

**Step 3: Use in pipeline**

```bash
# Run simulation
python3 scripts/run_simulation.py \
    --data-version data_2026_01_15_pos01 \
    --persona-version PersonaSet_v1.json \
    --scenario configs/baseline_scenario.json \
    --output-dir runs/pos_baseline/

# Run anchoring
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_15_pos01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/pos_baseline/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/pos_baseline/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --output-dir runs/pos_anchored/

# Run prompts
python3 scripts/run_from_prompt.py \
    "What happens if we increase prices by 10%?" \
    --data-version data_2026_01_15_pos01 \
    --enable-anchoring
```

---

## Summary Checklist

- [ ] Gather your revenue/transaction data
- [ ] Gather your price data
- [ ] Gather your promotion data
- [ ] Map your column names to required schemas
- [ ] Create brand/region ID mappings
- [ ] Transform data to required formats
- [ ] Normalize price data to index (1.0 = baseline)
- [ ] Normalize promo data to 0-1 intensity scale
- [ ] Create entity tables (brands.csv, regions.csv)
- [ ] Save all files to versioned directory
- [ ] Run validation script
- [ ] Check data coverage (weeks, brands, regions)
- [ ] Test with baseline simulation
- [ ] Run anchoring calibration
- [ ] Use in prompt workflows

---

## Next Steps

1. **Start with minimal data**: Get basic simulation working with just observed metrics, prices, and promos
2. **Add optional data**: Once basic pipeline works, add survey/preference data for better persona discovery
3. **Iterate on quality**: Use validation results to improve data quality
4. **Compare results**: Run same scenarios with synthetic vs. your data to understand differences

For detailed workflow instructions, see `COMPLETE_WORKFLOW_GUIDE.md`.

