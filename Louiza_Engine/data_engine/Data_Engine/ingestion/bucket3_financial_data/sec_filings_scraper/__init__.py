"""
SEC Filings Scraper for Fast Food Chains

Scrapes SEC EDGAR database to extract revenue data by geography from 10-K and 10-Q filings.
"""

from .scraper import SECFilingsScraper

__all__ = ['SECFilingsScraper']


