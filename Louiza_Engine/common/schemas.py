"""
Common data schemas and Pydantic models.

These schemas enforce the canonical data contracts across layers.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DataVersion(BaseModel):
    """Data version identifier."""
    version_id: str = Field(..., description="Format: data_YYYY_MM_DD_runNN")
    created_at: datetime
    generation_config: Optional[Dict[str, Any]] = None
    random_seed: Optional[int] = None


class PersonaVersion(BaseModel):
    """PersonaSet version identifier."""
    version: str = Field(..., description="Format: PersonaSet_vN")
    created_at: datetime
    data_version: str  # Links to DataVersion


class RunMetadata(BaseModel):
    """Simulation run metadata for reproducibility."""
    run_id: str
    persona_version: str
    data_version: str
    ibde_version: str
    lpm_version: str
    scenario_hash: str
    seed: int
    num_agents: int
    timesteps: int
    created_at: datetime


class CanonicalDimensions(BaseModel):
    """Canonical dimensions for all tables."""
    week_id: Optional[int] = None
    brand_id: Optional[str] = None
    region_id: Optional[str] = None
    channel_id: Optional[str] = None
    cohort_id: Optional[str] = None

