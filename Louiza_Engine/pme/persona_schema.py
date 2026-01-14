"""
Persona JSON schema definitions.

This module enforces the authoritative persona contract used by IBDE, LPM, and Anchoring.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import numpy as np


class PopulationWeight(BaseModel):
    """Population weight configuration."""
    global_weight: float = Field(..., ge=0.0, le=1.0, description="Global population fraction")
    by_region: Dict[str, float] = Field(default_factory=dict, description="Region-specific weights")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "global": 0.14,
                "by_region": {"US_South": 0.21}
            }
        }
    
    @validator("by_region")
    def validate_region_weights(cls, v):
        """Ensure region weights are in valid range."""
        for region, weight in v.items():
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"Region weight must be in [0, 1]: {region}={weight}")
        return v


class BehavioralParams(BaseModel):
    """Behavioral parameters used by IBDE."""
    price_sensitivity: float = Field(..., ge=0.0, description="Price sensitivity coefficient")
    promo_responsiveness: float = Field(..., ge=0.0, description="Promotion responsiveness")
    habit_strength: float = Field(..., ge=0.0, description="Habit strength (state inertia)")
    brand_loyalty_bias: float = Field(..., ge=0.0, description="Brand loyalty bias coefficient")
    choice_noise: float = Field(..., ge=0.0, le=1.0, description="Choice noise level")


class TasteEmbedding(BaseModel):
    """Taste embedding distribution parameters."""
    mean: List[float] = Field(..., description="Mean vector")
    cov: List[List[float]] = Field(..., description="Covariance matrix")
    
    @validator("cov")
    def validate_covariance(cls, v, values):
        """Validate covariance matrix is square and matches mean dimension."""
        if "mean" in values:
            mean_dim = len(values["mean"])
            if len(v) != mean_dim:
                raise ValueError(f"Covariance matrix rows ({len(v)}) must match mean dimension ({mean_dim})")
            for row in v:
                if len(row) != mean_dim:
                    raise ValueError(f"Covariance matrix must be square")
        return v


class StatePriors(BaseModel):
    """State prior distributions for agent initialization."""
    taste_embedding: TasteEmbedding = Field(..., description="Taste embedding distribution")


class FeatureGates(BaseModel):
    """Feature gating parameters for IBDE."""
    health_signal: float = Field(default=0.5, ge=0.0, le=1.0, description="Health signal gate")
    convenience_signal: float = Field(default=0.5, ge=0.0, le=1.0, description="Convenience signal gate")
    promo_signal: float = Field(default=1.0, ge=0.0, le=1.0, description="Promo signal gate")
    advertising_signal: float = Field(default=0.5, ge=0.0, le=1.0, description="Advertising signal gate")


class InteractionEffects(BaseModel):
    """Interaction effect parameters."""
    price_x_loyalty: float = Field(default=0.0, description="Price × loyalty interaction")
    promo_x_habit: float = Field(default=0.0, description="Promo × habit interaction")


class Constraints(BaseModel):
    """Behavioral constraints."""
    max_price_tolerance: float = Field(default=2.0, ge=1.0, description="Maximum price tolerance multiplier")
    min_repeat_interval_days: int = Field(default=1, ge=0, description="Minimum days between purchases")


class CalibrationHooks(BaseModel):
    """Calibration hooks for anchoring."""
    anchor_targets: List[str] = Field(default_factory=lambda: ["transactions", "revenue"], description="Target metrics")
    adjustable_params: List[str] = Field(default_factory=lambda: ["population_weight.global"], description="Adjustable parameters")
    regularization_strength: float = Field(default=0.1, ge=0.0, description="Regularization strength")


class Diagnostics(BaseModel):
    """Persona diagnostics."""
    fit_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Fit score")
    residual_explained: float = Field(default=0.0, ge=0.0, le=1.0, description="Residual variance explained")
    stability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Stability score")


class Lineage(BaseModel):
    """Persona lineage metadata."""
    parent_personas: List[str] = Field(default_factory=list, description="Parent persona IDs")
    creation_reason: str = Field(default="", description="Reason for creation")
    data_version: str = Field(..., description="Data version used")
    pme_run_id: str = Field(default="", description="PME run ID")


class Explainability(BaseModel):
    """Explainability metadata."""
    human_label: str = Field(..., description="Human-readable label")
    dominant_drivers: List[str] = Field(default_factory=list, description="Dominant behavioral drivers")


class Persona(BaseModel):
    """
    Persona definition schema.
    
    This is the authoritative contract for personas used by IBDE, LPM, and Anchoring.
    """
    persona_id: str = Field(..., description="Unique persona identifier")
    version: str = Field(default="v1.0", description="Persona definition version")
    status: str = Field(default="active", description="Status: active | shadow | deprecated")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    population_weight: PopulationWeight = Field(..., description="Population weight configuration")
    behavioral_params: BehavioralParams = Field(..., description="Behavioral parameters")
    state_priors: StatePriors = Field(..., description="State prior distributions")
    feature_gates: FeatureGates = Field(default_factory=FeatureGates, description="Feature gates")
    interaction_effects: InteractionEffects = Field(default_factory=InteractionEffects, description="Interaction effects")
    constraints: Constraints = Field(default_factory=Constraints, description="Behavioral constraints")
    calibration_hooks: CalibrationHooks = Field(default_factory=CalibrationHooks, description="Calibration hooks")
    diagnostics: Diagnostics = Field(default_factory=Diagnostics, description="Diagnostics")
    lineage: Lineage = Field(..., description="Lineage metadata")
    explainability: Explainability = Field(..., description="Explainability metadata")
    
    @validator("status")
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed = {"active", "shadow", "deprecated"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}, got {v}")
        return v
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            np.ndarray: lambda v: v.tolist()
        }


class PersonaSet(BaseModel):
    """
    PersonaSet container.
    
    Contains multiple personas and metadata.
    """
    version: str = Field(..., description="PersonaSet version (e.g., PersonaSet_v1)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    data_version: str = Field(..., description="Data version used")
    pme_run_id: str = Field(default="", description="PME run ID")
    
    personas: List[Persona] = Field(..., description="List of personas")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("personas")
    def validate_personas(cls, v):
        """Validate persona set constraints."""
        if len(v) == 0:
            raise ValueError("PersonaSet must contain at least one persona")
        
        # Check for duplicate persona IDs
        persona_ids = [p.persona_id for p in v]
        if len(persona_ids) != len(set(persona_ids)):
            raise ValueError("Duplicate persona IDs found")
        
        # Validate population weights sum to 1.0 (approximately)
        global_weights = [p.population_weight.global_weight for p in v if p.status == "active"]
        if global_weights:
            total_weight = sum(global_weights)
            if not 0.99 <= total_weight <= 1.01:  # Allow small floating point errors
                raise ValueError(f"Active persona global weights must sum to 1.0, got {total_weight}")
        
        return v
    
    def get_active_personas(self) -> List[Persona]:
        """Get only active personas."""
        return [p for p in self.personas if p.status == "active"]
    
    def get_persona_by_id(self, persona_id: str) -> Optional[Persona]:
        """Get persona by ID."""
        for persona in self.personas:
            if persona.persona_id == persona_id:
                return persona
        return None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

