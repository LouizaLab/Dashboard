"""
Request schemas for Agent-Tron API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal


class Demographics(BaseModel):
    age_bucket: str
    gender: str
    region: str
    income: str


class Psychographics(BaseModel):
    price_sensitivity: float = Field(ge=0, le=1)
    novelty_seeking: float = Field(ge=0, le=1)
    health_consciousness: float = Field(ge=0, le=1)
    brand_loyalty: float = Field(ge=0, le=1)
    psychographic: Optional[str] = None  # For LPM compatibility


class Persona(BaseModel):
    agent_id: str
    archetype: str
    demographics: Demographics
    psychographics: Psychographics
    traits: Dict[str, float] = Field(default_factory=dict)


class Constraints(BaseModel):
    brands: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    year: Optional[int] = None


class Context(BaseModel):
    time_of_day: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    year: Optional[int] = None
    occasion: Optional[str] = None
    price_shown: Optional[float] = None
    extra: Dict[str, str] = Field(default_factory=dict)


class PersonaDecisionRequest(BaseModel):
    request_id: str
    hypothesis: str
    question_type: Literal["comparison", "what_if", "forecast", "preference"]
    time_horizon: Optional[str] = None
    persona: Persona
    constraints: Constraints = Field(default_factory=Constraints)
    context: Context = Field(default_factory=Context)
    seed: Optional[int] = None
    num_samples: Optional[int] = Field(default=1, ge=1, le=100, description="Number of samples to draw from LPM")


class BatchRequest(BaseModel):
    """Batch request for multiple personas"""
    request_id: str
    hypothesis: str
    question_type: Literal["comparison", "what_if", "forecast", "preference"]
    time_horizon: Optional[str] = None
    personas: List[Persona]
    constraints: Constraints = Field(default_factory=Constraints)
    context: Context = Field(default_factory=Context)
    seed: Optional[int] = None

