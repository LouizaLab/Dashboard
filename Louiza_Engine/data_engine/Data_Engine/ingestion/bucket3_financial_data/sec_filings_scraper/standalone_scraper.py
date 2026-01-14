#!/usr/bin/env python3
"""
Standalone SEC Filings Scraper
Can be run directly without the full Data_Engine package dependencies
"""

import re
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import logging
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas not installed. Install with: pip install pandas")

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


class StandaloneSECScraper:
    """Standalone SEC filings scraper."""
    
    def __init__(self):
        """Initialize scraper."""
        self.base_url = "https://www.sec.gov"
        self.edgar_api_url = "https://data.sec.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    def _get_company_filings(self, cik: str, form_type: str = "10-K", limit: int = 5) -> List[Dict]:
        """Get recent filings for a company."""
        if not cik:
            return []
        
        # SEC API expects CIK padded to 10 digits with leading zeros
        cik_padded = cik.zfill(10)
        
        try:
            url = f"{self.edgar_api_url}/submissions/CIK{cik_padded}.json"
            time.sleep(0.1)  # Rate limiting
            
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch filings for CIK {cik}: {response.status_code}")
                return []
            
            data = response.json()
            
            # Handle different response structures
            if 'filings' in data:
                filings = data.get('filings', {}).get('recent', {})
            elif 'recent' in data:
                filings = data.get('recent', {})
            else:
                # Try direct access
                filings = data
            
            if not filings or not isinstance(filings, dict):
                return []
            
            forms = filings.get('form', [])
            dates = filings.get('reportDate', [])
            accession_numbers = filings.get('accessionNumber', [])
            
            # Debug: log what we found
            if not forms:
                logger.debug(f"No forms found in response for CIK {cik}")
                return []
            
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
        """Get the content of a specific filing."""
        try:
            accession_no_dash = accession_number.replace('-', '')
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
        """Extract revenue data by geography from filing text."""
        revenue_records = []
        
        if not filing_text:
            return revenue_records
        
        regions = [
            "United States", "U.S.", "US", "North America",
            "Europe", "Asia", "Asia Pacific", "APAC",
            "Latin America", "Latin America and Caribbean", "LATAM",
            "Middle East", "Africa", "EMEA",
            "China", "Japan", "Canada", "Mexico", "Brazil",
            "United Kingdom", "UK", "France", "Germany", "Australia"
        ]
        
        sections = re.split(r'\n\s*\n|\r\n\r\n', filing_text)
        
        for section in sections:
            section_lower = section.lower()
            if any(word in section_lower for word in ['geographic', 'geography', 'region', 'segment']) and \
               any(word in section_lower for word in ['revenue', 'sales', 'net sales']):
                
                for region in regions:
                    pattern = rf'{re.escape(region)}[^\$]*?\$?\s*(\d{{1,3}}(?:,\d{{3}})*(?:\.\d+)?)\s*(?:million|billion|M|B)?'
                    matches = re.finditer(pattern, section, re.IGNORECASE)
                    
                    for match in matches:
                        amount_str = match.group(1).replace(',', '')
                        try:
                            amount = float(amount_str)
                            context = section[max(0, match.start()-50):match.end()+50].lower()
                            if 'billion' in context or 'b' in context:
                                amount = amount * 1000
                            
                            revenue_records.append({
                                'company': company_name,
                                'region': region,
                                'revenue_millions': amount,
                                'source': 'sec_filing',
                                'extraction_method': 'pattern_matching'
                            })
                        except ValueError:
                            continue
        
        # Remove duplicates
        seen = set()
        unique_records = []
        for record in revenue_records:
            key = (record['company'], record['region'])
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def scrape_all(self, limit: int = 2) -> List[Dict]:
        """Scrape all configured companies."""
        all_revenue_data = []
        
        for company_name, company_info in FAST_FOOD_CHAINS.items():
            cik = company_info.get('cik')
            ticker = company_info.get('ticker')
            
            if not cik:
                logger.warning(f"Skipping {company_name} - no CIK available")
                continue
            
            logger.info(f"Processing {company_name} (CIK: {cik}, Ticker: {ticker})")
            
            filings = self._get_company_filings(cik, form_type="10-K", limit=limit)
            
            if not filings:
                filings = self._get_company_filings(cik, form_type="10-Q", limit=limit)
            
            for filing in filings:
                filing_date = filing.get('date')
                accession_number = filing.get('accession_number')
                
                logger.info(f"  Fetching filing {accession_number} dated {filing_date}")
                
                filing_text = self._get_filing_content(cik, accession_number)
                
                if not filing_text:
                    continue
                
                revenue_data = self._extract_revenue_by_geography(filing_text, company_name)
                
                if revenue_data:
                    logger.info(f"  Extracted {len(revenue_data)} revenue records")
                    
                    for record in revenue_data:
                        all_revenue_data.append({
                            'company': record['company'],
                            'region': record['region'],
                            'revenue_millions': record['revenue_millions'],
                            'filing_date': filing_date,
                            'filing_type': filing.get('form'),
                            'accession_number': accession_number,
                            'ticker': ticker,
                            'extraction_method': record['extraction_method']
                        })
                
                time.sleep(0.5)
        
        return all_revenue_data


def main():
    """Main function."""
    print("="*70)
    print("SEC Filings Scraper - Fast Food Chains Revenue by Geography")
    print("="*70)
    
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scraper = StandaloneSECScraper()
    
    try:
        print("\nScraping SEC filings for top fast food chains...")
        print(f"Companies: {', '.join([c for c in FAST_FOOD_CHAINS.keys() if FAST_FOOD_CHAINS[c]['cik']])}\n")
        
        revenue_data = scraper.scrape_all(limit=2)
        
        print(f"\n✓ Scraped {len(revenue_data)} revenue records")
        
        if revenue_data:
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(revenue_data)
                csv_file = output_dir / 'revenue_by_geography.csv'
                df.to_csv(csv_file, index=False)
                print(f"✓ Saved revenue data to: {csv_file}")
                print(f"  Records: {len(df)}")
                print(f"\nSample data:")
                print(df.head(10).to_string())
            else:
                json_file = output_dir / 'revenue_by_geography.json'
                with open(json_file, 'w') as f:
                    json.dump(revenue_data, f, indent=2)
                print(f"✓ Saved revenue data to: {json_file}")
        else:
            print("\n⚠️  No revenue data extracted.")
            print("  This could be due to:")
            print("  - Rate limiting by SEC (wait a few minutes)")
            print("  - Changes in SEC filing format")
            print("  - Network issues")
            print("\n  Note: SEC EDGAR has rate limits. If you see 429 errors,")
            print("  wait a few minutes before running again.")
        
        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
