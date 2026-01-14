"""
SEC Filings Scraper for Fast Food Chains

Scrapes SEC EDGAR database to find revenue data by geography for top fast food chains.
Uses SEC EDGAR API and direct scraping to extract financial data from 10-K and 10-Q filings.
"""

import re
import time
import requests
from typing import Iterator, Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from ..base_scraper import BaseScraper
from ...core.schema import DataRecord, BucketType, SourceType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Top 10 fast food chains with their CIK (Central Index Key) codes
FAST_FOOD_CHAINS = {
    "McDonald's": {"cik": "0000063908", "ticker": "MCD"},
    "Burger King": {"cik": "0001039504", "ticker": "QSR"},  # Restaurant Brands International
    "Wendy's": {"cik": "0000107076", "ticker": "WEN"},
    "Taco Bell": {"cik": "0001048891", "ticker": "YUM"},  # Yum! Brands
    "KFC": {"cik": "0001048891", "ticker": "YUM"},  # Yum! Brands
    "Pizza Hut": {"cik": "0001048891", "ticker": "YUM"},  # Yum! Brands
    "Subway": {"cik": None, "ticker": None},  # Private company
    "Starbucks": {"cik": "0000829224", "ticker": "SBUX"},
    "Domino's": {"cik": "0001286681", "ticker": "DPZ"},
    "Chipotle": {"cik": "0001058090", "ticker": "CMG"},
}


class SECFilingsScraper(BaseScraper):
    """
    Scraper for SEC EDGAR filings to extract revenue data by geography.
    
    Searches for 10-K (annual) and 10-Q (quarterly) filings and extracts
    revenue breakdowns by geographic region.
    """
    
    def __init__(self, source_name: str = "sec_filings"):
        """Initialize SEC filings scraper."""
        super().__init__(source_name=source_name, platform="sec_edgar")
        self.base_url = "https://www.sec.gov"
        self.edgar_api_url = "https://data.sec.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })
    
    def _get_company_filings(self, cik: str, form_type: str = "10-K", limit: int = 5) -> List[Dict]:
        """
        Get recent filings for a company.
        
        Args:
            cik: Central Index Key (CIK) for the company
            form_type: Form type (10-K, 10-Q, etc.)
            limit: Maximum number of filings to retrieve
        
        Returns:
            List of filing dictionaries
        """
        if not cik:
            return []
        
        # Pad CIK with zeros
        cik_padded = cik.zfill(10)
        
        try:
            # Get company submissions
            url = f"{self.edgar_api_url}/submissions/CIK{cik_padded}.json"
            time.sleep(0.1)  # Rate limiting
            
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch filings for CIK {cik}: {response.status_code}")
                return []
            
            data = response.json()
            filings = data.get('filings', {}).get('recent', {})
            
            if not filings:
                return []
            
            # Filter by form type
            forms = filings.get('form', [])
            dates = filings.get('reportDate', [])
            accession_numbers = filings.get('accessionNumber', [])
            
            matching_filings = []
            for i, form in enumerate(forms):
                if form == form_type and len(matching_filings) < limit:
                    if i < len(dates) and i < len(accession_numbers):
                        matching_filings.append({
                            'form': form,
                            'date': dates[i],
                            'accession_number': accession_numbers[i],
                            'cik': cik
                        })
            
            return matching_filings
            
        except Exception as e:
            logger.error(f"Error fetching filings for CIK {cik}: {e}")
            return []
    
    def _get_filing_content(self, cik: str, accession_number: str) -> Optional[str]:
        """
        Get the content of a specific filing.
        
        Args:
            cik: Central Index Key
            accession_number: Filing accession number
        
        Returns:
            Filing content as text, or None if error
        """
        try:
            # Convert accession number format (e.g., 0000063908-23-000001 -> 000006390823000001)
            accession_no_dash = accession_number.replace('-', '')
            
            # Try to get the filing document
            # Most recent filings use the new format
            url = f"{self.base_url}/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_number}&xbrl_type=v"
            
            # Alternative: direct document URL
            # Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_no_dash}/{accession_number}.txt
            doc_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_no_dash}/{accession_number}.txt"
            
            time.sleep(0.1)  # Rate limiting
            response = self.session.get(doc_url, timeout=60)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch filing {accession_number}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching filing content: {e}")
            return None
    
    def _extract_revenue_by_geography(self, filing_text: str, company_name: str) -> List[Dict]:
        """
        Extract revenue data by geography from filing text.
        
        Args:
            filing_text: Full text of the SEC filing
            company_name: Name of the company
        
        Returns:
            List of revenue records by geography
        """
        revenue_records = []
        
        if not filing_text:
            return revenue_records
        
        # Common geographic regions to look for
        regions = [
            "United States", "U.S.", "US", "North America",
            "Europe", "Asia", "Asia Pacific", "APAC",
            "Latin America", "Latin America and Caribbean", "LATAM",
            "Middle East", "Africa", "EMEA",
            "China", "Japan", "Canada", "Mexico", "Brazil",
            "United Kingdom", "UK", "France", "Germany", "Australia"
        ]
        
        # Patterns to find revenue tables
        # Look for "Revenue" or "Net Sales" followed by geographic breakdowns
        patterns = [
            r'(?:Revenue|Net Sales|Total Revenue).*?(?:by.*?geography|geographic.*?segment|geographic.*?region)',
            r'(?:Geographic.*?Revenue|Revenue.*?by.*?Region)',
            r'(?:Segment.*?Revenue|Revenue.*?by.*?Segment)',
        ]
        
        # Try to find revenue tables
        text_lower = filing_text.lower()
        
        # Look for tables with geographic data
        # Common patterns in SEC filings:
        # - "United States" followed by dollar amounts
        # - "International" followed by dollar amounts
        # - Geographic segment tables
        
        # Extract numbers that might be revenue (in millions or billions)
        revenue_pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|M|B)?'
        
        # Look for geographic revenue sections
        # Try to find sections that mention geography and revenue together
        geo_revenue_sections = []
        
        # Split text into sections (by headers or line breaks)
        sections = re.split(r'\n\s*\n|\r\n\r\n', filing_text)
        
        for section in sections:
            section_lower = section.lower()
            # Check if section mentions both geography and revenue
            if any(word in section_lower for word in ['geographic', 'geography', 'region', 'segment']) and \
               any(word in section_lower for word in ['revenue', 'sales', 'net sales']):
                geo_revenue_sections.append(section)
        
        # Extract revenue data from sections
        for section in geo_revenue_sections[:5]:  # Limit to first 5 relevant sections
            # Look for region names followed by dollar amounts
            for region in regions:
                # Pattern: region name, then dollar amount
                pattern = rf'{re.escape(region)}[^\$]*?\$?\s*(\d{{1,3}}(?:,\d{{3}})*(?:\.\d+)?)\s*(?:million|billion|M|B)?'
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        
                        # Determine if it's millions or billions based on context
                        context = section[max(0, match.start()-50):match.end()+50].lower()
                        if 'billion' in context or 'b' in context:
                            amount = amount * 1000  # Convert to millions
                        
                        revenue_records.append({
                            'company': company_name,
                            'region': region,
                            'revenue_millions': amount,
                            'source': 'sec_filing',
                            'extraction_method': 'pattern_matching'
                        })
                    except ValueError:
                        continue
        
        # Also try to find structured tables (if HTML/XML format)
        # Look for table-like structures
        table_pattern = r'(?:United States|U\.S\.|International|Europe|Asia)[^\$]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        table_matches = re.finditer(table_pattern, filing_text, re.IGNORECASE)
        
        for match in list(table_matches)[:10]:  # Limit matches
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                context = filing_text[max(0, match.start()-100):match.end()+100]
                
                # Try to identify the region
                region = "Unknown"
                for r in regions:
                    if r.lower() in context.lower():
                        region = r
                        break
                
                if region != "Unknown":
                    revenue_records.append({
                        'company': company_name,
                        'region': region,
                        'revenue_millions': amount,
                        'source': 'sec_filing',
                        'extraction_method': 'table_parsing'
                    })
            except ValueError:
                continue
        
        # Remove duplicates (same company + region)
        seen = set()
        unique_records = []
        for record in revenue_records:
            key = (record['company'], record['region'])
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def scrape(self, 
               query: Optional[str] = None, 
               brand: Optional[str] = None, 
               limit: Optional[int] = None,
               **kwargs) -> Iterator[DataRecord]:
        """
        Scrape SEC filings for revenue data by geography.
        
        Args:
            query: Not used (scrapes all configured chains)
            brand: Specific brand to scrape (optional)
            limit: Maximum number of filings per company
            **kwargs: Additional parameters
        
        Yields:
            DataRecord objects with revenue data
        """
        companies_to_scrape = []
        
        if brand:
            # Scrape specific brand
            if brand in FAST_FOOD_CHAINS:
                companies_to_scrape.append((brand, FAST_FOOD_CHAINS[brand]))
        else:
            # Scrape all top chains
            companies_to_scrape = list(FAST_FOOD_CHAINS.items())
        
        filings_limit = limit or 3  # Default to 3 most recent filings per company
        
        logger.info(f"Scraping SEC filings for {len(companies_to_scrape)} companies")
        
        for company_name, company_info in companies_to_scrape:
            cik = company_info.get('cik')
            ticker = company_info.get('ticker')
            
            if not cik:
                logger.warning(f"Skipping {company_name} - no CIK available (may be private)")
                continue
            
            logger.info(f"Processing {company_name} (CIK: {cik}, Ticker: {ticker})")
            
            # Get recent 10-K filings (annual reports)
            filings = self._get_company_filings(cik, form_type="10-K", limit=filings_limit)
            
            if not filings:
                logger.warning(f"No 10-K filings found for {company_name}")
                # Try 10-Q filings as fallback
                filings = self._get_company_filings(cik, form_type="10-Q", limit=filings_limit)
            
            for filing in filings:
                filing_date = filing.get('date')
                accession_number = filing.get('accession_number')
                
                logger.info(f"  Fetching filing {accession_number} dated {filing_date}")
                
                # Get filing content
                filing_text = self._get_filing_content(cik, accession_number)
                
                if not filing_text:
                    logger.warning(f"  Could not retrieve filing content")
                    continue
                
                # Extract revenue by geography
                revenue_data = self._extract_revenue_by_geography(filing_text, company_name)
                
                if not revenue_data:
                    logger.warning(f"  No revenue data extracted from filing")
                    continue
                
                logger.info(f"  Extracted {len(revenue_data)} revenue records")
                
                # Create DataRecord for each revenue entry
                for revenue_record in revenue_data:
                    # Create structured text description
                    text = f"{company_name} reported revenue of ${revenue_record['revenue_millions']:.2f} million in {revenue_record['region']} region (from SEC filing dated {filing_date})"
                    
                    record = self._create_record(
                        text=text,
                        brand=company_name,
                        timestamp=datetime.strptime(filing_date, "%Y-%m-%d") if filing_date else None,
                        metadata={
                            'filing_date': filing_date,
                            'filing_type': filing.get('form'),
                            'accession_number': accession_number,
                            'cik': cik,
                            'ticker': ticker,
                            'region': revenue_record['region'],
                            'extraction_method': revenue_record['extraction_method']
                        }
                    )
                    
                    # Add structured fields
                    record.structured_fields = {
                        'company': company_name,
                        'region': revenue_record['region'],
                        'filing_date': filing_date,
                        'filing_type': filing.get('form'),
                        'accession_number': accession_number
                    }
                    
                    # Add numerical fields
                    record.numerical_fields = {
                        'revenue_millions': revenue_record['revenue_millions']
                    }
                    
                    # Add categorical fields
                    record.categorical_fields = {
                        'company': company_name,
                        'region': revenue_record['region'],
                        'filing_type': filing.get('form', '10-K')
                    }
                    
                    yield record
                
                # Rate limiting between filings
                time.sleep(0.5)


def main():
    """Main function to run the SEC filings scraper."""
    import sys
    from pathlib import Path
    
    print("="*70)
    print("SEC Filings Scraper - Fast Food Chains Revenue by Geography")
    print("="*70)
    
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scraper = SECFilingsScraper()
    
    # Collect all records
    all_records = []
    revenue_data = []
    
    try:
        print("\nScraping SEC filings for top fast food chains...")
        print(f"Companies: {', '.join(FAST_FOOD_CHAINS.keys())}\n")
        
        for record in scraper.scrape(limit=2):  # Get 2 most recent filings per company
            all_records.append(record)
            
            # Extract data for CSV
            revenue_data.append({
                'company': record.brand,
                'region': record.categorical_fields.get('region', 'Unknown'),
                'revenue_millions': record.numerical_fields.get('revenue_millions', 0),
                'filing_date': record.structured_fields.get('filing_date', ''),
                'filing_type': record.categorical_fields.get('filing_type', ''),
                'accession_number': record.structured_fields.get('accession_number', ''),
                'ticker': record.metadata.get('ticker', ''),
                'extraction_method': record.metadata.get('extraction_method', '')
            })
        
        print(f"\n✓ Scraped {len(all_records)} revenue records")
        
        # Save to CSV if pandas is available
        if PANDAS_AVAILABLE and revenue_data:
            df = pd.DataFrame(revenue_data)
            csv_file = output_dir / 'revenue_by_geography.csv'
            df.to_csv(csv_file, index=False)
            print(f"✓ Saved revenue data to: {csv_file}")
            print(f"  Records: {len(df)}")
            print(f"\nSample data:")
            print(df.head(10).to_string())
        else:
            # Save as JSON
            json_file = output_dir / 'revenue_by_geography.json'
            with open(json_file, 'w') as f:
                json.dump(revenue_data, f, indent=2)
            print(f"✓ Saved revenue data to: {json_file}")
        
        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        
        if len(revenue_data) == 0:
            print("\n⚠️  No revenue data extracted.")
            print("  This could be due to:")
            print("  - Rate limiting by SEC (wait a few minutes)")
            print("  - Changes in SEC filing format")
            print("  - Network issues")
            print("\n  Note: SEC EDGAR has rate limits. If you see 429 errors,")
            print("  wait a few minutes before running again.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


