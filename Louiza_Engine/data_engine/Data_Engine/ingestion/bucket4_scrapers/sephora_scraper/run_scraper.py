#!/usr/bin/env python3
"""
Main runner script for Sephora scraper.
Runs all scraping steps in sequence.
"""
import subprocess
import sys
import os

def run_script(script_name):
    """Run a Python script and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} failed with error: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ {script_name} not found")
        return False

def main():
    """Run all scraper scripts in sequence."""
    print("="*60)
    print("Sephora Scraper - Full Pipeline")
    print("="*60)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    scripts = [
        'scrape_brand_links.py',
        'scrape_product_links.py',
        'scrape_product_info.py',
        'scrape_reviews.py',
        'parse_reviews.py'
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"⚠ Warning: {script} not found, skipping...")
            continue
        
        success = run_script(script)
        if not success:
            print(f"\n⚠ Pipeline stopped at {script}")
            print("You can continue manually or fix the error and rerun.")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ All scraping steps completed successfully!")
    print("="*60)
    print("\nOutput files:")
    print("  - data/brand_link.txt")
    print("  - data/product_links.txt")
    print("  - data/pd_info.csv")
    print("  - data/scraper_result.json")
    print("  - data/review_data.csv")
    print("  - data/product_data.csv")

if __name__ == "__main__":
    main()




