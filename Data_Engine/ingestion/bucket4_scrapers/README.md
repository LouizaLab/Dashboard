# Bucket 4: Scraped Public Data

This module contains automated scrapers for collecting public data from various platforms (Google Reviews, Reddit, Sephora, etc.) and converting them to the unified `DataRecord` format.

## Architecture

All scrapers inherit from `BaseScraper`, which provides:
- Unified interface for scraping operations
- Automatic conversion to `DataRecord` format
- Integration with the ingestion pipeline
- Helper methods for creating records

## BaseScraper

The `BaseScraper` class extends `IngestionBase` and provides:

### Key Methods

- `scrape(query, brand=None, limit=None, **kwargs)` - Abstract method that must be implemented by each scraper
- `ingest(file_path=None, **kwargs)` - Calls `scrape()` method (file_path is ignored for scrapers)
- `_create_record(text, brand, timestamp, sentiment, metadata)` - Helper to create DataRecord objects

### Usage Example

```python
from Data_Engine.ingestion import BaseScraper

class MyScraper(BaseScraper):
    def __init__(self, source_name: str):
        super().__init__(source_name=source_name, platform="my_platform")
    
    def scrape(self, query: str, brand: Optional[str] = None, 
               limit: Optional[int] = None, **kwargs) -> Iterator[DataRecord]:
        # Your scraping logic here
        for item in self._fetch_data(query, limit):
            yield self._create_record(
                text=item['text'],
                brand=brand or item.get('brand'),
                timestamp=item.get('timestamp'),
                sentiment=item.get('sentiment'),
                metadata={'custom_field': item.get('custom')}
            )
```

## Available Scrapers

### 1. Reddit Beauty Scraper
- **Location**: `reddit_beauty_scraper/`
- **Purpose**: Scrapes beauty-related subreddits for trend detection
- **Output**: `processed_posts.csv`, `trends_analysis.json`

### 2. Google Reviews Fast Food Scraper
- **Location**: `google_reviews_fast_food_scraper/`
- **Purpose**: Scrapes Google Maps reviews for fast-food brands
- **Output**: `processed_reviews.csv`, visualizations

### 3. Sephora Scraper
- **Location**: `sephora_scraper/`
- **Purpose**: Scrapes product information and reviews from Sephora.com
- **Output**: `product_reviews.csv`, `product_data.csv`

### 4. Delivery Platforms Scraper
- **Location**: `delivery_platforms_scraper/`
- **Purpose**: Scrapes menu items from Uber Eats
- **Output**: `menu_items.csv`, `processed_reviews.csv`

## Integration with Ingestion Pipeline

All scrapers can be used through the unified ingestion interface:

```python
from Data_Engine.ingestion import BaseScraper

# Create scraper instance
scraper = MyScraper(source_name="my_source")

# Scrape data
for record in scraper.ingest(query="search_query", brand="Brand Name", limit=100):
    print(f"Record ID: {record.record_id}")
    print(f"Text: {record.raw_text[:100]}...")
    print(f"Brand: {record.brand}")
    print(f"Sentiment: {record.sentiment}")
```

## DataRecord Output

All scrapers output `DataRecord` objects with:
- `bucket_id`: Set to `BucketType.SCRAPED_PUBLIC_DATA.value` (4)
- `source_name`: Name of the scraper/source
- `source_type`: `SourceType.SCRAPED.value`
- `platform`: Platform name (e.g., "reddit", "google_reviews")
- `raw_text`: Scraped text content
- `brand`: Brand name if applicable
- `timestamp`: When content was created
- `sentiment`: Sentiment score if available
- `metadata`: Additional platform-specific metadata

## Adding New Scrapers

To add a new scraper:

1. Create a new directory under `bucket4_scrapers/`
2. Create a scraper class that inherits from `BaseScraper`
3. Implement the `scrape()` method
4. Add a `README.md` documenting usage
5. Update this README with the new scraper

Example structure:
```
bucket4_scrapers/
  my_new_scraper/
    __init__.py
    scraper.py
    README.md
```

