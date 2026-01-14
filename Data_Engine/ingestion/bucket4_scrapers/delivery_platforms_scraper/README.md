# Delivery Platform Scraper

Simple scraper for Uber Eats - scrapes McDonald's menu items.

## Quick Start

```bash
cd Data_Engine/ingestion/bucket4_scrapers/delivery_platforms_scraper
python3 scraper.py
```

## Installation

```bash
pip install playwright pandas
playwright install chromium
```

## What It Does

- Searches for McDonald's on Uber Eats in New York, NY
- Scrapes menu items (name, price, category, description)
- Saves to `menu_items.csv` and `processed_reviews.csv`

## Output Files

- **`menu_items.csv`** - All menu items with details
- **`processed_reviews.csv`** - Reviews (currently empty, can be extended)

## Customization

To scrape a different brand or location, edit `scraper.py`:

```python
# In the main() function, change:
store = scraper.search_store("McDonald's", "New York, NY")
```

## Notes

- Uses Playwright for browser automation
- Runs headless by default (set `headless=False` to see browser)
- Simple, single-file design for easy modification
