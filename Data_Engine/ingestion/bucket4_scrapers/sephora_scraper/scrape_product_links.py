"""
Scrape product links from brand pages.
"""
import requests
from bs4 import BeautifulSoup
import time
import os

def scrape_product_links():
    """Scrape product links from brand pages."""
    brand_file = 'data/brand_link.txt'
    
    if not os.path.exists(brand_file):
        print(f"Error: {brand_file} not found. Run scrape_brand_links.py first.")
        return
    
    # Read brand links
    with open(brand_file, 'r') as f:
        brand_links = [line.strip() for line in f if line.strip()]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    product_links = []
    
    print(f"Processing {len(brand_links)} brands...")
    
    for idx, brand_url in enumerate(brand_links, 1):
        try:
            print(f"[{idx}/{len(brand_links)}] Processing {brand_url}...")
            response = requests.get(brand_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product links (adjust selector based on actual HTML structure)
            product_elements = soup.find_all('a', href=True)
            
            for element in product_elements:
                href = element.get('href', '')
                if '/product/' in href:
                    full_url = href if href.startswith('http') else f"https://www.sephora.com{href}"
                    if full_url not in product_links:
                        product_links.append(full_url)
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error processing {brand_url}: {e}")
            continue
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    output_file = 'data/product_links.txt'
    with open(output_file, 'w') as f:
        for link in product_links:
            f.write(f"{link}\n")
    
    print(f"\nSaved {len(product_links)} product links to {output_file}")
    return product_links

if __name__ == "__main__":
    scrape_product_links()



