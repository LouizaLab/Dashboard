#!/usr/bin/env python
"""
Example usage of Agent-Tron API
Shows how to use Agent-Tron programmatically in your own code
"""

import requests
import json
from typing import Dict, List


class AgentTronClient:
    """Simple client for Agent-Tron API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.endpoints = {
            "persona_decision": f"{base_url}/agent_tron/persona_decision",
            "batch_decisions": f"{base_url}/agent_tron/batch_decisions",
            "aggregate": f"{base_url}/agent_tron/aggregate"
        }
    
    def get_persona_decision(
        self,
        request_id: str,
        hypothesis: str,
        persona: Dict,
        context: Dict,
        question_type: str = "preference",
        seed: int = None
    ) -> Dict:
        """
        Get decision for a single persona
        
        Args:
            request_id: Unique request identifier
            hypothesis: Hypothesis/question to answer
            persona: Persona dict with agent_id, archetype, demographics, psychographics
            context: Context dict with time_of_day, location, etc.
            question_type: One of "comparison", "what_if", "forecast", "preference"
            seed: Optional random seed for determinism
        
        Returns:
            PersonaDecisionResponse as dict
        """
        request_data = {
            "request_id": request_id,
            "hypothesis": hypothesis,
            "question_type": question_type,
            "persona": persona,
            "context": context
        }
        
        if seed is not None:
            request_data["seed"] = seed
        
        response = requests.post(
            self.endpoints["persona_decision"],
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def get_batch_decisions(
        self,
        request_id: str,
        hypothesis: str,
        personas: List[Dict],
        context: Dict,
        question_type: str = "comparison",
        seed: int = None
    ) -> List[Dict]:
        """
        Get decisions for multiple personas
        
        Args:
            request_id: Unique request identifier
            hypothesis: Hypothesis/question
            personas: List of persona dicts
            context: Shared context
            question_type: Question type
            seed: Optional seed
        
        Returns:
            List of PersonaDecisionResponse dicts
        """
        request_data = {
            "request_id": request_id,
            "hypothesis": hypothesis,
            "question_type": question_type,
            "personas": personas,
            "context": context
        }
        
        if seed is not None:
            request_data["seed"] = seed
        
        response = requests.post(
            self.endpoints["batch_decisions"],
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def aggregate_responses(self, responses: List[Dict]) -> Dict:
        """
        Aggregate multiple responses into executive summary
        
        Args:
            responses: List of PersonaDecisionResponse dicts
        
        Returns:
            AggregateResponse as dict
        """
        response = requests.post(
            self.endpoints["aggregate"],
            json=responses,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = AgentTronClient()
    
    # Example 1: Single persona decision
    print("Example 1: Single Persona Decision")
    print("-" * 50)
    
    persona = {
        "agent_id": "user_123",
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
    }
    
    context = {
        "time_of_day": "morning",
        "location": "cafe",
        "region": "north"
    }
    
    try:
        result = client.get_persona_decision(
            request_id="example_001",
            hypothesis="What product would this user prefer?",
            persona=persona,
            context=context,
            seed=42
        )
        
        print(f"Decision: {result['sampled_decision']['choice']}")
        print(f"Probability: {result['sampled_decision']['probability']:.4f}")
        print(f"Confidence: {result['uncertainty']['confidence']:.4f}")
        print(f"Entropy: {result['uncertainty']['entropy']:.4f}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the server is running: python agent_tron/run_server.py")
    
    # Example 2: Batch decisions
    print("\nExample 2: Batch Decisions")
    print("-" * 50)
    
    personas = [
        {
            "agent_id": "health_user",
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
            "agent_id": "price_user",
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
        }
    ]
    
    try:
        batch_results = client.get_batch_decisions(
            request_id="batch_example_001",
            hypothesis="Compare preferences across personas",
            personas=personas,
            context={"time_of_day": "afternoon", "location": "store"}
        )
        
        print(f"Received {len(batch_results)} responses:")
        for resp in batch_results:
            print(f"  {resp['agent_id']}: {resp['sampled_decision']['choice']} "
                  f"(prob: {resp['sampled_decision']['probability']:.4f})")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Aggregate
    print("\nExample 3: Aggregate Responses")
    print("-" * 50)
    
    try:
        if 'batch_results' in locals():
            aggregated = client.aggregate_responses(batch_results)
            print(f"Agents Tested: {aggregated['agents_tested']}")
            print(f"Overall Confidence: {aggregated['overall_confidence']:.4f}")
            print(f"Overall Entropy: {aggregated['overall_entropy']:.4f}")
            print("\nTop Preferences:")
            sorted_prefs = sorted(
                aggregated['preference_breakdown'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for product, prob in sorted_prefs:
                print(f"  {product}: {prob:.4f}")
    except Exception as e:
        print(f"Error: {e}")

