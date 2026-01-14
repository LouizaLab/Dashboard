#!/usr/bin/env python
"""
Test script to demonstrate sampling multiple responses from Agent-Tron
"""

import requests
import json
from collections import Counter


BASE_URL = "http://localhost:8001"


def test_single_sample():
    """Test single sample (default behavior)"""
    print("=" * 70)
    print("TEST 1: Single Sample (Default)")
    print("=" * 70)
    
    request_data = {
        "request_id": "single_sample_test",
        "hypothesis": "What product would this persona choose?",
        "question_type": "preference",
        "persona": {
            "agent_id": "test_agent",
            "archetype": "health_conscious",
            "demographics": {
                "age_bucket": "26-35",
                "gender": "female",
                "region": "north",
                "income": "middle"
            },
            "psychographics": {
                "price_sensitivity": 0.3,
                "novelty_seeking": 0.4,
                "health_consciousness": 0.9,
                "brand_loyalty": 0.6
            }
        },
        "context": {
            "time_of_day": "morning",
            "location": "cafe"
        },
        "seed": 42
    }
    
    response = requests.post(f"{BASE_URL}/agent_tron/persona_decision", json=request_data)
    response.raise_for_status()
    data = response.json()
    
    print(f"\n✓ Single sample received")
    print(f"  Decision: {data['sampled_decision']['choice']}")
    print(f"  Probability: {data['sampled_decision']['probability']:.4f}")
    print(f"  Number of additional samples: {len(data.get('sampled_responses', []))}")
    print()


def test_multiple_samples():
    """Test multiple samples"""
    print("=" * 70)
    print("TEST 2: Multiple Samples (num_samples=10)")
    print("=" * 70)
    
    request_data = {
        "request_id": "multi_sample_test",
        "hypothesis": "What products would this persona choose? (sample 10 times)",
        "question_type": "preference",
        "num_samples": 10,  # Request 10 samples
        "persona": {
            "agent_id": "test_agent",
            "archetype": "health_conscious",
            "demographics": {
                "age_bucket": "26-35",
                "gender": "female",
                "region": "north",
                "income": "middle"
            },
            "psychographics": {
                "price_sensitivity": 0.3,
                "novelty_seeking": 0.4,
                "health_consciousness": 0.9,
                "brand_loyalty": 0.6
            }
        },
        "context": {
            "time_of_day": "morning",
            "location": "cafe"
        },
        "seed": 42
    }
    
    response = requests.post(f"{BASE_URL}/agent_tron/persona_decision", json=request_data)
    response.raise_for_status()
    data = response.json()
    
    print(f"\n✓ Received {len(data.get('sampled_responses', []))} samples")
    print(f"\nPrimary Decision: {data['sampled_decision']['choice']} (prob: {data['sampled_decision']['probability']:.4f})")
    
    # Count occurrences of each product
    all_choices = [data['sampled_decision']['choice']]
    all_choices.extend([s['choice'] for s in data.get('sampled_responses', [])])
    choice_counts = Counter(all_choices)
    
    print(f"\nSampled Responses Distribution:")
    print(f"  Total samples: {len(all_choices)}")
    print(f"\n  Product frequencies:")
    for product, count in choice_counts.most_common(10):
        percentage = (count / len(all_choices)) * 100
        print(f"    {product}: {count} times ({percentage:.1f}%)")
    
    print(f"\n  All {len(data.get('sampled_responses', []))} samples:")
    for sample in data.get('sampled_responses', []):
        print(f"    Sample {sample['sample_id']}: {sample['choice']} (prob: {sample['probability']:.4f}, seed: {sample['seed']})")
    print()


def test_sampling_variability():
    """Test that sampling shows variability"""
    print("=" * 70)
    print("TEST 3: Sampling Variability (50 samples)")
    print("=" * 70)
    
    request_data = {
        "request_id": "variability_test",
        "hypothesis": "Sample many times to see distribution",
        "question_type": "preference",
        "num_samples": 50,
        "persona": {
            "agent_id": "test_agent",
            "archetype": "balanced",
            "demographics": {
                "age_bucket": "26-35",
                "gender": "male",
                "region": "south",
                "income": "middle"
            },
            "psychographics": {
                "price_sensitivity": 0.5,
                "novelty_seeking": 0.5,
                "health_consciousness": 0.5,
                "brand_loyalty": 0.5
            }
        },
        "context": {
            "time_of_day": "afternoon",
            "location": "store"
        }
    }
    
    response = requests.post(f"{BASE_URL}/agent_tron/persona_decision", json=request_data)
    response.raise_for_status()
    data = response.json()
    
    # Count all samples
    all_choices = [data['sampled_decision']['choice']]
    all_choices.extend([s['choice'] for s in data.get('sampled_responses', [])])
    choice_counts = Counter(all_choices)
    
    print(f"\n✓ Sampled {len(all_choices)} times")
    print(f"\nDistribution of sampled products:")
    print(f"  Unique products sampled: {len(choice_counts)}")
    print(f"\n  Top 10 most frequently sampled:")
    for i, (product, count) in enumerate(choice_counts.most_common(10), 1):
        percentage = (count / len(all_choices)) * 100
        # Get probability from conditioned distribution
        prob = data['conditioned_distribution'].get(product, 0.0)
        print(f"    {i}. {product}: {count} times ({percentage:.1f}%) [LPM prob: {prob:.4f}]")
    
    print(f"\n  Uncertainty Metrics:")
    print(f"    Entropy: {data['uncertainty']['entropy']:.4f}")
    print(f"    Confidence: {data['uncertainty']['confidence']:.4f}")
    print()


def main():
    """Run all sampling tests"""
    print("\n" + "=" * 70)
    print("  AGENT-TRON SAMPLING TEST SUITE")
    print("=" * 70)
    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the server is running: python agent_tron/run_server.py\n")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to server!")
        print("  Please start the server first:")
        print("  python agent_tron/run_server.py")
        return
    
    test_single_sample()
    test_multiple_samples()
    test_sampling_variability()
    
    print("=" * 70)
    print("  Sampling Tests Complete!")
    print("=" * 70)
    print("\nKey Points:")
    print("  • Agent-Tron samples responses from the LPM distribution")
    print("  • Use num_samples parameter to get multiple samples")
    print("  • Each sample is deterministic based on seed")
    print("  • Multiple samples show the variability in the distribution")
    print()


if __name__ == "__main__":
    main()

