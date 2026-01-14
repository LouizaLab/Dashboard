import csv
import json
import math
import requests

from math import ceil
from pathlib import Path
from multiprocessing.pool import ThreadPool
from pydantic_basemodel import ReviewInfo


base_url = 'https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId:{}&Limit=100&Offset={}&Include=Products,Comments&Stats=Reviews&passkey=calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus&apiversion=5.4'
remaining_product_urls = []
# Cache for product names
product_name_cache = {}


def make_request(url: str):
    """Makes GET request and retries several times if unsuccessful.

    Args:
        url: URL to make a get request
    Returns:
        Response | None
    """

    # Proxy configuration - set to None if you don't need a proxy
    # Format: 'http://username:password@proxy-server:port' or 'http://proxy-server:port'
    proxy = None  # Change to your proxy URL if needed, e.g., 'http://proxy.example.com:8080'
    proxies = {"https": proxy} if proxy else None
    num_retries = 3
    success_list = [200, 404]
    for _ in range(num_retries):
        try:
            resp = requests.get(url, proxies=proxies, timeout=30)
            if resp.status_code in success_list:
                resp.encoding = 'utf-8'
                print('process')
                return resp  # Return response if successful
        except:
            pass
    return None


def get_first_page_reviews(product_id: str):
    """Extracts and cleans review information from the response using the Pydantic model.
    Counts and stores additional pages if they exist

    Args:
        product_id: The ID of the product to retrieve reviews for
    Returns:
         Success response - List of dictionaries, each dictionary contains 17 keys.
         Unsuccessful response - None.
    """

    # With 'format' function in base url change 'Filter=ProductId:{}' and 'Offset={}' parameters
    first_page_resp = make_request(base_url.format(f'{product_id}', 0))

    if first_page_resp is not None and first_page_resp.status_code == 200:
        try:
            response_data = first_page_resp.json()
            product_reviews = ReviewInfo(**response_data).dict()['Results']
            
            # Extract product name from API response
            product_name = None
            try:
                if 'Includes' in response_data and 'Products' in response_data['Includes']:
                    products = response_data['Includes']['Products']
                    if product_id in products:
                        product_name = products[product_id].get('Name', None)
                        if product_name:
                            product_name_cache[product_id] = product_name
                            print(f"  Found product name: {product_name}")
            except Exception as e:
                print(f"  Warning: Could not extract product name: {e}")
            
            # Add product ID and name to each review
            cur_product_data = {
                'product_id': f'{product_id}',
                'product_name': product_name or 'Unknown'
            }
            for review in product_reviews:
                review.update(cur_product_data)

            # Count the number of additional pages and store the generated URL for each in the list
            total_results = response_data.get('TotalResults', 0)
            num_pages = math.ceil(total_results / 100)
            print(f"  Product {product_id}: {total_results} total reviews, {num_pages} pages")
            
            if num_pages > 1:
                cnt = 100
                for page in range(1, num_pages):  # Start from page 2 (page 1 is already done)
                    remaining_product_urls.append(base_url.format(f'{product_id}', cnt))
                    cnt += 100
            return product_reviews

        except Exception as e:
            print(f'Unexpected error occurred: {type(e).__name__} - {e}')
            return None
    return None


def get_remaining_reviews(page_url: str):
    """Extracts and cleans review information from the response using the Pydantic model.

    Args:
        page_url: The product page URL to retrieve reviews for
    Returns:
         Success response - List of dictionaries, each dictionary contains 17 keys.
         Unsuccessful response - None.
    """

    page_resp = make_request(page_url)

    if page_resp is not None and page_resp.status_code == 200:
        try:
            response_data = page_resp.json()
            product_reviews = ReviewInfo(**response_data).dict()['Results']
            # Extract product ID from URL
            product_id = page_url[63:page_url.find("&")]
            
            # Get product name from cache or extract from response
            product_name = product_name_cache.get(product_id, None)
            if not product_name:
                try:
                    if 'Includes' in response_data and 'Products' in response_data['Includes']:
                        products = response_data['Includes']['Products']
                        if product_id in products:
                            product_name = products[product_id].get('Name', None)
                            if product_name:
                                product_name_cache[product_id] = product_name
                except Exception:
                    pass
            
            cur_product_data = {
                'product_id': f'{product_id}',
                'product_name': product_name or 'Unknown'
            }
            for review in product_reviews:
                review.update(cur_product_data)
            return product_reviews

        except Exception as e:
            print(f'Unexpected error occurred: {type(e).__name__} - {e}')
            return None

    return None


def save_to_csv(all_info: list, table_name: str, first_page_reviews=True) -> None:
    """Saves reviews data to a CSV file in the 'Output' folder.

    Args:
        all_info: A list containing dictionaries with reviews data
        table_name: The name of the CSV file to be created
        first_page_reviews: Reviews from the first page or not
    """

    # Unpack nested lists
    all_info = [dct for sublist in all_info for dct in sublist]
    
    if not all_info:
        print(f'No reviews to save for "{table_name}"')
        return

    # Create a new 'Output' folder if it doesn't exist
    output_path = Path.cwd() / 'Output'
    output_path.mkdir(exist_ok=True)
    csv_path = output_path / f'{table_name}.csv'

    # Ensure product_name is in all reviews
    for review in all_info:
        if 'product_name' not in review:
            review['product_name'] = 'Unknown'

    # Get fieldnames - ensure product_name comes right after product_id
    fieldnames = list(all_info[0].keys())
    if 'product_id' in fieldnames and 'product_name' in fieldnames:
        # Reorder to put product_name right after product_id
        fieldnames.remove('product_name')
        idx = fieldnames.index('product_id')
        fieldnames.insert(idx + 1, 'product_name')

    # Write data to the CSV file
    print(f'Saving {len(all_info)} reviews to "{table_name}.csv"...')

    # If first page, overwrite file; otherwise append
    mode = 'w' if first_page_reviews else 'a'
    with open(csv_path, mode, encoding='utf-8', newline='') as out_file:
        dw = csv.DictWriter(out_file, fieldnames=fieldnames)
        if first_page_reviews:
            dw.writeheader()
        dw.writerows(all_info)

    print(f'✓ Saved {len(all_info)} reviews to "{table_name}.csv"\n')


def main():
    # Upload a file of product IDs in one list
    print('Opening input file...')
    with open('product_ids.txt', 'r', encoding='utf-8') as f:
        product_ids = [line.strip() for line in f if line.strip()]

    print(f'Found {len(product_ids)} product IDs to process')
    
    # Limit processing if you want to test with fewer products first
    # Uncomment the next line to process only first 100 products for testing
    # product_ids = product_ids[:100]

    # Get reviews from the first page of each product and save them in CSV
    print(f'Processing {len(product_ids)} first pages...')
    with ThreadPool(10) as pool:
        all_reviews = list(filter(None, pool.map(get_first_page_reviews, product_ids)))
    save_to_csv(all_reviews, 'product_reviews')

    # If the remaining pages exist, get reviews from them and add to the already created CSV
    if remaining_product_urls:
        print(f'Processing {len(remaining_product_urls)} remaining pages...')
        with ThreadPool(10) as pool:
            all_reviews = list(filter(None, pool.map(get_remaining_reviews, remaining_product_urls)))
        save_to_csv(all_reviews, 'product_reviews', first_page_reviews=False)
    
    # Count total reviews scraped
    csv_path = Path.cwd() / 'Output' / 'product_reviews.csv'
    total_reviews = 0
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            total_reviews = sum(1 for line in f) - 1  # -1 for header
    
    print(f'\n✓ Scraping complete!')
    print(f'  Total products processed: {len(product_ids)}')
    print(f'  Total review pages scraped: {len(product_ids) + len(remaining_product_urls)}')
    print(f'  Total reviews collected: {total_reviews}')
    
    if total_reviews < 1000:
        print(f'\n⚠ Only {total_reviews} reviews collected (target: 1000+)')
        print('  Run: python3 add_few_more_ids.py to add more products')
    else:
        print(f'\n🎉 Success! Collected {total_reviews} reviews (target: 1000+)')


if __name__ == '__main__':
    main()