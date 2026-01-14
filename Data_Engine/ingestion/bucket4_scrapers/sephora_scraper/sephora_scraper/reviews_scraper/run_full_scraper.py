#!/usr/bin/env python3
"""
Run the full scraper pipeline:
1. Delete old CSV
2. Collect product IDs (if needed)
3. Run reviews scraper with product names
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show output."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run the full pipeline."""
    script_dir = Path(__file__).parent
    
    print("="*60)
    print("Sephora Reviews Scraper - Full Pipeline")
    print("="*60)
    
    # Step 1: Delete old CSV
    print("\n[1/3] Deleting old CSV file...")
    csv_path = script_dir / 'Output' / 'product_reviews.csv'
    if csv_path.exists():
        csv_path.unlink()
        print(f"✓ Deleted {csv_path}")
    else:
        print("  No old CSV to delete")
    
    # Step 2: Check if we need more product IDs
    print("\n[2/3] Checking product IDs...")
    product_ids_file = script_dir / 'product_ids.txt'
    if product_ids_file.exists():
        with open(product_ids_file, 'r') as f:
            product_ids = [line.strip() for line in f if line.strip()]
        print(f"  Found {len(product_ids)} product IDs")
        
        if len(product_ids) < 50:
            print(f"\n  ⚠ Only {len(product_ids)} product IDs found.")
            print("  Collecting more product IDs...")
            if run_command("python3 get_product_ids.py", "Collecting Product IDs"):
                # Re-read to get updated count
                with open(product_ids_file, 'r') as f:
                    product_ids = [line.strip() for line in f if line.strip()]
                print(f"  ✓ Now have {len(product_ids)} product IDs")
            else:
                print("  ⚠ Product ID collection had issues, continuing with existing IDs...")
    else:
        print("  ⚠ product_ids.txt not found! Creating with sample IDs...")
        with open(product_ids_file, 'w') as f:
            f.write("P399755\nP444614\nP460622\nP505392\n")
        print("  ✓ Created product_ids.txt with sample IDs")
    
    # Step 3: Run the reviews scraper
    print("\n[3/3] Running reviews scraper...")
    if run_command("python3 reviews_scraper.py", "Scraping Reviews"):
        print("\n" + "="*60)
        print("✓ Scraping Complete!")
        print("="*60)
        
        # Show results
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                print(f"\nResults:")
                print(f"  Total reviews: {len(lines) - 1}")  # -1 for header
                print(f"  Output file: {csv_path}")
                
                # Show first few lines to verify product_name column
                if len(lines) > 1:
                    print(f"\nFirst review (showing columns):")
                    headers = lines[0].strip().split(',')
                    print(f"  Columns: {', '.join(headers[:5])}...")
                    if 'product_name' in headers:
                        print(f"  ✓ product_name column found!")
                    else:
                        print(f"  ⚠ product_name column NOT found")
    else:
        print("\n✗ Scraping failed. Check errors above.")

if __name__ == '__main__':
    main()



