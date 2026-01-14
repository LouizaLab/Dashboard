"""
Google Reviews Scraper using SerpAPI
Fast, production-ready scraper for Google Maps reviews.
"""
import os
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class GoogleReviewsScraper:
    """Scrape Google Maps reviews using SerpAPI."""
    
    def __init__(self, api_key: Optional[str] = None, delay: float = 1.0):
        """
        Initialize scraper.
        
        Args:
            api_key: SerpAPI key (or set SERPAPI_KEY env var)
            delay: Delay between requests (seconds)
        """
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError(
                "SerpAPI key required. Set SERPAPI_KEY env var or pass api_key parameter."
            )
        self.delay = delay
        self.base_url = "https://serpapi.com/search"
    
    def search_places(self, brand: str, city: str, max_results: int = 10) -> List[str]:
        """
        Find multiple place_ids for a brand in a city.
        
        Args:
            brand: Brand name (e.g., "McDonald's")
            city: City name (e.g., "New York")
            max_results: Maximum number of locations to return
            
        Returns:
            List of place IDs
        """
        query = f"{brand} {city}"
        params = {
            'engine': 'google_maps',
            'q': query,
            'api_key': self.api_key,
            'type': 'search'
        }
        
        time.sleep(self.delay)
        
        place_ids = []
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Get all results' place_ids
            if 'local_results' in data:
                for result in data['local_results'][:max_results]:
                    place_id = result.get('place_id')
                    if place_id:
                        place_ids.append(place_id)
            
            return place_ids
        except Exception as e:
            print(f"  ⚠️  Error searching for {query}: {e}")
            return []
    
    def search_place(self, brand: str, city: str) -> Optional[str]:
        """Legacy method - returns first place_id."""
        places = self.search_places(brand, city, max_results=1)
        return places[0] if places else None
    
    def get_reviews(self, place_id: str, max_reviews: int = 1000, max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        Get reviews for a place.
        
        Args:
            place_id: Google Maps place ID
            max_reviews: Maximum reviews to fetch
            max_pages: Maximum pages to fetch (to avoid infinite loops)
            
        Returns:
            List of review dictionaries
        """
        all_reviews = []
        next_page_token = None
        reviews_per_page = 20  # SerpAPI returns ~20 per page
        pages_fetched = 0
        
        print(f"    Fetching reviews (max {max_reviews}, up to {max_pages} pages)...")
        
        while len(all_reviews) < max_reviews and pages_fetched < max_pages:
            params = {
                'engine': 'google_maps_reviews',
                'place_id': place_id,
                'api_key': self.api_key,
            }
            
            if next_page_token:
                params['next_page_token'] = next_page_token
            
            time.sleep(self.delay)
            
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                reviews = data.get('reviews', [])
                if not reviews:
                    break
                
                for review in reviews:
                    if len(all_reviews) >= max_reviews:
                        break
                    
                    all_reviews.append({
                        'review_text': review.get('snippet', ''),
                        'rating': review.get('rating', 0),
                        'date': review.get('date', ''),
                        'likes': review.get('thumbs_up', 0),
                        'author': review.get('user', {}).get('name', ''),
                    })
                
                pages_fetched += 1
                
                # Check for next page
                next_page_token = data.get('serpapi_pagination', {}).get('next_page_token')
                if not next_page_token:
                    break
                    
                if pages_fetched % 5 == 0:  # Print every 5 pages
                    print(f"      Fetched {len(all_reviews)}/{max_reviews} reviews (page {pages_fetched})...")
                
            except Exception as e:
                print(f"    ⚠️  Error fetching reviews: {e}")
                break
        
        return all_reviews[:max_reviews]
    
    def scrape_brand_city(self, brand: str, city: str, max_reviews: int = 1000, locations_per_city: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape reviews for a brand in a specific city from multiple locations.
        
        Args:
            brand: Brand name
            city: City name
            max_reviews: Maximum reviews to fetch total
            locations_per_city: Number of locations to scrape per city
            
        Returns:
            List of reviews with brand and city metadata
        """
        print(f"  Scraping {brand} in {city} (up to {locations_per_city} locations)...")
        
        # Find multiple locations
        place_ids = self.search_places(brand, city, max_results=locations_per_city)
        if not place_ids:
            print(f"    ⚠️  Could not find {brand} in {city}")
            return []
        
        print(f"    Found {len(place_ids)} location(s)")
        
        all_reviews = []
        # Fixed amount per location - aim for 150 reviews per location consistently
        reviews_per_location = 150  # Fixed amount for consistency
        
        # Get reviews from ALL locations - collect maximum possible
        for idx, place_id in enumerate(place_ids, 1):
            remaining = max_reviews - len(all_reviews)
            if remaining <= 0:
                break
            
            reviews_to_fetch = min(reviews_per_location, remaining)
            
            print(f"    Location {idx}/{len(place_ids)}: Fetching up to {reviews_to_fetch} reviews...")
            # Fetch up to 10 pages per location (10 pages × 20 reviews = ~200 reviews max)
            reviews = self.get_reviews(place_id, reviews_to_fetch, max_pages=10)
            
            # Add metadata
            for review in reviews:
                review['brand'] = brand
                review['city'] = city
                review['place_id'] = place_id
                review['location_index'] = idx
            
            all_reviews.extend(reviews)
            print(f"      ✓ Got {len(reviews)} reviews from location {idx}")
        
        print(f"    ✓ Total: {len(all_reviews)} reviews from {len(place_ids)} locations")
        return all_reviews[:max_reviews]
    
    def scrape_all(self, brands: List[str], cities: List[str], max_reviews_per_brand: int = 1000, locations_per_city: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape reviews for all brand-city combinations.
        
        Args:
            brands: List of brand names
            cities: List of city names
            max_reviews_per_brand: Max reviews per brand (distributed across cities)
            locations_per_city: Number of locations to scrape per city
            
        Returns:
            List of all reviews
        """
        all_reviews = []
        # Calculate reviews per city - aim for more total
        reviews_per_city = (max_reviews_per_brand // len(cities)) if cities else max_reviews_per_brand
        reviews_per_city = max(reviews_per_city, 200)  # At least 200 per city to maximize total
        
        for brand_idx, brand in enumerate(brands, 1):
            print(f"\n[{brand_idx}/{len(brands)}] Processing {brand}...")
            brand_reviews = []
            
            for city_idx, city in enumerate(cities, 1):
                print(f"  [{city_idx}/{len(cities)}] {city}")
                reviews = self.scrape_brand_city(brand, city, reviews_per_city, locations_per_city)
                brand_reviews.extend(reviews)
                # Collect from ALL cities - don't stop early
        
            # Collect ALL reviews from all cities (no limit)
            all_reviews.extend(brand_reviews)
            print(f"\n✓ {brand}: Collected {len(brand_reviews)} reviews")
        
        return all_reviews

