"""
Test contracts: ensure response JSON always includes required keys
"""

import pytest
from agent_tron.schemas.response import PersonaDecisionResponse, DecisionSample, Uncertainty


def test_response_contract():
    """Test that PersonaDecisionResponse has all required fields"""
    # Create minimal valid response
    response = PersonaDecisionResponse(
        request_id="test_001",
        agent_id="agent_001",
        hypothesis="Test hypothesis",
        population_prior={"product_1": 0.5, "product_2": 0.5},
        conditioned_distribution={"product_1": 0.6, "product_2": 0.4},
        sampled_decision=DecisionSample(
            choice="product_1",
            probability=0.6,
            alternatives={"product_2": 0.4}
        ),
        dominant_drivers=[{"product_id": "product_1", "probability": 0.6}],
        uncertainty=Uncertainty(entropy=1.0, confidence=0.6),
        ground_truth_evidence=[],
        lpm_trace={},
        constraints_for_downstream_llm={}
    )
    
    # Verify all required fields exist
    assert hasattr(response, 'request_id')
    assert hasattr(response, 'agent_id')
    assert hasattr(response, 'hypothesis')
    assert hasattr(response, 'population_prior')
    assert hasattr(response, 'conditioned_distribution')
    assert hasattr(response, 'sampled_decision')
    assert hasattr(response, 'dominant_drivers')
    assert hasattr(response, 'uncertainty')
    assert hasattr(response, 'ground_truth_evidence')
    assert hasattr(response, 'lpm_trace')
    assert hasattr(response, 'constraints_for_downstream_llm')
    
    # Verify sampled_decision structure
    assert hasattr(response.sampled_decision, 'choice')
    assert hasattr(response.sampled_decision, 'probability')
    assert hasattr(response.sampled_decision, 'alternatives')
    
    # Verify uncertainty structure
    assert hasattr(response.uncertainty, 'entropy')
    assert hasattr(response.uncertainty, 'confidence')


def test_response_json_serializable():
    """Test that response can be serialized to JSON"""
    import json
    
    response = PersonaDecisionResponse(
        request_id="test_001",
        agent_id="agent_001",
        hypothesis="Test hypothesis",
        population_prior={"product_1": 0.5, "product_2": 0.5},
        conditioned_distribution={"product_1": 0.6, "product_2": 0.4},
        sampled_decision=DecisionSample(
            choice="product_1",
            probability=0.6,
            alternatives={"product_2": 0.4}
        ),
        dominant_drivers=[{"product_id": "product_1", "probability": 0.6}],
        uncertainty=Uncertainty(entropy=1.0, confidence=0.6),
        ground_truth_evidence=[],
        lpm_trace={},
        constraints_for_downstream_llm={}
    )
    
    # Should not raise exception
    json_str = response.json()
    assert isinstance(json_str, str)
    
    # Should be able to parse back
    parsed = json.loads(json_str)
    assert parsed['request_id'] == "test_001"
    assert parsed['agent_id'] == "agent_001"

