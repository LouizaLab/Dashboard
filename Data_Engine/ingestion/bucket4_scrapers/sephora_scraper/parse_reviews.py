"""
Parse reviews JSON and create structured CSV files.
"""
import json
import pandas as pd
import os

def parse_reviews():
    """Parse reviews JSON and create CSV files."""
    reviews_file = 'data/scraper_result.json'
    
    if not os.path.exists(reviews_file):
        print(f"Error: {reviews_file} not found. Run scrape_reviews.py first.")
        return
    
    # Load reviews
    with open(reviews_file, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
    
    if not reviews:
        print("No reviews found in JSON file.")
        return
    
    # Create reviews DataFrame
    reviews_df = pd.DataFrame(reviews)
    
    # Save review data
    os.makedirs('data', exist_ok=True)
    reviews_output = 'data/review_data.csv'
    reviews_df.to_csv(reviews_output, index=False)
    print(f"Saved {len(reviews_df)} reviews to {reviews_output}")
    
    # Create product data with review counts
    product_data = []
    for product_url in reviews_df['product_url'].unique():
        product_reviews = reviews_df[reviews_df['product_url'] == product_url]
        product_data.append({
            'product_url': product_url,
            'review_count': len(product_reviews),
            'avg_rating': product_reviews['rating'].mean() if 'rating' in product_reviews.columns else None
        })
    
    products_df = pd.DataFrame(product_data)
    products_output = 'data/product_data.csv'
    products_df.to_csv(products_output, index=False)
    print(f"Saved {len(products_df)} products to {products_output}")
    
    print("\n✓ Parsing complete!")

if __name__ == "__main__":
    parse_reviews()



