#!/usr/bin/env python3
"""
Add a few more product IDs to ensure we get 1000+ reviews total.
Tests product IDs to find ones with many reviews.
"""
import requests
import time

def test_product_id(pid):
    """Test if product exists and return review count."""
    url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{pid}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            return data.get('TotalResults', 0)
    except:
        pass
    return 0

def main():
    """Find products with many reviews."""
    print("Finding products with many reviews...")
    print("Goal: Get enough products to reach 1000+ reviews total\n")
    
    # Load existing
    existing = set()
    try:
        with open('product_ids.txt', 'r') as f:
            existing = {line.strip() for line in f if line.strip()}
        print(f"Current product IDs: {len(existing)}")
    except:
        pass
    
    # Test existing IDs to see review counts
    print("\nChecking review counts for existing products...")
    total_reviews = 0
    for pid in existing:
        count = test_product_id(pid)
        total_reviews += count
        print(f"  {pid}: {count} reviews")
        time.sleep(0.1)
    
    print(f"\nCurrent total reviews: {total_reviews}")
    
    if total_reviews >= 1000:
        print("✓ You already have enough products for 1000+ reviews!")
        return
    
    # Find more products with many reviews
    print(f"\nNeed {1000 - total_reviews} more reviews. Finding products...")
    
    found = []
    # Test ranges around known IDs
    for base in [400000, 444000, 460000, 500000, 505000, 512000]:
        print(f"\nTesting range around P{base}...")
        for offset in range(0, 1000, 20):  # Test every 20th ID
            pid = f"P{base + offset}"
            if pid not in existing:
                count = test_product_id(pid)
                if count > 50:  # Only keep products with 50+ reviews
                    found.append((pid, count))
                    total_reviews += count
                    print(f"  ✓ Found: {pid} ({count} reviews) - Total: {total_reviews}")
                    
                    if total_reviews >= 1000:
                        print(f"\n✓ Reached 1000+ reviews! Found {len(found)} new products")
                        break
            time.sleep(0.1)
        
        if total_reviews >= 1000:
            break
    
    # Add found products
    all_ids = existing | {pid for pid, count in found}
    with open('product_ids.txt', 'w') as f:
        for pid in sorted(all_ids):
            f.write(f"{pid}\n")
    
    print(f"\n✓ Total: {len(all_ids)} products, ~{total_reviews} reviews")
    print("Now run: python3 reviews_scraper.py")

if __name__ == '__main__':
    main()


