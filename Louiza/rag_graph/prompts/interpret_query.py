"""
Prompt template for query interpretation node.
"""

INTERPRET_QUERY_PROMPT = """You are a query interpretation system for a food industry data retrieval system.

Your task is to analyze a user query and extract:
1. Intent type (one of: sentiment_analysis, preference_discovery, demographic_comparison, behavioral_evolution, market_inference, general_query)
2. Entities: brands, segments/demographics, time ranges, metrics, keywords, attributes

Query: {query}

Respond with a JSON object containing:
{{
    "primary_intent": "intent_type",
    "intent_confidence": 0.0-1.0,
    "intent_scores": {{"intent_type": score}},
    "entities": {{
        "brands": ["brand1", "brand2"],
        "segments": ["Gen Z", "Millennial"],
        "time_range": {{"start": "2023-01-01", "end": "2024-01-01"}} or null,
        "metrics": ["revenue", "sales"],
        "keywords": ["keyword1", "keyword2"],
        "attributes": ["taste", "price", "health"]
    }}
}}
"""

