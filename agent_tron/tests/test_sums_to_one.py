"""
Test that distributions sum to 1 within tolerance
"""

import pytest
from agent_tron.utils.validation import validate_distribution


def test_validate_distribution_valid():
    """Test validation with valid distribution"""
    distribution = {"product_1": 0.5, "product_2": 0.5}
    assert validate_distribution(distribution) is True


def test_validate_distribution_close():
    """Test validation with distribution close to 1.0"""
    distribution = {"product_1": 0.5001, "product_2": 0.4999}
    assert validate_distribution(distribution, tolerance=0.01) is True


def test_validate_distribution_invalid():
    """Test validation fails with invalid distribution"""
    distribution = {"product_1": 0.5, "product_2": 0.3}  # Sums to 0.8
    
    with pytest.raises(ValueError, match="does not sum to 1.0"):
        validate_distribution(distribution)


def test_validate_distribution_empty():
    """Test validation with empty distribution"""
    distribution = {}
    
    with pytest.raises(ValueError):
        validate_distribution(distribution)

