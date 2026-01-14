#!/usr/bin/env python3
"""Download Sephora scraper files from GitHub."""
import os
import urllib.request
import json
import base64

# GitHub API URLs for raw files
BASE_URL = "https://raw.githubusercontent.com/nadyinky/sephora-analysis/main/sephora_scraper/"

# Files to download
FILES = [
    "scrape_brand_links.py",
    "scrape_product_links.py", 
    "scrape_product_info.py",
    "scrape_reviews.py",
    "parse_reviews.py",
    "requirements.txt"
]

def download_file(filename, output_dir):
    """Download a file from GitHub."""
    url = BASE_URL + filename
    output_path = os.path.join(output_dir, filename)
    
    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"✓ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def main():
    """Download all scraper files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # Create data directory
    os.makedirs(data_dir, exist_ok=True)
    
    print("Downloading Sephora scraper files...")
    print("=" * 50)
    
    success_count = 0
    for filename in FILES:
        if download_file(filename, script_dir):
            success_count += 1
    
    print("=" * 50)
    print(f"Downloaded {success_count}/{len(FILES)} files")
    
    if success_count == len(FILES):
        print("\n✓ Setup complete!")
        print("\nNext: Install dependencies with: pip install -r requirements.txt")
    else:
        print("\n⚠ Some files failed to download. Check GitHub repository manually.")

if __name__ == "__main__":
    main()




