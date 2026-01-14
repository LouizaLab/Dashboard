"""
Node A: ParseRequest

Extracts scope, entities, and intent from the user prompt.
"""

import re
from reasoning.state import ReasoningState


def parse_request(state: ReasoningState) -> ReasoningState:
    """
    Parse user prompt and extract structured constraints.
    
    Uses simple pattern matching for POC. Production would use LLM.
    """
    prompt = state.request.user_prompt.lower()
    
    # Extract time horizon
    time_horizon = 12  # Default
    time_matches = re.findall(r'(\d+)\s*(?:weeks?|months?)', prompt)
    if time_matches:
        time_horizon = int(time_matches[0])
        if 'month' in prompt:
            time_horizon *= 4  # Convert months to weeks
    
    # Extract regions (simple keyword matching)
    regions = []
    region_keywords = ['us_south', 'us_north', 'us_west', 'us_east', 'us_central', 'south', 'north', 'west', 'east']
    for keyword in region_keywords:
        if keyword in prompt:
            # Map to canonical region IDs
            if 'south' in keyword:
                regions.append('REGION_02')  # Assuming REGION_02 is US_South
            elif 'north' in keyword:
                regions.append('REGION_01')
            elif 'west' in keyword:
                regions.append('REGION_03')
    
    # Extract brands (simple keyword matching)
    brands = []
    brand_keywords = ['bk', 'burger king', 'mcd', 'mcdonalds', 'brand']
    for keyword in brand_keywords:
        if keyword in prompt:
            if 'bk' in keyword or 'burger king' in keyword:
                brands.append('BRAND_01')
            elif 'mcd' in keyword or 'mcdonalds' in keyword:
                brands.append('BRAND_02')
    
    # Update constraints
    state.request.constraints.time_horizon_weeks = time_horizon
    if regions:
        state.request.constraints.regions = list(set(regions))
    if brands:
        state.request.constraints.brands = list(set(brands))
    
    return state

