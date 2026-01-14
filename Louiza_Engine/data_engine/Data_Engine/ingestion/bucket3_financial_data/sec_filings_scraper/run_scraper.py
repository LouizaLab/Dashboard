#!/usr/bin/env python3
"""
Standalone runner for SEC Filings Scraper
Can be run directly without importing the full Data_Engine package
"""

import sys
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import and run
from Data_Engine.ingestion.bucket4_scrapers.sec_filings_scraper.scraper import main

if __name__ == "__main__":
    main()
