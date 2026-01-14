"""
Scrape product reviews from product pages.
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import os

def scrape_reviews():
    """Scrape reviews from product pages."""
    product_file = 'data/product_links.txt'
    
    if not os.path.exists(product_file):
        print(f"Error: {product_file} not found. Run scrape_product_links.py first.")
        return
    
    # Read product links
    with open(product_file, 'r') as f:
        product_links = [line.strip() for line in f if line.strip()]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_reviews = []
    
    print(f"Processing {len(product_links)} products for reviews...")
    
    for idx, product_url in enumerate(product_links, 1):
        try:
            print(f"[{idx}/{len(product_links)}] Processing reviews for {product_url}...")
            
            # Try to find reviews API endpoint or scrape from page
            # Sephora often uses API endpoints like: /api/product/{id}/reviews
            response = requests.get(product_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find review elements (adjust selectors)
            review_elements = soup.find_all('div', class_='review') or soup.find_all('div', {'data-at': 'review'})
            
            product_reviews = []
            for review_elem in review_elements:
                review_data = {
                    'product_url': product_url,
                    'rating': '',
                    'review_text': '',
                    'author': '',
                    'date': '',
                    'verified_purchase': False
                }
                
                # Extract rating
                rating_elem = review_elem.find('span', class_='rating') or review_elem.find('div', {'data-at': 'rating'})
                if rating_elem:
                    review_data['rating'] = rating_elem.get_text(strip=True)
                
                # Extract review text
                text_elem = review_elem.find('div', class_='review-text') or review_elem.find('p')
                if text_elem:
                    review_data['review_text'] = text_elem.get_text(strip=True)
                
                # Extract author
                author_elem = review_elem.find('span', class_='author') or review_elem.find('div', {'data-at': 'author'})
                if author_elem:
                    review_data['author'] = author_elem.get_text(strip=True)
                
                # Extract date
                date_elem = review_elem.find('span', class_='date') or review_elem.find('time')
                if date_elem:
                    review_data['date'] = date_elem.get_text(strip=True)
                
                if review_data['review_text']:
                    product_reviews.append(review_data)
            
            all_reviews.extend(product_reviews)
            print(f"  Found {len(product_reviews)} reviews")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error processing {product_url}: {e}")
            continue
    
    # Save to JSON
    os.makedirs('data', exist_ok=True)
    output_file = 'data/scraper_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(all_reviews)} reviews to {output_file}")
    return all_reviews

if __name__ == "__main__":
    scrape_reviews()




