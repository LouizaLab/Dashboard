"""
Insight Engine: Multi-agent orchestration for answering consultant questions.
Implements Explorer, Analyst, Critic, and Anchoring agents.
"""
import json
import random
import numpy as np
from typing import Dict, List, Optional, Tuple
from django.db.models import Q
from .market_insight_models import (
    MarketDefinition, Brand, Product, MarketSignal, InnovationEvent,
    InsightQuery, InsightAnswer
)


class InsightEngine:
    """Orchestrates multiple agents to answer consultant questions."""
    
    def __init__(self, use_llm=True, mock_mode=False):
        self.use_llm = use_llm
        self.mock_mode = mock_mode
    
    def answer_question(
        self,
        question: str,
        case_template: str = 'custom',
        vertical: str = 'beauty',
        filters: Dict = None,
        context: Dict = None
    ) -> Dict:
        """
        Answer a consultant question using multi-agent orchestration.
        
        Returns structured JSON with:
        - executive_summary
        - answers (keyed by sub-question)
        - market_map_insights
        - recommended_actions
        - whitespace_opportunities
        - risks_and_watchouts
        - evidence
        - confidence (score, entropy, rationale)
        - next_questions
        """
        filters = filters or {}
        context = context or {}
        
        # Store query
        query = InsightQuery.objects.create(
            question=question,
            case_template=case_template,
            vertical=vertical,
            context={**filters, **context},
        )
        
        # Step 1: Explorer - Retrieve relevant markets/brands/products/signals
        explorer_results = self._explorer_agent(question, vertical, filters, context)
        
        # Step 2: Analyst - Synthesize trends and answer sub-questions
        analyst_results = self._analyst_agent(question, case_template, explorer_results, vertical)
        
        # Step 3: Critic - Check for overreach and highlight uncertainty
        critic_results = self._critic_agent(analyst_results, explorer_results)
        
        # Step 4: Anchoring - Attach evidence and compute confidence/entropy
        final_answer = self._anchoring_agent(
            question, case_template, analyst_results, critic_results, explorer_results
        )
        
        # Store answer
        answer = InsightAnswer.objects.create(
            query=query,
            json_output=final_answer,
            confidence_score=final_answer['confidence']['score'],
            entropy_score=final_answer['confidence']['entropy'],
        )
        
        return final_answer
    
    def _explorer_agent(
        self,
        question: str,
        vertical: str,
        filters: Dict,
        context: Dict
    ) -> Dict:
        """Explorer: Retrieves relevant markets, brands, products, signals, innovation patterns."""
        results = {
            'markets': [],
            'brands': [],
            'products': [],
            'signals': [],
            'innovation_events': [],
        }
        
        # Extract keywords from question
        question_lower = question.lower()
        
        # Find relevant markets
        markets_query = MarketDefinition.objects.filter(vertical=vertical)
        
        # Apply filters
        if filters.get('category'):
            markets_query = markets_query.filter(category__icontains=filters['category'])
        if filters.get('price_tier'):
            markets_query = markets_query.filter(price_tier=filters['price_tier'])
        if filters.get('selected_markets'):
            markets_query = markets_query.filter(id__in=filters['selected_markets'])
        
        # Keyword matching
        if 'skincare' in question_lower:
            markets_query = markets_query.filter(category='Skincare')
        elif 'makeup' in question_lower or 'cosmetic' in question_lower:
            markets_query = markets_query.filter(category='Makeup')
        elif 'fragrance' in question_lower or 'perfume' in question_lower:
            markets_query = markets_query.filter(category='Fragrance')
        elif 'serum' in question_lower:
            markets_query = markets_query.filter(sub_category__icontains='Serum')
        elif 'moisturizer' in question_lower:
            markets_query = markets_query.filter(sub_category__icontains='Moisturizer')
        
        results['markets'] = list(markets_query[:20])
        
        # Get signals for these markets
        market_ids = [m.id for m in results['markets']]
        signals = MarketSignal.objects.filter(market_id__in=market_ids).order_by('-date')[:50]
        results['signals'] = list(signals)
        
        # Get innovation events
        events = InnovationEvent.objects.filter(market_id__in=market_ids).order_by('-date')[:30]
        results['innovation_events'] = list(events)
        
        # Get brands from competitor sets
        brand_ids = set()
        for market in results['markets']:
            if market.competitor_set:
                brand_ids.update(market.competitor_set)
        
        if brand_ids:
            brands = Brand.objects.filter(id__in=list(brand_ids)[:30])
            results['brands'] = list(brands)
            
            # Get products from these brands
            products = Product.objects.filter(brand_id__in=[b.id for b in results['brands']])[:50]
            results['products'] = list(products)
        
        return results
    
    def _analyst_agent(
        self,
        question: str,
        case_template: str,
        explorer_results: Dict,
        vertical: str
    ) -> Dict:
        """Analyst: Synthesizes trends and answers sub-questions."""
        
        if case_template == 'case1':  # Food Growth & Whitespace
            return self._analyze_case1_food(explorer_results, question)
        elif case_template == 'case2':  # Beauty Portfolio Strategy
            return self._analyze_case2_beauty(explorer_results, question)
        else:
            return self._analyze_custom(explorer_results, question, vertical)
    
    def _analyze_case1_food(self, explorer_results: Dict, question: str) -> Dict:
        """Case 1: Food Growth & Whitespace analysis."""
        markets = explorer_results['markets']
        signals = explorer_results['signals']
        events = explorer_results['innovation_events']
        
        # Analyze functional jobs
        functional_jobs = {
            'mood': {'mentions': 0, 'evidence': []},
            'focus': {'mentions': 0, 'evidence': []},
            'sleep': {'mentions': 0, 'evidence': []},
            'gut_health': {'mentions': 0, 'evidence': []},
            'social_moments': {'mentions': 0, 'evidence': []},
            'energy': {'mentions': 0, 'evidence': []},
        }
        
        # Analyze cohort differences
        cohort_insights = {
            'gen_z': {'preferences': [], 'evidence': []},
            'millennials': {'preferences': [], 'evidence': []},
            'fitness_oriented': {'preferences': [], 'evidence': []},
            'time_starved': {'preferences': [], 'evidence': []},
        }
        
        # Whitespace map: jobs × formats
        whitespace_map = {}
        formats = ['bar', 'pack', 'drink', 'powder']
        jobs = list(functional_jobs.keys())
        
        for job in jobs:
            whitespace_map[job] = {}
            for fmt in formats:
                # Check if this combination exists
                exists = any(
                    job.replace('_', ' ') in str(m.name).lower() and fmt in str(m.name).lower()
                    for m in markets
                )
                whitespace_map[job][fmt] = {
                    'exists': exists,
                    'opportunity_score': random.uniform(0.3, 0.9) if not exists else random.uniform(0.1, 0.5),
                }
        
        # Generate synthetic insights
        if self.mock_mode:
            return {
                'executive_summary': [
                    "Functional snacking is expanding beyond protein to mood, focus, and gut health",
                    "Gen Z prioritizes mood enhancement and social moments; Millennials focus on gut health and sleep",
                    "Whitespace exists in mood-enhancing formats beyond bars (drinks, powders)",
                    "Fitness-oriented consumers want performance; time-starved want convenience",
                ],
                'functional_jobs': {
                    'emerging': ['mood', 'focus', 'gut_health'],
                    'sizing': {'mood': 'High', 'focus': 'Medium', 'gut_health': 'High'},
                    'evidence': ['synthetic_demo'],
                },
                'cohort_differences': {
                    'gen_z_vs_millennials': {
                        'gen_z': ['mood enhancement', 'social moments', 'portability'],
                        'millennials': ['gut health', 'sleep support', 'clean ingredients'],
                    },
                    'fitness_vs_time_starved': {
                        'fitness': ['protein content', 'performance claims', 'low-sugar'],
                        'time_starved': ['convenience', 'meal replacement', 'on-the-go'],
                    },
                },
                'whitespace_map': whitespace_map,
                'recommendations': [
                    "Launch mood-enhancing drink format targeting Gen Z",
                    "Develop gut health bar with probiotics for Millennials",
                    "Create focus-enhancing powder for professionals",
                ],
            }
        
        # TODO: Real LLM analysis would go here
        return {
            'executive_summary': ["Analysis pending LLM integration"],
            'functional_jobs': functional_jobs,
            'cohort_differences': cohort_insights,
            'whitespace_map': whitespace_map,
        }
    
    def _analyze_case2_beauty(self, explorer_results: Dict, question: str) -> Dict:
        """Case 2: Prestige Beauty Portfolio Strategy analysis."""
        markets = explorer_results['markets']
        brands = explorer_results['brands']
        products = explorer_results['products']
        signals = explorer_results['signals']
        events = explorer_results['innovation_events']
        
        # Category strategic importance
        category_importance = {}
        for market in markets:
            cat = market.category
            if cat not in category_importance:
                category_importance[cat] = {
                    'markets': 0,
                    'avg_momentum': 0.0,
                    'innovation_density': 0,
                }
            category_importance[cat]['markets'] += 1
            
            # Get signals for this market
            market_signals = [s for s in signals if s.market_id == market.id]
            if market_signals:
                category_importance[cat]['avg_momentum'] += market_signals[0].trend_momentum or 0.0
            
            # Count innovation events
            market_events = [e for e in events if e.market_id == market.id]
            category_importance[cat]['innovation_density'] += len(market_events)
        
        # Normalize
        for cat in category_importance:
            cat_data = category_importance[cat]
            if cat_data['markets'] > 0:
                cat_data['avg_momentum'] /= cat_data['markets']
                cat_data['innovation_density'] /= cat_data['markets']
        
        # Tier analysis
        tier_analysis = {}
        for market in markets:
            if market.price_tier:
                tier = market.price_tier
                if tier not in tier_analysis:
                    tier_analysis[tier] = {'markets': 0, 'growth': 0.0}
                tier_analysis[tier]['markets'] += 1
        
        # Competitor positioning
        competitor_positioning = {}
        for brand in brands[:10]:  # Top 10
            brand_products = [p for p in products if p.brand_id == brand.id]
            if brand_products:
                categories = set(p.category for p in brand_products)
                tiers = [p.price_tier for p in brand_products if p.price_tier]
                competitor_positioning[str(brand.id)] = {
                    'brand_name': brand.name,
                    'categories': list(categories),
                    'avg_tier': max(set(tiers), key=tiers.count) if tiers else 'premium',
                    'positioning': brand.positioning_tags[:3],
                }
        
        # Innovation patterns
        innovation_patterns = {
            'indie': {'launches': 0, 'claims': [], 'formats': []},
            'luxury': {'launches': 0, 'claims': [], 'formats': []},
            'heritage': {'launches': 0, 'claims': [], 'formats': []},
        }
        
        for event in events[:20]:
            if event.brand:
                brand_type = event.brand.brand_type
                if brand_type in ['indie', 'luxury', 'heritage']:
                    innovation_patterns[brand_type]['launches'] += 1
                    if event.innovation_tags:
                        innovation_patterns[brand_type]['claims'].extend(event.innovation_tags)
                    if event.product:
                        innovation_patterns[brand_type]['formats'].append(event.product.format)
        
        if self.mock_mode:
            return {
                'executive_summary': [
                    "Serums and targeted treatments show highest strategic importance (45% YoY growth)",
                    "Premium tier is expanding; super-premium showing trade-up momentum",
                    "Indie brands driving innovation in clean claims and new formats",
                    "Luxury brands focusing on heritage positioning and ultra-premium launches",
                ],
                'category_importance': {
                    'Skincare': {'importance': 'High', 'growth': 0.45, 'rationale': 'Serums driving growth'},
                    'Makeup': {'importance': 'Medium', 'growth': 0.18, 'rationale': 'Steady growth'},
                    'Fragrance': {'importance': 'High', 'growth': 0.32, 'rationale': 'Premiumization trend'},
                },
                'tier_analysis': {
                    'premium': {'trend': 'stable', 'trade_up_potential': 'medium'},
                    'super_premium': {'trend': 'growing', 'trade_up_potential': 'high'},
                    'ultra_luxury': {'trend': 'niche', 'trade_up_potential': 'low'},
                },
                'competitor_positioning': competitor_positioning,
                'innovation_patterns': innovation_patterns,
                'recommendations': [
                    "Prioritize Skincare serums in super-premium tier",
                    "Launch targeted treatment format with clean claims",
                    "Consider fragrance expansion in premium tier",
                ],
            }
        
        return {
            'executive_summary': ["Analysis pending LLM integration"],
            'category_importance': category_importance,
            'tier_analysis': tier_analysis,
            'competitor_positioning': competitor_positioning,
            'innovation_patterns': innovation_patterns,
        }
    
    def _analyze_custom(self, explorer_results: Dict, question: str, vertical: str) -> Dict:
        """Custom question analysis."""
        # Generic analysis structure
        return {
            'executive_summary': [f"Analysis of {question[:100]}"],
            'key_findings': [],
            'recommendations': [],
        }
    
    def _critic_agent(self, analyst_results: Dict, explorer_results: Dict) -> Dict:
        """Critic: Checks for overreach and highlights uncertainty."""
        flags = []
        uncertainty_factors = []
        
        # Check evidence coverage
        evidence_count = (
            len(explorer_results['markets']) +
            len(explorer_results['brands']) +
            len(explorer_results['signals'])
        )
        
        if evidence_count < 5:
            flags.append('Limited evidence coverage')
            uncertainty_factors.append('Low data coverage')
        
        # Check for conflicting signals
        signals = explorer_results['signals']
        if signals:
            momentums = [s.trend_momentum for s in signals if s.trend_momentum]
            if momentums:
                momentum_range = max(momentums) - min(momentums)
                if momentum_range > 0.5:
                    flags.append('Conflicting momentum signals')
                    uncertainty_factors.append('High signal dispersion')
        
        return {
            'flags': flags,
            'uncertainty_factors': uncertainty_factors,
            'evidence_quality': 'high' if evidence_count >= 10 else 'medium' if evidence_count >= 5 else 'low',
        }
    
    def _anchoring_agent(
        self,
        question: str,
        case_template: str,
        analyst_results: Dict,
        critic_results: Dict,
        explorer_results: Dict
    ) -> Dict:
        """Anchoring: Attaches evidence and computes confidence/entropy."""
        
        # Compute confidence (1-5 scale)
        evidence_count = (
            len(explorer_results['markets']) +
            len(explorer_results['brands']) +
            len(explorer_results['signals'])
        )
        
        base_confidence = min(5, max(1, 1 + (evidence_count // 5)))
        
        # Adjust based on critic flags
        if critic_results['flags']:
            base_confidence -= len(critic_results['flags'])
        
        confidence_score = max(1, min(5, base_confidence))
        
        # Compute entropy (0-1 scale)
        signals = explorer_results['signals']
        if signals and len(signals) > 1:
            momentums = [s.trend_momentum for s in signals if s.trend_momentum]
            if momentums:
                momentum_std = np.std(momentums) if len(momentums) > 1 else 0.0
                entropy_score = min(1.0, momentum_std / 0.5)  # Normalize
            else:
                entropy_score = 0.3
        else:
            entropy_score = 0.5  # Default uncertainty
        
        # Adjust entropy based on critic
        if critic_results['uncertainty_factors']:
            entropy_score = min(1.0, entropy_score + 0.2 * len(critic_results['uncertainty_factors']))
        
        # Build evidence list
        evidence = []
        for market in explorer_results['markets'][:10]:
            evidence.append({
                'type': 'market',
                'id': str(market.id),
                'label': market.name,
                'evidence_type': 'synthetic_demo' if self.mock_mode else 'market_data',
            })
        
        for brand in explorer_results['brands'][:5]:
            evidence.append({
                'type': 'brand',
                'id': str(brand.id),
                'label': brand.name,
                'evidence_type': 'synthetic_demo' if self.mock_mode else 'brand_data',
            })
        
        # Build final structured answer
        answer = {
            'title': f"Market Insight: {question[:60]}",
            'executive_summary': analyst_results.get('executive_summary', []),
            'answers': analyst_results,  # Full analyst results
            'market_map_insights': {
                'clusters_impacted': [],
                'rationale': 'Analysis based on selected markets',
            },
            'recommended_actions': {
                'now': analyst_results.get('recommendations', [])[:2],
                'next': analyst_results.get('recommendations', [])[2:4] if len(analyst_results.get('recommendations', [])) > 2 else [],
                'long_term': analyst_results.get('recommendations', [])[4:] if len(analyst_results.get('recommendations', [])) > 4 else [],
            },
            'whitespace_opportunities': analyst_results.get('whitespace_map', {}),
            'risks_and_watchouts': critic_results['flags'],
            'evidence': evidence,
            'confidence': {
                'score': confidence_score,
                'entropy': entropy_score,
                'rationale': self._generate_confidence_rationale(confidence_score, entropy_score, critic_results),
            },
            'next_questions': self._generate_next_questions(case_template, analyst_results),
        }
        
        return answer
    
    def _generate_confidence_rationale(self, score: int, entropy: float, critic_results: Dict) -> str:
        """Generate plain-English confidence explanation."""
        parts = []
        
        if score >= 4:
            parts.append("High confidence based on strong evidence coverage")
        elif score >= 3:
            parts.append("Moderate confidence with good evidence")
        else:
            parts.append("Lower confidence due to limited evidence")
        
        if entropy > 0.7:
            parts.append("High uncertainty due to conflicting signals")
        elif entropy > 0.4:
            parts.append("Moderate uncertainty in outcomes")
        else:
            parts.append("Low uncertainty with consistent signals")
        
        if critic_results['flags']:
            parts.append(f"Note: {', '.join(critic_results['flags'])}")
        
        return ". ".join(parts) + "."
    
    def _generate_next_questions(self, case_template: str, analyst_results: Dict) -> List[str]:
        """Generate follow-up questions."""
        if case_template == 'case1':
            return [
                "What specific ingredients drive mood enhancement claims?",
                "How do price points vary across functional job categories?",
                "What channel strategies work best for Gen Z vs Millennials?",
            ]
        elif case_template == 'case2':
            return [
                "Which specific serum sub-categories show highest growth?",
                "How do indie brand innovation patterns differ by price tier?",
                "What channel mix optimizes super-premium launches?",
            ]
        else:
            return [
                "What are the key drivers of this trend?",
                "How do different segments respond?",
                "What are the competitive implications?",
            ]
