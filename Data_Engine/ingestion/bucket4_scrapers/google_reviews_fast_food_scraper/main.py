"""
Main pipeline for Google Reviews analysis
Fast, production-ready pipeline for fast-food consumer preference analysis.
"""
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper import GoogleReviewsScraper
from processor import ReviewProcessor
from analyzer import ReviewAnalyzer
from visualizer import ReviewVisualizer


def _create_sample_data():
    """Create sample review data for testing without API."""
    brands = [
        "McDonald's", "Burger King", "Wendy's", "Chick-fil-A",
        "Popeyes", "KFC", "Taco Bell", "Subway", "Domino's",
        "Pizza Hut", "Chipotle", "Starbucks", "Dunkin'",
        "Arby's", "Jack in the Box", "Carl's Jr.", "Hardee's"
    ]
    cities = [
        "New York", "Los Angeles", "Chicago", "Dallas", "Atlanta",
        "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego",
        "Miami", "Seattle", "Boston", "Denver", "Portland"
    ]
    food_items = ["burger", "fries", "chicken sandwich", "nuggets", "taco", "pizza", "wrap", "salad", "coffee", "shake"]
    attributes = ["crispy", "greasy", "juicy", "dry", "expensive", "cheap", "fresh", "stale", "hot", "cold"]
    
    reviews = []
    # Generate ~3000 reviews (more realistic)
    target_reviews = 3000
    reviews_per_brand_city = target_reviews // (len(brands) * len(cities))
    
    for brand in brands:
        for city in cities:
            for _ in range(reviews_per_brand_city):
                review_text = f"The {random.choice(food_items)} was {random.choice(attributes)}. "
                review_text += f"Overall {random.choice(['good', 'okay', 'great', 'terrible', 'amazing', 'disappointing'])} experience."
                
                reviews.append({
                    'brand': brand,
                    'city': city,
                    'review_text': review_text,
                    'rating': random.randint(1, 5),
                    'date': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'likes': random.randint(0, 50),
                    'author': f"User{random.randint(1000, 9999)}",
                    'place_id': f"place_{brand}_{city}_{random.randint(1, 5)}"
                })
    
    return reviews


def main():
    """Main execution function."""
    print("=" * 70)
    print("Google Reviews Fast-Food Analysis Pipeline")
    print("=" * 70)
    print("\nAnalyzing consumer preferences and trends")
    print("=" * 70)
    
    # Configuration - Expanded for 2-5k reviews
    BRANDS = [
        "McDonald's", "Burger King", "Wendy's", "Chick-fil-A",
        "Popeyes", "KFC", "Taco Bell", "Subway", "Domino's",
        "Pizza Hut", "Chipotle", "Starbucks", "Dunkin'",
        "Arby's", "Jack in the Box", "Carl's Jr.", "Hardee's"
    ]
    
    CITIES = [
        "New York", "Los Angeles", "Chicago", "Dallas", "Atlanta",
        "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego",
        "Miami", "Seattle", "Boston", "Denver", "Portland"
    ]
    
    # Target: 2,000-5,000 total reviews
    # Math: 17 brands × 15 cities × 8 locations × 150 reviews/location = potential for many reviews
    # But we'll limit per brand to avoid API overload
    MAX_REVIEWS_PER_BRAND = 400  # Reviews per brand (distributed across cities)
    LOCATIONS_PER_CITY = 8  # Multiple locations per city for more coverage
    
    OUTPUT_DIR = Path(__file__).parent
    
    # Step 1: Scrape reviews
    print("\n[1/6] Scraping Google Reviews...")
    print("-" * 70)
    
    reviews = []
    try:
        scraper = GoogleReviewsScraper(delay=1.0)
        reviews = scraper.scrape_all(
            BRANDS, 
            CITIES, 
            MAX_REVIEWS_PER_BRAND,
            LOCATIONS_PER_CITY
        )
        print(f"\n✓ Total reviews scraped: {len(reviews)}")
        print(f"  Target: 2,000-5,000 reviews")
        print(f"  Actual: {len(reviews)} reviews")
    except ValueError as e:
        print(f"\n⚠️  {e}")
        print("\nTo scrape reviews, you need a SerpAPI key:")
        print("  1. Sign up at https://serpapi.com/ (free tier available)")
        print("  2. Set environment variable: export SERPAPI_KEY='your_key'")
        print("\nFor now, using sample data for demonstration...")
        reviews = _create_sample_data()
    except Exception as e:
        print(f"\n⚠️  Error scraping reviews: {e}")
        print("Using sample data for demonstration...")
        reviews = _create_sample_data()
    
    if not reviews:
        print("\n⚠️  No reviews available. Exiting.")
        return
    
    # Step 2: Process reviews
    print("\n[2/6] Processing reviews...")
    print("-" * 70)
    
    processor = ReviewProcessor()
    df = processor.process_reviews(reviews)
    
    print(f"✓ Processed {len(df)} reviews")
    food_mentions = sum(len(items) for items in df['food_items_list'])
    print(f"✓ Found {food_mentions} food item mentions")
    
    # Step 3: Analyze
    print("\n[3/6] Analyzing trends...")
    print("-" * 70)
    
    analyzer = ReviewAnalyzer(df)
    insights = analyzer.generate_all_insights()
    
    print(f"✓ Brand trends: {len(insights['brand_sentiment_trends'])} data points")
    print(f"✓ Item analysis: {len(insights['item_sentiment_by_brand'])} brand-item pairs")
    print(f"✓ Attributes: {len(insights['attribute_frequency'])} attribute mentions")
    print(f"✓ Regional data: {len(insights['regional_differences'])} brand-city pairs")
    
    # Step 4: Save CSVs
    print("\n[4/6] Saving CSV files...")
    print("-" * 70)
    
    for name, data_df in insights.items():
        if not data_df.empty:
            csv_path = OUTPUT_DIR / f"{name}.csv"
            data_df.to_csv(csv_path, index=False)
            print(f"  ✓ Saved: {name}.csv ({len(data_df)} rows)")
    
    # Also save processed reviews
    df.to_csv(OUTPUT_DIR / "processed_reviews.csv", index=False)
    print(f"  ✓ Saved: processed_reviews.csv ({len(df)} rows)")
    
    # Cleanup: Delete all CSV files except processed_reviews.csv
    print("\n[4.5/6] Cleaning up CSV files...")
    print("-" * 70)
    
    csv_files_to_delete = [
        "attribute_frequency.csv",
        "brand_sentiment_trends.csv",
        "item_sentiment_by_brand.csv",
        "monthly_trends.csv",
        "regional_differences.csv"
    ]
    
    for csv_file in csv_files_to_delete:
        csv_path = OUTPUT_DIR / csv_file
        if csv_path.exists():
            csv_path.unlink()
            print(f"  ✓ Deleted: {csv_file}")
    
    print("  ✓ Cleanup complete - only processed_reviews.csv remains")
    
    # Step 5: Generate visualizations (optional)
    print("\n[5/6] Generating visualizations...")
    print("-" * 70)
    
    try:
        visualizer = ReviewVisualizer(OUTPUT_DIR)
        visualizer.generate_all_plots(insights)
    except Exception as e:
        print(f"  ⚠️  Visualization skipped: {e}")
        print("     Install matplotlib and seaborn for graphs: pip install matplotlib seaborn")
    
    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n📊 Results saved to: {OUTPUT_DIR}/")
    print("\nGenerated files:")
    print("  - processed_reviews.csv (all processed reviews)")
    print("  - brand_sentiment_trends.csv")
    print("  - item_sentiment_by_brand.csv")
    print("  - attribute_frequency.csv")
    print("  - regional_differences.csv")
    print("  - monthly_trends.csv")
    print("\nVisualizations:")
    print("  - brand_trends.png")
    print("  - item_comparison.png")
    print("  - attribute_heatmap.png")
    print("  - regional_comparison.png")
    
    # Print top insights
    if not insights['brand_sentiment_trends'].empty:
        print("\n📈 Top Brands by Sentiment:")
        top_brands = insights['brand_sentiment_trends'].groupby('brand')['avg_sentiment'].mean().sort_values(ascending=False)
        for i, (brand, sentiment) in enumerate(top_brands.head(5).items(), 1):
            print(f"  {i}. {brand}: {sentiment:.3f}")


if __name__ == "__main__":
    main()

