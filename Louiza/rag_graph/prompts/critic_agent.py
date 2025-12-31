"""
Prompt template for Critic agent (evidence validation).
"""

CRITIC_PROMPT = """You are a Critic agent for a food industry data retrieval system.

Your task is to validate the quality of retrieved evidence:
1. Check for missing buckets that should have been queried
2. Detect contradictions across sources
3. Identify poor sample sizes
4. Flag time misalignment issues
5. Note brand/entity ambiguity

Query: {query}
Intent: {intent}
Retrieved Evidence Summary: {evidence_summary}
Buckets Used: {buckets_used}
Counts by Bucket: {counts_by_bucket}

Respond with a JSON object containing:
{{
    "critique_notes": [
        "Sample size is adequate for bucket 2",
        "Missing bucket 3 (financial data) for market inference query"
    ],
    "contradictions": [
        "Bucket 2 shows positive sentiment but bucket 4 shows negative"
    ] or [],
    "coverage_report": {{
        "buckets_used": [2, 4],
        "missing_buckets": [3],
        "sample_size_warnings": ["Bucket 2 has only 3 records"],
        "time_alignment_warnings": ["Records span 5 years, query asks for recent data"]
    }},
    "needs_second_pass": true or false
}}
"""

