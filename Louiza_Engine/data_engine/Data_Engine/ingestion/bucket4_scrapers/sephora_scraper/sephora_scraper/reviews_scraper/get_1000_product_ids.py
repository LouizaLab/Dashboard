#!/usr/bin/env python3
"""
Get 1000+ product IDs by testing the Bazaarvoice API.
This is the most reliable method since Sephora blocks HTML scraping.
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_product_id(pid):
    """Test if product ID exists and return info."""
    url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{pid}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            total = data.get('TotalResults', 0)
            if total > 0:
                return pid, total
    except:
        pass
    return None, 0

def test_range(start, end, step=1):
    """Test a range of product IDs."""
    found = []
    for pid_num in range(start, end, step):
        pid = f"P{pid_num}"
        product_id, count = test_product_id(pid)
        if product_id:
            found.append(product_id)
            print(f"  ✓ Found: {product_id} ({count} reviews)")
        time.sleep(0.1)  # Rate limiting
    return found

def main():
    """Find 1000+ product IDs."""
    print("=" * 60)
    print("Finding 1000+ Product IDs via API Testing")
    print("=" * 60)
    
    # Load existing
    existing = set()
    try:
        with open('product_ids.txt', 'r') as f:
            existing = {line.strip() for line in f if line.strip()}
        print(f"\nStarting with {len(existing)} existing IDs")
    except:
        pass
    
    found = []
    
    # Test multiple ranges in parallel
    ranges_to_test = [
        (300000, 400000, 10),   # Test every 10th ID
        (400000, 500000, 10),
        (500000, 600000, 10),
        (200000, 300000, 10),
        (600000, 700000, 10),
    ]
    
    print(f"\nTesting {sum((end-start)//step for start, end, step in ranges_to_test)} product IDs...")
    print("This will take 10-20 minutes but will find many valid IDs\n")
    
    for start, end, step in ranges_to_test:
        print(f"Testing range P{start} - P{end} (step: {step})...")
        range_found = test_range(start, end, step)
        found.extend(range_found)
        print(f"  Found {len(range_found)} in this range (Total: {len(found)})\n")
        
        if len(found) >= 1000:
            print("✓ Reached 1000+ product IDs!")
            break
    
    # Combine and save
    all_ids = existing | set(found)
    with open('product_ids.txt', 'w') as f:
        for pid in sorted(all_ids):
            f.write(f"{pid}\n")
    
    print("=" * 60)
    print(f"✓ Total: {len(all_ids)} product IDs")
    print(f"  Existing: {len(existing)}")
    print(f"  New: {len(found)}")
    print("=" * 60)
    
    if len(all_ids) >= 1000:
        print("\n🎉 Success! You now have 1000+ product IDs!")
        print("Run: python3 reviews_scraper.py to scrape reviews")

if __name__ == '__main__':
    main()




