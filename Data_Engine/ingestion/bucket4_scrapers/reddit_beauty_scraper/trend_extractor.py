"""
Trend Extractor - Identifies emerging trends, products, ingredients, and pain points.
Focuses on early signals, not raw popularity.
"""
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json


class TrendExtractor:
    """Extract trends from Reddit posts and comments."""
    
    def __init__(self):
        """Initialize trend extractor."""
        # Common beauty brands (for reference, but we'll extract dynamically)
        self.common_brands = {
            'cerave', 'cetaphil', 'la roche-posay', 'the ordinary', 
            'paula\'s choice', 'glossier', 'fenty', 'rare beauty',
            'tatcha', 'drunk elephant', 'kiehl\'s', 'clinique',
            'estee lauder', 'l\'oreal', 'maybelline', 'neutrogena',
        }
        
        # Common ingredients (for reference)
        self.common_ingredients = {
            'retinol', 'retinoid', 'tretinoin', 'niacinamide',
            'hyaluronic acid', 'vitamin c', 'ascorbic acid',
            'salicylic acid', 'aha', 'bha', 'glycolic acid',
            'lactic acid', 'azelaic acid', 'peptides', 'ceramides',
        }
        
        # Stop words and grammar words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us',
            'them', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
            'why', 'how', 'if', 'then', 'than', 'so', 'because', 'although',
            'though', 'while', 'until', 'unless', 'since', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'once', 'here', 'there', 'when', 'where', 'why',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'now', 'get', 'got', 'go', 'went',
            'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought',
            'want', 'wanted', 'need', 'needed', 'try', 'tried', 'use', 'used',
            'make', 'made', 'take', 'took', 'give', 'gave', 'say', 'said',
            'tell', 'told', 'ask', 'asked', 'look', 'looked', 'find', 'found',
            'work', 'worked', 'seem', 'seemed', 'feel', 'felt', 'become', 'became',
        }
        
        # Common grammar phrases to exclude
        self.grammar_phrases = {
            'in the', 'to the', 'of the', 'for the', 'on the', 'at the',
            'with the', 'from the', 'by the', 'i have', 'i am', 'i was',
            'i will', 'i would', 'i can', 'i should', 'i could', 'i want',
            'i need', 'i think', 'i feel', 'i know', 'i see', 'i get',
            'i got', 'i went', 'i came', 'i made', 'i took', 'i gave',
            'i said', 'i told', 'i asked', 'i looked', 'i found', 'i tried',
            'i used', 'i worked', 'i seemed', 'i felt', 'i became',
            'you have', 'you are', 'you were', 'you will', 'you would',
            'you can', 'you should', 'you could', 'you want', 'you need',
            'you think', 'you feel', 'you know', 'you see', 'you get',
            'it is', 'it was', 'it will', 'it would', 'it can', 'it should',
            'it could', 'it seems', 'it feels', 'it looks', 'it gets',
            'this is', 'that is', 'there is', 'there are', 'there was',
            'there were', 'here is', 'here are', 'here was', 'here were',
            'have a', 'has a', 'had a', 'have been', 'has been', 'had been',
            'have to', 'has to', 'had to', 'have not', 'has not', 'had not',
            'want to', 'wants to', 'wanted to', 'need to', 'needs to',
            'needed to', 'try to', 'tries to', 'tried to', 'used to',
            'going to', 'gonna', 'supposed to', 'able to', 'about to',
            'look at', 'looks at', 'looked at', 'look for', 'looks for',
            'looked for', 'look like', 'looks like', 'looked like',
            'seem to', 'seems to', 'seemed to', 'feel like', 'feels like',
            'felt like', 'get to', 'gets to', 'got to', 'get a', 'gets a',
            'got a', 'get the', 'gets the', 'got the', 'get it', 'gets it',
            'got it', 'get out', 'gets out', 'got out', 'get in', 'gets in',
            'got in', 'get on', 'gets on', 'got on', 'get off', 'gets off',
            'got off', 'get up', 'gets up', 'got up', 'get down', 'gets down',
            'got down', 'get back', 'gets back', 'got back', 'get over',
            'gets over', 'got over', 'get through', 'gets through', 'got through',
            'make a', 'makes a', 'made a', 'make the', 'makes the', 'made the',
            'make it', 'makes it', 'made it', 'make sure', 'makes sure',
            'made sure', 'make sense', 'makes sense', 'made sense',
            'take a', 'takes a', 'took a', 'take the', 'takes the', 'took the',
            'take it', 'takes it', 'took it', 'take care', 'takes care',
            'took care', 'take time', 'takes time', 'took time',
            'give a', 'gives a', 'gave a', 'give the', 'gives the', 'gave the',
            'give it', 'gives it', 'gave it', 'give up', 'gives up', 'gave up',
            'give in', 'gives in', 'gave in', 'give out', 'gives out', 'gave out',
            'say a', 'says a', 'said a', 'say the', 'says the', 'said the',
            'say it', 'says it', 'said it', 'say that', 'says that', 'said that',
            'tell a', 'tells a', 'told a', 'tell the', 'tells the', 'told the',
            'tell it', 'tells it', 'told it', 'tell me', 'tells me', 'told me',
            'tell you', 'tells you', 'told you', 'tell him', 'tells him', 'told him',
            'tell her', 'tells her', 'told her', 'tell them', 'tells them', 'told them',
            'ask a', 'asks a', 'asked a', 'ask the', 'asks the', 'asked the',
            'ask it', 'asks it', 'asked it', 'ask me', 'asks me', 'asked me',
            'ask you', 'asks you', 'asked you', 'ask him', 'asks him', 'asked him',
            'ask her', 'asks her', 'asked her', 'ask them', 'asks them', 'asked them',
            'find a', 'finds a', 'found a', 'find the', 'finds the', 'found the',
            'find it', 'finds it', 'found it', 'find out', 'finds out', 'found out',
            'work on', 'works on', 'worked on', 'work for', 'works for', 'worked for',
            'work with', 'works with', 'worked with', 'work out', 'works out',
            'worked out', 'work in', 'works in', 'worked in', 'work at', 'works at',
            'worked at', 'work the', 'works the', 'worked the', 'work a', 'works a',
            'worked a', 'work it', 'works it', 'worked it',
            'seem like', 'seems like', 'seemed like', 'seem to', 'seems to',
            'seemed to', 'seem a', 'seems a', 'seemed a', 'seem the', 'seems the',
            'seemed the', 'seem it', 'seems it', 'seemed it',
            'feel a', 'feels a', 'felt a', 'feel the', 'feels the', 'felt the',
            'feel it', 'feels it', 'felt it', 'feel like', 'feels like', 'felt like',
            'feel to', 'feels to', 'felt to', 'feel that', 'feels that', 'felt that',
            'become a', 'becomes a', 'became a', 'become the', 'becomes the',
            'became the', 'become it', 'becomes it', 'became it', 'become to',
            'becomes to', 'became to', 'become like', 'becomes like', 'became like',
            'become that', 'becomes that', 'became that',
            'no na', 'no na.', 'no na,', 'no na:', 'no na;', 'no na!', 'no na?',
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text using pattern matching.
        Returns products, brands, ingredients, concerns, routines.
        """
        text_lower = text.lower()
        entities = {
            'products': [],
            'brands': [],
            'ingredients': [],
            'concerns': [],
            'routines': [],
            'phrases': [],
        }
        
        # Extract product mentions (Brand + Product Type)
        product_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:serum|cream|moisturizer|cleanser|toner|essence|ampoule|mask|sunscreen|spf|treatment)\b',
            r'\b(the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:serum|cream|moisturizer)\b',
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                product = match if isinstance(match, str) else ' '.join(match)
                if len(product) > 3:
                    entities['products'].append(product.lower())
        
        # Extract ingredient mentions
        ingredient_keywords = [
            'retinol', 'retinoid', 'tretinoin', 'niacinamide', 'hyaluronic acid',
            'vitamin c', 'ascorbic acid', 'salicylic acid', 'aha', 'bha',
            'glycolic acid', 'lactic acid', 'azelaic acid', 'peptides', 'ceramides',
            'snail mucin', 'centella', 'green tea', 'tranexamic acid', 'arbutin',
            'kojic acid', 'alpha arbutin', 'squalane', 'rosehip oil', 'jojoba oil',
        ]
        
        for ingredient in ingredient_keywords:
            if ingredient in text_lower:
                entities['ingredients'].append(ingredient)
        
        # Extract concerns/pain points - focus on actual skincare issues, not generic phrases
        concern_patterns = [
            r'\b(?:struggling|struggle|issue|problem|concern|worried|frustrated|hate|disappointed)\s+with\s+([^.!?]{5,50})',  # Must be 5-50 chars
            r'\b(?:having|experiencing)\s+(?:acne|breakout|dryness|irritation|redness|texture|pores|hyperpigmentation|sensitivity|rosacea|eczema|dermatitis)',
            r'\b(?:doesn\'t|does not|not working|not helping)\s+([^.!?]{5,50})',  # Must be 5-50 chars
            r'\b(?:worse|breakout|irritation|stinging|burning|peeling|flaking|redness|rash)\b',
        ]
        
        # Generic phrases to exclude from concerns
        generic_concern_phrases = {
            'my skin', 'my face', 'my', 'skin', 'face', 'worse', 'bad', 'good',
            'help', 'need', 'want', 'like', 'think', 'feel', 'know', 'see',
            'get', 'got', 'have', 'has', 'had', 'was', 'were', 'is', 'are',
            'this', 'that', 'these', 'those', 'it', 'they', 'them', 'you',
            'i', 'me', 'my', 'your', 'his', 'her', 'our', 'their',
        }
        
        for pattern in concern_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                # Clean and validate match
                if isinstance(match, tuple):
                    match = ' '.join(match)
                match = match.strip().lower()
                # Filter out generic phrases and ensure it's meaningful
                if (match and 
                    len(match) >= 5 and 
                    match not in generic_concern_phrases and
                    not match.startswith(('my ', 'your ', 'his ', 'her ', 'our ', 'their ', 'the ', 'a ', 'an ')) and
                    any(kw in match for kw in ['acne', 'breakout', 'dry', 'oily', 'sensitive', 'irritat', 'red', 'texture', 'pore', 'wrinkle', 'spot', 'dark', 'hyperpigment', 'rosacea', 'eczema', 'dermatitis', 'rash', 'burn', 'sting', 'peel', 'flake', 'product', 'routine', 'ingredient', 'serum', 'cream', 'moisturizer', 'cleanser', 'toner'])):
                    entities['concerns'].append(match)
        
        # Extract routine mentions
        routine_keywords = [
            'double cleansing', 'slugging', 'glass skin', 'korean skincare',
            'skincare routine', 'morning routine', 'evening routine', 'night routine',
            'layering', 'essence', 'toner', 'serum', 'ampoule',
        ]
        
        for keyword in routine_keywords:
            if keyword in text_lower:
                entities['routines'].append(keyword)
        
        # Extract meaningful phrases (2-4 word phrases) - filter out stop words
        words = text_lower.split()
        # Clean words: remove punctuation and filter stop words
        cleaned_words = []
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w\s]', '', word)
            if word and word not in self.stop_words and len(word) > 2:
                cleaned_words.append(word)
        
        # Beauty-related keywords that indicate meaningful phrases
        beauty_keywords = {
            'skin', 'skincare', 'face', 'acne', 'moisturizer', 'serum', 'cream',
            'cleanser', 'toner', 'sunscreen', 'spf', 'retinol', 'vitamin', 'acid',
            'peptide', 'ceramide', 'niacinamide', 'hyaluronic', 'texture', 'pore',
            'wrinkle', 'fine line', 'dark spot', 'hyperpigmentation', 'redness',
            'irritation', 'sensitive', 'dry', 'oily', 'combination', 'glow',
            'dewy', 'matte', 'finish', 'routine', 'product', 'ingredient', 'brand',
            'korean', 'japanese', 'k-beauty', 'glass skin', 'slugging', 'double cleanse',
            'breakout', 'pimple', 'blackhead', 'whitehead', 'cyst', 'nodule',
            'exfoliate', 'exfoliation', 'chemical peel', 'mask', 'sheet mask',
            'essence', 'ampoule', 'treatment', 'repair', 'barrier', 'hydration',
            'moisture', 'sebum', 'oil', 'gel', 'lotion', 'balm', 'stick',
            'foundation', 'concealer', 'primer', 'powder', 'blush', 'bronzer',
            'highlighter', 'lipstick', 'lip balm', 'mascara', 'eyeliner', 'eyeshadow',
        }
        
        # Extract 2-3 word phrases that are meaningful
        for i in range(len(cleaned_words) - 1):
            # 2-word phrases
            phrase = f"{cleaned_words[i]} {cleaned_words[i+1]}"
            # Check if phrase contains beauty keywords or is substantial
            contains_beauty_keyword = any(kw in phrase for kw in beauty_keywords)
            is_substantial = len(phrase) > 8  # Longer phrases are more likely to be meaningful
            
            if (len(phrase) > 5 and 
                phrase not in self.grammar_phrases and
                not phrase.startswith(('the ', 'a ', 'an ', 'i ', 'you ', 'it ', 'this ', 'that ')) and
                (contains_beauty_keyword or is_substantial)):
                entities['phrases'].append(phrase)
            
            # 3-word phrases (if available)
            if i < len(cleaned_words) - 2:
                phrase3 = f"{cleaned_words[i]} {cleaned_words[i+1]} {cleaned_words[i+2]}"
                contains_beauty_keyword3 = any(kw in phrase3 for kw in beauty_keywords)
                is_substantial3 = len(phrase3) > 12
                
                if (len(phrase3) > 8 and 
                    phrase3 not in self.grammar_phrases and
                    not phrase3.startswith(('the ', 'a ', 'an ', 'i ', 'you ', 'it ', 'this ', 'that ')) and
                    (contains_beauty_keyword3 or is_substantial3)):
                    entities['phrases'].append(phrase3)
        
        return entities
    
    def detect_language_shifts(self, posts: List[Dict[str, Any]], 
                               time_window_days: int = 30) -> Dict[str, Any]:
        """
        Detect language shifts - new phrases or changing terminology.
        """
        now = datetime.now()
        recent_cutoff = now - timedelta(days=time_window_days)
        older_cutoff = recent_cutoff - timedelta(days=time_window_days)
        
        recent_posts = [p for p in posts if p.get('timestamp') and p['timestamp'] >= recent_cutoff]
        older_posts = [p for p in posts if older_cutoff <= p.get('timestamp', datetime.min) < recent_cutoff]
        
        # Extract phrases from each period
        recent_phrases = Counter()
        older_phrases = Counter()
        
        for post in recent_posts:
            text = f"{post.get('title', '')} {post.get('text', '')}"
            entities = self.extract_entities(text)
            recent_phrases.update(entities['phrases'])
        
        for post in older_posts:
            text = f"{post.get('title', '')} {post.get('text', '')}"
            entities = self.extract_entities(text)
            older_phrases.update(entities['phrases'])
        
        # Find phrases that are new or growing rapidly
        language_shifts = []
        
        for phrase, recent_count in recent_phrases.most_common(100):
            older_count = older_phrases.get(phrase, 0)
            
            if older_count == 0 and recent_count >= 3:
                # New phrase
                language_shifts.append({
                    'phrase': phrase,
                    'type': 'new',
                    'recent_mentions': recent_count,
                    'older_mentions': 0,
                    'growth_rate': float('inf'),
                })
            elif older_count > 0:
                growth_rate = recent_count / older_count
                if growth_rate > 2.0:  # 2x growth
                    language_shifts.append({
                        'phrase': phrase,
                        'type': 'growing',
                        'recent_mentions': recent_count,
                        'older_mentions': older_count,
                        'growth_rate': growth_rate,
                    })
        
        language_shifts.sort(key=lambda x: x['growth_rate'], reverse=True)
        return {'shifts': language_shifts[:50]}
    
    def detect_emerging_trends(self, posts: List[Dict[str, Any]], 
                              comments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect emerging trends with early signal detection.
        """
        # Combine posts and comments
        all_texts = []
        for post in posts:
            all_texts.append({
                'text': f"{post.get('title', '')} {post.get('text', '')}",
                'timestamp': post.get('timestamp'),
                'score': post.get('score', 0),
                'comment_count': post.get('comment_count', 0),
            })
        
        if comments:
            for comment in comments:
                all_texts.append({
                    'text': comment.get('text', ''),
                    'timestamp': comment.get('timestamp'),
                    'score': comment.get('score', 0),
                    'comment_count': 0,
                })
        
        # Group by time periods
        now = datetime.now()
        time_buckets = {
            'recent': (now - timedelta(days=7), now),
            'mid': (now - timedelta(days=30), now - timedelta(days=7)),
            'older': (now - timedelta(days=90), now - timedelta(days=30)),
        }
        
        bucket_data = {bucket: [] for bucket in time_buckets}
        
        for item in all_texts:
            ts = item.get('timestamp')
            if not ts:
                continue
            
            for bucket_name, (start, end) in time_buckets.items():
                if start <= ts <= end:
                    bucket_data[bucket_name].append(item)
                    break
        
        # Extract entities from each bucket
        bucket_entities = {}
        for bucket, items in bucket_data.items():
            entity_counts = defaultdict(lambda: {'count': 0, 'scores': [], 'quotes': []})
            
            for item in items:
                entities = self.extract_entities(item['text'])
                
                for category, entity_list in entities.items():
                    for entity in entity_list:
                        key = f"{category}:{entity}"
                        entity_counts[key]['count'] += 1
                        entity_counts[key]['scores'].append(item['score'])
                        
                        # Store representative quote
                        if len(entity_counts[key]['quotes']) < 3:
                            quote = item['text'][:200]
                            if quote:
                                entity_counts[key]['quotes'].append(quote)
            
            bucket_entities[bucket] = entity_counts
        
        # Calculate trends
        emerging_products = []
        emerging_ingredients = []
        emerging_routines = []
        pain_points = []
        
        recent_entities = bucket_entities['recent']
        mid_entities = bucket_entities['mid']
        older_entities = bucket_entities['older']
        
        # Find emerging items (low baseline, rapid growth)
        for key, recent_data in recent_entities.items():
            category, entity = key.split(':', 1)
            recent_count = recent_data['count']
            mid_count = mid_entities.get(key, {}).get('count', 0)
            older_count = older_entities.get(key, {}).get('count', 0)
            
            # Calculate growth metrics
            baseline = max(mid_count, older_count, 1)
            growth_rate = recent_count / baseline if baseline > 0 else recent_count
            
            # Early signal: low baseline but growing
            if older_count <= 2 and recent_count >= 3:
                momentum = recent_count * growth_rate
                avg_score = sum(recent_data['scores']) / len(recent_data['scores']) if recent_data['scores'] else 0
                
                trend_data = {
                    'entity': entity,
                    'category': category,
                    'recent_mentions': recent_count,
                    'mid_mentions': mid_count,
                    'older_mentions': older_count,
                    'growth_rate': growth_rate,
                    'momentum': momentum,
                    'avg_score': avg_score,
                    'quotes': recent_data['quotes'][:3],
                }
                
                if category == 'products':
                    emerging_products.append(trend_data)
                elif category == 'ingredients':
                    emerging_ingredients.append(trend_data)
                elif category == 'routines':
                    emerging_routines.append(trend_data)
                elif category == 'concerns':
                    pain_points.append(trend_data)
        
        # Sort by momentum
        emerging_products.sort(key=lambda x: x['momentum'], reverse=True)
        emerging_ingredients.sort(key=lambda x: x['momentum'], reverse=True)
        emerging_routines.sort(key=lambda x: x['momentum'], reverse=True)
        pain_points.sort(key=lambda x: x['momentum'], reverse=True)
        
        return {
            'emerging_products': emerging_products[:20],
            'emerging_ingredients': emerging_ingredients[:20],
            'emerging_routines': emerging_routines[:20],
            'pain_points': pain_points[:20],
        }
    
    def cluster_pain_points(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster pain points to identify repeated frustrations.
        """
        concern_texts = []
        
        # Extract concern-related posts
        concern_keywords = ['problem', 'issue', 'struggle', 'frustrated', 
                          'disappointed', 'not working', 'breakout', 'irritation']
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('text', '')}".lower()
            if any(keyword in text for keyword in concern_keywords):
                concern_texts.append({
                    'text': text,
                    'score': post.get('score', 0),
                    'timestamp': post.get('timestamp'),
                })
        
        # Simple clustering by keyword overlap
        clusters = defaultdict(list)
        
        for concern in concern_texts:
            # Extract key phrases
            entities = self.extract_entities(concern['text'])
            key = ' '.join(sorted(entities['concerns'][:3]))
            if key:
                clusters[key].append(concern)
        
        # Format clusters
        pain_clusters = []
        for key, items in clusters.items():
            if len(items) >= 3:  # At least 3 mentions
                pain_clusters.append({
                    'theme': key,
                    'mention_count': len(items),
                    'avg_score': sum(i['score'] for i in items) / len(items),
                    'representative_quotes': [i['text'][:200] for i in items[:3]],
                })
        
        pain_clusters.sort(key=lambda x: x['mention_count'], reverse=True)
        return pain_clusters[:15]

