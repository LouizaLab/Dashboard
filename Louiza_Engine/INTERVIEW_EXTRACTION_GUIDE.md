# Interview Data Extraction Guide

Complete guide for extracting structured data from interview transcripts and creating Louiza Engine datasets.

---

## Overview

This system extracts data from 11 Labs interview transcripts (conversations between agents and users about food preferences) and creates structured datasets compatible with the Louiza Engine pipeline.

**Key Features**:
- ✅ **LLM-powered extraction** - Uses GPT to extract structured data from transcripts
- ✅ **Web search integration** - Fetches real revenue/financial data for brands
- ✅ **Sentiment analysis** - Analyzes preferences and price/promo sensitivity
- ✅ **Automatic dataset creation** - Generates all required CSV files
- ✅ **Schema compliance** - Outputs match Louiza Engine requirements exactly

---

## Quick Start

### Basic Extraction (Pattern Matching)

```bash
python3 data_engine/interview_to_dataset.py \
    --output-version data_2026_01_15_interviews01 \
    --num-weeks 12
```

### With LLM Extraction (Recommended)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run with LLM extraction
python3 data_engine/interview_to_dataset.py \
    --output-version data_2026_01_15_interviews01 \
    --num-weeks 12 \
    --use-llm
```

### With Web Search for Revenue Data

The script automatically attempts web search for brand revenue data. Known revenue data is used as fallback.

---

## How It Works

### Step 1: Interview Processing

The system reads all `.txt` files from `data_engine/11_labs_interviews/` and extracts:

**From Each Interview**:
- **Brands mentioned**: McDonald's, Burger King, Arby's, Wendy's, etc.
- **Favorite brand**: Primary brand preference
- **Favorite item**: Specific menu item
- **Price sensitivity**: High/Medium/Low based on interview content
- **Promo sensitivity**: High/Medium/Low based on deal mentions
- **Purchase frequency**: Daily/Weekly/Biweekly/Monthly/Rarely
- **Preferred time**: Breakfast/Lunch/Dinner/Snack
- **Preferred channel**: Drive-thru/Dine-in/Delivery/Mobile
- **Value factors**: Taste, Price, Speed, etc.

**Extraction Methods**:

1. **LLM Extraction** (with `--use-llm`):
   - Uses GPT-4o-mini to parse transcripts
   - Extracts structured JSON data
   - More accurate but requires API key

2. **Pattern Matching** (default):
   - Uses keyword matching and regex
   - No API key required
   - Faster but less accurate

### Step 2: Brand Revenue Fetching

For each brand found in interviews:

1. **Web Search** (attempted):
   - Searches for "{Brand} annual revenue 2024 2023 financial data"
   - Parses results for revenue numbers
   - Extracts year information

2. **Known Data** (fallback):
   - Uses pre-populated revenue data for major brands
   - Based on public financial reports

3. **Estimation** (if needed):
   - Estimates revenue based on market position
   - Uses interview mention frequency as proxy

### Step 3: Dataset Creation

Creates all required datasets:

1. **brands.csv**: All brands mentioned in interviews
2. **regions.csv**: Default US regions
3. **observed_metrics_brand_week_region.csv**: 
   - Estimated from brand revenue × market share (from interview mentions)
   - Weekly transactions and revenue
4. **brand_price_schedule.csv**: Price indices over time
5. **brand_promo_schedule.csv**: Promo intensity based on interview sensitivity
6. **survey_responses.csv**: Preference scores from interviews
7. **brand_menu_availability.csv**: Default availability scores

---

## Data Extraction Details

### LLM Extraction Prompt

When using `--use-llm`, the system sends this prompt to GPT:

```
Extract structured data from this fast-food preference interview transcript.

Extract the following information as JSON:
{
    "respondent_id": "respondent_{interview_id}",
    "favorite_brand": "brand_name_or_null",
    "favorite_item": "item_name_or_null",
    "brands_mentioned": ["brand1", "brand2"],
    "items_mentioned": [{"brand": "brand", "item": "item", "preference_score": 0.5}],
    "price_sensitivity": "high/medium/low",
    "promo_sensitivity": "high/medium/low",
    "region": "region_name_or_null",
    "purchase_frequency": "daily/weekly/biweekly/monthly/rarely",
    "preferred_time": "breakfast/lunch/dinner/snack",
    "preferred_channel": "drive_thru/dine_in/delivery/mobile",
    "value_factors": ["taste", "price"],
    "price_change_response": "brief_summary",
    "deal_response": "brief_summary"
}
```

### Pattern Matching Rules

**Brand Detection**:
- Searches for brand name patterns (case-insensitive)
- Handles variations: "McDonald's" = "McDonald" = "MCD"

**Price Sensitivity**:
- **High**: Mentions "budget", "tight budget", "less money", "can't afford", "too expensive"
- **Low**: Mentions "worth it", "don't care about price", "price doesn't matter"
- **Medium**: Default

**Promo Sensitivity**:
- **High**: Mentions "deal", "coupon", "promo", "free item", "app points"
- **Low**: Ignores deals or says deals don't matter
- **Medium**: Default

---

## Web Search Integration

### Revenue Data Sources

The system searches for:
```
"{Brand Name} annual revenue 2024 2023 financial data"
```

**Known Revenue Data** (used as fallback):
- McDonald's: $25.5B (2023)
- Burger King: $1.9B (2023)
- Wendy's: $2.1B (2023)
- Arby's: $400M (2023)
- Taco Bell: $14B (2023, Yum Brands)
- Subway: $9.4B (2023)
- KFC: $6.8B (2023, Yum Brands)
- Chick-fil-A: $18.8B (2023)
- Pizza Hut: $5.8B (2023, Yum Brands)
- Domino's: $4.5B (2023)
- Longhorn: $1.2B (2023, Darden Restaurants)

### Revenue Parsing

The system looks for patterns in search results:
- `"XX.X billion"` → Converts to USD (multiply by 1e9)
- `"XX.X million"` → Converts to USD (multiply by 1e6)
- Year extraction: `"2024"`, `"2023"`, etc.

---

## Output Datasets

### observed_metrics_brand_week_region.csv

**Calculation Method**:
1. Count brand mentions across all interviews
2. Calculate market share: `mentions / total_mentions`
3. Estimate weekly revenue: `(annual_revenue × market_share) / 52`
4. Estimate transactions: `weekly_revenue / $10` (avg transaction value)
5. Add week-to-week variation (seasonality + noise)

**Columns**:
- `week_id`: 1-12 (or specified num_weeks)
- `brand_id`: BRAND_01, BRAND_02, etc.
- `region_id`: REGION_01, REGION_02, REGION_03
- `transactions_obs`: Estimated transaction count
- `revenue_obs`: Estimated revenue
- `confidence_weight`: 0.8 (medium confidence for estimated data)

### brand_price_schedule.csv

**Calculation**:
- Base price index: 1.0
- Small random variations: ±5%
- Clamped to 0.8-1.2 range

### brand_promo_schedule.csv

**Calculation**:
- Base promo intensity from interview promo sensitivity
- High sensitivity → 0.7 avg intensity
- Medium sensitivity → 0.4 avg intensity
- Low sensitivity → 0.2 avg intensity
- Week-to-week variation added

### survey_responses.csv

**From Interviews**:
- Each interview becomes a respondent
- Favorite brand gets preference_score = 0.9
- Other mentioned brands get preference_score = 0.5

---

## Usage Examples

### Example 1: Basic Extraction

```bash
python3 data_engine/interview_to_dataset.py \
    --output-version data_2026_01_15_interviews01 \
    --num-weeks 12
```

**Output**: `data/synthetic/data_2026_01_15_interviews01/`

### Example 2: With LLM (Better Accuracy)

```bash
export OPENAI_API_KEY="sk-..."
python3 data_engine/interview_to_dataset.py \
    --output-version data_2026_01_15_interviews02 \
    --num-weeks 12 \
    --use-llm
```

### Example 3: Custom Interviews Directory

```bash
python3 data_engine/interview_to_dataset.py \
    --interviews-dir data/my_interviews \
    --output-version data_2026_01_15_custom01 \
    --num-weeks 8
```

---

## Validation

After extraction, validate your data:

```bash
python3 scripts/validate_custom_data.py data_2026_01_15_interviews01
```

**Checks**:
- ✅ All required files present
- ✅ Required columns exist
- ✅ Data types correct
- ✅ No negative values
- ✅ Entity consistency (brands/regions match)
- ✅ Price/promo ranges valid

---

## Using Extracted Data

### Step 1: Validate

```bash
python3 scripts/validate_custom_data.py data_2026_01_15_interviews01
```

### Step 2: Run Simulation

```bash
python3 scripts/run_simulation.py \
    --persona-version PersonaSet_v1.json \
    --scenario configs/baseline_scenario.json \
    --data-version data_2026_01_15_interviews01 \
    --num-agents 10000 \
    --output-dir runs/interview_baseline/
```

### Step 3: Run Anchoring

```bash
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_15_interviews01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/interview_baseline/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/interview_baseline/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --output-dir runs/interview_anchored/
```

### Step 4: Run Prompt Workflow

```bash
python3 scripts/run_from_prompt.py \
    "What happens if McDonald's launches a new burger promotion?" \
    --data-version data_2026_01_15_interviews01 \
    --persona-version PersonaSet_v1.json \
    --enable-anchoring
```

---

## File Structure

```
data_engine/
├── 11_labs_interviews/          # Source interview files
│   ├── Interview1.txt
│   ├── Interview2.txt
│   └── ...
├── interview_extractor.py        # Extraction logic
├── interview_to_dataset.py       # Main extraction script
└── fetch_brand_revenue.py         # Revenue fetching utilities

data/synthetic/
└── data_2026_01_15_interviews01/ # Output data version
    ├── brands.csv
    ├── regions.csv
    ├── observed_metrics_brand_week_region.csv
    ├── brand_price_schedule.csv
    ├── brand_promo_schedule.csv
    ├── survey_responses.csv
    ├── brand_menu_availability.csv
    └── extraction_metadata.json
```

---

## Troubleshooting

### Problem: "No interviews found"

**Solution**: Check that interview files are in `data_engine/11_labs_interviews/` and have `.txt` extension

### Problem: "LLM extraction failed"

**Solution**: 
- Check `OPENAI_API_KEY` is set
- Verify API key is valid
- Check API quota/limits
- Falls back to pattern matching automatically

### Problem: "No revenue data found"

**Solution**:
- System uses known revenue data as fallback
- Check `extraction_metadata.json` for sources used
- Web search may not always find data (uses known data)

### Problem: "Brands not matching"

**Solution**:
- Check brand name consistency in interviews
- Review `brands.csv` to see extracted brands
- Adjust brand patterns in `interview_extractor.py` if needed

### Problem: "Transactions seem too high/low"

**Solution**:
- Transactions are estimated from revenue × market share
- Adjust average transaction value ($10 default) in code
- Review market share calculations in `extraction_metadata.json`

---

## Advanced: Customizing Extraction

### Adding New Brand Patterns

Edit `data_engine/interview_extractor.py`:

```python
brand_patterns = {
    "McDonald's": ["McDonald's", "McDonald", "MCD"],
    "Your Brand": ["Your Brand", "YB", "yourbrand"],  # Add here
    # ...
}
```

### Adjusting Revenue Estimation

Edit `data_engine/interview_to_dataset.py`:

```python
# Change average transaction value
transactions = weekly_revenue / 15.0  # $15 per transaction instead of $10

# Adjust market share calculation
market_share = market_shares.get(brand_name, 0.15)  # Different default
```

### Customizing LLM Extraction

Edit `data_engine/interview_extractor.py`:

```python
# Modify the extraction prompt
prompt = f"""Your custom extraction prompt here...
{content_sample}
"""
```

---

## Output Metadata

Each extraction creates `extraction_metadata.json`:

```json
{
  "data_version": "data_2026_01_15_interviews01",
  "created_at": "2026-01-08T17:07:42.583350",
  "source": "11_labs_interviews",
  "num_interviews": 46,
  "num_brands": 10,
  "num_weeks": 12,
  "brands": ["McDonald's", "Burger King", ...],
  "extraction_method": "llm" or "pattern_matching",
  "web_search_used": true,
  "brand_revenues": {
    "McDonald's": 25500000000,
    "Burger King": 1900000000,
    ...
  }
}
```

---

## Summary

The interview extraction system:

1. ✅ **Reads interview transcripts** from `data_engine/11_labs_interviews/`
2. ✅ **Extracts structured data** using LLM or pattern matching
3. ✅ **Fetches brand revenue** via web search (with known data fallback)
4. ✅ **Creates all datasets** in Louiza Engine format
5. ✅ **Saves to versioned directory** in `data/synthetic/`
6. ✅ **Ready for simulation** - can be used immediately in pipeline

**Next Steps**:
1. Run extraction: `python3 data_engine/interview_to_dataset.py --output-version data_2026_01_15_interviews01 --use-llm`
2. Validate: `python3 scripts/validate_custom_data.py data_2026_01_15_interviews01`
3. Run simulation: Use the data version in your simulation commands
4. Run anchoring: Calibrate to the extracted observed metrics
5. Run prompts: Test scenarios with your interview-derived data

---

For more details on using the extracted data, see `COMPLETE_WORKFLOW_GUIDE.md`.

