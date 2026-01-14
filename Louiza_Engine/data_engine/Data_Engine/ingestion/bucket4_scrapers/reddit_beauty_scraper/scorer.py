"""
Trend Scorer - Scores trends based on early signal metrics.
Prioritizes growth velocity, cross-subreddit presence, engagement, sentiment, and novelty.
"""
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class TrendScorer:
    """Score trends for early signal detection."""
    
    def __init__(self):
        """Initialize scorer."""
        pass
    
    def score_trends(self, trends: Dict[str, List[Dict[str, Any]]], 
                    posts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Score all trends using multiple metrics.
        
        Args:
            trends: Dictionary with 'emerging_products', 'emerging_ingredients', etc.
            posts: All posts for cross-subreddit analysis
            
        Returns:
            Scored trends dictionary
        """
        scored_trends = {}
        
        # Build subreddit index
        subreddit_index = defaultdict(list)
        for post in posts:
            subreddit_index[post.get('subreddit', '')].append(post)
        
        # Score each category
        for category, trend_list in trends.items():
            scored = []
            for trend in trend_list:
                score_data = self._score_single_trend(trend, posts, subreddit_index)
                trend['scores'] = score_data
                trend['total_score'] = self._calculate_total_score(score_data)
                scored.append(trend)
            
            # Sort by total score
            scored.sort(key=lambda x: x['total_score'], reverse=True)
            scored_trends[category] = scored
        
        return scored_trends
    
    def _score_single_trend(self, trend: Dict[str, Any], 
                           posts: List[Dict[str, Any]],
                           subreddit_index: Dict[str, List]) -> Dict[str, float]:
        """Score a single trend."""
        entity = trend.get('entity', '')
        category = trend.get('category', '')
        
        scores = {
            'growth_velocity': 0.0,
            'cross_subreddit': 0.0,
            'engagement': 0.0,
            'novelty': 0.0,
            'momentum': 0.0,
        }
        
        # Growth velocity (recent vs baseline)
        growth_rate = trend.get('growth_rate', 0)
        recent_mentions = trend.get('recent_mentions', 0)
        
        # Normalize growth velocity (0-1 scale)
        if growth_rate > 10:
            scores['growth_velocity'] = 1.0
        elif growth_rate > 5:
            scores['growth_velocity'] = 0.8
        elif growth_rate > 2:
            scores['growth_velocity'] = 0.6
        elif growth_rate > 1.5:
            scores['growth_velocity'] = 0.4
        else:
            scores['growth_velocity'] = 0.2
        
        # Cross-subreddit presence
        subreddit_count = 0
        for subreddit, sub_posts in subreddit_index.items():
            for post in sub_posts:
                text = f"{post.get('title', '')} {post.get('text', '')}".lower()
                if entity.lower() in text:
                    subreddit_count += 1
                    break
        
        # Normalize (0-1 scale, max 10 subreddits)
        scores['cross_subreddit'] = min(subreddit_count / 10.0, 1.0)
        
        # Engagement intensity (score + comments)
        avg_score = trend.get('avg_score', 0)
        # Normalize (assume max score ~1000)
        scores['engagement'] = min(avg_score / 1000.0, 1.0)
        
        # Novelty (low historical baseline = high novelty)
        older_mentions = trend.get('older_mentions', 0)
        if older_mentions == 0:
            scores['novelty'] = 1.0
        elif older_mentions <= 2:
            scores['novelty'] = 0.8
        elif older_mentions <= 5:
            scores['novelty'] = 0.5
        else:
            scores['novelty'] = 0.2
        
        # Momentum (combination of growth and volume)
        momentum = trend.get('momentum', 0)
        # Normalize (assume max momentum ~100)
        scores['momentum'] = min(momentum / 100.0, 1.0)
        
        return scores
    
    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted total score.
        Weights favor early signals over raw popularity.
        """
        weights = {
            'growth_velocity': 0.30,  # Most important for early signals
            'novelty': 0.25,           # New trends get higher weight
            'momentum': 0.20,          # Growth momentum
            'cross_subreddit': 0.15,   # Spread across communities
            'engagement': 0.10,        # Less important (can be gamed)
        }
        
        total = sum(scores.get(key, 0) * weight 
                   for key, weight in weights.items())
        
        return total
    
    def rank_trends(self, scored_trends: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Rank trends into categories: accelerating, emerging, plateauing.
        Filters out generic phrases and focuses on meaningful trends.
        """
        ranked = {
            'accelerating': [],
            'emerging': [],
            'plateauing': [],
        }
        
        # Generic phrases to exclude from accelerating trends
        generic_phrases = {
            'my skin', 'my face', 'my', 'skin', 'face', 'worse', 'bad', 'good',
            'help', 'need', 'want', 'like', 'think', 'feel', 'know', 'see',
            'get', 'got', 'have', 'has', 'had', 'was', 'were', 'is', 'are',
            'this', 'that', 'these', 'those', 'it', 'they', 'them', 'you',
            'i', 'me', 'my', 'your', 'his', 'her', 'our', 'their',
            'routine help', 'help thread', 'product product', 'anything goes',
            'december 2025', 'alterdaily help', 'product question', 'current routine',
        }
        
        def is_meaningful_trend(trend: Dict[str, Any]) -> bool:
            """Check if trend is meaningful (not generic phrase)."""
            entity = trend.get('entity', '').lower().strip()
            category = trend.get('category', '')
            
            # Exclude generic phrases
            if entity in generic_phrases:
                return False
            
            # Exclude very short entities
            if len(entity) < 4:
                return False
            
            # For concerns, require actual skincare-related terms
            if category == 'concerns':
                skincare_keywords = [
                    'acne', 'breakout', 'dry', 'oily', 'sensitive', 'irritat', 'red',
                    'texture', 'pore', 'wrinkle', 'spot', 'dark', 'hyperpigment',
                    'rosacea', 'eczema', 'dermatitis', 'rash', 'burn', 'sting',
                    'peel', 'flake', 'product', 'routine', 'ingredient', 'serum',
                    'cream', 'moisturizer', 'cleanser', 'toner', 'sunscreen',
                ]
                if not any(kw in entity for kw in skincare_keywords):
                    return False
            
            # Exclude phrases starting with pronouns/articles
            if entity.startswith(('my ', 'your ', 'his ', 'her ', 'our ', 'their ', 'the ', 'a ', 'an ', 'i ', 'you ')):
                return False
            
            return True
        
        # Prioritize meaningful categories (products, ingredients, routines over concerns)
        category_priority = {
            'products': 3,
            'ingredients': 3,
            'routines': 2,
            'concerns': 1,  # Lower priority - only include if very specific
        }
        
        for category, trends in scored_trends.items():
            priority = category_priority.get(category, 1)
            
            for trend in trends[:10]:  # Top 10 per category
                # Skip generic phrases
                if not is_meaningful_trend(trend):
                    continue
                
                total_score = trend.get('total_score', 0)
                growth_rate = trend.get('growth_rate', 0)
                recent_mentions = trend.get('recent_mentions', 0)
                
                # Higher threshold for concerns to filter out generic phrases
                if category == 'concerns':
                    min_growth = 5.0  # Higher threshold
                    min_mentions = 7   # More mentions required
                else:
                    min_growth = 3.0
                    min_mentions = 5
                
                if growth_rate > min_growth and recent_mentions >= min_mentions:
                    # Boost score for higher priority categories
                    trend['boosted_score'] = total_score * priority
                    ranked['accelerating'].append(trend)
                elif growth_rate > 1.5 and recent_mentions >= 3:
                    ranked['emerging'].append(trend)
                elif growth_rate < 1.2 and recent_mentions >= 10:
                    ranked['plateauing'].append(trend)
        
        # Sort each category - use boosted_score if available, otherwise total_score
        ranked['accelerating'].sort(key=lambda x: x.get('boosted_score', x.get('total_score', 0)), reverse=True)
        ranked['emerging'].sort(key=lambda x: x['total_score'], reverse=True)
        ranked['plateauing'].sort(key=lambda x: x['total_score'], reverse=True)
        
        return ranked

