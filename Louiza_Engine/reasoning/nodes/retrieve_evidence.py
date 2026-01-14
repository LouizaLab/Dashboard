"""
Node C: RetrieveEvidence

Queries Data Engine for relevant tables and metadata.
"""

from reasoning.state import ReasoningState
from data_engine.loaders import DataLoader


def retrieve_evidence(state: ReasoningState) -> ReasoningState:
    """
    Retrieve evidence from Data Engine.
    
    Loads observed metrics and schedules for the specified data version.
    """
    if not state.pins.data_version:
        # Use default if not pinned
        state.pins.data_version = "data_2026_01_08_run01"
    
    try:
        data_loader = DataLoader("data/synthetic", state.pins.data_version)
        
        # Retrieve observed metrics
        observed_metrics = data_loader.load_observed_metrics()
        
        # Retrieve schedules
        price_schedule = data_loader.load_price_schedule()
        promo_schedule = data_loader.load_promo_schedule()
        
        # Store evidence with provenance
        state.evidence.retrieved_tables = [
            {
                "table_name": "observed_metrics_brand_week_region",
                "data_version": state.pins.data_version,
                "num_rows": len(observed_metrics),
                "columns": list(observed_metrics.columns)
            },
            {
                "table_name": "brand_price_schedule",
                "data_version": state.pins.data_version,
                "num_rows": len(price_schedule),
                "columns": list(price_schedule.columns)
            },
            {
                "table_name": "brand_promo_schedule",
                "data_version": state.pins.data_version,
                "num_rows": len(promo_schedule),
                "columns": list(promo_schedule.columns)
            }
        ]
        
        # Coverage summary
        state.evidence.coverage = {
            "weeks": sorted(observed_metrics['week_id'].unique().tolist()),
            "brands": sorted(observed_metrics['brand_id'].unique().tolist()),
            "regions": sorted(observed_metrics['region_id'].unique().tolist())
        }
        
        # Trust summary
        if 'confidence_weight' in observed_metrics.columns:
            state.evidence.data_trust_summary = {
                "mean_confidence": float(observed_metrics['confidence_weight'].mean()),
                "min_confidence": float(observed_metrics['confidence_weight'].min()),
                "coverage_pct": 1.0  # Simplified
            }
        
    except Exception as e:
        # If data not available, mark evidence as incomplete
        state.evidence.data_trust_summary = {
            "error": str(e),
            "coverage_pct": 0.0
        }
    
    return state

