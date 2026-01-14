"""
Node D: CriticCheck

Validates hypothesis + evidence sufficiency.
"""

from reasoning.state import ReasoningState


def critic_check(state: ReasoningState) -> ReasoningState:
    """
    Validate hypothesis and evidence sufficiency.
    
    Checks:
    - Are required metrics available?
    - Is coverage acceptable?
    - Are assumptions reasonable?
    """
    # For POC, simple validation
    # In production, would use LLM for more sophisticated checking
    
    # Check evidence coverage
    if not state.evidence.retrieved_tables:
        # Need more evidence
        return state
    
    # Check metrics availability
    required_metrics = set()
    for hypothesis in state.hypotheses:
        required_metrics.update(hypothesis.metrics)
    
    # Check if observed metrics table has required columns
    observed_table = next(
        (t for t in state.evidence.retrieved_tables if "observed_metrics" in t["table_name"]),
        None
    )
    
    if observed_table:
        available_columns = set(observed_table.get("columns", []))
        # Check for transactions and revenue
        has_transactions = any("transaction" in col.lower() for col in available_columns)
        has_revenue = any("revenue" in col.lower() for col in available_columns)
        
        if not (has_transactions and has_revenue):
            # Coverage insufficient
            return state
    
    # Check confidence weights
    trust_summary = state.evidence.data_trust_summary
    if trust_summary.get("coverage_pct", 0.0) < 0.5:
        # Low coverage
        return state
    
    # All checks passed - approved
    return state

