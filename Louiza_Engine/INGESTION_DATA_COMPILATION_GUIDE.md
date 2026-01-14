# Ingestion Data Compilation Guide

This guide explains how to compile datasets from the `Data_Engine/ingestion/` directory into LPM-compatible schemas for use in the simulation pipeline.

## Overview

The `compile_ingestion_data_for_lpm.py` script transforms raw datasets (reviews, sentiment data, ratings) from the ingestion directory into the structured formats required by the Louiza Engine simulation pipeline.

## What It Does

The script:

1. **Loads datasets** from `data_engine/Data_Engine/ingestion/bucket1_online_datasets/`:
   - McDonald's Sentiment Reviews (`McDonaldsSentimentReviews.csv`)
   - English Tweets Dataset (`English dataset.csv`)
   - Restaurant Ratings (`restaurant_ratings_reviews.csv`)

2. **Extracts entities**:
   - Brands (from brand mentions in tweets, restaurant names)
   - Regions (from user locations, restaurant states)
   - Channels (default: drive_thru, dine_in)

3. **Transforms data** into required schemas:
   - **Survey responses**: Converts reviews/sentiment into preference scores
   - **Taste ratings**: Generates item ratings with attributes
   - **Choice experiments**: Creates choice experiment data
   - **Price schedules**: Generates price indices from restaurant price levels
   - **Promo schedules**: Generates promotion intensities
   - **Availability schedules**: Generates menu availability scores
   - **Observed metrics**: Aggregates review data into transaction/revenue proxies

4. **Outputs** all data in versioned directories matching the expected schema format.

## Usage

### Basic Usage

```bash
python scripts/compile_ingestion_data_for_lpm.py \
    --start-week 1 \
    --num-weeks 52 \
    --seed 42 \
    --output-dir data/synthetic/
```

### Options

- `--start-week`: Starting week ID (default: 1)
- `--num-weeks`: Number of weeks to generate (default: 52)
- `--seed`: Random seed for reproducibility (required)
- `--output-dir`: Output directory (default: `data/synthetic/`)
- `--data-version`: Optional data version ID (auto-generated if not provided)

### Example: Generate Full Year Dataset

```bash
python scripts/compile_ingestion_data_for_lpm.py \
    --start-week 1 \
    --num-weeks 52 \
    --seed 42 \
    --output-dir data/synthetic/
```

This will create a versioned directory like `data/synthetic/data_2026_01_15_run01/` containing all the required CSV files.

## Output Schema

The script generates the following tables (matching the LPM requirements):

### Entity Tables
- `brands.csv`: brand_id, name, category
- `regions.csv`: region_id, name
- `channels.csv`: channel_id, name

### Environment Schedules (for LPM)
- `brand_price_schedule.csv`: week_id, brand_id, region_id, price_index
- `brand_promo_schedule.csv`: week_id, brand_id, region_id, promo_intensity
- `brand_menu_availability.csv`: week_id, brand_id, region_id, availability_score

### Survey/Preference Data (for PME)
- `survey_responses.csv`: respondent_id, week_id, region_id, brand_id, preference_score
- `taste_ratings.csv`: respondent_id, item_id, rating, attributes...
- `choice_experiments.csv`: respondent_id, week_id, option_set_id, chosen_brand_id, prices..., context...

### Observed Metrics (for Anchoring)
- `observed_metrics_brand_week_region.csv`: week_id, brand_id, region_id, transactions_obs, revenue_obs, confidence_weight

### Metadata
- `metadata.json`: Generation metadata including data version, seed, source datasets used

## Data Transformation Details

### Brand Extraction
- Extracts brands from `marka_type` column in English tweets dataset
- Matches restaurant names to known fast food brands
- Adds "McDonald's" explicitly if reviews are present

### Region Extraction
- Maps user locations from tweets to US regions
- Maps restaurant states to US regions (CA/OR/WA → US_West, TX/FL/GA → US_South, etc.)
- Falls back to default regions if no location data found

### Survey Responses
- **McDonald's Reviews**: Converts review text length to preference scores (longer = higher engagement)
- **English Tweets**: Maps sentiment labels (negatif/positif) and polarity scores to preference scores
- **Restaurant Ratings**: Converts average ratings (1-5 scale) to preference scores (0-1 scale)

### Price Schedules
- Uses restaurant price levels (high/medium/low) to set base prices
- Applies seasonality patterns
- Adds region-specific multipliers
- Includes price volatility

### Observed Metrics
- Base transactions derived from review counts per brand
- Revenue computed as transactions × price_index
- Confidence weights based on review volume (more reviews = higher confidence)
- Includes price elasticity and promo effects

## Using the Compiled Data

After compilation, use the data version ID in downstream layers:

```bash
# Initialize personas
python scripts/initialize_personas.py \
    --data-version data_2026_01_15_run01 \
    --output PersonaSet_v1.json

# Run simulation
python scripts/run_simulation.py \
    --persona-version PersonaSet_v1 \
    --scenario configs/baseline_scenario.json \
    --data-version data_2026_01_15_run01 \
    --seed 123 \
    --num-agents 200000 \
    --output-dir runs/baseline_001/
```

## Troubleshooting

### No Brands Found
If no brands are extracted from the datasets, the script will use defaults:
- McDonald's, Burger King, Wendy's, KFC, Taco Bell

### No Regions Found
If no regions are extracted, defaults are used:
- US_North, US_South, US_West, US_East

### Missing Datasets
The script will continue even if some datasets are missing. It will:
- Use available datasets
- Fill in missing data with defaults
- Log warnings for missing files

### Encoding Issues
CSV files are read with pandas which handles multiple encodings automatically (UTF-8, latin-1, etc.).

## Integration with Existing Pipeline

This script complements the existing synthetic data generator (`generate_synthetic_data.py`):

- **Synthetic generator**: Creates fully synthetic data from config parameters
- **Ingestion compiler**: Transforms real-world datasets into compatible schemas

Both produce the same schema format, so you can use either (or both) with the simulation pipeline.

## Next Steps

1. Run the compilation script to generate your dataset
2. Validate the output using `scripts/validate_custom_data.py`
3. Use the data version ID in persona initialization and simulations
4. Compare results with synthetic data to understand differences

