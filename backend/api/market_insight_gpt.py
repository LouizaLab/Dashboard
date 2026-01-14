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
        sim_result, question, vertical, region, pinned_nodes, scenario_params, manifold_data
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
    return """You are Louiza Market Insight, a consultant-grade strategist. You convert market manifold data and simulation outputs into clear strategic recommendations.

Your role:
- Analyze market manifold structure (clusters, spatial relationships, cluster characteristics)
- Convert simulation data AND manifold cluster data into consultant-grade insights
- Reference specific clusters by name and their characteristics (claims, tiers, channels, categories)
- Explain spatial relationships between clusters and what they mean strategically
- Be explicit about assumptions and uncertainty
- Do NOT invent data outside the provided manifold and simulation payload
- Ground all recommendations in the actual cluster structure and characteristics
- Output STRICT JSON that matches the given schema—no markdown, no commentary

Output format (strict JSON schema):
{
  "title": "string",
  "executive_summary": ["bullet 1", "bullet 2", ...],
  "direct_answers": {
    "sub_question_1": "comprehensive answer referencing specific clusters",
    "sub_question_2": "comprehensive answer referencing specific clusters"
  },
  "market_map_takeaways": {
    "clusters_impacted": ["specific cluster name 1", "specific cluster name 2"],
    "cluster_relationships": "explanation of spatial relationships between clusters",
    "cluster_characteristics": "summary of key cluster attributes (claims, tiers, channels)",
    "rationale": "why these clusters matter based on manifold structure"
  },
  "recommended_actions": {
    "now": ["action 1", "action 2"],
    "next": ["action 3", "action 4"],
    "long_term": ["action 5"]
  },
  "whitespace_opportunities": {
    "opportunity_1": {"description": "...", "sizing": "..."}
  },
  "risks_and_watchouts": ["risk 1", "risk 2"],
  "assumptions": ["assumption 1", "assumption 2"],
  "evidence": [
    {"type": "cluster", "id": "...", "label": "..."}
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
    
    prompt = f"""Context: {region} {vertical.title()} Market Analysis

Client Question: {question}

Scenario Parameters:
- Price Tier Shift: {scenario_params.get('price_tier_shift', 'None')}
- Channel Shift: {scenario_params.get('channel_shift', 'None')}
- Claim Emphasis: {scenario_params.get('claim_emphasis', 'None')}
- Bundle Strategy: {scenario_params.get('bundle_vs_single', 'None')}

Pinned Markets/Brands: {len(pinned_nodes)} nodes selected

{manifold_context}

Simulation Results Summary:

Top Impacted Clusters:
{cluster_summary}
{shifts_summary}
{comp_summary}
{innovation_summary}

Confidence: {sim_result.confidence_score}/5
Entropy: {sim_result.entropy_score:.2f}

=== INSTRUCTIONS ===
You must provide a comprehensive consultant-grade strategic answer that:

1. **Directly answers the question** using the manifold cluster data and simulation results
2. **References specific clusters** by name (e.g., "Clean Indie Skincare cluster", "Clinical Derm Skincare cluster")
3. **Explains spatial relationships** - which clusters are adjacent, which are distant, and what that means strategically
4. **Uses cluster drivers** - reference the claims, tiers, channels, and categories from the manifold clusters
5. **Provides actionable recommendations** grounded in the actual cluster structure
6. **Explains market dynamics** - how clusters interact, where whitespace exists between clusters
7. **Quantifies opportunities** - use cluster sizes and counts to size opportunities
8. **Addresses uncertainty** - be explicit about what the manifold data tells us vs. what requires more research

CRITICAL: Your answer must be grounded in the manifold cluster data provided above. Reference specific cluster names, their characteristics (claims, tiers, channels), and their relationships to each other.

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
