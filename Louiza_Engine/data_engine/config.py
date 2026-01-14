"""
Configuration schemas for synthetic data generation.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SyntheticDataConfig(BaseModel):
    """Configuration for synthetic data generation."""
    
    # Time range
    start_week: int = Field(..., description="Starting week ID")
    num_weeks: int = Field(..., ge=1, description="Number of weeks to generate")
    
    # Entity counts
    num_brands: int = Field(default=5, ge=1, description="Number of brands")
    num_regions: int = Field(default=3, ge=1, description="Number of regions")
    num_channels: int = Field(default=2, ge=1, description="Number of channels")
    num_respondents: int = Field(default=1000, ge=1, description="Number of survey respondents")
    
    # Distribution parameters
    price_base: float = Field(default=1.0, description="Base price index")
    price_volatility: float = Field(default=0.1, ge=0, description="Price volatility")
    promo_base_intensity: float = Field(default=0.3, ge=0, le=1, description="Base promo intensity")
    availability_base: float = Field(default=0.9, ge=0, le=1, description="Base availability score")
    
    # Seasonality
    seasonality_strength: float = Field(default=0.2, ge=0, description="Seasonality amplitude")
    
    # Noise parameters
    transaction_noise_level: float = Field(default=0.15, ge=0, description="Transaction noise level")
    revenue_noise_level: float = Field(default=0.2, ge=0, description="Revenue noise level")
    
    # Confidence weights
    confidence_weight_base: float = Field(default=0.8, ge=0, le=1, description="Base confidence weight")
    confidence_weight_noise: float = Field(default=0.1, ge=0, description="Confidence weight noise")
    
    # Optional interventions/shocks
    interventions: List[Dict[str, Any]] = Field(default_factory=list, description="Optional price/promo shocks")
    
    # Random seed (will be set by generator)
    seed: Optional[int] = None

