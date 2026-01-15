"""
GPT-4 Integration for Market Insight - Converts simulation results to consultant-grade answers.
"""
import json
import hashlib
import os
from typing import Dict, List, Optional
from django.core.cache import cache
from .services import client, OPENAI_AVAILABLE, OPENAI_API_KEY
from typing import List
from .market_insight_models import MarketSimResult, MarketInsightAnswer


# Environment variable for mode - default to 'gpt' if OpenAI is available, otherwise 'mock'
MARKET_INSIGHT_MODE = os.environ.get('MARKET_INSIGHT_MODE', 'auto').lower()
if MARKET_INSIGHT_MODE == 'auto':
    # Auto-detect: use GPT if available, otherwise mock
    MARKET_INSIGHT_MODE = 'gpt' if (OPENAI_AVAILABLE and OPENAI_API_KEY and client) else 'mock'

# Allow bypassing cache via environment variable
BYPASS_CACHE = os.environ.get('MARKET_INSIGHT_BYPASS_CACHE', 'false').lower() == 'true'


def generate_insight_from_simulation(
    sim_result: MarketSimResult,
    question: str,
    vertical: str,
    region: str,
    pinned_nodes: List[str],
    scenario_params: Dict,
    filters: Dict = None,
    force_gpt: bool = False,
    manifold_data: Optional[Dict] = None
) -> Dict:
    """
    Generate consultant-grade insight from simulation result using GPT-4.

    Args:
        force_gpt: If True, bypass cache and use GPT even if mode is mock

    Returns strict JSON schema matching the required format.
    """
    # Check cache (unless bypassed)
    if not BYPASS_CACHE and not force_gpt:
        cache_key = _get_cache_key(sim_result, question, scenario_params)
        cached_result = cache.get(cache_key)
        if cached_result:
            print(f"[Market Insight] Using cached result for key: {cache_key[:20]}...")
            return cached_result

    # Determine if we should use GPT
    use_gpt = force_gpt or (MARKET_INSIGHT_MODE == 'gpt' and OPENAI_AVAILABLE and OPENAI_API_KEY and client)

    if not use_gpt:
        print(f"[Market Insight] Using mock mode (MARKET_INSIGHT_MODE={MARKET_INSIGHT_MODE}, OPENAI_AVAILABLE={OPENAI_AVAILABLE}, client={client is not None})")
        return _generate_mock_insight(sim_result, question, vertical, scenario_params)

    print(f"[Market Insight] Using GPT-4 API (model: gpt-4o)")

    # Build prompt
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        sim_result, question, vertical, region, pinned_nodes, scenario_params, filters or {}, manifold_data
    )

    # Call GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=3000,  # Increased for more comprehensive responses
        )

        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None

        # Parse JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback to mock if JSON parsing fails
            result = _generate_mock_insight(sim_result, question, vertical, scenario_params)

        # Cache result (unless bypassed)
        if not BYPASS_CACHE:
            cache_key = _get_cache_key(sim_result, question, scenario_params)
            cache.set(cache_key, result, timeout=3600 * 24)  # Cache for 24 hours

        # Store in DB
        try:
            MarketInsightAnswer.objects.create(
                sim_result=sim_result,
                json_output=result,
                gpt_model="gpt-4o",
                tokens_used=tokens_used,
                cached=False,
            )
        except Exception as db_error:
            print(f"[Market Insight] Warning: Could not save to DB: {db_error}")

        print(f"[Market Insight] GPT-4 response generated successfully (tokens: {tokens_used})")
        return result

    except Exception as e:
        print(f"[Market Insight] GPT-4 error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to mock
        print(f"[Market Insight] Falling back to mock insight")
        return _generate_mock_insight(sim_result, question, vertical, scenario_params)


def _get_cache_key(sim_result: MarketSimResult, question: str, scenario_params: Dict) -> str:
    """Generate cache key."""
    key_str = f"{sim_result.id}_{question}_{json.dumps(scenario_params, sort_keys=True)}"
    return f"market_insight_{hashlib.md5(key_str.encode()).hexdigest()}"


def _build_system_prompt() -> str:
    """Build system prompt for GPT."""
    return """You are Louiza Market Insight, a consultant-grade strategist specializing in consumer segment analysis. You convert market manifold data and simulation outputs into direct, actionable answers to consultant questions.

Your role:
- **Answer the question directly** - The user's question is the primary focus. Structure your response to directly address what they asked.
- **Use consumer segment context** - When consumer segment filters are provided, tailor your answer to that specific segment, but still answer the question asked.
- **Map to categories/sub-categories** - When questions ask about categories, sub-categories, or product types, explicitly identify which ones are gaining/losing importance, not just market segments.
- **Be specific** - Name specific categories (e.g., "face skincare", "serums", "eye products", "lip products", "fragrance") and sub-categories when relevant.
- **Reference market segments (clusters) as supporting evidence** - Use cluster data to support your answer about categories, but don't make clusters the primary answer.
- **Quantify changes** - When asked about "gaining" or "losing" importance, provide directional indicators (↑ gaining, ↓ losing, → stable) and explain why.
- Be explicit about assumptions and uncertainty
- Do NOT invent data outside the provided manifold and simulation payload
- Output STRICT JSON that matches the given schema—no markdown, no commentary

Output format (strict JSON schema):
{
  "title": "string",
  "executive_summary": ["bullet 1 focused on consumer segment behavior", "bullet 2 mapping segments to markets", ...],
  "consumer_segment_insights": {
    "segment_name": {
      "description": "description of this consumer segment's behavior",
      "preferred_markets": ["market segment 1", "market segment 2"],
      "avoided_markets": ["market segment 3"],
      "engagement_percentages": {
        "market_segment_1": 65,
        "market_segment_2": 45
      },
      "key_drivers": ["driver 1", "driver 2"]
    }
  },
  "direct_answers": {
    "sub_question_1": "comprehensive answer focused on consumer segment behavior and market mapping",
    "sub_question_2": "comprehensive answer referencing how consumer segments interact with clusters"
  },
  "market_map_takeaways": {
    "clusters_impacted": ["specific cluster name 1", "specific cluster name 2"],
    "consumer_segment_to_market_mapping": "explanation of which consumer segments engage with which market segments and why",
    "cluster_relationships": "explanation of spatial relationships between clusters from consumer segment perspective",
    "rationale": "why these clusters matter for the target consumer segment"
  },
  "recommended_actions": {
    "now": ["action 1 tailored to consumer segment", "action 2"],
    "next": ["action 3", "action 4"],
    "long_term": ["action 5"]
  },
  "whitespace_opportunities": {
    "opportunity_1": {"description": "...", "sizing": "...", "target_segment": "consumer segment name"}
  },
  "risks_and_watchouts": ["risk 1", "risk 2"],
  "assumptions": ["assumption 1", "assumption 2"],
  "evidence": [
    {"type": "cluster", "id": "...", "label": "...", "consumer_relevance": "why this matters to consumer segment"}
  ],
  "confidence": {
    "score": 4,
    "entropy": 0.3,
    "rationale": "explanation"
  },
  "next_questions": ["question 1", "question 2"]
}"""


def _build_user_prompt(
    sim_result: MarketSimResult,
    question: str,
    vertical: str,
    region: str,
    pinned_nodes: List[str],
    scenario_params: Dict,
    filters: Dict = None,
    manifold_data: Optional[Dict] = None
) -> str:
    """Build user prompt with simulation context and manifold data."""
    # Summarize simulation results
    top_clusters = sim_result.impacted_clusters[:5]
    cluster_summary = "\n".join([
        f"- {c['cluster_label']}: impact {c['impact_score']:.2f} ({', '.join(c.get('drivers', []))})"
        for c in top_clusters
    ])

    # Add manifold data context
    manifold_context = ""
    if manifold_data:
        clusters = manifold_data.get('clusters', [])
        points = manifold_data.get('points', [])

        if clusters:
            manifold_context += "\n\n=== MARKET MANIFOLD STRUCTURE ===\n"
            manifold_context += f"Total clusters identified: {len(clusters)}\n"
            manifold_context += "Key Market Clusters:\n"
            for cluster in clusters[:10]:  # Top 10 clusters
                drivers = cluster.get('drivers', {})
                claims = drivers.get('claims', [])
                tier = drivers.get('tier', 'unknown')
                category = drivers.get('category', 'unknown')
                channel = drivers.get('channel', 'unknown')

                manifold_context += f"\n• {cluster.get('label', 'Unknown')} ({cluster.get('count', 0)} points):\n"
                manifold_context += f"  - Category: {category}\n"
                manifold_context += f"  - Price Tier: {tier}\n"
                if claims:
                    manifold_context += f"  - Key Claims: {', '.join(claims[:3])}\n"
                manifold_context += f"  - Primary Channel: {channel}\n"

        # Analyze pinned nodes if any
        if pinned_nodes and points:
            pinned_info = []
            for node_id in pinned_nodes[:5]:  # Limit to 5
                point = next((p for p in points if str(p.get('id')) == str(node_id)), None)
                if point:
                    pinned_info.append(f"{point.get('label', 'Unknown')} (Cluster: {point.get('cluster_label', 'N/A')})")
            if pinned_info:
                manifold_context += f"\n\nPinned Context Nodes:\n"
                manifold_context += "\n".join([f"- {info}" for info in pinned_info])

        # Spatial relationships
        if clusters and len(clusters) > 1:
            manifold_context += "\n\n=== SPATIAL RELATIONSHIPS ===\n"
            manifold_context += "The manifold reveals market structure where:\n"
            manifold_context += "- Clusters represent distinct preference-based market segments\n"
            manifold_context += "- Proximity indicates similar consumer preferences or competitive dynamics\n"
            manifold_context += "- Cluster boundaries show clear market separation\n"

    # Category/tier shifts summary
    shifts_summary = ""
    if sim_result.category_tier_shifts:
        shifts_summary = "\nCategory/Tier Shifts:\n"
        for key, shift in list(sim_result.category_tier_shifts.items())[:5]:
            shifts_summary += f"- {shift['category']} / {shift['tier']}: {shift['trend']} (impact {shift['impact']:.2f})\n"

    # Competitor positioning summary
    comp_summary = ""
    if sim_result.competitor_positioning and sim_result.competitor_positioning.get('grid'):
        comp_summary = "\nCompetitor Positioning:\n"
        for key, brands in list(sim_result.competitor_positioning['grid'].items())[:3]:
            comp_summary += f"- {key}: {len(brands)} competitors\n"

    # Innovation patterns summary
    innovation_summary = ""
    if sim_result.innovation_patterns:
        innovation_summary = "\nInnovation Patterns:\n"
        for brand_type, patterns in sim_result.innovation_patterns.items():
            if patterns.get('launches', 0) > 0:
                innovation_summary += f"- {brand_type.title()}: {patterns['launches']} launches, claims: {', '.join(patterns.get('claims', [])[:2])}\n"

    # Build consumer segment context from filters
    consumer_segment_context = ""
    if filters and isinstance(filters, dict):
        segment_parts = []
        if filters.get('age_group'):
            age_labels = {
                'gen_z': 'Gen Z (16-24)',
                'young_millennials': 'Young Millennials (25-34)',
                'mid_millennials': 'Mid Millennials (35-44)',
                'gen_x': 'Gen X (45-54)',
                '55_plus': '55+'
            }
            segment_parts.append(f"Age: {age_labels.get(filters['age_group'], filters['age_group'])}")
        if filters.get('gender'):
            segment_parts.append(f"Gender: {filters['gender'].title()}")
        if filters.get('income_tier'):
            income_labels = {
                'budget_constrained': 'Budget-constrained',
                'middle_income': 'Middle income',
                'upper_middle_income': 'Upper-middle income',
                'high_income': 'High income / Affluent'
            }
            segment_parts.append(f"Income: {income_labels.get(filters['income_tier'], filters['income_tier'])}")
        if filters.get('area_type'):
            area_labels = {
                'urban': 'Urban',
                'suburban': 'Suburban',
                'rural': 'Rural',
                'coastal_metro': 'Coastal Metro',
                'secondary_cities': 'Secondary Cities'
            }
            segment_parts.append(f"Area Type: {area_labels.get(filters['area_type'], filters['area_type'])}")
        if filters.get('beauty_archetype'):
            archetype_labels = {
                'minimalist': 'Minimalist / Low-Routine',
                'beauty_enthusiast': 'Beauty Enthusiast',
                'ingredient_obsessed': 'Ingredient-Obsessed',
                'trend_follower': 'Trend-Follower (TikTok-led)',
                'prestige_luxury': 'Prestige / Luxury Buyer',
                'value_driven': 'Value-Driven Shopper',
                'problem_solution': 'Problem-Solution Seeker'
            }
            segment_parts.append(f"Archetype: {archetype_labels.get(filters['beauty_archetype'], filters['beauty_archetype'])}")
        if filters.get('primary_motivation'):
            motivation_labels = {
                'appearance': 'Appearance / Aesthetics',
                'skin_health': 'Skin Health / Repair',
                'anti_aging': 'Anti-aging / Prevention',
                'confidence': 'Confidence / Identity',
                'experimentation': 'Experimentation / Fun',
                'value': 'Value / Price'
            }
            segment_parts.append(f"Motivation: {motivation_labels.get(filters['primary_motivation'], filters['primary_motivation'])}")

        if segment_parts:
            consumer_segment_context = f"""
=== CONSUMER SEGMENT CONTEXT ===
Target Consumer Profile: {', '.join(segment_parts)}

IMPORTANT: Use this consumer segment context to tailor your answer, but still directly answer the question asked. If the question is about categories/sub-categories, answer with specific categories/sub-categories and explain how this consumer segment's preferences affect which categories are gaining/losing importance.
"""

    prompt = f"""Context: {region} {vertical.title()} Market Analysis

Client Question: {question}
{consumer_segment_context}
Scenario Parameters:
- Price Tier Shift: {scenario_params.get('price_tier_shift', 'None')}
- Channel Shift: {scenario_params.get('channel_shift', 'None')}
- Claim Emphasis: {scenario_params.get('claim_emphasis', 'None')}
- Bundle Strategy: {scenario_params.get('bundle_vs_single', 'None')}

Pinned Markets/Brands: {len(pinned_nodes)} nodes selected

{manifold_context}

Simulation Results Summary:

Top Impacted Market Segments (Clusters):
{cluster_summary}
{shifts_summary}
{comp_summary}
{innovation_summary}

Confidence: {sim_result.confidence_score}/5
Entropy: {sim_result.entropy_score:.2f}

=== INSTRUCTIONS ===
You must provide a comprehensive consultant-grade strategic answer that:

1. **ANSWER THE QUESTION DIRECTLY** - The user's question is your PRIMARY FOCUS. Read the question carefully and structure your entire response to directly answer what was asked.

2. **If the question asks about categories/sub-categories:**
   - List specific categories and sub-categories (e.g., "face skincare", "serums", "eye products", "lip products", "fragrance", "foundation", "concealer", etc.)
   - Clearly indicate which are GAINING ↑ strategic importance and which are LOSING ↓ strategic importance
   - Explain WHY each category is gaining/losing importance
   - Use market segments (clusters) as SUPPORTING EVIDENCE - explain which clusters represent which categories
   - Tailor to consumer segment if provided - explain how this segment's preferences affect category trends

3. **If the question asks about consumer segments:**
   - Focus on consumer behavior, preferences, and decision-making
   - Map consumer segments to market segments (clusters)
   - Explain engagement patterns

4. **Structure your answer by the question type:**
   - Executive Summary: High-level direct answer to the question
   - Direct Answers: Specific, detailed answers addressing each part of the question
   - Market Map Takeaways: Use clusters as evidence to support your answer
   - Recommended Actions: Actionable steps based on your answer

5. **Use market segments (clusters) as supporting evidence, not the primary answer** - Reference clusters to support category/consumer insights, but don't make clusters the main focus unless the question specifically asks about market segments.

CRITICAL: Answer the question asked. If asked "Which categories are gaining/losing importance?", answer with specific categories and sub-categories with ↑/↓ indicators. Use consumer segment context and market clusters to enrich and support your answer, but make the question the primary focus.

Follow the JSON schema exactly."""

    return prompt


def _generate_mock_insight(
    sim_result: MarketSimResult,
    question: str,
    vertical: str,
    scenario_params: Dict
) -> Dict:
    """Generate deterministic mock insight based on simulation result."""
    # Extract key info
    top_clusters = sim_result.impacted_clusters[:3]
    cluster_labels = [c['cluster_label'] for c in top_clusters]

    # Generate mock answer based on question type
    question_lower = question.lower()

    if 'whitespace' in question_lower or 'opportunity' in question_lower:
        return _generate_whitespace_mock(sim_result, vertical, cluster_labels)
    elif 'portfolio' in question_lower or 'strategy' in question_lower:
        return _generate_portfolio_mock(sim_result, vertical, cluster_labels, scenario_params)
    else:
        return _generate_general_mock(sim_result, question, vertical, cluster_labels)


def _generate_whitespace_mock(sim_result, vertical, cluster_labels) -> Dict:
    """Generate mock whitespace analysis."""
    return {
        "title": "Market Insight: Whitespace Opportunities",
        "executive_summary": [
            f"Analysis reveals {len(cluster_labels)} key opportunity areas",
            "Functional jobs expanding beyond traditional categories",
            "Cohort preferences creating new format opportunities",
            "Whitespace exists at intersection of jobs × formats",
        ],
        "direct_answers": {
            "functional_jobs": "Mood enhancement, focus, gut health emerging as key functional jobs",
            "formats": "Drinks and powders showing growth vs traditional bars",
            "cohort_differences": "Gen Z prioritizes mood/social; Millennials focus on gut health/sleep",
        },
        "market_map_takeaways": {
            "clusters_impacted": cluster_labels,
            "rationale": "These clusters show highest whitespace potential based on simulation",
        },
        "recommended_actions": {
            "now": [
                "Launch mood-enhancing drink format targeting Gen Z",
                "Develop gut health bar with probiotics",
            ],
            "next": [
                "Test focus-enhancing powder for professionals",
                "Explore social moment formats",
            ],
            "long_term": [
                "Build functional job portfolio across formats",
            ],
        },
        "whitespace_opportunities": {
            "mood_drinks": {"description": "Mood-enhancing drinks for Gen Z", "sizing": "High"},
            "gut_bars": {"description": "Gut health bars for Millennials", "sizing": "Medium"},
        },
        "risks_and_watchouts": [
            "Regulatory scrutiny on functional claims",
            "Competition from established players",
        ],
        "assumptions": [
            "Simulation based on synthetic data",
            "Consumer preferences stable over 12-24 months",
        ],
        "evidence": [
            {"type": "cluster", "id": str(c['cluster_id']), "label": c['cluster_label']}
            for c in sim_result.impacted_clusters[:5]
        ],
        "confidence": {
            "score": sim_result.confidence_score,
            "entropy": sim_result.entropy_score,
            "rationale": f"Confidence {sim_result.confidence_score}/5 based on {len(sim_result.impacted_clusters)} impacted clusters. Entropy {sim_result.entropy_score:.2f} indicates moderate uncertainty.",
        },
        "next_questions": [
            "What specific ingredients drive mood enhancement claims?",
            "How do price points vary across functional job categories?",
        ],
    }


def _generate_portfolio_mock(sim_result, vertical, cluster_labels, scenario_params) -> Dict:
    """Generate mock portfolio strategy analysis."""
    return {
        "title": "Market Insight: Portfolio Strategy",
        "executive_summary": [
            f"{cluster_labels[0] if cluster_labels else 'Key categories'} show highest strategic importance",
            "Premium tier expanding; super-premium showing trade-up momentum",
            "Indie brands driving innovation in clean claims",
            "Luxury brands focusing on heritage positioning",
        ],
        "direct_answers": {
            "category_importance": "Serums and targeted treatments highest priority",
            "tier_evolution": "Trade-up to super-premium accelerating",
            "competitor_positioning": "Heritage brands strong in ultra-luxury; indie gaining in premium",
            "innovation_patterns": "Clean claims and new formats driving indie growth",
        },
        "market_map_takeaways": {
            "clusters_impacted": cluster_labels,
            "rationale": "These clusters represent strategic focus areas",
        },
        "recommended_actions": {
            "now": [
                "Prioritize Skincare serums in super-premium tier",
                "Launch targeted treatment format with clean claims",
            ],
            "next": [
                "Consider fragrance expansion in premium tier",
                "Test bundle strategy",
            ],
            "long_term": [
                "Build portfolio across category × tier matrix",
            ],
        },
        "whitespace_opportunities": {},
        "risks_and_watchouts": [
            "Competitor response to tier shifts",
            "Channel mix changes require supply chain adjustments",
        ],
        "assumptions": [
            "Simulation based on synthetic data",
            "Market trends continue current trajectory",
        ],
        "evidence": [
            {"type": "cluster", "id": str(c['cluster_id']), "label": c['cluster_label']}
            for c in sim_result.impacted_clusters[:5]
        ],
        "confidence": {
            "score": sim_result.confidence_score,
            "entropy": sim_result.entropy_score,
            "rationale": f"Confidence {sim_result.confidence_score}/5 based on simulation coverage. Entropy {sim_result.entropy_score:.2f} indicates moderate signal dispersion.",
        },
        "next_questions": [
            "Which specific serum sub-categories show highest growth?",
            "How do indie brand innovation patterns differ by price tier?",
        ],
    }


def _generate_general_mock(sim_result, question, vertical, cluster_labels) -> Dict:
    """Generate general mock analysis."""
    return {
        "title": f"Market Insight: {question[:50]}",
        "executive_summary": [
            f"Analysis of {len(cluster_labels)} key market clusters",
            "Simulation reveals strategic opportunities",
            "Multiple factors influencing market dynamics",
        ],
        "direct_answers": {
            "analysis": f"Based on simulation, {cluster_labels[0] if cluster_labels else 'key markets'} show highest impact",
        },
        "market_map_takeaways": {
            "clusters_impacted": cluster_labels,
            "rationale": "These clusters are most relevant to the question",
        },
        "recommended_actions": {
            "now": ["Analyze top impacted clusters", "Review competitor positioning"],
            "next": ["Develop strategic recommendations", "Test scenarios"],
            "long_term": ["Build long-term strategy"],
        },
        "whitespace_opportunities": {},
        "risks_and_watchouts": ["Simulation based on synthetic data"],
        "assumptions": ["Market conditions stable"],
        "evidence": [
            {"type": "cluster", "id": str(c['cluster_id']), "label": c['cluster_label']}
            for c in sim_result.impacted_clusters[:5]
        ],
        "confidence": {
            "score": sim_result.confidence_score,
            "entropy": sim_result.entropy_score,
            "rationale": f"Confidence {sim_result.confidence_score}/5, entropy {sim_result.entropy_score:.2f}",
        },
        "next_questions": ["What are the key drivers?", "How do segments differ?"],
    }
