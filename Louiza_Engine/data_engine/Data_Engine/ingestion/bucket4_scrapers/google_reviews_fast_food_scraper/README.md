# Google Reviews Fast-Food Analysis Pipeline

Fast, production-ready pipeline for analyzing Google Reviews to detect consumer preferences and trends for fast-food brands.

## Features

- ✅ **SerpAPI Integration** - Scrapes Google Maps reviews efficiently
- ✅ **Food Item Extraction** - Identifies mentions of burgers, fries, chicken, etc.
- ✅ **Attribute Detection** - Extracts taste, value, and quality attributes
- ✅ **Sentiment Analysis** - Uses VADER for social media sentiment
- ✅ **Trend Analysis** - Brand trends, item-level sentiment, regional differences
- ✅ **Visualizations** - Clean graphs and heatmaps

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy matplotlib seaborn requests vaderSentiment
```

### 2. Set SerpAPI Key

```bash
export SERPAPI_KEY="your_api_key_here"
```

Or get a free key from: https://serpapi.com/

### 3. Run Pipeline

```bash
cd Data_Engine/ingestion/bucket4_scrapers/google_reviews_fast_food_scraper
python3 main.py
```

## Configuration

Edit `main.py` to customize:

- **Brands**: List of fast-food brands to analyze
- **Cities**: Cities to scrape reviews from
- **Max Reviews**: Limit reviews per brand (default: 1000)

## Outputs

### CSV Files

1. **processed_reviews.csv** - All normalized reviews with extracted items/attributes
2. **brand_sentiment_trends.csv** - Sentiment trends by brand over time
3. **item_sentiment_by_brand.csv** - Average sentiment by food item per brand
4. **attribute_frequency.csv** - Frequency of taste/value/quality attributes
5. **regional_differences.csv** - Sentiment differences by city
6. **monthly_trends.csv** - Month-over-month trend deltas

### Visualizations

1. **brand_trends.png** - Line chart of sentiment trends over time
2. **item_comparison.png** - Bar chart comparing food items across brands
3. **attribute_heatmap.png** - Heatmap of attribute frequencies
4. **regional_comparison.png** - Bar chart of regional sentiment differences

## Architecture

```
google_reviews_fast_food_scraper/
├── scraper.py      # SerpAPI integration for scraping reviews
├── processor.py    # Normalize, extract items/attributes, sentiment
├── analyzer.py     # Aggregate and calculate trends
├── visualizer.py   # Generate graphs and charts
└── main.py         # Main execution script
```

## Food Items Tracked

- burger, fries, chicken sandwich, nuggets, taco, burrito, sauce, shake, soda, coffee, salad, wrap, sandwich, chicken, fish, breakfast, hash browns, mcmuffin, biscuit

## Attributes Tracked

**Taste**: crispy, greasy, juicy, bland, dry, tender, tough, flavorful, tasty, delicious, yummy

**Value**: expensive, cheap, worth it, value, overpriced, affordable, pricey, budget

**Quality**: fresh, stale, hot, cold, warm, quality, premium, standard

## Performance

- **Speed**: Processes ~1000 reviews per brand in ~5-10 minutes
- **Rate Limiting**: 1 second delay between API calls
- **Memory**: Efficient pandas operations, processes in batches

## Notes

- Focuses on food opinions, filters out service/location complaints
- Uses simple, reliable NLP methods (keyword matching + VADER)
- All outputs are interpretable and actionable
- Falls back to sample data if SerpAPI key is not available (for testing)

