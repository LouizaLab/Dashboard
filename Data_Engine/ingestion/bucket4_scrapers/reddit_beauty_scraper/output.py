"""
Output Generator - Exports trends to CSV, JSON, and Markdown.
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class OutputGenerator:
    """Generate output files for trend analysis."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize output generator.
        
        Args:
            output_dir: Directory to save output files (defaults to current directory)
        """
        if output_dir is None:
            # Save in the reddit_scraper folder
            self.output_dir = Path(__file__).parent
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, data: Dict[str, Any], filename: str):
        """Save data as JSON."""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        print(f"  ✓ Saved JSON: {filepath}")
    
    def save_csv(self, trends: Dict[str, List[Dict[str, Any]]], filename: str):
        """Save trends as CSV."""
        filepath = self.output_dir / filename
        
        # Flatten trends into rows
        rows = []
        for category, trend_list in trends.items():
            for trend in trend_list:
                row = {
                    'category': category,
                    'entity': trend.get('entity', ''),
                    'recent_mentions': trend.get('recent_mentions', 0),
                    'growth_rate': trend.get('growth_rate', 0),
                    'momentum': trend.get('momentum', 0),
                    'total_score': trend.get('total_score', 0),
                    'avg_score': trend.get('avg_score', 0),
                    'quotes': ' | '.join(trend.get('quotes', [])[:2]),
                }
                rows.append(row)
        
        if rows:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            print(f"  ✓ Saved CSV: {filepath}")
    
    def save_processed_posts_csv(self, posts: List[Dict[str, Any]], filename: str = "processed_posts.csv"):
        """Save processed posts as CSV."""
        filepath = self.output_dir / filename
        
        if not HAS_PANDAS:
            # Fallback to manual CSV writing if pandas not available
            if posts:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['title', 'text', 'subreddit', 'score', 'comment_count', 'timestamp', 'url', 'post_id']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for post in posts:
                        writer.writerow({
                            'title': post.get('title', ''),
                            'text': post.get('text', ''),
                            'subreddit': post.get('subreddit', ''),
                            'score': post.get('score', 0),
                            'comment_count': post.get('comment_count', 0),
                            'timestamp': post.get('timestamp'),
                            'url': post.get('url', ''),
                            'post_id': post.get('post_id', ''),
                        })
                print(f"  ✓ Saved CSV: {filepath}")
            return
        
        # Convert posts to DataFrame
        df_data = []
        for post in posts:
            df_data.append({
                'title': post.get('title', ''),
                'text': post.get('text', ''),
                'subreddit': post.get('subreddit', ''),
                'score': post.get('score', 0),
                'comment_count': post.get('comment_count', 0),
                'timestamp': post.get('timestamp'),
                'url': post.get('url', ''),
                'post_id': post.get('post_id', ''),
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            df.to_csv(filepath, index=False)
            print(f"  ✓ Saved CSV: {filepath}")
    
    def save_markdown_summary(self, trends: Dict[str, Any], 
                            ranked: Dict[str, List[Dict[str, Any]]],
                            language_shifts: Dict[str, Any],
                            pain_clusters: List[Dict[str, Any]]):
        """Generate Markdown summary report."""
        filepath = self.output_dir / "trend_summary.md"
        
        lines = []
        lines.append("# Reddit Beauty Trends Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        # Accelerating Trends
        lines.append("## 🚀 Accelerating Trends")
        lines.append("\nTrends with rapid growth (>3x) and high momentum:\n")
        for i, trend in enumerate(ranked.get('accelerating', [])[:10], 1):
            lines.append(f"{i}. **{trend['entity']}** ({trend['category']})")
            lines.append(f"   - Growth: {trend['growth_rate']:.1f}x")
            lines.append(f"   - Score: {trend['total_score']:.2f}")
            lines.append(f"   - Recent mentions: {trend['recent_mentions']}")
            if trend.get('quotes'):
                lines.append(f"   - Quote: \"{trend['quotes'][0][:100]}...\"")
            lines.append("")
        
        # Emerging Products
        lines.append("## 💎 Emerging Products")
        lines.append("\nProducts with low baseline but growing mentions:\n")
        for i, product in enumerate(trends.get('emerging_products', [])[:10], 1):
            lines.append(f"{i}. **{product['entity']}**")
            lines.append(f"   - Growth: {product['growth_rate']:.1f}x")
            lines.append(f"   - Momentum: {product['momentum']:.1f}")
            lines.append("")
        
        # Emerging Ingredients
        lines.append("## 🧪 Emerging Ingredients")
        lines.append("\nIngredients showing rapid growth:\n")
        for i, ingredient in enumerate(trends.get('emerging_ingredients', [])[:10], 1):
            lines.append(f"{i}. **{ingredient['entity']}**")
            lines.append(f"   - Growth: {ingredient['growth_rate']:.1f}x")
            lines.append(f"   - Recent mentions: {ingredient['recent_mentions']}")
            lines.append("")
        
        # Pain Points
        lines.append("## 😟 Pain Points & Unmet Needs")
        lines.append("\nRepeated consumer frustrations:\n")
        for i, pain in enumerate(pain_clusters[:10], 1):
            lines.append(f"{i}. **{pain['theme']}**")
            lines.append(f"   - Mentions: {pain['mention_count']}")
            lines.append(f"   - Avg score: {pain['avg_score']:.1f}")
            lines.append("")
        
        # Language Shifts
        lines.append("## 📝 Language Shifts")
        lines.append("\nNew or rapidly growing phrases:\n")
        for i, shift in enumerate(language_shifts.get('shifts', [])[:10], 1):
            lines.append(f"{i}. **{shift['phrase']}**")
            lines.append(f"   - Type: {shift['type']}")
            lines.append(f"   - Growth: {shift['growth_rate']:.1f}x")
            lines.append("")
        
        # Write file
        content = "\n".join(lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Saved Markdown: {filepath}")

