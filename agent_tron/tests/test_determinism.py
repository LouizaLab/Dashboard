"""
Test determinism: same request_id + agent_id + seed → identical sampled_decision
"""

import pytest
from agent_tron.core.seeding import derive_seed


def test_seed_determinism():
    """Test that seed derivation is deterministic"""
    request_id = "req_001"
    agent_id = "agent_001"
    
    seed1 = derive_seed(request_id, agent_id)
    seed2 = derive_seed(request_id, agent_id)
    
    assert seed1 == seed2, "Seed derivation should be deterministic"


def test_seed_with_provided():
    """Test that provided seed is used directly"""
    request_id = "req_001"
    agent_id = "agent_001"
    provided_seed = 42
    
    seed = derive_seed(request_id, agent_id, provided_seed=provided_seed)
    
    assert seed == provided_seed, "Provided seed should be used directly"


def test_seed_different_agents():
    """Test that different agents get different seeds"""
    request_id = "req_001"
    agent_id1 = "agent_001"
    agent_id2 = "agent_002"
    
    seed1 = derive_seed(request_id, agent_id1)
    seed2 = derive_seed(request_id, agent_id2)
    
    assert seed1 != seed2, "Different agents should get different seeds"


def test_seed_different_requests():
    """Test that different requests get different seeds"""
    request_id1 = "req_001"
    request_id2 = "req_002"
    agent_id = "agent_001"
    
    seed1 = derive_seed(request_id1, agent_id)
    seed2 = derive_seed(request_id2, agent_id)
    
    assert seed1 != seed2, "Different requests should get different seeds"

