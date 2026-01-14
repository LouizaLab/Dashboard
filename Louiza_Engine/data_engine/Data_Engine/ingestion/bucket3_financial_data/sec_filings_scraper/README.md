# SEC Filings Scraper - Fast Food Chains Revenue by Geography

This scraper extracts revenue data by geography from SEC EDGAR filings for top fast food chains.

## Quick Start

```bash
cd Data_Engine/ingestion/bucket4_scrapers/sec_filings_scraper
python3 scraper.py
```

## Installation

```bash
pip install requests pandas
```

## What It Does

- Scrapes SEC EDGAR database for 10-K (annual) and 10-Q (quarterly) filings
- Extracts revenue breakdowns by geographic region
- Focuses on top 10 fast food chains:
  - McDonald's (MCD)
  - Burger King (QSR - Restaurant Brands International)
  - Wendy's (WEN)
  - Taco Bell (YUM - Yum! Brands)
  - KFC (YUM - Yum! Brands)
  - Pizza Hut (YUM - Yum! Brands)
  - Starbucks (SBUX)
  - Domino's (DPZ)
  - Chipotle (CMG)
  - Subway (Private - no SEC filings available)

## Output Files

- **`revenue_by_geography.csv`** - Revenue data by company, region, and filing date
  - Columns: company, region, revenue_millions, filing_date, filing_type, accession_number, ticker, extraction_method

## Usage

### Basic Usage

```python
from Data_Engine.ingestion.bucket4_scrapers.sec_filings_scraper import SECFilingsScraper

scraper = SECFilingsScraper()

# Scrape all configured companies
for record in scraper.scrape(limit=3):  # Get 3 most recent filings per company
    print(f"{record.brand}: {record.numerical_fields.get('revenue_millions')}M in {record.categorical_fields.get('region')}")
```

### Scrape Specific Brand

```python
# Scrape only McDonald's
for record in scraper.scrape(brand="McDonald's", limit=5):
    print(record.to_dict())
```

## How It Works

1. **Company Lookup**: Uses CIK (Central Index Key) codes to identify companies in SEC database
2. **Filing Retrieval**: Fetches recent 10-K and 10-Q filings from SEC EDGAR API
3. **Content Extraction**: Downloads full filing text from SEC archives
4. **Revenue Parsing**: Uses pattern matching to extract revenue figures by geographic region
5. **Data Normalization**: Converts to DataRecord format with structured, numerical, and categorical fields

## Geographic Regions Extracted

The scraper looks for revenue data in these regions:
- United States / U.S. / US
- North America
- Europe
- Asia / Asia Pacific / APAC
- Latin America / LATAM
- Middle East / Africa / EMEA
- Individual countries: China, Japan, Canada, Mexico, Brazil, UK, France, Germany, Australia

## Rate Limiting

**Important**: SEC EDGAR has strict rate limits:
- Maximum 10 requests per second
- The scraper includes delays to respect these limits
- If you see 429 (Too Many Requests) errors, wait a few minutes before retrying

## Limitations

1. **Pattern Matching**: Revenue extraction uses pattern matching, which may miss some data if filing formats change
2. **Private Companies**: Subway is a private company and doesn't file with SEC
3. **Format Variations**: Different companies format their geographic revenue tables differently
4. **Data Accuracy**: Extracted data should be verified against original filings

## Data Structure

Each record contains:
- **Structured Fields**: company, region, filing_date, filing_type, accession_number
- **Numerical Fields**: revenue_millions
- **Categorical Fields**: company, region, filing_type
- **Metadata**: CIK, ticker, extraction_method, filing details

## Example Output

```csv
company,region,revenue_millions,filing_date,filing_type,accession_number,ticker,extraction_method
McDonald's,United States,8500.0,2023-12-31,10-K,0000063908-23-000001,MCD,pattern_matching
McDonald's,Europe,3200.0,2023-12-31,10-K,0000063908-23-000001,MCD,pattern_matching
Starbucks,United States,12000.0,2023-09-30,10-K,0000829224-23-000001,SBUX,table_parsing
```

## Troubleshooting

### No Data Extracted

If no revenue data is found:
1. Check SEC website is accessible
2. Verify CIK codes are correct (they may change)
3. Check if filings contain geographic revenue breakdowns
4. Review extraction patterns - may need adjustment for specific companies

### Rate Limit Errors

If you see 429 errors:
- Wait 5-10 minutes before retrying
- Reduce the number of filings requested (lower `limit` parameter)
- Run scraper during off-peak hours

### Missing Companies

Some companies may not be found:
- Private companies don't file with SEC (e.g., Subway)
- Some companies may have changed tickers/CIKs
- Check SEC EDGAR directly to verify CIK codes

## Future Improvements

- Use XBRL data for more accurate extraction
- Implement machine learning for better table parsing
- Add support for more filing types (8-K, etc.)
- Cache filing content to avoid re-downloading
- Add support for historical data analysis


