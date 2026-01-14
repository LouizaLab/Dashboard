#!/usr/bin/env python3
"""
Quick script to expand product_ids.txt with more IDs.
Uses API testing which is more reliable than HTML scraping.
"""
import requests
import time

def test_product_id(pid):
    """Quick test if product exists."""
    url = f'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{pid}&Limit=1&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200 and r.json().get('TotalResults', 0) > 0:
            return True
    except:
        pass
    return False

# Load existing
existing = set()
try:
    with open('product_ids.txt', 'r') as f:
        existing = {line.strip() for line in f if line.strip()}
except:
    pass

print(f"Starting with {len(existing)} existing IDs")
print("Testing product ID ranges...")

# Test ranges around known IDs
found = []
for base in [300000, 400000, 444000, 460000, 500000, 505000]:
    print(f"\nTesting range {base}000-{base+1}000...")
    for i in range(0, 1000, 5):  # Test every 5th ID
        pid = f"P{base + i}"
        if pid not in existing and test_product_id(pid):
            found.append(pid)
            print(f"  ✓ Found: {pid}")
        if len(found) >= 50:  # Stop after finding 50 new ones
            break
        time.sleep(0.1)
    if len(found) >= 50:
        break

# Combine and save
all_ids = existing | set(found)
with open('product_ids.txt', 'w') as f:
    for pid in sorted(all_ids):
        f.write(f"{pid}\n")

print(f"\n✓ Total: {len(all_ids)} product IDs ({len(found)} new)")



