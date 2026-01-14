"""
Basic tests for common utilities.

These tests verify that the scaffolding is correct.
"""

import pytest
from common import schemas, versioning, seeds


def test_data_version_generation():
    """Test data version ID generation."""
    version_id = versioning.generate_data_version(run_number=1)
    assert version_id.startswith("data_")
    assert "_run" in version_id


def test_personaset_version_generation():
    """Test PersonaSet version ID generation."""
    version = versioning.generate_personaset_version(version_number=1)
    assert version == "PersonaSet_v1"


def test_seed_manager():
    """Test seed manager determinism."""
    sm1 = seeds.SeedManager(base_seed=42)
    sm2 = seeds.SeedManager(base_seed=42)
    
    seed1 = sm1.get_seed("test_component")
    seed2 = sm2.get_seed("test_component")
    
    assert seed1 == seed2, "Seeds should be deterministic"


def test_scenario_hash():
    """Test scenario config hashing."""
    config1 = {"scenario_id": "test", "time_horizon": 12}
    config2 = {"scenario_id": "test", "time_horizon": 12}
    config3 = {"scenario_id": "test", "time_horizon": 10}
    
    hash1 = versioning.hash_scenario_config(config1)
    hash2 = versioning.hash_scenario_config(config2)
    hash3 = versioning.hash_scenario_config(config3)
    
    assert hash1 == hash2, "Identical configs should have same hash"
    assert hash1 != hash3, "Different configs should have different hashes"

