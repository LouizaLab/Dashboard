"""
Scrape product information from product pages.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json

def scrape_product_info():
    """Scrape product information from product pages."""
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
    
    products = []
    
    print(f"Processing {len(product_links)} products...")
    
    for idx, product_url in enumerate(product_links, 1):
        try:
            print(f"[{idx}/{len(product_links)}] Processing {product_url}...")
            response = requests.get(product_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product information (adjust selectors based on actual HTML)
            product_data = {
                'url': product_url,
                'name': '',
                'brand': '',
                'price': '',
                'rating': '',
                'description': '',
                'ingredients': '',
                'category': ''
            }
            
            # Try to find product name
            name_elem = soup.find('h1') or soup.find('span', {'data-at': 'product_name'})
            if name_elem:
                product_data['name'] = name_elem.get_text(strip=True)
            
            # Try to find brand
            brand_elem = soup.find('a', {'data-at': 'brand_name'}) or soup.find('span', class_='brand')
            if brand_elem:
                product_data['brand'] = brand_elem.get_text(strip=True)
            
            # Try to find price
            price_elem = soup.find('span', {'data-at': 'product_price'}) or soup.find('span', class_='price')
            if price_elem:
                product_data['price'] = price_elem.get_text(strip=True)
            
            # Try to find rating
            rating_elem = soup.find('span', {'data-at': 'product_rating'}) or soup.find('span', class_='rating')
            if rating_elem:
                product_data['rating'] = rating_elem.get_text(strip=True)
            
            products.append(product_data)
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error processing {product_url}: {e}")
            continue
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    df = pd.DataFrame(products)
    output_file = 'data/pd_info.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\nSaved {len(products)} products to {output_file}")
    return products

if __name__ == "__main__":
    scrape_product_info()




