"""
Interview Data Extractor

Extracts structured data from 11 Labs interview transcripts using LLM calls.
Creates datasets compatible with Louiza Engine pipeline.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

# For LLM calls - we'll use a simple approach
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI not available, using fallback extraction")


class InterviewExtractor:
    """
    Extracts structured data from interview transcripts.
    """
    
    def __init__(self, interviews_dir: str, use_llm: bool = True):
        """
        Initialize extractor.
        
        Args:
            interviews_dir: Directory containing interview .txt files
            use_llm: Whether to use LLM for extraction (requires OpenAI API key)
        """
        self.interviews_dir = Path(interviews_dir)
        self.use_llm = use_llm and HAS_OPENAI
        
        if self.use_llm:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                print("Warning: OPENAI_API_KEY not set, using fallback extraction")
                self.use_llm = False
        
        # Storage for extracted data
        self.brands = {}
        self.regions = {}
        self.interview_data = []
        self.survey_responses = []
        self.taste_ratings = []
        self.choice_experiments = []
    
    def extract_from_interview(self, interview_file: Path) -> Dict[str, Any]:
        """
        Extract structured data from a single interview.
        
        Args:
            interview_file: Path to interview .txt file
            
        Returns:
            Dictionary with extracted data
        """
        with open(interview_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract using LLM or pattern matching
        if self.use_llm:
            return self._extract_with_llm(content, interview_file.stem)
        else:
            return self._extract_with_patterns(content, interview_file.stem)
    
    def _extract_with_llm(self, content: str, interview_id: str) -> Dict[str, Any]:
        """Extract data using LLM."""
        prompt = f"""Extract structured data from this fast-food preference interview transcript.

Interview ID: {interview_id}

Transcript:
{content[:4000]}  # Limit to avoid token limits

Extract the following information as JSON:
{{
    "respondent_id": "unique_id_for_this_interview",
    "favorite_brand": "brand_name",
    "favorite_item": "item_name",
    "brands_mentioned": ["brand1", "brand2", ...],
    "items_mentioned": [{{"brand": "brand", "item": "item", "preference_score": 0.0-1.0}}],
    "price_sensitivity": "high/medium/low",
    "promo_sensitivity": "high/medium/low",
    "region": "region_name_if_mentioned",
    "purchase_frequency": "daily/weekly/biweekly/monthly/rarely",
    "preferred_time": "breakfast/lunch/dinner/snack",
    "preferred_channel": "drive_thru/dine_in/delivery/mobile",
    "value_factors": ["taste", "price", "speed", ...],
    "price_change_response": "what_they_said_about_price_increases",
    "deal_response": "what_they_said_about_deals"
}}

Focus on extracting:
- All brand names mentioned (McDonald's, Burger King, Arby's, Wendy's, Taco Bell, etc.)
- Specific menu items mentioned
- Price sensitivity indicators
- Promotion/deal sensitivity
- Purchase patterns and frequency
- Geographic location if mentioned
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for extraction
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract structured data from interview transcripts and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._extract_with_patterns(content, interview_id)
                
        except Exception as e:
            print(f"Warning: LLM extraction failed for {interview_id}: {e}")
            return self._extract_with_patterns(content, interview_id)
    
    def _extract_with_patterns(self, content: str, interview_id: str) -> Dict[str, Any]:
        """Extract data using pattern matching (fallback)."""
        # Brand patterns
        brand_patterns = {
            "McDonald's": ["McDonald's", "McDonald", "MCD"],
            "Burger King": ["Burger King", "BK"],
            "Arby's": ["Arby's", "Arby"],
            "Wendy's": ["Wendy's", "Wendy"],
            "Taco Bell": ["Taco Bell", "TacoBell"],
            "Subway": ["Subway"],
            "KFC": ["KFC", "Kentucky Fried Chicken"],
            "Chick-fil-A": ["Chick-fil-A", "Chick fil A"],
            "Pizza Hut": ["Pizza Hut"],
            "Domino's": ["Domino's", "Dominos"],
            "Longhorn": ["Longhorn", "Longhorn Steakhouse"]
        }
        
        brands_mentioned = []
        for brand, patterns in brand_patterns.items():
            for pattern in patterns:
                if pattern.lower() in content.lower():
                    brands_mentioned.append(brand)
                    break
        
        # Extract favorite item (look for "favorite" + brand + item)
        favorite_match = re.search(r'favorite.*?(\w+).*?(\w+.*?)(?:\.|,|$)', content, re.IGNORECASE)
        favorite_brand = None
        favorite_item = None
        
        if favorite_match:
            # Try to identify brand and item
            for brand in brands_mentioned:
                if brand.lower() in content.lower()[:500]:  # Check first part
                    favorite_brand = brand
                    break
        
        # Price sensitivity indicators
        price_sensitive_keywords = ["budget", "cheaper", "price", "expensive", "cost", "money", "afford"]
        price_sensitivity = "medium"
        if any(kw in content.lower() for kw in ["tight budget", "less money", "can't afford", "too expensive"]):
            price_sensitivity = "high"
        elif any(kw in content.lower() for kw in ["worth it", "don't care about price", "price doesn't matter"]):
            price_sensitivity = "low"
        
        # Promo sensitivity
        promo_sensitive_keywords = ["deal", "promo", "coupon", "discount", "free", "app points"]
        promo_sensitivity = "medium"
        if any(kw in content.lower() for kw in ["deal", "coupon", "promo", "free item"]):
            promo_sensitivity = "high"
        
        return {
            "respondent_id": f"respondent_{interview_id}",
            "favorite_brand": favorite_brand or (brands_mentioned[0] if brands_mentioned else None),
            "favorite_item": favorite_item or "Unknown",
            "brands_mentioned": list(set(brands_mentioned)),
            "items_mentioned": [],
            "price_sensitivity": price_sensitivity,
            "promo_sensitivity": promo_sensitivity,
            "region": None,
            "purchase_frequency": "biweekly",  # Default
            "preferred_time": "lunch",
            "preferred_channel": "drive_thru",
            "value_factors": ["taste", "price"],
            "price_change_response": "",
            "deal_response": ""
        }
    
    def process_all_interviews(self) -> Dict[str, Any]:
        """Process all interview files."""
        interview_files = list(self.interviews_dir.glob("*.txt"))
        print(f"Found {len(interview_files)} interview files")
        
        for i, interview_file in enumerate(interview_files, 1):
            print(f"Processing {i}/{len(interview_files)}: {interview_file.name}")
            try:
                data = self.extract_from_interview(interview_file)
                self.interview_data.append(data)
                
                # Track brands
                for brand in data.get("brands_mentioned", []):
                    if brand not in self.brands:
                        self.brands[brand] = {
                            "name": brand,
                            "category": self._infer_category(brand)
                        }
                
            except Exception as e:
                print(f"Error processing {interview_file.name}: {e}")
        
        print(f"\n✓ Processed {len(self.interview_data)} interviews")
        print(f"✓ Found {len(self.brands)} unique brands")
        
        return {
            "interviews": self.interview_data,
            "brands": self.brands
        }
    
    def _infer_category(self, brand: str) -> str:
        """Infer brand category."""
        categories = {
            "McDonald's": "Fast Food",
            "Burger King": "Fast Food",
            "Wendy's": "Fast Food",
            "Arby's": "Fast Food",
            "Taco Bell": "Fast Food",
            "Subway": "Fast Casual",
            "KFC": "Fast Food",
            "Chick-fil-A": "Fast Food",
            "Pizza Hut": "Fast Food",
            "Domino's": "Fast Food",
            "Longhorn": "Casual Dining"
        }
        return categories.get(brand, "Fast Food")
    
    def create_brands_table(self) -> pd.DataFrame:
        """Create brands.csv."""
        brands_list = []
        for i, (brand_name, brand_info) in enumerate(self.brands.items(), 1):
            brands_list.append({
                "brand_id": f"BRAND_{i:02d}",
                "name": brand_info["name"],
                "category": brand_info["category"]
            })
        
        return pd.DataFrame(brands_list)
    
    def create_regions_table(self) -> pd.DataFrame:
        """Create regions.csv (default regions if not found in interviews)."""
        # Default US regions
        regions = [
            {"region_id": "REGION_01", "name": "US_North"},
            {"region_id": "REGION_02", "name": "US_South"},
            {"region_id": "REGION_03", "name": "US_West"},
            {"region_id": "REGION_04", "name": "US_East"},
            {"region_id": "REGION_05", "name": "US_Central"}
        ]
        return pd.DataFrame(regions)
    
    def create_survey_responses(self) -> pd.DataFrame:
        """Create survey_responses.csv from interview data."""
        responses = []
        
        for interview in self.interview_data:
            respondent_id = interview["respondent_id"]
            favorite_brand = interview.get("favorite_brand")
            
            if favorite_brand:
                # Map brand name to brand_id
                brand_id = self._get_brand_id(favorite_brand)
                if brand_id:
                    responses.append({
                        "respondent_id": respondent_id,
                        "week_id": 1,  # Default to week 1
                        "region_id": "REGION_01",  # Default
                        "brand_id": brand_id,
                        "preference_score": 0.9  # High preference for favorite
                    })
            
            # Add other mentioned brands with lower preference
            for brand in interview.get("brands_mentioned", []):
                if brand != favorite_brand:
                    brand_id = self._get_brand_id(brand)
                    if brand_id:
                        responses.append({
                            "respondent_id": respondent_id,
                            "week_id": 1,
                            "region_id": "REGION_01",
                            "brand_id": brand_id,
                            "preference_score": 0.5  # Medium preference
                        })
        
        return pd.DataFrame(responses)
    
    def _get_brand_id(self, brand_name: str) -> Optional[str]:
        """Get brand_id from brand name."""
        brands_df = self.create_brands_table()
        match = brands_df[brands_df["name"] == brand_name]
        if not match.empty:
            return match.iloc[0]["brand_id"]
        return None
    
    def get_brand_mapping(self) -> Dict[str, str]:
        """Get mapping from brand name to brand_id."""
        brands_df = self.create_brands_table()
        return dict(zip(brands_df["name"], brands_df["brand_id"]))


def fetch_brand_revenue(brand_name: str) -> Dict[str, Any]:
    """
    Fetch revenue/financial data for a brand using web search.
    
    Returns:
        Dictionary with revenue data
    """
    # This will use web_search tool
    # For now, return placeholder structure
    return {
        "brand": brand_name,
        "annual_revenue_usd": None,  # Will be filled by web search
        "quarterly_revenue_usd": None,
        "revenue_year": None
    }

