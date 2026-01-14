#!/usr/bin/env python3
"""
Main script to extract data from interviews and create Louiza Engine datasets.

Usage:
    python data_engine/interview_to_dataset.py --output-version data_2026_01_15_interviews01
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_engine.interview_extractor import InterviewExtractor


def fetch_brand_financials(brand_name: str) -> Dict[str, Any]:
    """
    Fetch financial data for a brand using web search.
    
    Args:
        brand_name: Brand name (e.g., "McDonald's")
        
    Returns:
        Dictionary with financial data
    """
    print(f"  Searching for {brand_name} revenue data...")
    
    # Use web_search tool directly (available in this environment)
    search_results = None
    try:
        # Use the web_search tool available in this environment
        from web_search import web_search
        search_query = f"{brand_name} annual revenue 2024 2023 financial data"
        search_results = web_search(search_query)
    except (ImportError, NameError):
        # web_search not available, will use known data
        pass
    
    # Extract revenue from search results
    revenue = None
    revenue_year = None
    
    # Known revenue data (fallback if web search doesn't work)
    known_revenues = {
        "McDonald's": 25.5e9,  # ~$25.5B annually
        "Burger King": 1.9e9,  # ~$1.9B annually
        "Wendy's": 2.1e9,  # ~$2.1B annually
        "Arby's": 0.4e9,  # ~$400M annually
        "Taco Bell": 14.0e9,  # ~$14B annually
        "Subway": 9.4e9,  # ~$9.4B annually
        "KFC": 6.8e9,  # ~$6.8B annually
        "Chick-fil-A": 18.8e9,  # ~$18.8B annually
        "Pizza Hut": 5.8e9,  # ~$5.8B annually
        "Domino's": 4.5e9,  # ~$4.5B annually
        "Longhorn": 1.2e9,  # ~$1.2B annually (Darden Restaurants)
    }
    
    # Try to extract from web search results
    import re
    if search_results:
        # Look through search results for revenue numbers
        results_list = search_results if isinstance(search_results, list) else search_results.get("results", [])
        for result in results_list[:5]:
            if isinstance(result, dict):
                snippet = result.get("snippet", "").lower()
            else:
                snippet = str(result).lower()
            # Look for billion/million patterns
            billion_match = re.search(r'(\d+\.?\d*)\s*billion', snippet)
            if billion_match:
                revenue = float(billion_match.group(1)) * 1e9
                # Try to find year
                year_match = re.search(r'20\d{2}', snippet)
                if year_match:
                    revenue_year = int(year_match.group(0))
                break
    
    # Use known data if web search didn't find anything
    if revenue is None and brand_name in known_revenues:
        revenue = known_revenues[brand_name]
        revenue_year = 2023
        print(f"    Using known revenue data: ${revenue/1e9:.1f}B")
    elif revenue is None:
        # Estimate based on market position
        revenue = 2.0e9  # Default estimate
        revenue_year = 2023
        print(f"    Using estimated revenue: ${revenue/1e9:.1f}B")
    
    return {
        "brand": brand_name,
        "annual_revenue_usd": revenue,
        "revenue_year": revenue_year or 2023,
        "source": "web_search" if revenue and brand_name not in known_revenues else "known_data"
    }


def create_observed_metrics_from_interviews(
    interviews_data: List[Dict],
    brands_mapping: Dict[str, str],
    num_weeks: int = 12
) -> pd.DataFrame:
    """
    Create observed_metrics_brand_week_region.csv from interview data.
    
    Uses brand revenue data and interview frequency to estimate transactions.
    """
    # Fetch revenue data for all brands
    brand_revenues = {}
    for brand_name in brands_mapping.keys():
        financials = fetch_brand_financials(brand_name)
        brand_revenues[brand_name] = financials
    
    # Estimate transactions from revenue and interview data
    # More mentions = higher market share = more transactions
    brand_mentions = {}
    for interview in interviews_data:
        for brand in interview.get("brands_mentioned", []):
            brand_mentions[brand] = brand_mentions.get(brand, 0) + 1
    
    # Normalize mentions to get market share estimate
    total_mentions = sum(brand_mentions.values())
    market_shares = {brand: count / total_mentions for brand, count in brand_mentions.items()}
    
    # Create observed metrics
    rows = []
    regions = ["REGION_01", "REGION_02", "REGION_03"]
    
    for week_id in range(1, num_weeks + 1):
        for brand_name, brand_id in brands_mapping.items():
            for region_id in regions:
                # Estimate transactions based on market share and revenue
                market_share = market_shares.get(brand_name, 0.1)
                annual_revenue = brand_revenues[brand_name].get("annual_revenue_usd")
                
                if annual_revenue:
                    # Estimate weekly transactions
                    # Assume average transaction value of $10
                    weekly_revenue = (annual_revenue * market_share) / 52
                    transactions = weekly_revenue / 10.0  # $10 per transaction
                    revenue = weekly_revenue
                else:
                    # Fallback: use market share to estimate
                    base_transactions = 10000 * market_share
                    transactions = base_transactions * (0.8 + 0.4 * np.random.random())
                    revenue = transactions * 10.0
                
                # Add some week-to-week variation
                week_variation = 0.9 + 0.2 * np.sin(week_id * 0.5) + 0.1 * np.random.random()
                transactions *= week_variation
                revenue *= week_variation
                
                rows.append({
                    "week_id": week_id,
                    "brand_id": brand_id,
                    "region_id": region_id,
                    "transactions_obs": round(transactions, 2),
                    "revenue_obs": round(revenue, 2),
                    "confidence_weight": 0.8  # Medium confidence for estimated data
                })
    
    return pd.DataFrame(rows)


def create_price_schedule(
    brands_mapping: Dict[str, str],
    num_weeks: int = 12
) -> pd.DataFrame:
    """Create brand_price_schedule.csv with realistic price variations."""
    rows = []
    regions = ["REGION_01", "REGION_02", "REGION_03"]
    
    for week_id in range(1, num_weeks + 1):
        for brand_id in brands_mapping.values():
            for region_id in regions:
                # Base price index = 1.0, with small variations
                price_index = 1.0 + np.random.normal(0, 0.05)
                price_index = max(0.8, min(1.2, price_index))  # Clamp to reasonable range
                
                rows.append({
                    "week_id": week_id,
                    "brand_id": brand_id,
                    "region_id": region_id,
                    "price_index": round(price_index, 4)
                })
    
    return pd.DataFrame(rows)


def create_promo_schedule(
    interviews_data: List[Dict],
    brands_mapping: Dict[str, str],
    num_weeks: int = 12
) -> pd.DataFrame:
    """Create brand_promo_schedule.csv based on promo sensitivity from interviews."""
    # Calculate average promo sensitivity per brand
    brand_promo_sensitivity = {}
    for interview in interviews_data:
        for brand in interview.get("brands_mentioned", []):
            if brand not in brand_promo_sensitivity:
                brand_promo_sensitivity[brand] = []
            
            promo_sens = interview.get("promo_sensitivity", "medium")
            score = {"high": 0.7, "medium": 0.4, "low": 0.2}.get(promo_sens, 0.4)
            brand_promo_sensitivity[brand].append(score)
    
    # Average promo intensity per brand
    brand_avg_promo = {
        brand: np.mean(scores) if scores else 0.3
        for brand, scores in brand_promo_sensitivity.items()
    }
    
    rows = []
    regions = ["REGION_01", "REGION_02", "REGION_03"]
    
    for week_id in range(1, num_weeks + 1):
        for brand_name, brand_id in brands_mapping.items():
            for region_id in regions:
                # Base promo intensity from interview data
                base_intensity = brand_avg_promo.get(brand_name, 0.3)
                
                # Add week-to-week variation
                promo_intensity = base_intensity * (0.5 + 0.5 * np.random.random())
                promo_intensity = max(0.0, min(1.0, promo_intensity))
                
                rows.append({
                    "week_id": week_id,
                    "brand_id": brand_id,
                    "region_id": region_id,
                    "promo_intensity": round(promo_intensity, 4)
                })
    
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Extract data from interviews and create Louiza Engine datasets"
    )
    parser.add_argument(
        "--interviews-dir",
        type=str,
        default="data_engine/11_labs_interviews",
        help="Directory containing interview .txt files"
    )
    parser.add_argument(
        "--output-version",
        type=str,
        required=True,
        help="Output data version ID (e.g., data_2026_01_15_interviews01)"
    )
    parser.add_argument(
        "--num-weeks",
        type=int,
        default=12,
        help="Number of weeks to generate data for"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for extraction (requires OPENAI_API_KEY)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Interview Data Extraction")
    print("="*60)
    print(f"Interviews directory: {args.interviews_dir}")
    print(f"Output version: {args.output_version}")
    print(f"Number of weeks: {args.num_weeks}")
    print()
    
    # Initialize extractor
    extractor = InterviewExtractor(args.interviews_dir, use_llm=args.use_llm)
    
    # Process all interviews
    print("Step 1: Processing interviews...")
    extraction_results = extractor.process_all_interviews()
    
    interviews_data = extraction_results["interviews"]
    brands_mapping = extractor.get_brand_mapping()
    
    print(f"\n✓ Extracted data from {len(interviews_data)} interviews")
    print(f"✓ Found {len(brands_mapping)} brands: {list(brands_mapping.keys())}")
    
    # Create output directory
    output_dir = Path("data/synthetic") / args.output_version
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nStep 2: Creating datasets in {output_dir}...")
    
    # Create brands table
    print("  Creating brands.csv...")
    brands_df = extractor.create_brands_table()
    brands_df.to_csv(output_dir / "brands.csv", index=False)
    print(f"    ✓ {len(brands_df)} brands")
    
    # Create regions table
    print("  Creating regions.csv...")
    regions_df = extractor.create_regions_table()
    regions_df.to_csv(output_dir / "regions.csv", index=False)
    print(f"    ✓ {len(regions_df)} regions")
    
    # Create observed metrics (with web search for revenue)
    print("  Creating observed_metrics_brand_week_region.csv...")
    print("    Fetching brand revenue data from web...")
    observed_metrics_df = create_observed_metrics_from_interviews(
        interviews_data, brands_mapping, num_weeks=args.num_weeks
    )
    observed_metrics_df.to_csv(output_dir / "observed_metrics_brand_week_region.csv", index=False)
    print(f"    ✓ {len(observed_metrics_df)} rows")
    
    # Create price schedule
    print("  Creating brand_price_schedule.csv...")
    price_schedule_df = create_price_schedule(brands_mapping, num_weeks=args.num_weeks)
    price_schedule_df.to_csv(output_dir / "brand_price_schedule.csv", index=False)
    print(f"    ✓ {len(price_schedule_df)} rows")
    
    # Create promo schedule
    print("  Creating brand_promo_schedule.csv...")
    promo_schedule_df = create_promo_schedule(
        interviews_data, brands_mapping, num_weeks=args.num_weeks
    )
    promo_schedule_df.to_csv(output_dir / "brand_promo_schedule.csv", index=False)
    print(f"    ✓ {len(promo_schedule_df)} rows")
    
    # Create survey responses
    print("  Creating survey_responses.csv...")
    survey_responses_df = extractor.create_survey_responses()
    survey_responses_df.to_csv(output_dir / "survey_responses.csv", index=False)
    print(f"    ✓ {len(survey_responses_df)} rows")
    
    # Create menu availability (default)
    print("  Creating brand_menu_availability.csv...")
    menu_availability_rows = []
    for week_id in range(1, args.num_weeks + 1):
        for brand_id in brands_mapping.values():
            for region_id in regions_df["region_id"]:
                menu_availability_rows.append({
                    "week_id": week_id,
                    "brand_id": brand_id,
                    "region_id": region_id,
                    "availability_score": 0.95  # Default high availability
                })
    menu_availability_df = pd.DataFrame(menu_availability_rows)
    menu_availability_df.to_csv(output_dir / "brand_menu_availability.csv", index=False)
    print(f"    ✓ {len(menu_availability_df)} rows")
    
    # Save extraction metadata
    metadata = {
        "data_version": args.output_version,
        "created_at": datetime.now().isoformat(),
        "source": "11_labs_interviews",
        "num_interviews": len(interviews_data),
        "num_brands": len(brands_mapping),
        "num_weeks": args.num_weeks,
        "brands": list(brands_mapping.keys()),
        "extraction_method": "llm" if args.use_llm else "pattern_matching"
    }
    
    with open(output_dir / "extraction_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*60)
    print("✓ Extraction Complete!")
    print("="*60)
    print(f"\nData version: {args.output_version}")
    print(f"Location: {output_dir}")
    print(f"\nFiles created:")
    for csv_file in sorted(output_dir.glob("*.csv")):
        df = pd.read_csv(csv_file)
        print(f"  - {csv_file.name}: {len(df)} rows")
    
    print(f"\n📋 Next steps:")
    print(f"  1. Validate: python3 scripts/validate_custom_data.py {args.output_version}")
    print(f"  2. Run simulation: python3 scripts/run_simulation.py --data-version {args.output_version} ...")
    print(f"  3. Run anchoring: python3 scripts/run_anchoring.py --observed-data {output_dir}/observed_metrics_brand_week_region.csv ...")

if __name__ == "__main__":
    main()

