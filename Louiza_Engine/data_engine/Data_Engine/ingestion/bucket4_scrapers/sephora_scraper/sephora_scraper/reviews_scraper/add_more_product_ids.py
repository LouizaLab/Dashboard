#!/usr/bin/env python3
"""
Add more product IDs by testing the Bazaarvoice API directly.
This is more reliable than scraping HTML.
"""
import requests
import time
import random

def test_product_id(product_id):
    """Test if a product ID exists by checking the API."""
    url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{product_id}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            total = data.get('TotalResults', 0)
            if total > 0:
                # Try to get product name
                product_name = "Unknown"
                if 'Includes' in data and 'Products' in data['Includes']:
                    products = data['Includes']['Products']
                    if product_id in products:
                        product_name = products[product_id].get('Name', 'Unknown')
                return True, total, product_name
    except:
        pass
    return False, 0, None

def generate_and_test_ids():
    """Generate and test product IDs in ranges."""
    found_ids = []
    
    # Known working ranges from existing IDs
    # P399755, P444614, P460622, P505392
    ranges_to_test = [
        (300000, 600000, 100),  # Test every 100th ID in this range
    ]
    
    print("Testing product ID ranges...")
    print("This will take a while but is more reliable than HTML scraping")
    print("=" * 60)
    
    tested = 0
    for start, end, step in ranges_to_test:
        for pid_num in range(start, end, step):
            product_id = f"P{pid_num}"
            exists, review_count, name = test_product_id(product_id)
            
            if exists:
                found_ids.append((product_id, review_count, name))
                print(f"✓ Found: {product_id} ({review_count} reviews) - {name[:50]}")
            
            tested += 1
            if tested % 20 == 0:
                print(f"  Tested {tested} IDs, found {len(found_ids)} valid products...")
            
            time.sleep(0.2)  # Rate limiting
    
    return found_ids

def main():
    """Find more product IDs."""
    print("=" * 60)
    print("Finding Product IDs via API Testing")
    print("=" * 60)
    print("\nThis method tests product IDs directly via the Bazaarvoice API.")
    print("It's slower but more reliable than HTML scraping.\n")
    
    # Load existing IDs
    existing_ids = set()
    try:
        with open('product_ids.txt', 'r') as f:
            existing_ids = {line.strip() for line in f if line.strip()}
        print(f"Loaded {len(existing_ids)} existing product IDs")
    except:
        pass
    
    # Find new IDs
    found_ids = generate_and_test_ids()
    
    # Add to existing file
    all_ids = existing_ids.copy()
    for pid, count, name in found_ids:
        all_ids.add(pid)
    
    # Save
    with open('product_ids.txt', 'w') as f:
        for pid in sorted(all_ids):
            f.write(f"{pid}\n")
    
    print("\n" + "=" * 60)
    print(f"✓ Total product IDs: {len(all_ids)}")
    print(f"  Existing: {len(existing_ids)}")
    print(f"  New: {len(found_ids)}")
    print("=" * 60)

if __name__ == '__main__':
    main()




