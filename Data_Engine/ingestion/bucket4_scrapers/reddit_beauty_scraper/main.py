"""
Main script for Reddit beauty trends scraper.
Scrapes old.reddit.com to identify emerging trends without API.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper import RedditScraper
from trend_extractor import TrendExtractor
from scorer import TrendScorer
from output import OutputGenerator


def main():
    """Main execution function."""
    print("=" * 70)
    print("Reddit Beauty Trends Scraper (old.reddit.com)")
    print("=" * 70)
    print("\nFocus: Early trend signals, not raw popularity")
    print("=" * 70)
    
    # Configuration - optimized for speed (only 2 subreddits)
    subreddits = [
        'SkincareAddiction',  # Main skincare community
        'AsianBeauty',        # Popular for emerging trends
    ]
    
    # Reduced pages for faster scraping - only 1 page per subreddit
    pages_per_subreddit = ['hot']  # Only scrape hot page (most relevant for trends)
    posts_per_page = 20  # Reduced from 25
    
    # Initialize components (optimized for speed)
    scraper = RedditScraper(delay_min=0.5, delay_max=1.5)
    extractor = TrendExtractor()
    scorer = TrendScorer()
    output_gen = OutputGenerator()
    
    # Scrape all subreddits
    print("\n[1/5] Scraping subreddits...")
    print("-" * 70)
    
    all_posts = []
    all_comments = []
    
    for subreddit in subreddits:
        try:
            posts = scraper.scrape_subreddit(
                subreddit, 
                pages=pages_per_subreddit,
                posts_per_page=posts_per_page
            )
            
            # Skip comment fetching for speed - posts contain enough data for trend detection
            # Uncomment below if you need comments (slower):
            # for post in posts[:3]:  # Sample 3 posts per subreddit
            #     comments = scraper.get_post_comments(post['url'], limit=5)
            #     for comment in comments:
            #         comment['subreddit'] = subreddit
            #         comment['post_url'] = post['url']
            #     all_comments.extend(comments)
            
            all_posts.extend(posts)
            
        except Exception as e:
            print(f"  ⚠️  Error scraping r/{subreddit}: {e}")
            continue
    
    print(f"\n✓ Total posts scraped: {len(all_posts)}")
    print(f"✓ Total comments scraped: {len(all_comments)}")
    
    # Save raw data and processed posts
    print("\n[2/5] Saving raw data...")
    output_gen.save_json(
        {
            'posts': [{**p, 'timestamp': p['timestamp'].isoformat() if p.get('timestamp') else None} 
                     for p in all_posts],
            'comments': [{**c, 'timestamp': c['timestamp'].isoformat() if c.get('timestamp') else None}
                        for c in all_comments],
        },
        'raw_data.json'
    )
    
    # Save processed posts as CSV
    output_gen.save_processed_posts_csv(all_posts, 'processed_posts.csv')
    
    # Extract trends
    print("\n[3/5] Extracting trends...")
    print("-" * 70)
    
    trends = extractor.detect_emerging_trends(all_posts, all_comments)
    language_shifts = extractor.detect_language_shifts(all_posts)
    pain_clusters = extractor.cluster_pain_points(all_posts)
    
    print(f"  ✓ Found {len(trends.get('emerging_products', []))} emerging products")
    print(f"  ✓ Found {len(trends.get('emerging_ingredients', []))} emerging ingredients")
    print(f"  ✓ Found {len(trends.get('emerging_routines', []))} emerging routines")
    print(f"  ✓ Found {len(pain_clusters)} pain point clusters")
    
    # Score trends
    print("\n[4/5] Scoring trends...")
    print("-" * 70)
    
    scored_trends = scorer.score_trends(trends, all_posts)
    ranked = scorer.rank_trends(scored_trends)
    
    print(f"  ✓ Accelerating trends: {len(ranked['accelerating'])}")
    print(f"  ✓ Emerging trends: {len(ranked['emerging'])}")
    print(f"  ✓ Plateauing trends: {len(ranked['plateauing'])}")
    
    # Generate outputs
    print("\n[5/5] Generating outputs...")
    print("-" * 70)
    
    # JSON output
    output_data = {
        'summary': {
            'total_posts': len(all_posts),
            'total_comments': len(all_comments),
            'subreddits': subreddits,
            'generated_at': datetime.now().isoformat(),
        },
        'trends': scored_trends,
        'ranked_trends': ranked,
        'language_shifts': language_shifts,
        'pain_points': pain_clusters,
    }
    
    output_gen.save_json(output_data, 'trends_analysis.json')
    
    # CSV output
    output_gen.save_csv(scored_trends, 'trends.csv')
    
    # Markdown summary
    output_gen.save_markdown_summary(scored_trends, ranked, language_shifts, pain_clusters)
    
    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nTop 5 Accelerating Trends:")
    for i, trend in enumerate(ranked['accelerating'][:5], 1):
        print(f"  {i}. {trend['entity']} ({trend['category']}) - "
              f"{trend['growth_rate']:.1f}x growth, score: {trend['total_score']:.2f}")
    
    print(f"\n📁 Results saved to: {output_gen.output_dir}/")
    print("   - processed_posts.csv (all processed posts)")
    print("   - trends_analysis.json (full data)")
    print("   - trends.csv (spreadsheet)")
    print("   - trend_summary.md (readable report)")
    print("   - raw_data.json (all scraped posts/comments)")


if __name__ == "__main__":
    main()

