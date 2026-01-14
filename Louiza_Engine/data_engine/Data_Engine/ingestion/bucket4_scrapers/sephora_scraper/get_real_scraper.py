#!/usr/bin/env python3
"""
Download the actual scraper files from the GitHub repository.
"""
import urllib.request
import os

# GitHub raw file URLs
BASE_URL = "https://raw.githubusercontent.com/nadyinky/sephora-analysis/main/sephora_scraper/"

FILES = [
    "scrape_brand_links.py",
    "scrape_product_links.py",
    "scrape_product_info.py",
    "scrape_reviews.py",
    "parse_reviews.py",
    "requirements.txt"
]

def download_file(filename):
    """Download a file from GitHub."""
    url = BASE_URL + filename
    output_path = filename
    
    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"✓ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def main():
    """Download all files."""
    print("Downloading actual scraper files from GitHub...")
    print("=" * 60)
    
    success = 0
    for filename in FILES:
        if download_file(filename):
            success += 1
    
    print("=" * 60)
    print(f"Downloaded {success}/{len(FILES)} files")
    
    if success == len(FILES):
        print("\n✓ All files downloaded successfully!")
        print("\nBacking up custom files...")
        # Backup the files I created
        for filename in ["scrape_brand_links.py", "scrape_product_links.py", 
                        "scrape_product_info.py", "scrape_reviews.py", "parse_reviews.py"]:
            if os.path.exists(filename):
                backup_name = filename.replace(".py", "_backup.py")
                os.rename(filename, backup_name)
                print(f"  Backed up {filename} -> {backup_name}")
    else:
        print("\n⚠ Some files failed to download")

if __name__ == "__main__":
    main()




