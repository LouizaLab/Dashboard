#!/usr/bin/env python
"""
Test script for Agent-Tron API
Tests all endpoints and demonstrates functionality
"""

import requests
import json
from typing import Dict, Any
import time


# Configuration
BASE_URL = "http://localhost:8001"
ENDPOINTS = {
    "root": f"{BASE_URL}/",
    "persona_decision": f"{BASE_URL}/agent_tron/persona_decision",
    "batch_decisions": f"{BASE_URL}/agent_tron/batch_decisions",
    "aggregate": f"{BASE_URL}/agent_tron/aggregate"
}


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_json(data: Dict[str, Any], indent: int = 2):
    """Pretty print JSON"""
    print(json.dumps(data, indent=indent))


def test_root_endpoint():
    """Test root endpoint"""
    print_section("TEST 1: Root Endpoint")
    try:
        response = requests.get(ENDPOINTS["root"])
        response.raise_for_status()
        data = response.json()
        print("✓ Root endpoint working!")
        print_json(data)
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_persona_decision():
    """Test single persona decision endpoint"""
    print_section("TEST 2: Single Persona Decision")
    
    request_data = {
        "request_id": "test_persona_001",
        "hypothesis": "Which product would a health-conscious persona prefer in the morning?",
        "question_type": "preference",
        "persona": {
            "agent_id": "health_agent_001",
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
            "location": "cafe",
            "region": "north"
        },
        "seed": 42
    }
    
    try:
        print("Request:")
        print_json(request_data)
        print("\nSending request...")
        
        response = requests.post(
            ENDPOINTS["persona_decision"],
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        print("\n✓ Request successful!")
        print("\nResponse Summary:")
        print(f"  Agent ID: {data['agent_id']}")
        print(f"  Hypothesis: {data['hypothesis']}")
        print(f"  Sampled Decision: {data['sampled_decision']['choice']}")
        print(f"  Probability: {data['sampled_decision']['probability']:.4f}")
        print(f"  Entropy: {data['uncertainty']['entropy']:.4f}")
        print(f"  Confidence: {data['uncertainty']['confidence']:.4f}")
        print(f"  Top 3 Alternatives:")
        for i, (product, prob) in enumerate(list(data['sampled_decision']['alternatives'].items())[:3], 1):
            print(f"    {i}. {product}: {prob:.4f}")
        
        print(f"\n  Dominant Drivers: {len(data['dominant_drivers'])} drivers")
        print(f"  Evidence Items: {len(data['ground_truth_evidence'])} items")
        
        # Validate distribution sums to ~1
        prior_sum = sum(data['population_prior'].values())
        cond_sum = sum(data['conditioned_distribution'].values())
        print(f"\n  Validation:")
        print(f"    Population Prior Sum: {prior_sum:.6f} (should be ~1.0)")
        print(f"    Conditioned Distribution Sum: {cond_sum:.6f} (should be ~1.0)")
        
        if abs(prior_sum - 1.0) < 0.01 and abs(cond_sum - 1.0) < 0.01:
            print("    ✓ Distributions are valid!")
        else:
            print("    ⚠ Warning: Distributions may not sum to 1.0")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_determinism():
    """Test that same inputs produce same outputs"""
    print_section("TEST 3: Determinism Test")
    
    request_data = {
        "request_id": "determinism_test",
        "hypothesis": "Test determinism",
        "question_type": "preference",
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
            "time_of_day": "afternoon"
        },
        "seed": 12345  # Fixed seed
    }
    
    try:
        print("Making two identical requests with same seed...")
        
        # First request
        response1 = requests.post(ENDPOINTS["persona_decision"], json=request_data)
        response1.raise_for_status()
        data1 = response1.json()
        
        time.sleep(0.5)  # Small delay
        
        # Second request (identical)
        response2 = requests.post(ENDPOINTS["persona_decision"], json=request_data)
        response2.raise_for_status()
        data2 = response2.json()
        
        # Compare results
        decision1 = data1['sampled_decision']['choice']
        decision2 = data2['sampled_decision']['choice']
        prob1 = data1['sampled_decision']['probability']
        prob2 = data2['sampled_decision']['probability']
        
        print(f"\nRequest 1 Decision: {decision1} (prob: {prob1:.6f})")
        print(f"Request 2 Decision: {decision2} (prob: {prob2:.6f})")
        
        if decision1 == decision2 and abs(prob1 - prob2) < 0.0001:
            print("\n✓ Determinism test PASSED!")
            print("  Same inputs → Same outputs")
            return True
        else:
            print("\n✗ Determinism test FAILED!")
            print("  Same inputs → Different outputs")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_batch_decisions():
    """Test batch decisions endpoint"""
    print_section("TEST 4: Batch Decisions")
    
    request_data = {
        "request_id": "batch_test_001",
        "hypothesis": "Compare preferences across different personas",
        "question_type": "comparison",
        "personas": [
            {
                "agent_id": "health_agent",
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
            {
                "agent_id": "price_agent",
                "archetype": "price_sensitive",
                "demographics": {
                    "age_bucket": "18-25",
                    "gender": "male",
                    "region": "south",
                    "income": "low"
                },
                "psychographics": {
                    "price_sensitivity": 0.9,
                    "novelty_seeking": 0.2,
                    "health_consciousness": 0.3,
                    "brand_loyalty": 0.4
                }
            },
            {
                "agent_id": "novelty_agent",
                "archetype": "novelty_seeker",
                "demographics": {
                    "age_bucket": "18-25",
                    "gender": "female",
                    "region": "east",
                    "income": "high"
                },
                "psychographics": {
                    "price_sensitivity": 0.2,
                    "novelty_seeking": 0.9,
                    "health_consciousness": 0.4,
                    "brand_loyalty": 0.3
                }
            }
        ],
        "context": {
            "time_of_day": "afternoon",
            "location": "store"
        }
    }
    
    try:
        print(f"Requesting decisions for {len(request_data['personas'])} personas...")
        
        response = requests.post(
            ENDPOINTS["batch_decisions"],
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        responses = response.json()
        
        print(f"\n✓ Received {len(responses)} responses!")
        print("\nResults Summary:")
        for i, resp in enumerate(responses, 1):
            print(f"\n  Persona {i}: {resp['agent_id']}")
            print(f"    Decision: {resp['sampled_decision']['choice']}")
            print(f"    Probability: {resp['sampled_decision']['probability']:.4f}")
            print(f"    Confidence: {resp['uncertainty']['confidence']:.4f}")
            print(f"    Entropy: {resp['uncertainty']['entropy']:.4f}")
        
        return responses
    except Exception as e:
        print(f"✗ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return None


def test_aggregate(responses):
    """Test aggregation endpoint"""
    print_section("TEST 5: Aggregate Responses")
    
    if not responses:
        print("⚠ No responses to aggregate. Skipping test.")
        return None
    
    try:
        print(f"Aggregating {len(responses)} responses...")
        
        response = requests.post(
            ENDPOINTS["aggregate"],
            json=responses,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        aggregated = response.json()
        
        print("\n✓ Aggregation successful!")
        print("\nAggregate Summary:")
        print(f"  Agents Tested: {aggregated['agents_tested']}")
        print(f"  Overall Entropy: {aggregated['overall_entropy']:.4f}")
        print(f"  Overall Confidence: {aggregated['overall_confidence']:.4f}")
        print(f"  Top 5 Preferences:")
        sorted_prefs = sorted(
            aggregated['preference_breakdown'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for i, (product, prob) in enumerate(sorted_prefs, 1):
            print(f"    {i}. {product}: {prob:.4f}")
        
        print(f"\n  Segment Insights: {len(aggregated['segment_insights'])} segments")
        for segment, data in aggregated['segment_insights'].items():
            print(f"    - {segment}: {data['count']} agents")
        
        print(f"\n  Top Drivers: {len(aggregated['top_drivers'])} drivers")
        for i, driver in enumerate(aggregated['top_drivers'][:5], 1):
            print(f"    {i}. {driver['product_id']}: {driver['weight']:.4f}")
        
        print(f"\n  Evidence Coverage:")
        print(f"    Total Items: {aggregated['evidence_coverage']['total_evidence_items']}")
        print(f"    Unique Types: {aggregated['evidence_coverage']['unique_evidence_types']}")
        
        return aggregated
    except Exception as e:
        print(f"✗ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return None


def test_different_contexts():
    """Test how context affects decisions"""
    print_section("TEST 6: Context Sensitivity")
    
    base_request = {
        "request_id": "context_test",
        "hypothesis": "How does context affect preferences?",
        "question_type": "what_if",
        "persona": {
            "agent_id": "test_context_agent",
            "archetype": "balanced",
            "demographics": {
                "age_bucket": "26-35",
                "gender": "female",
                "region": "north",
                "income": "middle"
            },
            "psychographics": {
                "price_sensitivity": 0.5,
                "novelty_seeking": 0.5,
                "health_consciousness": 0.5,
                "brand_loyalty": 0.5
            }
        },
        "seed": 999
    }
    
    contexts = [
        {"time_of_day": "morning", "location": "cafe"},
        {"time_of_day": "afternoon", "location": "store"},
        {"time_of_day": "evening", "location": "home"}
    ]
    
    try:
        print("Testing same persona with different contexts...\n")
        results = []
        
        for i, context in enumerate(contexts, 1):
            request_data = {**base_request, "context": context}
            request_data["request_id"] = f"context_test_{i}"
            
            response = requests.post(ENDPOINTS["persona_decision"], json=request_data)
            response.raise_for_status()
            data = response.json()
            
            decision = data['sampled_decision']['choice']
            prob = data['sampled_decision']['probability']
            
            print(f"  Context {i}: {context['time_of_day']} @ {context['location']}")
            print(f"    → Decision: {decision} (prob: {prob:.4f})")
            print(f"    → Confidence: {data['uncertainty']['confidence']:.4f}")
            
            results.append({
                "context": context,
                "decision": decision,
                "probability": prob
            })
        
        # Check if context affects decisions
        unique_decisions = len(set(r['decision'] for r in results))
        if unique_decisions > 1:
            print(f"\n✓ Context sensitivity confirmed!")
            print(f"  Different contexts → Different decisions ({unique_decisions} unique)")
        else:
            print(f"\n  Note: Same decision across contexts (may be expected)")
        
        return results
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  AGENT-TRON TEST SUITE")
    print("=" * 70)
    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the server is running: python agent_tron/run_server.py\n")
    
    # Check if server is running
    try:
        requests.get(ENDPOINTS["root"], timeout=2)
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to server!")
        print("  Please start the server first:")
        print("  python agent_tron/run_server.py")
        return
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return
    
    results = {}
    
    # Run tests
    results['root'] = test_root_endpoint()
    results['persona'] = test_persona_decision()
    results['determinism'] = test_determinism()
    results['batch'] = test_batch_decisions()
    
    # Aggregate if batch worked
    if results['batch']:
        results['aggregate'] = test_aggregate(results['batch'])
    
    results['context'] = test_different_contexts()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v is not False and v is not None)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print("\nStatus:")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL" if result is False else "⚠ SKIP"
        print(f"  {test_name:15} {status}")
    
    print("\n" + "=" * 70)
    print("  Testing Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

