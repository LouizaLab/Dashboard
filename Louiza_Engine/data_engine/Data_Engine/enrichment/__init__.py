"""
Enrichment layer

Optional enrichment pipelines for:
- Text cleaning
- Chunking
- Sentiment analysis
- Topic clustering
- Brand/entity tagging
"""

from .base import EnrichmentPipeline
from .text_cleaner import TextCleaner
from .sentiment_analyzer import SentimentAnalyzer

__all__ = [
    'EnrichmentPipeline',
    'TextCleaner',
    'SentimentAnalyzer',
]

