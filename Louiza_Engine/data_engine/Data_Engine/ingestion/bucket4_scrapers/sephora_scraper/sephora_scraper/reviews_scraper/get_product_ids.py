"""
Script to collect product IDs from Sephora.
This helps expand the product_ids.txt file to 1000+ products.
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random

def get_product_ids_from_category(category_url, max_pages=10):
    """Extract product IDs from a Sephora category page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    product_ids = set()
    
    for page in range(1, max_pages + 1):
        try:
            # Sephora category URLs often support pagination
            url = f"{category_url}?page={page}" if '?' not in category_url else f"{category_url}&page={page}"
            
            print(f"Scraping page {page}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product links - Sephora product URLs contain product IDs
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                # Match product URLs like /product/product-name-P123456
                match = re.search(r'/product/[^/]+-P(\d+)', href)
                if match:
                    product_id = f"P{match.group(1)}"
                    product_ids.add(product_id)
            
            # Also check for data attributes that might contain product IDs
            product_elements = soup.find_all(attrs={'data-product-id': True})
            for elem in product_elements:
                pid = elem.get('data-product-id')
                if pid and pid.startswith('P'):
                    product_ids.add(pid)
            
            time.sleep(random.uniform(1, 2))  # Rate limiting
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    return product_ids

def get_product_ids_from_search(search_term, max_pages=20):
    """Extract product IDs from Sephora search results."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    product_ids = set()
    base_url = "https://www.sephora.com/search"
    
    for page in range(1, max_pages + 1):
        try:
            url = f"{base_url}?keyword={search_term}&page={page}"
            print(f"Searching page {page} for '{search_term}'...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                match = re.search(r'/product/[^/]+-P(\d+)', href)
                if match:
                    product_id = f"P{match.group(1)}"
                    product_ids.add(product_id)
            
            # Check if there are more pages
            if not soup.find('a', {'data-at': 'pagination_next'}):
                break
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    return product_ids

def main():
    """Collect product IDs from multiple sources."""
    all_product_ids = set()
    
    # Popular Sephora categories to scrape
    categories = [
        "https://www.sephora.com/shop/makeup",
        "https://www.sephora.com/shop/skincare",
        "https://www.sephora.com/shop/hair",
        "https://www.sephora.com/shop/fragrance",
        "https://www.sephora.com/shop/bath-body",
    ]
    
    # Popular search terms
    search_terms = [
        "foundation", "mascara", "lipstick", "serum", "moisturizer",
        "cleanser", "shampoo", "perfume", "sunscreen", "concealer"
    ]
    
    print("=" * 60)
    print("Collecting Product IDs from Sephora")
    print("=" * 60)
    
    # Scrape categories
    print("\n1. Scraping categories...")
    for category_url in categories:
        print(f"\n  Category: {category_url}")
        ids = get_product_ids_from_category(category_url, max_pages=10)
        all_product_ids.update(ids)
        print(f"  Found {len(ids)} products (Total: {len(all_product_ids)})")
    
    # Scrape search results
    print("\n2. Scraping search results...")
    for term in search_terms:
        print(f"\n  Search term: {term}")
        ids = get_product_ids_from_search(term, max_pages=10)
        all_product_ids.update(ids)
        print(f"  Found {len(ids)} products (Total: {len(all_product_ids)})")
    
    # Save to file
    output_file = 'product_ids.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for pid in sorted(all_product_ids):
            f.write(f"{pid}\n")
    
    print("\n" + "=" * 60)
    print(f"✓ Collected {len(all_product_ids)} unique product IDs")
    print(f"✓ Saved to {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()




