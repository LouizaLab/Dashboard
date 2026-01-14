"""
Data ingestion layer

Handles ingestion from multiple sources into unified DataRecord format.
"""

from .base import IngestionBase
from .bucket1_online_datasets import OnlineDatasetsIngester
from .bucket2_surveys_interviews import SurveysInterviewsIngester
from .bucket3_financial_data import FinancialDataIngester
from .bucket4_scrapers.base_scraper import BaseScraper

__all__ = [
    'IngestionBase',
    'OnlineDatasetsIngester',
    'SurveysInterviewsIngester',
    'FinancialDataIngester',
    'BaseScraper',
]

