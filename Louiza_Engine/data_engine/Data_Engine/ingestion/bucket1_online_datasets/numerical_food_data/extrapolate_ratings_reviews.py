#!/usr/bin/env python3
"""
Extrapolate Ratings and Reviews for Restaurants

This script combines data from multiple CSV files in the archive folder to:
1. Join restaurant information with ratings
2. Calculate aggregated statistics (average ratings, review counts)
3. Generate comprehensive restaurant ratings and reviews dataset
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# File paths
ARCHIVE_DIR = Path(__file__).parent

def load_data():
    """Load all CSV files from the archive directory."""
    print("Loading data files...")
    
    # Load restaurant data
    restaurants = pd.read_csv(ARCHIVE_DIR / 'geoplaces2.csv')
    print(f"  ✓ Loaded {len(restaurants)} restaurants")
    
    # Load ratings
    ratings = pd.read_csv(ARCHIVE_DIR / 'rating_final.csv')
    print(f"  ✓ Loaded {len(ratings)} ratings")
    
    # Load user profiles
    users = pd.read_csv(ARCHIVE_DIR / 'userprofile.csv')
    print(f"  ✓ Loaded {len(users)} user profiles")
    
    # Load restaurant details
    cuisine = pd.read_csv(ARCHIVE_DIR / 'chefmozcuisine.csv')
    print(f"  ✓ Loaded {len(cuisine)} cuisine entries")
    
    parking = pd.read_csv(ARCHIVE_DIR / 'chefmozparking.csv')
    print(f"  ✓ Loaded {len(parking)} parking entries")
    
    payment = pd.read_csv(ARCHIVE_DIR / 'chefmozaccepts.csv')
    print(f"  ✓ Loaded {len(payment)} payment method entries")
    
    hours = pd.read_csv(ARCHIVE_DIR / 'chefmozhours4.csv')
    print(f"  ✓ Loaded {len(hours)} hours entries")
    
    return {
        'restaurants': restaurants,
        'ratings': ratings,
        'users': users,
        'cuisine': cuisine,
        'parking': parking,
        'payment': payment,
        'hours': hours
    }

def aggregate_ratings(ratings_df):
    """Aggregate ratings by restaurant (placeID)."""
    print("\nAggregating ratings...")
    
    # Group by placeID and calculate statistics
    agg_stats = ratings_df.groupby('placeID').agg({
        'rating': ['mean', 'count', 'std', 'min', 'max'],
        'food_rating': ['mean', 'std'],
        'service_rating': ['mean', 'std']
    }).round(2)
    
    # Flatten column names
    agg_stats.columns = [
        'avg_rating', 'num_reviews', 'rating_std', 'min_rating', 'max_rating',
        'avg_food_rating', 'food_rating_std',
        'avg_service_rating', 'service_rating_std'
    ]
    
    # Reset index to make placeID a column
    agg_stats = agg_stats.reset_index()
    
    # Calculate rating distribution
    rating_dist = ratings_df.groupby(['placeID', 'rating']).size().unstack(fill_value=0)
    rating_dist.columns = [f'rating_{col}' for col in rating_dist.columns]
    rating_dist = rating_dist.reset_index()
    
    # Merge distribution with aggregated stats
    agg_stats = agg_stats.merge(rating_dist, on='placeID', how='left')
    
    # Fill NaN values
    agg_stats = agg_stats.fillna(0)
    
    print(f"  ✓ Aggregated ratings for {len(agg_stats)} restaurants")
    
    return agg_stats

def enrich_restaurant_data(restaurants_df, ratings_agg, cuisine_df, parking_df, payment_df, hours_df):
    """Enrich restaurant data with ratings and additional information."""
    print("\nEnriching restaurant data...")
    
    # Merge ratings
    enriched = restaurants_df.merge(ratings_agg, on='placeID', how='left')
    
    # Add cuisine information (aggregate multiple cuisines per restaurant)
    cuisine_agg = cuisine_df.groupby('placeID')['Rcuisine'].apply(
        lambda x: ', '.join(x.unique())
    ).reset_index()
    cuisine_agg.columns = ['placeID', 'cuisines']
    enriched = enriched.merge(cuisine_agg, on='placeID', how='left')
    
    # Add parking information
    parking_agg = parking_df.groupby('placeID')['parking_lot'].apply(
        lambda x: ', '.join(x.unique())
    ).reset_index()
    parking_agg.columns = ['placeID', 'parking_options']
    enriched = enriched.merge(parking_agg, on='placeID', how='left')
    
    # Add payment methods
    payment_agg = payment_df.groupby('placeID')['Rpayment'].apply(
        lambda x: ', '.join(x.unique())
    ).reset_index()
    payment_agg.columns = ['placeID', 'payment_methods']
    enriched = enriched.merge(payment_agg, on='placeID', how='left')
    
    # Add hours information (aggregate hours by day)
    hours_agg = hours_df.groupby('placeID').apply(
        lambda x: '; '.join([f"{row['days']}: {row['hours']}" 
                            for _, row in x.iterrows()])
    ).reset_index()
    hours_agg.columns = ['placeID', 'hours']
    enriched = enriched.merge(hours_agg, on='placeID', how='left')
    
    # Fill NaN values
    enriched['num_reviews'] = enriched['num_reviews'].fillna(0).astype(int)
    enriched['avg_rating'] = enriched['avg_rating'].fillna(0)
    enriched['cuisines'] = enriched['cuisines'].fillna('Unknown')
    enriched['parking_options'] = enriched['parking_options'].fillna('Unknown')
    enriched['payment_methods'] = enriched['payment_methods'].fillna('Unknown')
    enriched['hours'] = enriched['hours'].fillna('Unknown')
    
    print(f"  ✓ Enriched data for {len(enriched)} restaurants")
    
    return enriched

def generate_review_summaries(ratings_df, restaurants_df, users_df):
    """Generate review summaries for each restaurant."""
    print("\nGenerating review summaries...")
    
    # Merge ratings with restaurant and user info
    reviews = ratings_df.merge(
        restaurants_df[['placeID', 'name']], 
        on='placeID', 
        how='left'
    )
    reviews = reviews.merge(
        users_df[['userID', 'drink_level', 'dress_preference', 'ambience', 'budget']],
        on='userID',
        how='left'
    )
    
    # Create review summaries by restaurant
    summaries = []
    
    for place_id in reviews['placeID'].unique():
        restaurant_reviews = reviews[reviews['placeID'] == place_id]
        restaurant_name = restaurant_reviews['name'].iloc[0]
        
        # Calculate statistics
        total_reviews = len(restaurant_reviews)
        avg_rating = restaurant_reviews['rating'].mean()
        avg_food = restaurant_reviews['food_rating'].mean()
        avg_service = restaurant_reviews['service_rating'].mean()
        
        # Rating distribution
        rating_dist = restaurant_reviews['rating'].value_counts().to_dict()
        
        # User preferences analysis
        drink_levels = restaurant_reviews['drink_level'].value_counts().to_dict()
        dress_prefs = restaurant_reviews['dress_preference'].value_counts().to_dict()
        ambience_prefs = restaurant_reviews['ambience'].value_counts().to_dict()
        budgets = restaurant_reviews['budget'].value_counts().to_dict()
        
        summary = {
            'placeID': place_id,
            'restaurant_name': restaurant_name,
            'total_reviews': int(total_reviews),
            'average_rating': round(avg_rating, 2),
            'average_food_rating': round(avg_food, 2),
            'average_service_rating': round(avg_service, 2),
            'rating_distribution': rating_dist,
            'reviewer_drink_levels': drink_levels,
            'reviewer_dress_preferences': dress_prefs,
            'reviewer_ambience_preferences': ambience_prefs,
            'reviewer_budgets': budgets
        }
        
        summaries.append(summary)
    
    summaries_df = pd.DataFrame(summaries)
    print(f"  ✓ Generated summaries for {len(summaries_df)} restaurants")
    
    return summaries_df

def calculate_rating_insights(enriched_df):
    """Calculate additional insights and metrics."""
    print("\nCalculating insights...")
    
    # Add rating category
    enriched_df['rating_category'] = enriched_df['avg_rating'].apply(
        lambda x: 'Excellent' if x >= 1.8 else ('Good' if x >= 1.3 else ('Fair' if x >= 0.7 else 'Poor'))
    )
    
    # Add review volume category
    enriched_df['review_volume'] = enriched_df['num_reviews'].apply(
        lambda x: 'High' if x >= 20 else ('Medium' if x >= 10 else ('Low' if x >= 1 else 'No Reviews'))
    )
    
    # Calculate rating consistency (lower std = more consistent)
    enriched_df['rating_consistency'] = enriched_df['rating_std'].apply(
        lambda x: 'Very Consistent' if x <= 0.3 else ('Consistent' if x <= 0.6 else ('Variable' if x <= 1.0 else 'Highly Variable'))
    )
    
    # Calculate overall score (weighted average)
    enriched_df['overall_score'] = (
        enriched_df['avg_rating'] * 0.5 +
        enriched_df['avg_food_rating'] * 0.3 +
        enriched_df['avg_service_rating'] * 0.2
    ).round(2)
    
    print("  ✓ Calculated insights and metrics")
    
    return enriched_df

def main():
    """Main function to extrapolate ratings and reviews."""
    print("="*70)
    print("Restaurant Ratings and Reviews Extrapolation")
    print("="*70)
    
    # Load data
    data = load_data()
    
    # Aggregate ratings
    ratings_agg = aggregate_ratings(data['ratings'])
    
    # Enrich restaurant data
    enriched = enrich_restaurant_data(
        data['restaurants'],
        ratings_agg,
        data['cuisine'],
        data['parking'],
        data['payment'],
        data['hours']
    )
    
    # Generate review summaries
    summaries = generate_review_summaries(
        data['ratings'],
        data['restaurants'],
        data['users']
    )
    
    # Calculate insights
    enriched = calculate_rating_insights(enriched)
    
    # Select and order columns for output
    output_columns = [
        'placeID', 'name', 'city', 'state', 'country',
        'num_reviews', 'avg_rating', 'avg_food_rating', 'avg_service_rating',
        'overall_score', 'rating_category', 'review_volume', 'rating_consistency',
        'rating_0', 'rating_1', 'rating_2',
        'min_rating', 'max_rating', 'rating_std',
        'cuisines', 'price', 'alcohol', 'smoking_area', 'dress_code',
        'parking_options', 'payment_methods', 'hours',
        'latitude', 'longitude', 'address', 'url'
    ]
    
    # Filter to available columns
    available_columns = [col for col in output_columns if col in enriched.columns]
    output_df = enriched[available_columns].copy()
    
    # Sort by overall score (descending) and number of reviews
    output_df = output_df.sort_values(
        ['overall_score', 'num_reviews'], 
        ascending=[False, False]
    )
    
    # Save results
    output_file = ARCHIVE_DIR / 'restaurant_ratings_reviews.csv'
    output_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved results to: {output_file}")
    print(f"  Total restaurants: {len(output_df)}")
    print(f"  Restaurants with reviews: {len(output_df[output_df['num_reviews'] > 0])}")
    
    # Save summaries
    summaries_file = ARCHIVE_DIR / 'restaurant_review_summaries.csv'
    summaries.to_csv(summaries_file, index=False)
    print(f"✓ Saved summaries to: {summaries_file}")
    
    # Print statistics
    print("\n" + "="*70)
    print("Statistics")
    print("="*70)
    print(f"Total restaurants: {len(output_df)}")
    print(f"Restaurants with reviews: {len(output_df[output_df['num_reviews'] > 0])}")
    print(f"Average rating (all restaurants): {output_df['avg_rating'].mean():.2f}")
    print(f"Average rating (with reviews): {output_df[output_df['num_reviews'] > 0]['avg_rating'].mean():.2f}")
    print(f"Total reviews: {output_df['num_reviews'].sum()}")
    print(f"\nTop 10 Restaurants by Overall Score:")
    print(output_df.head(10)[['name', 'city', 'avg_rating', 'num_reviews', 'overall_score', 'rating_category']].to_string(index=False))
    
    print("\n" + "="*70)
    print("EXTRAPOLATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()

