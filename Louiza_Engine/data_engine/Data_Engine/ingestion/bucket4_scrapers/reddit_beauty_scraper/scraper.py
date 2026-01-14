"""
Reddit Scraper - Crawls old.reddit.com without API.
Handles HTTP requests, rate limiting, and page navigation.
"""
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
import re


class RedditScraper:
    """Scrape old.reddit.com without API."""
    
    def __init__(self, delay_min: float = 0.5, delay_max: float = 1.5):
        """
        Initialize scraper with rate limiting.
        
        Args:
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
        """
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        
        # More realistic browser headers to avoid 403
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        })
        self.base_url = "https://old.reddit.com"
        
        # Visit homepage first to get cookies
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting homepage to get cookies."""
        try:
            # Visit homepage to establish session
            self.session.get(self.base_url, timeout=10)
            time.sleep(1)
        except:
            pass  # Continue even if this fails
    
    def _rate_limit(self):
        """Add random delay between requests."""
        # Reduced delay for JSON API (faster)
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def get_page(self, url: str, retry: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a Reddit page.
        
        Args:
            url: Full URL to fetch
            retry: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        self._rate_limit()
        
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=15, allow_redirects=True)
                
                # Handle different status codes
                if response.status_code == 403:
                    if attempt < retry - 1:
                        print(f"  ⚠️  403 Forbidden, waiting longer (attempt {attempt + 1}/{retry})...")
                        time.sleep(10 + attempt * 5)  # Exponential backoff
                        # Try refreshing session
                        self._initialize_session()
                        continue
                    else:
                        print(f"  ⚠️  403 Forbidden after {retry} attempts. Reddit may be blocking.")
                        return None
                
                if response.status_code == 429:
                    print(f"  ⚠️  Rate limited, waiting longer...")
                    time.sleep(15)
                    continue
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if we got a redirect or error page
                if soup.find('title') and 'error' in soup.find('title').get_text().lower():
                    print(f"  ⚠️  Error page detected")
                    return None
                
                return soup
                
            except requests.exceptions.RequestException as e:
                if attempt < retry - 1:
                    print(f"  ⚠️  Error fetching {url} (attempt {attempt + 1}/{retry}): {e}")
                    time.sleep(5)
                else:
                    print(f"  ⚠️  Error fetching {url} after {retry} attempts: {e}")
                    return None
        
        return None
    
    def scrape_subreddit_page(self, subreddit: str, sort: str = 'new', 
                             time_filter: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Scrape a single page of posts from a subreddit.
        Uses JSON API as fallback if HTML scraping fails.
        
        Args:
            subreddit: Subreddit name (without r/)
            sort: 'new', 'hot', 'top'
            time_filter: For 'top': 'hour', 'day', 'week', 'month', 'year', 'all'
            limit: Max posts to return
            
        Returns:
            List of post dictionaries
        """
        # Try JSON API first (more reliable, less likely to be blocked)
        print(f"    Trying JSON API...")
        json_posts = self._scrape_via_json(subreddit, sort, time_filter, limit)
        if json_posts:
            return json_posts
        
        print(f"    JSON API failed, trying HTML fallback...")
        
        # Fallback to HTML scraping
        if sort == 'top' and time_filter:
            url = f"{self.base_url}/r/{subreddit}/top/?sort=top&t={time_filter}"
        else:
            url = f"{self.base_url}/r/{subreddit}/{sort}/"
        
        soup = self.get_page(url)
        if not soup:
            return []
        
        posts = []
        
        # Find all post entries
        post_entries = soup.find_all('div', {'class': 'thing'})
        
        for entry in post_entries[:limit]:
            try:
                post_data = self._parse_post_entry(entry, subreddit)
                if post_data:
                    posts.append(post_data)
            except Exception as e:
                print(f"  ⚠️  Error parsing post: {e}")
                continue
        
        return posts
    
    def _scrape_via_json(self, subreddit: str, sort: str = 'new', 
                        time_filter: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Scrape using Reddit's JSON API (more reliable, less blocking).
        """
        try:
            # Reddit JSON endpoints
            if sort == 'top' and time_filter:
                json_url = f"https://www.reddit.com/r/{subreddit}/top.json"
                params = {'t': time_filter, 'limit': min(limit, 100)}
            elif sort == 'new':
                json_url = f"https://www.reddit.com/r/{subreddit}/new.json"
                params = {'limit': min(limit, 100)}
            elif sort == 'hot':
                json_url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                params = {'limit': min(limit, 100)}
            else:
                return []
            
            # Use simpler headers for JSON API (Reddit prefers this)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Shorter delay for JSON API
            time.sleep(0.3)  # Minimal delay for JSON endpoints
            response = self.session.get(json_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                for child in data.get('data', {}).get('children', [])[:limit]:
                    post_data_raw = child.get('data', {})
                    
                    post_data = {
                        'subreddit': subreddit,
                        'title': post_data_raw.get('title', ''),
                        'text': post_data_raw.get('selftext', ''),
                        'url': f"https://old.reddit.com{post_data_raw.get('permalink', '')}",
                        'post_id': post_data_raw.get('id', ''),
                        'score': post_data_raw.get('score', 0),
                        'comment_count': post_data_raw.get('num_comments', 0),
                        'timestamp': datetime.fromtimestamp(post_data_raw.get('created_utc', 0)),
                    }
                    posts.append(post_data)
                
                if posts:
                    print(f"    ✓ Got {len(posts)} posts via JSON API")
                return posts
            elif response.status_code == 403:
                print(f"    ⚠️  JSON API returned 403 - Reddit may be blocking")
                # Try with a fresh session
                time.sleep(5)
                return []
            else:
                print(f"    ⚠️  JSON API returned {response.status_code}")
                return []
                
        except Exception as e:
            # If JSON fails, return empty to try HTML
            return []
    
    def _parse_post_entry(self, entry, subreddit: str) -> Optional[Dict[str, Any]]:
        """Parse a single post entry from HTML."""
        try:
            # Title and URL
            title_elem = entry.find('a', class_='title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            post_url = title_elem.get('href', '')
            if post_url.startswith('/'):
                post_url = urljoin(self.base_url, post_url)
            
            # Score
            score_elem = entry.find('div', class_='score')
            score = 0
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                # Handle "•" or "score hidden"
                if score_text and score_text not in ['•', 'score hidden']:
                    try:
                        score = int(score_text.replace(',', ''))
                    except:
                        score = 0
            
            # Comment count
            comments_elem = entry.find('a', class_='comments')
            comment_count = 0
            if comments_elem:
                comment_text = comments_elem.get_text(strip=True)
                # Extract number from "X comments" or "comment"
                match = re.search(r'(\d+)', comment_text)
                if match:
                    comment_count = int(match.group(1))
            
            # Timestamp
            time_elem = entry.find('time')
            timestamp = None
            if time_elem:
                timestamp_str = time_elem.get('datetime', '')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        pass
            
            # Post body (selftext) - need to fetch post page
            post_id = entry.get('data-fullname', '').replace('t3_', '')
            
            post_data = {
                'subreddit': subreddit,
                'title': title,
                'url': post_url,
                'post_id': post_id,
                'score': score,
                'comment_count': comment_count,
                'timestamp': timestamp,
                'text': '',  # Will be filled when fetching post details
            }
            
            return post_data
            
        except Exception as e:
            print(f"  ⚠️  Error parsing post entry: {e}")
            return None
    
    def get_post_details(self, post_url: str) -> Dict[str, Any]:
        """
        Fetch full post details including body text.
        
        Args:
            post_url: Full URL to post
            
        Returns:
            Dictionary with post details
        """
        soup = self.get_page(post_url)
        if not soup:
            return {}
        
        details = {}
        
        # Find post body text
        post_body = soup.find('div', class_='usertext-body')
        if post_body:
            details['text'] = post_body.get_text(strip=True)
        else:
            details['text'] = ''
        
        return details
    
    def get_post_comments(self, post_url: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape comments from a post page.
        
        Args:
            post_url: Full URL to post
            limit: Max top-level comments to return
            
        Returns:
            List of comment dictionaries
        """
        soup = self.get_page(post_url)
        if not soup:
            return []
        
        comments = []
        
        # Find comment entries
        comment_entries = soup.find_all('div', {'class': 'comment'})[:limit]
        
        for entry in comment_entries:
            try:
                comment_data = self._parse_comment_entry(entry)
                if comment_data:
                    comments.append(comment_data)
            except Exception as e:
                continue
        
        return comments
    
    def _parse_comment_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse a single comment entry."""
        try:
            # Comment text
            comment_body = entry.find('div', class_='usertext-body')
            if not comment_body:
                return None
            
            text = comment_body.get_text(strip=True)
            if not text or text == '[deleted]':
                return None
            
            # Score
            score_elem = entry.find('span', class_='score')
            score = 0
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                if score_text and score_text not in ['•', 'score hidden']:
                    try:
                        score = int(score_text.replace(',', ''))
                    except:
                        score = 0
            
            # Timestamp
            time_elem = entry.find('time')
            timestamp = None
            if time_elem:
                timestamp_str = time_elem.get('datetime', '')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        pass
            
            return {
                'text': text,
                'score': score,
                'timestamp': timestamp,
            }
            
        except Exception as e:
            return None
    
    def scrape_subreddit(self, subreddit: str, pages: List[str] = None, 
                        posts_per_page: int = 25) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages from a subreddit.
        
        Args:
            subreddit: Subreddit name
            pages: List of page types, e.g. ['new', 'hot', 'top?t=week']
            posts_per_page: Max posts per page
            
        Returns:
            List of all posts
        """
        if pages is None:
            pages = ['new', 'hot', 'top?t=week', 'top?t=month']
        
        all_posts = []
        seen_urls = set()
        
        print(f"\nScraping r/{subreddit}...")
        
        for page in pages:
            print(f"  Fetching {page}...")
            
            # Parse page type
            if page.startswith('top'):
                # Extract time filter
                if 't=' in page:
                    time_filter = page.split('t=')[1]
                else:
                    time_filter = 'week'
                posts = self.scrape_subreddit_page(subreddit, sort='top', 
                                                  time_filter=time_filter, 
                                                  limit=posts_per_page)
            elif page == 'new':
                posts = self.scrape_subreddit_page(subreddit, sort='new', 
                                                  limit=posts_per_page)
            elif page == 'hot':
                posts = self.scrape_subreddit_page(subreddit, sort='hot', 
                                                  limit=posts_per_page)
            else:
                continue
            
            # Deduplicate and fetch post details (only if text is missing)
            for post in posts:
                if post['url'] not in seen_urls:
                    seen_urls.add(post['url'])
                    
                    # Only fetch post body text if it's missing (JSON API already includes it)
                    if not post.get('text'):
                        details = self.get_post_details(post['url'])
                        post['text'] = details.get('text', '')
                    
                    all_posts.append(post)
            
            print(f"✓ {len(posts)} posts")
        
        print(f"  ✓ Total unique posts: {len(all_posts)}")
        return all_posts

