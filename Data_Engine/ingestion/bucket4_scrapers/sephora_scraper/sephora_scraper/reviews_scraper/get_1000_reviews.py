#!/usr/bin/env python3
"""
Get 1000+ reviews by:
1. Finding products with many reviews
2. Running the scraper to collect all reviews
"""
import requests
import time
import subprocess
import sys

def test_product_id(pid):
    """Test product and return review count."""
    url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{pid}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json().get('TotalResults', 0)
    except:
        pass
    return 0

def main():
    """Find products with many reviews, then scrape."""
    print("=" * 60)
    print("Getting 1000+ Reviews")
    print("=" * 60)
    
    # Load existing
    existing = set()
    try:
        with open('product_ids.txt', 'r') as f:
            existing = {line.strip() for line in f if line.strip()}
    except:
        pass
    
    print(f"\nCurrent products: {len(existing)}")
    
    # Check current review counts
    print("\nChecking review counts...")
    total_reviews = 0
    for pid in list(existing)[:5]:  # Check first 5
        count = test_product_id(pid)
        total_reviews += count
        print(f"  {pid}: {count} reviews")
        time.sleep(0.1)
    
    # Estimate total (assuming similar counts)
    estimated = total_reviews * len(existing) / min(5, len(existing))
    print(f"\nEstimated total reviews: ~{int(estimated)}")
    
    # Find more products if needed
    if estimated < 1000:
        print(f"\nNeed more products. Finding products with many reviews...")
        found = []
        
        # Test ranges to find products with 50+ reviews
        for base in [400000, 444000, 460000, 500000, 512000, 517000]:
            for offset in range(0, 500, 25):  # Test every 25th ID
                pid = f"P{base + offset}"
                if pid not in existing:
                    count = test_product_id(pid)
                    if count > 50:
                        found.append(pid)
                        print(f"  ✓ Found: {pid} ({count} reviews)")
                        if len(found) >= 10:  # Get 10 more products
                            break
                    time.sleep(0.1)
                if len(found) >= 10:
                    break
            if len(found) >= 10:
                break
        
        # Add to file
        if found:
            all_ids = existing | set(found)
            with open('product_ids.txt', 'w') as f:
                for pid in sorted(all_ids):
                    f.write(f"{pid}\n")
            print(f"\n✓ Added {len(found)} products")
    
    # Run scraper
    print("\n" + "=" * 60)
    print("Running reviews scraper...")
    print("=" * 60 + "\n")
    
    subprocess.run([sys.executable, 'reviews_scraper.py'])
    
    # Check results
    import os
    csv_path = 'Output/product_reviews.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            review_count = sum(1 for line in f) - 1
        print(f"\n{'='*60}")
        print(f"✓ Total reviews collected: {review_count}")
        if review_count >= 1000:
            print("🎉 Success! You have 1000+ reviews!")
        else:
            print(f"⚠ Only {review_count} reviews. Run this script again to add more products.")
        print("=" * 60)

if __name__ == '__main__':
    main()



