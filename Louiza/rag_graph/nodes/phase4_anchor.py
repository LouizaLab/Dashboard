"""
Phase-4 Anchor Node

Integrates with Phase-4 ground-truth anchoring system.
"""

from typing import Dict, Any, Optional

from ..state import RetrievalState, log_decision
from phase4_client.interface import AnchorClient
from phase4_client.schemas import AnchorRequest, AnchorResponse, create_disabled_response


class Phase4AnchorNode:
    """
    Node 8: Phase-4 Anchor
    
    Purpose:
    - Call Phase-4 anchoring service if applicable
    - Update confidence based on anchoring results
    - Incorporate calibration details
    """
    
    def __init__(self, anchor_client: Optional[AnchorClient] = None):
        """
        Initialize Phase-4 anchor node.
        
        Args:
            anchor_client: Optional AnchorClient instance (None = disabled)
        """
        self.anchor_client = anchor_client
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute Phase-4 anchoring.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with phase4 populated
        """
        # Check if anchoring should be applied
        intent = state["intent"]
        intent_type = intent.get("primary_intent", "")
        
        should_anchor = (
            intent_type in ["market_inference", "behavioral_evolution"] or
            state["entities"].get("metrics") or
            "anchor" in state["query"].lower()
        )
        
        if not should_anchor or not self.anchor_client:
            # Phase-4 disabled or not applicable
            state["phase4"] = create_disabled_response().to_dict()
            return state
        
        # Build anchor request
        request = self._build_anchor_request(state)
        
        # Call Phase-4
        try:
            response = self.anchor_client.anchor(request)
            
            state["phase4"] = response.to_dict()
            
            # Update confidence if Phase-4 provides updated confidence
            if response.success and response.updated_confidence > 0:
                state["confidence"] = response.updated_confidence
            
            # Log decision
            log_decision(state, "phase4_anchor", {
                "anchored_score": response.anchored_score,
                "updated_confidence": response.updated_confidence,
                "success": response.success,
            })
        
        except Exception as e:
            # Error calling Phase-4
            state["phase4"] = {
                "anchored_score": 0.0,
                "calibration_details": {"error": str(e)},
                "updated_confidence": state["confidence"],
                "notes": [],
                "warnings": [f"Phase-4 anchoring failed: {str(e)}"],
                "success": False,
                "error_message": str(e),
            }
        
        return state
    
    def _build_anchor_request(self, state: RetrievalState) -> AnchorRequest:
        """Build AnchorRequest from state"""
        # Extract time range if available
        time_range = None
        if state["entities"].get("time_range"):
            tr = state["entities"]["time_range"]
            if tr.get("years"):
                years = tr["years"]
                if len(years) >= 2:
                    time_range = {
                        "start": f"{years[0]}-01-01",
                        "end": f"{years[-1]}-12-31",
                    }
                else:
                    time_range = {
                        "start": f"{years[0]}-01-01",
                        "end": f"{years[0]}-12-31",
                    }
        
        # Extract market target variable
        market_target = None
        if state["entities"].get("metrics"):
            market_target = state["entities"]["metrics"][0]
        
        # Build structured aggregates
        structured_aggregates = {
            "total_records": len(state["retrieved"]),
            "buckets_used": list(state["retrieved_by_bucket"].keys()),
            "counts_by_bucket": {
                bid: len(recs) for bid, recs in state["retrieved_by_bucket"].items()
            },
            "confidence": state["confidence"],
        }
        
        # Add evidence summary
        if state.get("evidence_summary"):
            structured_aggregates["evidence_summary"] = state["evidence_summary"]
        
        return AnchorRequest(
            query=state["query"],
            retrieved_evidence_summary=state["rag_context"],
            structured_aggregates=structured_aggregates,
            market_target_variable=market_target,
            time_range=time_range,
            brands=state["entities"].get("brands"),
            confidence=state["confidence"],
            metadata={
                "intent": state["intent"],
                "entropy": state.get("entropy", {}),
            },
        )

