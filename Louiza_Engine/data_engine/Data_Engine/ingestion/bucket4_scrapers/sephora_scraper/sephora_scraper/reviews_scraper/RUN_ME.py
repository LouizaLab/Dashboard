#!/usr/bin/env python3
"""
Simple script to run the scraper - just execute this!
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("Running Sephora Reviews Scraper")
print("="*60)
print("\nThis will:")
print("1. Delete old CSV (if exists)")
print("2. Scrape reviews with product names")
print("3. Show results")
print("\nStarting...\n")

# Delete old CSV
csv_path = 'Output/product_reviews.csv'
if os.path.exists(csv_path):
    os.remove(csv_path)
    print(f"✓ Deleted old CSV")

# Run scraper
print("\nRunning reviews_scraper.py...\n")
subprocess.run([sys.executable, 'reviews_scraper.py'])

# Show results
if os.path.exists(csv_path):
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    print(f"\n{'='*60}")
    print(f"✓ Complete! Found {len(lines)-1} reviews")
    print(f"{'='*60}")
    
    # Check for product_name column
    if lines:
        headers = lines[0].strip().split(',')
        if 'product_name' in headers:
            print("✓ product_name column is included!")
        else:
            print("⚠ product_name column NOT found")
else:
    print("\n⚠ No CSV file created - check for errors above")




