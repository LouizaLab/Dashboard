# Sephora Scraper

This scraper collects product information and reviews from Sephora.com.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd Data_Engine/ingestion/bucket4_scrapers/sephora_scraper
   python3 install_dependencies.py
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the full pipeline:**
   ```bash
   python3 run_scraper.py
   ```

## Manual Usage

Run the scraper scripts in the following order:

1. **Scrape Brand Links:**
   ```bash
   python3 scrape_brand_links.py
   ```
   Output: `data/brand_link.txt`

2. **Scrape Product Links:**
   ```bash
   python3 scrape_product_links.py
   ```
   Output: `data/product_links.txt`

3. **Scrape Product Information:**
   ```bash
   python3 scrape_product_info.py
   ```
   Output: `data/pd_info.csv`

4. **Scrape Reviews:**
   ```bash
   python3 scrape_reviews.py
   ```
   Output: `data/scraper_result.json`

5. **Parse Reviews:**
   ```bash
   python3 parse_reviews.py
   ```
   Output: `data/review_data.csv` and `data/product_data.csv`

## Important Notes

- **Rate Limiting**: Sephora may block your IP if you scrape too aggressively. Consider:
  - Using proxies
  - Adding delays between requests
  - Scraping in smaller batches

- **Data Storage**: All scraped data is stored in the `data/` directory

- **HTML Selectors**: The scraper uses generic selectors. You may need to adjust them based on Sephora's current HTML structure.

## Source

This scraper is based on: https://github.com/nadyinky/sephora-analysis/tree/main/sephora_scraper

