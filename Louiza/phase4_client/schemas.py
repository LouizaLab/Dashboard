"""
Phase-4 Anchor Request/Response Schemas

Defines the JSON I/O contract for Phase-4 integration.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AnchorRequest:
    """
    Request to Phase-4 anchoring service.
    
    This defines the stable JSON contract for interoperability
    between the RAG system and Phase-4 codebase.
    """
    
    query: str
    retrieved_evidence_summary: str  # Summary of retrieved evidence with citations
    structured_aggregates: Optional[Dict[str, Any]] = None  # Aggregated metrics, counts, etc.
    market_target_variable: Optional[str] = None  # e.g., "revenue", "sales", "intent_score"
    time_range: Optional[Dict[str, Any]] = None  # {"start": "2023-01-01", "end": "2024-01-01"}
    brands: Optional[List[str]] = None  # Brands mentioned in query
    confidence: Optional[float] = None  # Initial confidence score
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class AnchorResponse:
    """
    Response from Phase-4 anchoring service.
    
    Contains anchored scores, calibration details, and updated confidence.
    """
    
    anchored_score: float  # Anchored prediction/score
    calibration_details: Dict[str, Any]  # Calibration parameters and diagnostics
    updated_confidence: float  # Updated confidence after anchoring (0.0-1.0)
    notes: List[str] = field(default_factory=list)  # Informational notes
    warnings: List[str] = field(default_factory=list)  # Warnings about calibration
    predicted_market_metric: Optional[Dict[str, Any]] = None  # Optional: distribution of predicted metric
    success: bool = True  # Whether anchoring succeeded
    error_message: Optional[str] = None  # Error message if success=False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "anchored_score": self.anchored_score,
            "calibration_details": self.calibration_details,
            "updated_confidence": self.updated_confidence,
            "notes": self.notes,
            "warnings": self.warnings,
            "predicted_market_metric": self.predicted_market_metric,
            "success": self.success,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnchorResponse":
        """Create AnchorResponse from dictionary"""
        return cls(
            anchored_score=data.get("anchored_score", 0.0),
            calibration_details=data.get("calibration_details", {}),
            updated_confidence=data.get("updated_confidence", 0.0),
            notes=data.get("notes", []),
            warnings=data.get("warnings", []),
            predicted_market_metric=data.get("predicted_market_metric"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )


def create_disabled_response() -> AnchorResponse:
    """Create a response indicating Phase-4 is disabled"""
    return AnchorResponse(
        anchored_score=0.0,
        calibration_details={"status": "disabled"},
        updated_confidence=0.0,
        notes=["Phase-4 anchoring is disabled"],
        warnings=[],
        success=False,
        error_message="Phase-4 anchoring is not configured",
    )

