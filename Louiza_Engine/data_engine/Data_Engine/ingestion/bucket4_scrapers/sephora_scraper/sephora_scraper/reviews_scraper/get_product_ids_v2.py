#!/usr/bin/env python3
"""
Improved script to collect product IDs from Sephora.
Uses multiple methods to find product IDs.
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json

def get_product_ids_from_api():
    """Try to get product IDs from Sephora's internal API or JavaScript data."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    product_ids = set()
    
    # Try browsing popular product pages directly
    popular_urls = [
        "https://www.sephora.com/best-selling-makeup",
        "https://www.sephora.com/best-selling-skincare",
        "https://www.sephora.com/best-selling-fragrance",
        "https://www.sephora.com/best-selling-hair",
        "https://www.sephora.com/new-products",
        "https://www.sephora.com/shop/bestsellers",
    ]
    
    for url in popular_urls:
        try:
            print(f"Trying: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Method 1: Find product links in href attributes
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    # Match patterns like /product/name-P123456 or /product/P123456
                    matches = re.findall(r'/product/[^/]+-P(\d+)', href)
                    for match in matches:
                        product_ids.add(f"P{match}")
                
                # Method 2: Look for data attributes
                for elem in soup.find_all(attrs={'data-product-id': True}):
                    pid = elem.get('data-product-id')
                    if pid and re.match(r'^P\d+$', pid):
                        product_ids.add(pid)
                
                # Method 3: Look for product IDs in script tags (JSON data)
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        # Recursively search for product IDs
                        def find_ids(obj):
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if k in ['productId', 'product_id', 'id'] and isinstance(v, str) and re.match(r'^P\d+$', v):
                                        product_ids.add(v)
                                    find_ids(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    find_ids(item)
                        find_ids(data)
                    except:
                        pass
                
                # Method 4: Look in all text for product ID patterns
                text = soup.get_text()
                matches = re.findall(r'\bP\d{6,}\b', text)
                for match in matches:
                    if len(match) >= 7:  # Product IDs are usually P + 6+ digits
                        product_ids.add(match)
                
                print(f"  Found {len(product_ids)} unique products so far")
                time.sleep(random.uniform(1, 2))
                
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    return product_ids

def get_product_ids_from_search_improved(search_term, max_pages=5):
    """Improved search that looks for product IDs in multiple ways."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    product_ids = set()
    base_url = "https://www.sephora.com/search"
    
    for page in range(1, max_pages + 1):
        try:
            # Try different URL formats
            urls_to_try = [
                f"{base_url}?keyword={search_term}&currentPage={page}",
                f"{base_url}?keyword={search_term}&page={page}",
                f"{base_url}/{search_term}?page={page}",
            ]
            
            for url in urls_to_try:
                try:
                    print(f"  Trying search URL: {url}")
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find all product links
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            matches = re.findall(r'/product/[^/]+-P(\d+)', href)
                            for match in matches:
                                product_ids.add(f"P{match}")
                        
                        # Look in script tags
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string:
                                matches = re.findall(r'\bP\d{6,}\b', script.string)
                                for match in matches:
                                    if len(match) >= 7:
                                        product_ids.add(match)
                        
                        if product_ids:
                            break  # Found products, move to next page
                            
                except Exception as e:
                    continue
            
            if not product_ids and page == 1:
                break  # No products found on first page, skip this search term
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
    
    return product_ids

def generate_product_ids_from_range():
    """Generate potential product IDs by testing ranges (last resort)."""
    print("\nGenerating product IDs from known ranges...")
    product_ids = set()
    
    # Test a range around known product IDs
    # From your existing IDs: P399755, P444614, P460622, P505392
    # Try ranges around these
    base_ranges = [
        (399000, 400000),  # Around P399755
        (444000, 445000),  # Around P444614
        (460000, 461000),  # Around P460622
        (505000, 506000),  # Around P505392
        (300000, 310000),  # Lower range
        (500000, 510000),  # Higher range
    ]
    
    print("Testing product ID ranges (this may take a while)...")
    tested = 0
    for start, end in base_ranges[:2]:  # Only test first 2 ranges to avoid too many requests
        for pid_num in range(start, end, 10):  # Test every 10th ID
            product_id = f"P{pid_num}"
            # Quick test if product exists by checking API
            try:
                test_url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{product_id}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
                response = requests.get(test_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('TotalResults', 0) > 0:
                        product_ids.add(product_id)
                        print(f"  Found valid product: {product_id}")
            except:
                pass
            tested += 1
            if tested % 50 == 0:
                print(f"  Tested {tested} product IDs...")
            time.sleep(0.1)  # Small delay
    
    return product_ids

def main():
    """Collect product IDs using multiple methods."""
    all_product_ids = set()
    
    print("=" * 60)
    print("Collecting Product IDs from Sephora")
    print("=" * 60)
    
    # Method 1: Try popular pages
    print("\n[1/3] Scraping popular product pages...")
    ids = get_product_ids_from_api()
    all_product_ids.update(ids)
    print(f"  Found {len(ids)} products (Total: {len(all_product_ids)})")
    
    # Method 2: Try improved search
    print("\n[2/3] Trying improved search...")
    search_terms = ["foundation", "serum", "moisturizer", "mascara", "lipstick"]
    for term in search_terms:
        ids = get_product_ids_from_search_improved(term, max_pages=3)
        all_product_ids.update(ids)
        print(f"  '{term}': Found {len(ids)} products (Total: {len(all_product_ids)})")
    
    # Method 3: Load existing IDs
    print("\n[3/3] Loading existing product IDs...")
    try:
        with open('product_ids.txt', 'r') as f:
            existing = {line.strip() for line in f if line.strip() and line.strip().startswith('P')}
        all_product_ids.update(existing)
        print(f"  Loaded {len(existing)} existing IDs")
    except:
        pass
    
    # Save to file
    output_file = 'product_ids.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for pid in sorted(all_product_ids):
            f.write(f"{pid}\n")
    
    print("\n" + "=" * 60)
    print(f"✓ Collected {len(all_product_ids)} unique product IDs")
    print(f"✓ Saved to {output_file}")
    print("=" * 60)
    
    if len(all_product_ids) < 100:
        print("\n⚠ Warning: Only found a few product IDs.")
        print("Sephora may be blocking scraping. Consider:")
        print("1. Using a proxy")
        print("2. Manually adding product IDs to product_ids.txt")
        print("3. Finding product IDs from Sephora's website manually")

if __name__ == '__main__':
    main()




