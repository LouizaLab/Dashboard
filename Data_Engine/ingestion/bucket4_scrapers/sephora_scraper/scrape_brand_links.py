"""
Scrape brand links from Sephora's brand list page.
"""
import requests
from bs4 import BeautifulSoup
import time
import os

def scrape_brand_links():
    """Scrape all brand links from Sephora."""
    base_url = "https://www.sephora.com/brands-list"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    brand_links = []
    
    try:
        print("Fetching brand list page...")
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all brand links (adjust selector based on actual HTML structure)
        brand_elements = soup.find_all('a', href=True)
        
        for element in brand_elements:
            href = element.get('href', '')
            if '/brand/' in href or '/brands/' in href:
                full_url = href if href.startswith('http') else f"https://www.sephora.com{href}"
                if full_url not in brand_links:
                    brand_links.append(full_url)
        
        print(f"Found {len(brand_links)} brand links")
        
    except Exception as e:
        print(f"Error scraping brand links: {e}")
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    output_file = 'data/brand_link.txt'
    with open(output_file, 'w') as f:
        for link in brand_links:
            f.write(f"{link}\n")
    
    print(f"Saved {len(brand_links)} brand links to {output_file}")
    return brand_links

if __name__ == "__main__":
    scrape_brand_links()



