"""
Global graph state schema for LangGraph workflow.

Defines the single state object passed through the reasoning graph.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RequestConstraints(BaseModel):
    """Request constraints."""
    time_horizon_weeks: int = Field(default=12, ge=1)
    regions: List[str] = Field(default_factory=list)
    brands: List[str] = Field(default_factory=list)
    channels: List[str] = Field(default_factory=list)


class SimulationBudget(BaseModel):
    """Simulation budget constraints."""
    max_scenarios: int = Field(default=5, ge=1)
    max_runs: int = Field(default=10, ge=1)
    max_agents: int = Field(default=200000, ge=1)


class Request(BaseModel):
    """User request."""
    user_prompt: str = Field(..., description="Natural language prompt")
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)
    simulation_budget: SimulationBudget = Field(default_factory=SimulationBudget)


class Pins(BaseModel):
    """Version pins for reproducibility."""
    data_version: Optional[str] = None
    persona_version: Optional[str] = None
    ibde_version: str = Field(default="ibde_v1")
    lpm_version: str = Field(default="lpm_v1")


class AcceptanceCriteria(BaseModel):
    """Hypothesis acceptance criteria."""
    metric: str = Field(..., description="Metric to measure")
    delta_pct_min: float = Field(default=0.0, description="Minimum delta percentage")
    confidence_min: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence")


class Hypothesis(BaseModel):
    """Hypothesis definition."""
    hypothesis_id: str = Field(..., description="Unique hypothesis ID")
    statement: str = Field(..., description="Hypothesis statement")
    metrics: List[str] = Field(default_factory=lambda: ["transactions", "revenue"])
    segments: List[str] = Field(default_factory=list, description="Persona segments")
    baseline: str = Field(default="S0_baseline", description="Baseline scenario ID")
    treatment: str = Field(..., description="Treatment scenario ID")
    acceptance_criteria: List[AcceptanceCriteria] = Field(default_factory=list)


class Evidence(BaseModel):
    """Retrieved evidence."""
    retrieved_docs: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_tables: List[Dict[str, Any]] = Field(default_factory=list)
    coverage: Dict[str, Any] = Field(default_factory=dict)
    data_trust_summary: Dict[str, Any] = Field(default_factory=dict)


class Intervention(BaseModel):
    """Scenario intervention."""
    type: str = Field(..., description="Intervention type: price_change, promo, menu_launch")
    brand_id: Optional[str] = None
    region_id: Optional[str] = None
    item_id: Optional[str] = None
    delta_pct: Optional[float] = None
    intensity: Optional[float] = None
    start_week: int = Field(default=1, ge=1)
    end_week: Optional[int] = None


class ScenarioSpec(BaseModel):
    """Scenario specification."""
    scenario_id: str = Field(..., description="Unique scenario ID")
    kind: str = Field(..., description="baseline or counterfactual")
    time_horizon_weeks: int = Field(..., ge=1)
    scope: Dict[str, List[str]] = Field(default_factory=dict)
    interventions: List[Intervention] = Field(default_factory=list)


class RunArtifacts(BaseModel):
    """Run artifacts."""
    simulated_metrics_path: Optional[str] = None
    persona_contrib_path: Optional[str] = None
    plots_dir: Optional[str] = None


class Run(BaseModel):
    """Simulation run."""
    run_id: str = Field(..., description="Unique run ID")
    scenario_id: str = Field(..., description="Scenario ID")
    seed: int = Field(..., description="Random seed")
    num_agents: int = Field(..., ge=1)
    status: str = Field(default="pending", description="pending, running, completed, failed")
    artifacts: RunArtifacts = Field(default_factory=RunArtifacts)


class AnchoringState(BaseModel):
    """Anchoring state."""
    enabled: bool = Field(default=False)
    anchoring_run_id: Optional[str] = None
    status: str = Field(default="pending", description="pending, running, completed, failed")
    patch_path: Optional[str] = None
    fit_summary: Dict[str, Any] = Field(default_factory=dict)


class Analysis(BaseModel):
    """Analysis results."""
    scenario_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    uncertainty: Dict[str, Any] = Field(default_factory=dict)
    entropy: Dict[str, Any] = Field(default_factory=dict)


class FinalReport(BaseModel):
    """Final report."""
    markdown_path: Optional[str] = None
    summary: str = Field(default="")


class ReasoningState(BaseModel):
    """
    Global graph state for reasoning workflow.
    
    This is the single state object passed through the LangGraph.
    """
    request: Request = Field(..., description="User request")
    pins: Pins = Field(default_factory=Pins, description="Version pins")
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    evidence: Evidence = Field(default_factory=Evidence)
    scenario_specs: List[ScenarioSpec] = Field(default_factory=list)
    runs: List[Run] = Field(default_factory=list)
    anchoring: AnchoringState = Field(default_factory=AnchoringState)
    analysis: Analysis = Field(default_factory=Analysis)
    final_report: FinalReport = Field(default_factory=FinalReport)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    run_id: str = Field(default="", description="Overall run ID for this reasoning session")

