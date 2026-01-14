"""
Review Processor - Normalize, extract items/attributes, analyze sentiment
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    SentimentIntensityAnalyzer = None


class ReviewProcessor:
    """Process and analyze Google Reviews."""
    
    # Food item vocabulary
    FOOD_ITEMS = [
        "burger", "fries", "chicken sandwich", "nuggets", "taco", "burrito",
        "sauce", "shake", "soda", "coffee", "salad", "wrap", "sandwich",
        "chicken", "fish", "breakfast", "hash browns", "mcmuffin", "biscuit"
    ]
    
    # Attribute vocabulary
    TASTE_ATTRIBUTES = ["crispy", "greasy", "juicy", "bland", "dry", "tender", 
                        "tough", "flavorful", "tasty", "delicious", "yummy"]
    VALUE_ATTRIBUTES = ["expensive", "cheap", "worth it", "value", "overpriced",
                        "affordable", "pricey", "budget"]
    QUALITY_ATTRIBUTES = ["fresh", "stale", "hot", "cold", "warm", "quality",
                          "premium", "standard"]
    
    def __init__(self):
        """Initialize processor."""
        self.sentiment_analyzer = None
        if VADER_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        else:
            print("⚠️  VADER not installed. Install with: pip install vaderSentiment")
            print("   Using simple sentiment scoring instead.")
    
    def normalize_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize review into canonical schema.
        
        Args:
            review: Raw review dictionary
            
        Returns:
            Normalized review
        """
        text = review.get('review_text', '').lower()
        
        # Clean text
        text = re.sub(r'http\S+|www\.\S+', '', text)  # Remove URLs
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Parse date
        date_str = review.get('date', '')
        parsed_date = self._parse_date(date_str)
        
        return {
            'brand': review.get('brand', ''),
            'city': review.get('city', ''),
            'review_text': text,
            'rating': int(review.get('rating', 0)),
            'date': parsed_date,
            'likes': int(review.get('likes', 0)),
            'author': review.get('author', ''),
            'place_id': review.get('place_id', ''),
        }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Try relative dates (e.g., "2 weeks ago")
        if 'ago' in date_str.lower():
            # For now, return None - could implement relative date parsing
            return None
        
        return None
    
    def extract_food_items(self, text: str) -> List[str]:
        """
        Extract mentioned food items from text.
        
        Args:
            text: Review text
            
        Returns:
            List of mentioned food items
        """
        mentioned = []
        text_lower = text.lower()
        
        for item in self.FOOD_ITEMS:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(item) + r'\b'
            if re.search(pattern, text_lower):
                mentioned.append(item)
        
        return mentioned
    
    def extract_attributes(self, text: str) -> Dict[str, List[str]]:
        """
        Extract mentioned attributes from text.
        
        Args:
            text: Review text
            
        Returns:
            Dictionary with 'taste', 'value', 'quality' lists
        """
        text_lower = text.lower()
        attributes = {
            'taste': [],
            'value': [],
            'quality': []
        }
        
        for attr in self.TASTE_ATTRIBUTES:
            if re.search(r'\b' + re.escape(attr) + r'\b', text_lower):
                attributes['taste'].append(attr)
        
        for attr in self.VALUE_ATTRIBUTES:
            if re.search(r'\b' + re.escape(attr) + r'\b', text_lower):
                attributes['value'].append(attr)
        
        for attr in self.QUALITY_ATTRIBUTES:
            if re.search(r'\b' + re.escape(attr) + r'\b', text_lower):
                attributes['quality'].append(attr)
        
        return attributes
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Review text
            
        Returns:
            Dictionary with sentiment scores
        """
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }
        else:
            # Simple fallback: use rating-based sentiment
            # This is a placeholder - should use actual sentiment analysis
            return {
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0
            }
    
    def process_reviews(self, reviews: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Process all reviews into structured DataFrame.
        
        Args:
            reviews: List of raw reviews
            
        Returns:
            DataFrame with processed reviews
        """
        processed = []
        
        for review in reviews:
            normalized = self.normalize_review(review)
            text = normalized['review_text']
            
            # Extract items and attributes
            food_items = self.extract_food_items(text)
            attributes = self.extract_attributes(text)
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(text)
            
            # Create sentence-level analysis for food items
            sentences = re.split(r'[.!?]+', text)
            item_sentiments = {}
            
            for item in food_items:
                item_sentences = [s for s in sentences if item in s.lower()]
                if item_sentences:
                    item_text = ' '.join(item_sentences)
                    item_sentiment = self.analyze_sentiment(item_text)
                    item_sentiments[item] = item_sentiment['compound']
            
            processed.append({
                **normalized,
                'food_items': ','.join(food_items),
                'food_items_list': food_items,
                'taste_attributes': ','.join(attributes['taste']),
                'value_attributes': ','.join(attributes['value']),
                'quality_attributes': ','.join(attributes['quality']),
                'sentiment_compound': sentiment['compound'],
                'sentiment_positive': sentiment['positive'],
                'sentiment_negative': sentiment['negative'],
                'item_sentiments': item_sentiments,
            })
        
        return pd.DataFrame(processed)

