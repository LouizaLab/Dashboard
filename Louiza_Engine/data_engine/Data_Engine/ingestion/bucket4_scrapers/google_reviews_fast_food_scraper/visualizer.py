"""
Visualizer - Generate graphs and charts
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
    # Set style
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except:
        try:
            plt.style.use('seaborn-darkgrid')
        except:
            pass
    sns.set_palette("husl")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    sns = None


class ReviewVisualizer:
    """Generate visualizations for review analysis."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_brand_trends(self, trends_df: pd.DataFrame, filename: str = "brand_trends.png"):
        """
        Plot sentiment trends by brand over time.
        
        Args:
            trends_df: DataFrame from brand_sentiment_trends()
            filename: Output filename
        """
        if not MATPLOTLIB_AVAILABLE:
            print("  ⚠️  matplotlib not installed. Skipping visualization.")
            print("     Install with: pip install matplotlib seaborn")
            return
        
        if trends_df.empty:
            print("  ⚠️  No trend data to plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if 'date' in trends_df.columns:
            for brand in trends_df['brand'].unique():
                brand_data = trends_df[trends_df['brand'] == brand]
                ax.plot(brand_data['date'], brand_data['avg_sentiment'], 
                       marker='o', label=brand, linewidth=2)
        else:
            # Bar chart if no dates
            ax.bar(trends_df['brand'], trends_df['avg_sentiment'], alpha=0.7)
        
        ax.set_xlabel('Date' if 'date' in trends_df.columns else 'Brand', fontsize=12)
        ax.set_ylabel('Average Sentiment', fontsize=12)
        ax.set_title('Brand Sentiment Trends Over Time', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
    
    def plot_item_comparison(self, item_df: pd.DataFrame, filename: str = "item_comparison.png"):
        """
        Plot sentiment comparison by food item across brands.
        
        Args:
            item_df: DataFrame from item_sentiment_by_brand()
            filename: Output filename
        """
        if not MATPLOTLIB_AVAILABLE:
            return
        
        if item_df.empty:
            print("  ⚠️  No item data to plot")
            return
        
        # Get top items by mention count
        top_items = item_df.nlargest(10, 'mention_count')['food_item'].unique()
        plot_data = item_df[item_df['food_item'].isin(top_items)]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        pivot = plot_data.pivot_table(
            index='food_item',
            columns='brand',
            values='avg_sentiment',
            aggfunc='mean'
        )
        
        pivot.plot(kind='barh', ax=ax, width=0.8)
        
        ax.set_xlabel('Average Sentiment', fontsize=12)
        ax.set_ylabel('Food Item', fontsize=12)
        ax.set_title('Food Item Sentiment by Brand', fontsize=14, fontweight='bold')
        ax.legend(title='Brand', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
    
    def plot_attribute_heatmap(self, attr_df: pd.DataFrame, filename: str = "attribute_heatmap.png"):
        """
        Plot attribute frequency heatmap.
        
        Args:
            attr_df: DataFrame from attribute_frequency()
            filename: Output filename
        """
        if not MATPLOTLIB_AVAILABLE:
            return
        
        if attr_df.empty:
            print("  ⚠️  No attribute data to plot")
            return
        
        # Create pivot table
        pivot = attr_df.pivot_table(
            index='attribute',
            columns='brand',
            values='frequency',
            aggfunc='sum',
            fill_value=0
        )
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(pivot) * 0.5)))
        
        sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Frequency'})
        
        ax.set_xlabel('Brand', fontsize=12)
        ax.set_ylabel('Attribute', fontsize=12)
        ax.set_title('Attribute Frequency Heatmap', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
    
    def plot_regional_comparison(self, regional_df: pd.DataFrame, filename: str = "regional_comparison.png"):
        """
        Plot regional sentiment differences.
        
        Args:
            regional_df: DataFrame from regional_differences()
            filename: Output filename
        """
        if not MATPLOTLIB_AVAILABLE:
            return
        
        if regional_df.empty:
            print("  ⚠️  No regional data to plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        pivot = regional_df.pivot_table(
            index='city',
            columns='brand',
            values='avg_sentiment',
            aggfunc='mean'
        )
        
        pivot.plot(kind='bar', ax=ax, width=0.8)
        
        ax.set_xlabel('City', fontsize=12)
        ax.set_ylabel('Average Sentiment', fontsize=12)
        ax.set_title('Regional Sentiment Differences', fontsize=14, fontweight='bold')
        ax.legend(title='Brand', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
    
    def generate_all_plots(self, insights: Dict[str, pd.DataFrame]):
        """
        Generate all visualizations.
        
        Args:
            insights: Dictionary of insight DataFrames
        """
        print("\n[6/6] Generating visualizations...")
        print("-" * 70)
        
        self.plot_brand_trends(insights.get('brand_sentiment_trends', pd.DataFrame()))
        self.plot_item_comparison(insights.get('item_sentiment_by_brand', pd.DataFrame()))
        self.plot_attribute_heatmap(insights.get('attribute_frequency', pd.DataFrame()))
        self.plot_regional_comparison(insights.get('regional_differences', pd.DataFrame()))

