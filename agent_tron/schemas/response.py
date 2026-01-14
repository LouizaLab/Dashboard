"""
Response schemas for Agent-Tron API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union


class EvidenceItem(BaseModel):
    evidence_id: str
    source_type: str
    title: Optional[str] = None
    date: Optional[str] = None
    region: Optional[str] = None
    sample_size: Optional[int] = None
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    weight: Optional[float] = None


class Uncertainty(BaseModel):
    entropy: float
    confidence: float


class DecisionSample(BaseModel):
    choice: str
    probability: float
    alternatives: Dict[str, float] = Field(default_factory=dict)


class SampledResponse(BaseModel):
    """A single sampled response from LPM"""
    sample_id: int
    choice: str
    probability: float
    seed: int


class PersonaDecisionResponse(BaseModel):
    request_id: str
    agent_id: str
    hypothesis: str

    population_prior: Dict[str, float]
    conditioned_distribution: Dict[str, float]

    sampled_decision: DecisionSample
    sampled_responses: List[SampledResponse] = Field(default_factory=list, description="Multiple samples if num_samples > 1")
    dominant_drivers: List[Dict[str, Any]] = Field(default_factory=list)

    uncertainty: Uncertainty
    ground_truth_evidence: List[EvidenceItem] = Field(default_factory=list)

    lpm_trace: Dict[str, Optional[str]] = Field(default_factory=dict)
    constraints_for_downstream_llm: Dict[str, object] = Field(default_factory=dict)


class AggregateResponse(BaseModel):
    """Executive summary aggregation"""
    agents_tested: int
    preference_breakdown: Dict[str, float]
    segment_insights: Dict[str, Dict[str, Any]]  # Dict[str, {'count': int, 'mean_preferences': Dict[str, float]}]
    top_drivers: List[Dict[str, Any]]  # List[{'product_id': str, 'weight': float}]
    overall_entropy: float
    overall_confidence: float
    evidence_coverage: Dict[str, Any]  # Dict with 'total_evidence_items', 'unique_evidence_types', 'by_type': Dict[str, int]

