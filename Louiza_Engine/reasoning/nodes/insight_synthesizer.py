"""
Node J: InsightSynthesizer

Produces explanations and insights from results.
"""

from reasoning.state import ReasoningState


def insight_synthesizer(state: ReasoningState) -> ReasoningState:
    """
    Synthesize insights from simulation results.
    
    Produces explanations of what moved, why, and which personas drove it.
    """
    insights = []
    
    # Analyze scenario comparisons
    for comparison in state.analysis.scenario_comparisons:
        scenario_id = comparison["scenario_id"]
        tx_delta = comparison["mean_transactions_delta_pct"]
        rev_delta = comparison["mean_revenue_delta_pct"]
        
        insight = f"Scenario {scenario_id}: "
        
        if abs(tx_delta) > 1.0:
            direction = "increased" if tx_delta > 0 else "decreased"
            insight += f"Transactions {direction} by {abs(tx_delta):.1f}%. "
        
        if abs(rev_delta) > 1.0:
            direction = "increased" if rev_delta > 0 else "decreased"
            insight += f"Revenue {direction} by {abs(rev_delta):.1f}%. "
        
        # Add uncertainty note
        if comparison.get("transactions_uncertainty_std", 0) > 0:
            insight += f"(Uncertainty: ±{comparison['transactions_uncertainty_std']:.1f})"
        
        insights.append(insight)
    
    # Store insights in final report summary
    state.final_report.summary = "\n".join(insights) if insights else "No significant changes detected."
    
    return state

