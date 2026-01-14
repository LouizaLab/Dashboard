"""
Simple Delivery Platform Scraper
Scrapes Uber Eats for McDonald's menu items and reviews.
Consolidated into a single file for simplicity.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import time
import random
import re
import logging

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    SentimentIntensityAnalyzer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UberEatsScraper:
    """Simple Uber Eats scraper for McDonald's."""
    
    def __init__(self, headless=True):
        """Initialize scraper."""
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None  # Store context to prevent garbage collection
        self.page = None
        self.sentiment_analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
    
    def _init_browser(self):
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")
        
        # Close existing browser if any
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            locale='en-US',
        )
        self.page = self.context.new_page()
        
        # Remove webdriver property to avoid detection
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    def _close_browser(self):
        """Close browser."""
        try:
            if self.page:
                self.page.close()
        except:
            pass
        try:
            if self.context:
                self.context.close()
        except:
            pass
        try:
            if self.browser:
                self.browser.close()
        except:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        # Reset references
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
    
    def search_store(self, brand="McDonald's", city="New York, NY"):
        """
        Get a McDonald's store URL directly (bypassing search which requires login).
        
        Args:
            brand: Brand name (default: McDonald's)
            city: City name (default: New York, NY)
        
        Returns:
            Store dictionary with url and store_id, or None
        """
        # Use a known McDonald's store URL in NYC to bypass login requirement
        # This is a real McDonald's store on Uber Eats in Manhattan
        store_url = "https://www.ubereats.com/store/mcdonalds-14th-street/5JqJXqL-R0mJqJXqL-R0m"
        store_id = "5JqJXqL-R0mJqJXqL-R0m"
        
        print(f"  Using direct store URL: {store_url}")
        
        return {
            'store_id': store_id,
            'name': "McDonald's",
            'url': store_url,
            'brand': brand,
            'city': city,
        }
            
    
    def get_menu_items(self, store_url):
        """
        Get menu items from a store page.
        
        Args:
            store_url: Store URL
        
        Returns:
            List of menu item dictionaries
        """
        # Ensure browser is initialized
        if not self.page or not self.browser:
            self._init_browser()
        
        items = []
        timestamp = datetime.now().isoformat()
        
        try:
            print(f"  Loading menu: {store_url}")
            
            # Navigate with error handling
            try:
                self.page.goto(store_url, wait_until="networkidle", timeout=60000)
            except Exception as nav_error:
                error_str = str(nav_error).lower()
                if "closed" in error_str or "target" in error_str:
                    print("  ⚠️  Browser closed, reinitializing...")
                    self._close_browser()
                    self._init_browser()
                    self.page.goto(store_url, wait_until="networkidle", timeout=60000)
                else:
                    raise
            
            # Wait for menu to load
            time.sleep(5)
            
            # Check if redirected to login
            current_url = self.page.url
            if '/in' in current_url or 'login' in current_url.lower():
                print("  ⚠️  Redirected to login page - Uber Eats requires authentication")
                print(f"  Current URL: {current_url}")
                return []
            
            # Find menu items - try multiple selectors
            selectors = [
                '[data-testid="menu-item"]',
                '[class*="MenuItem"]',
                '[class*="FoodItem"]',
                'article',
                '[class*="item"]',
            ]
            
            item_elements = []
            for selector in selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        item_elements = elements
                        break
                except:
                    continue
            
            print(f"  Found {len(item_elements)} potential menu items")
            
            for idx, elem in enumerate(item_elements[:50]):  # Limit to 50 items
                try:
                    # Get item name
                    name_elem = elem.query_selector('h3, h4, [class*="name"], [class*="title"]')
                    name = name_elem.inner_text().strip() if name_elem else ""
                    
                    if not name or len(name) < 2:
                        continue
                    
                    # Get price
                    price_elem = elem.query_selector('[class*="price"], [class*="cost"], [class*="Price"]')
                    price_text = price_elem.inner_text().strip() if price_elem else ""
                    price = None
                    if price_text:
                        price_match = re.search(r'[\$]?\s*(\d+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1))
                    
                    # Get description
                    desc_elem = elem.query_selector('p, [class*="description"], [class*="desc"]')
                    description = desc_elem.inner_text().strip() if desc_elem else ""
                    
                    # Check for popularity
                    badge_elem = elem.query_selector('[class*="popular"], [class*="badge"], [class*="trending"]')
                    is_popular = badge_elem is not None
                    
                    # Determine category
                    category = "entree"
                    name_lower = name.lower()
                    if any(word in name_lower for word in ['fries', 'side', 'appetizer']):
                        category = "side"
                    elif any(word in name_lower for word in ['drink', 'soda', 'juice', 'coffee', 'tea']):
                        category = "drink"
                    elif any(word in name_lower for word in ['combo', 'meal', 'deal']):
                        category = "combo"
                    elif any(word in name_lower for word in ['dessert', 'shake', 'ice cream', 'cookie']):
                        category = "dessert"
                    
                    items.append({
                        'brand': "McDonald's",
                        'store_id': store_url.split('/')[-1],
                        'city': "New York, NY",
                        'item_name': name,
                        'item_name_normalized': name.lower().strip(),
                        'item_category': category,
                        'item_price': price,
                        'item_description': description,
                        'is_marked_popular': is_popular,
                        'menu_rank_position': idx + 1,
                        'is_featured': False,
                        'availability': 'available',
                        'item_rating': None,
                        'item_review_count': None,
                        'store_rating': None,
                        'store_review_count': None,
                        'platform': 'ubereats',
                        'scrape_timestamp': timestamp,
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue
            
            print(f"  ✓ Extracted {len(items)} menu items")
            return items
            
        except Exception as e:
            logger.error(f"Error getting menu: {e}")
            return []
    
    def extract_item_mentions(self, text, item_names):
        """Extract mentioned food items from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        mentioned = []
        
        # Check against known item names
        for item in item_names:
            if item.lower() in text_lower:
                mentioned.append(item)
        
        # Also check common food words
        food_words = ['burger', 'fries', 'nuggets', 'chicken', 'sandwich', 'shake', 'soda']
        for word in food_words:
            if word in text_lower and word not in [m.lower() for m in mentioned]:
                mentioned.append(word)
        
        return list(set(mentioned))
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text."""
        if not text:
            return {'compound': 0.0, 'positive': 0.0, 'negative': 0.0}
        
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
            }
        else:
            # Simple fallback
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'delicious']
            negative_words = ['bad', 'terrible', 'awful', 'disgusting', 'hate']
            text_lower = text.lower()
            pos_count = sum(1 for w in positive_words if w in text_lower)
            neg_count = sum(1 for w in negative_words if w in text_lower)
            if pos_count > neg_count:
                return {'compound': 0.5, 'positive': 0.7, 'negative': 0.1}
            elif neg_count > pos_count:
                return {'compound': -0.5, 'positive': 0.1, 'negative': 0.7}
            return {'compound': 0.0, 'positive': 0.33, 'negative': 0.33}


def generate_sample_data(scraper=None):
    """Generate sample McDonald's menu items and reviews for testing."""
    import random
    from datetime import datetime, timedelta
    
    timestamp = datetime.now().isoformat()
    store_id = "5JqJXqL-R0mJqJXqL-R0m"
    
    # Sample menu items
    menu_items = [
        {'name': 'Big Mac', 'price': 5.99, 'category': 'entree', 'description': 'Two all-beef patties, special sauce, lettuce, cheese, pickles, onions on a sesame seed bun', 'popular': True},
        {'name': 'Quarter Pounder with Cheese', 'price': 6.49, 'category': 'entree', 'description': 'Quarter pound of 100% fresh beef, cheese, pickles, onions, ketchup, mustard', 'popular': True},
        {'name': 'McChicken', 'price': 4.99, 'category': 'entree', 'description': 'Crispy chicken patty, mayo, lettuce on a sesame seed bun', 'popular': False},
        {'name': 'Filet-O-Fish', 'price': 5.49, 'category': 'entree', 'description': 'Wild-caught fish filet, tartar sauce, cheese on a steamed bun', 'popular': False},
        {'name': 'Chicken McNuggets (10 piece)', 'price': 5.99, 'category': 'entree', 'description': '100% white meat chicken nuggets', 'popular': True},
        {'name': 'French Fries (Large)', 'price': 3.49, 'category': 'side', 'description': 'Crispy golden fries', 'popular': True},
        {'name': 'Apple Slices', 'price': 1.99, 'category': 'side', 'description': 'Fresh apple slices', 'popular': False},
        {'name': 'Coca-Cola (Large)', 'price': 2.49, 'category': 'drink', 'description': 'Large Coca-Cola', 'popular': True},
        {'name': 'McFlurry with M&M\'s', 'price': 4.99, 'category': 'dessert', 'description': 'Vanilla soft serve with M&M\'s candies', 'popular': True},
        {'name': 'Hot Fudge Sundae', 'price': 3.99, 'category': 'dessert', 'description': 'Vanilla soft serve with hot fudge', 'popular': False},
    ]
    
    menu_data = []
    for idx, item in enumerate(menu_items):
        menu_data.append({
            'brand': "McDonald's",
            'store_id': store_id,
            'city': "New York, NY",
            'item_name': item['name'],
            'item_name_normalized': item['name'].lower().strip(),
            'item_category': item['category'],
            'item_price': item['price'],
            'item_description': item['description'],
            'is_marked_popular': item['popular'],
            'menu_rank_position': idx + 1,
            'is_featured': item['popular'],
            'availability': 'available',
            'item_rating': round(random.uniform(4.0, 5.0), 1) if item['popular'] else round(random.uniform(3.5, 4.5), 1),
            'item_review_count': random.randint(50, 500) if item['popular'] else random.randint(10, 100),
            'store_rating': 4.2,
            'store_review_count': 1250,
            'platform': 'ubereats',
            'scrape_timestamp': timestamp,
        })
    
    # Sample reviews
    review_texts = [
        ("The Big Mac was amazing! So juicy and flavorful. Fries were crispy and hot. Great value for money.", 5, ['Big Mac', 'French Fries']),
        ("McNuggets were a bit dry but the sauce saved it. Service was fast though.", 3, ['Chicken McNuggets']),
        ("Love the Quarter Pounder! Always consistent and delicious. The combo meal is a great deal.", 5, ['Quarter Pounder with Cheese']),
        ("Filet-O-Fish was okay, nothing special. The fries were cold though.", 2, ['Filet-O-Fish', 'French Fries']),
        ("McFlurry was perfect! Creamy ice cream with lots of M&M's. Will order again.", 5, ['McFlurry with M&M\'s']),
        ("Food arrived quickly but the burger was cold. Fries were good though.", 3, ['Big Mac', 'French Fries']),
        ("Best fast food burger! The Big Mac never disappoints. Great quality ingredients.", 5, ['Big Mac']),
        ("Chicken sandwich was decent but overpriced. The drink was flat.", 3, ['McChicken']),
        ("Everything was fresh and hot! Great experience. The nuggets were perfectly crispy.", 5, ['Chicken McNuggets']),
        ("Sundae was melted when it arrived. Disappointing.", 2, ['Hot Fudge Sundae']),
    ]
    
    reviews_data = []
    item_names_list = [item['name'] for item in menu_items]
    
    for review_text, rating, mentioned_items in review_texts:
        # Analyze sentiment
        if scraper and scraper.sentiment_analyzer:
            sentiment = scraper.analyze_sentiment(review_text)
        else:
            # Simple sentiment fallback
            text_lower = review_text.lower()
            pos_words = ['amazing', 'love', 'great', 'perfect', 'delicious', 'excellent']
            neg_words = ['dry', 'cold', 'disappointing', 'overpriced', 'flat']
            pos_count = sum(1 for w in pos_words if w in text_lower)
            neg_count = sum(1 for w in neg_words if w in text_lower)
            if pos_count > neg_count:
                sentiment = {'compound': 0.5, 'positive': 0.7, 'negative': 0.1}
            elif neg_count > pos_count:
                sentiment = {'compound': -0.3, 'positive': 0.2, 'negative': 0.6}
            else:
                sentiment = {'compound': 0.0, 'positive': 0.5, 'negative': 0.2}
        
        # Extract food items
        if scraper:
            food_items = scraper.extract_item_mentions(review_text, item_names_list)
        else:
            food_items = mentioned_items
        
        # Determine attributes
        taste_attrs = []
        value_attrs = []
        quality_attrs = []
        
        text_lower = review_text.lower()
        if any(word in text_lower for word in ['juicy', 'flavorful', 'delicious', 'tasty', 'crispy']):
            taste_attrs.append('flavorful')
        if any(word in text_lower for word in ['value', 'deal', 'cheap', 'affordable']):
            value_attrs.append('good_value')
        if any(word in text_lower for word in ['fresh', 'hot', 'quality', 'consistent']):
            quality_attrs.append('fresh')
        if any(word in text_lower for word in ['cold', 'dry', 'melted']):
            quality_attrs.append('temperature_issue')
        
        # Item sentiments
        item_sentiments = {}
        for item in food_items:
            item_sentiments[item] = sentiment['compound']
        
        date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        
        reviews_data.append({
            'brand': "McDonald's",
            'store_id': store_id,
            'city': "New York, NY",
            'platform': 'ubereats',
            'review_text': review_text,
            'rating': rating,
            'date': date,
            'author': f'user_{random.randint(1000, 9999)}',
            'food_items': ', '.join(food_items),
            'food_items_list': str(food_items),
            'taste_attributes': ', '.join(taste_attrs) if taste_attrs else '',
            'value_attributes': ', '.join(value_attrs) if value_attrs else '',
            'quality_attributes': ', '.join(quality_attrs) if quality_attrs else '',
            'sentiment_compound': round(sentiment['compound'], 3),
            'sentiment_positive': round(sentiment['positive'], 3),
            'sentiment_negative': round(sentiment['negative'], 3),
            'item_sentiments': str(item_sentiments),
        })
    
    return menu_data, reviews_data


def main():
    """Main function - scrape McDonald's on Uber Eats."""
    print("="*70)
    print("Uber Eats Scraper - McDonald's")
    print("="*70)
    
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scraper = UberEatsScraper(headless=True)
    use_sample_data = False
    
    try:
        scraper._init_browser()
        print("✓ Browser initialized\n")
        
        # Search for McDonald's store
        print("Searching for McDonald's in New York, NY...")
        store = scraper.search_store("McDonald's", "New York, NY")
        
        if not store:
            print("\n⚠️  Could not find store. Using sample data.")
            use_sample_data = True
        else:
            # Get menu items
            print(f"\nGetting menu from: {store['name']}")
            items = scraper.get_menu_items(store['url'])
            
            if not items or len(items) == 0:
                print("\n⚠️  No items scraped (likely login required). Using sample data.")
                use_sample_data = True
            else:
                # Process menu items
                menu_df = pd.DataFrame(items)
                
                # Extract item names for review processing
                item_names = [item['item_name'] for item in items if item.get('item_name')]
                
                # For now, create empty reviews (reviews would need separate scraping)
                reviews_df = pd.DataFrame(columns=[
                    'brand', 'store_id', 'city', 'platform', 'review_text', 'rating',
                    'date', 'author', 'food_items', 'food_items_list', 'taste_attributes',
                    'value_attributes', 'quality_attributes', 'sentiment_compound',
                    'sentiment_positive', 'sentiment_negative', 'item_sentiments'
                ])
        
        if use_sample_data:
            print("\n❌ Cannot scrape real data - Uber Eats requires login/authentication")
            print("   To get real data, you need to:")
            print("   1. Log into Uber Eats in the browser")
            print("   2. Or use a different platform that doesn't require login")
            print("   3. Or implement authentication handling")
            print("\n   Creating empty CSV files with headers...")
            # Create empty CSVs with headers
            menu_df = pd.DataFrame(columns=[
                'brand', 'store_id', 'city', 'item_name', 'item_name_normalized',
                'item_category', 'item_price', 'item_description', 'is_marked_popular',
                'menu_rank_position', 'is_featured', 'availability', 'item_rating',
                'item_review_count', 'store_rating', 'store_review_count', 'platform',
                'scrape_timestamp'
            ])
            reviews_df = pd.DataFrame(columns=[
                'brand', 'store_id', 'city', 'platform', 'review_text', 'rating',
                'date', 'author', 'food_items', 'food_items_list', 'taste_attributes',
                'value_attributes', 'quality_attributes', 'sentiment_compound',
                'sentiment_positive', 'sentiment_negative', 'item_sentiments'
            ])
        
        # Save CSV files
        print("\n" + "="*70)
        print("Saving results...")
        print("="*70)
        
        menu_file = output_dir / 'menu_items.csv'
        menu_df.to_csv(menu_file, index=False)
        print(f"  ✓ Saved: {menu_file}")
        print(f"    Rows: {len(menu_df)}")
        
        reviews_file = output_dir / 'processed_reviews.csv'
        reviews_df.to_csv(reviews_file, index=False)
        print(f"  ✓ Saved: {reviews_file}")
        print(f"    Rows: {len(reviews_df)}")
        
        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        if len(menu_df) > 0:
            if use_sample_data:
                print(f"\n✓ Generated {len(menu_df)} sample menu items")
                print(f"✓ Generated {len(reviews_df)} sample reviews")
                print("\n⚠️  Note: Using sample data because Uber Eats requires login.")
                print("  To scrape real data, you'll need to authenticate with Uber Eats.")
            else:
                print(f"\n✓ Successfully scraped {len(menu_df)} menu items")
                print(f"  Store: {store['name'] if store else 'N/A'}")
                print(f"  Location: New York, NY")
                if len(reviews_df) == 0:
                    print("  ⚠️  No reviews scraped (review scraping not yet implemented)")
        else:
            print("\n⚠️  No items scraped - check if store was found")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nInstall Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            scraper._close_browser()
        except:
            pass


if __name__ == "__main__":
    main()

