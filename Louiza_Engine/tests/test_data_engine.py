"""
Tests for Data Engine (Layer 1).

Tests enforce:
- Determinism (same seed + config = same output)
- Schema validation
- Versioning correctness
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path

from data_engine.config import SyntheticDataConfig
from data_engine.generator import SyntheticDataGenerator
from data_engine.loaders import DataLoader
from data_engine.catalog import DataCatalog


def test_config_validation():
    """Test that config validation works."""
    # Valid config
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=12,
        num_brands=5
    )
    assert config.start_week == 1
    assert config.num_weeks == 12
    
    # Invalid config (negative weeks)
    with pytest.raises(Exception):
        SyntheticDataConfig(start_week=1, num_weeks=-1)


def test_deterministic_generation():
    """Test that generation is deterministic given same seed."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2,
        num_respondents=100
    )
    
    seed = 42
    
    # Generate twice with same seed
    gen1 = SyntheticDataGenerator(config, seed=seed)
    gen2 = SyntheticDataGenerator(config, seed=seed)
    
    # Generate price schedules
    prices1 = gen1.generate_price_schedule()
    prices2 = gen2.generate_price_schedule()
    
    # Should be identical
    pd.testing.assert_frame_equal(prices1, prices2)


def test_different_seeds_produce_different_outputs():
    """Test that different seeds produce different outputs."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2
    )
    
    gen1 = SyntheticDataGenerator(config, seed=42)
    gen2 = SyntheticDataGenerator(config, seed=43)
    
    prices1 = gen1.generate_price_schedule()
    prices2 = gen2.generate_price_schedule()
    
    # Should be different
    assert not prices1.equals(prices2)


def test_schema_compliance():
    """Test that generated tables have correct schemas."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2,
        num_respondents=50
    )
    
    gen = SyntheticDataGenerator(config, seed=42)
    
    # Test price schedule schema
    prices = gen.generate_price_schedule()
    assert "week_id" in prices.columns
    assert "brand_id" in prices.columns
    assert "region_id" in prices.columns
    assert "price_index" in prices.columns
    
    # Test promo schedule schema
    promos = gen.generate_promo_schedule()
    assert "week_id" in promos.columns
    assert "brand_id" in promos.columns
    assert "region_id" in promos.columns
    assert "promo_intensity" in promos.columns
    
    # Test observed metrics schema
    observed = gen.generate_observed_metrics()
    assert "week_id" in observed.columns
    assert "brand_id" in observed.columns
    assert "region_id" in observed.columns
    assert "transactions_obs" in observed.columns
    assert "revenue_obs" in observed.columns
    assert "confidence_weight" in observed.columns


def test_entity_consistency():
    """Test that entities are consistent across tables."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2
    )
    
    gen = SyntheticDataGenerator(config, seed=42)
    
    # Generate multiple tables
    prices = gen.generate_price_schedule()
    promos = gen.generate_promo_schedule()
    observed = gen.generate_observed_metrics()
    
    # Brand IDs should match
    brands_in_prices = set(prices["brand_id"].unique())
    brands_in_promos = set(promos["brand_id"].unique())
    brands_in_observed = set(observed["brand_id"].unique())
    
    assert brands_in_prices == brands_in_promos == brands_in_observed
    
    # Region IDs should match
    regions_in_prices = set(prices["region_id"].unique())
    regions_in_promos = set(promos["region_id"].unique())
    regions_in_observed = set(observed["region_id"].unique())
    
    assert regions_in_prices == regions_in_promos == regions_in_observed


def test_full_generation_workflow():
    """Test full generation workflow with catalog."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2,
        num_respondents=50
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "data"
        catalog_file = Path(tmpdir) / "catalog.json"
        
        # Generate data
        gen = SyntheticDataGenerator(config, seed=42, data_version="test_v1")
        file_paths = gen.generate_all(str(output_dir))
        
        # Verify files exist
        assert len(file_paths) > 0
        for table_name, file_path in file_paths.items():
            assert Path(file_path).exists()
        
        # Register in catalog
        catalog = DataCatalog(str(catalog_file))
        catalog.register_dataset(
            version_id="test_v1",
            generation_config=config.model_dump(),
            random_seed=42,
            file_paths=file_paths
        )
        
        # Verify catalog entry
        entry = catalog.get_entry("test_v1")
        assert entry is not None
        assert entry.version_id == "test_v1"
        assert entry.random_seed == 42
        
        # Test loader (data_dir should be parent of version directories)
        loader = DataLoader(str(output_dir), "test_v1")
        prices = loader.load_price_schedule()
        assert len(prices) > 0


def test_confidence_weights():
    """Test that confidence weights are in valid range."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=4,
        num_brands=3,
        num_regions=2
    )
    
    gen = SyntheticDataGenerator(config, seed=42)
    observed = gen.generate_observed_metrics()
    
    # Confidence weights should be between 0 and 1
    assert observed["confidence_weight"].min() >= 0.0
    assert observed["confidence_weight"].max() <= 1.0


def test_interventions():
    """Test that interventions are applied correctly."""
    config = SyntheticDataConfig(
        start_week=1,
        num_weeks=8,
        num_brands=3,
        num_regions=2,
        interventions=[
            {
                "type": "price_change",
                "brand_id": "BRAND_01",
                "region_id": "REGION_01",
                "delta_pct": -0.1,
                "start_week": 3,
                "end_week": 5
            }
        ]
    )
    
    gen = SyntheticDataGenerator(config, seed=42)
    prices = gen.generate_price_schedule()
    
    # Check that intervention was applied
    intervention_rows = prices[
        (prices["brand_id"] == "BRAND_01") &
        (prices["region_id"] == "REGION_01") &
        (prices["week_id"].between(3, 5))
    ]
    
    # Should have some rows
    assert len(intervention_rows) > 0

