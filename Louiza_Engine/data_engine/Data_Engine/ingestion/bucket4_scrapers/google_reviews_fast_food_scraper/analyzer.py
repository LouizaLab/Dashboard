"""
Aggregator and Analyzer - Generate insights and trends
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path


class ReviewAnalyzer:
    """Analyze processed reviews and generate insights."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with processed reviews DataFrame.
        
        Args:
            df: Processed reviews DataFrame
        """
        self.df = df.copy()
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
    
    def brand_sentiment_trends(self) -> pd.DataFrame:
        """
        Calculate average sentiment by brand over time.
        
        Returns:
            DataFrame with brand, date, avg_sentiment, review_count
        """
        if 'date' not in self.df.columns or self.df['date'].isna().all():
            # If no dates, just aggregate by brand
            return self.df.groupby('brand').agg({
                'sentiment_compound': 'mean',
                'rating': 'mean',
                'review_text': 'count'
            }).reset_index().rename(columns={
                'sentiment_compound': 'avg_sentiment',
                'rating': 'avg_rating',
                'review_text': 'review_count'
            })
        
        # Group by brand and month
        self.df['year_month'] = self.df['date'].dt.to_period('M')
        
        trends = self.df.groupby(['brand', 'year_month']).agg({
            'sentiment_compound': 'mean',
            'rating': 'mean',
            'review_text': 'count'
        }).reset_index()
        
        trends.columns = ['brand', 'date', 'avg_sentiment', 'avg_rating', 'review_count']
        trends['date'] = trends['date'].astype(str)
        
        return trends
    
    def item_sentiment_by_brand(self) -> pd.DataFrame:
        """
        Calculate average sentiment by food item per brand.
        
        Returns:
            DataFrame with brand, food_item, avg_sentiment, mention_count
        """
        results = []
        
        for _, row in self.df.iterrows():
            brand = row['brand']
            items = row.get('food_items_list', [])
            item_sentiments = row.get('item_sentiments', {})
            
            for item in items:
                sentiment = item_sentiments.get(item, row['sentiment_compound'])
                results.append({
                    'brand': brand,
                    'food_item': item,
                    'sentiment': sentiment,
                    'rating': row['rating']
                })
        
        if not results:
            return pd.DataFrame()
        
        item_df = pd.DataFrame(results)
        
        return item_df.groupby(['brand', 'food_item']).agg({
            'sentiment': 'mean',
            'rating': 'mean'
        }).reset_index().assign(
            mention_count=item_df.groupby(['brand', 'food_item']).size().values
        ).rename(columns={
            'sentiment': 'avg_sentiment',
            'rating': 'avg_rating'
        })
    
    def attribute_frequency(self) -> pd.DataFrame:
        """
        Calculate attribute frequency by brand.
        
        Returns:
            DataFrame with brand, attribute_type, attribute, frequency
        """
        results = []
        
        for _, row in self.df.iterrows():
            brand = row['brand']
            
            for attr_type in ['taste', 'value', 'quality']:
                attrs = row.get(f'{attr_type}_attributes', '').split(',')
                attrs = [a.strip() for a in attrs if a.strip()]
                
                for attr in attrs:
                    results.append({
                        'brand': brand,
                        'attribute_type': attr_type,
                        'attribute': attr
                    })
        
        if not results:
            return pd.DataFrame()
        
        attr_df = pd.DataFrame(results)
        
        return attr_df.groupby(['brand', 'attribute_type', 'attribute']).size().reset_index(name='frequency')
    
    def regional_differences(self) -> pd.DataFrame:
        """
        Calculate sentiment differences by city.
        
        Returns:
            DataFrame with brand, city, avg_sentiment, review_count
        """
        return self.df.groupby(['brand', 'city']).agg({
            'sentiment_compound': 'mean',
            'rating': 'mean',
            'review_text': 'count'
        }).reset_index().rename(columns={
            'sentiment_compound': 'avg_sentiment',
            'rating': 'avg_rating',
            'review_text': 'review_count'
        })
    
    def monthly_trends(self) -> pd.DataFrame:
        """
        Calculate month-over-month trend deltas.
        
        Returns:
            DataFrame with brand, month, sentiment_delta, rating_delta
        """
        if 'date' not in self.df.columns or self.df['date'].isna().all():
            return pd.DataFrame()
        
        self.df['year_month'] = self.df['date'].dt.to_period('M')
        
        monthly = self.df.groupby(['brand', 'year_month']).agg({
            'sentiment_compound': 'mean',
            'rating': 'mean'
        }).reset_index()
        
        monthly = monthly.sort_values(['brand', 'year_month'])
        monthly['sentiment_delta'] = monthly.groupby('brand')['sentiment_compound'].diff()
        monthly['rating_delta'] = monthly.groupby('brand')['rating'].diff()
        
        return monthly[['brand', 'year_month', 'sentiment_delta', 'rating_delta']].dropna()
    
    def generate_all_insights(self) -> Dict[str, pd.DataFrame]:
        """
        Generate all insights.
        
        Returns:
            Dictionary of insight DataFrames
        """
        return {
            'brand_sentiment_trends': self.brand_sentiment_trends(),
            'item_sentiment_by_brand': self.item_sentiment_by_brand(),
            'attribute_frequency': self.attribute_frequency(),
            'regional_differences': self.regional_differences(),
            'monthly_trends': self.monthly_trends(),
        }

