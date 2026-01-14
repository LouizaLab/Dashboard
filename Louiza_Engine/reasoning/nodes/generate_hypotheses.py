"""
Node B: GenerateHypotheses

Turns prompt into 1-3 testable hypotheses with acceptance criteria.
"""

from reasoning.state import ReasoningState, Hypothesis, AcceptanceCriteria


def generate_hypotheses(state: ReasoningState) -> ReasoningState:
    """
    Generate testable hypotheses from user prompt.
    
    For POC, uses simple rule-based generation. Production would use LLM.
    """
    prompt = state.request.user_prompt.lower()
    
    hypotheses = []
    
    # Simple hypothesis generation based on keywords
    if 'promo' in prompt or 'promotion' in prompt:
        hypothesis = Hypothesis(
            hypothesis_id="H1",
            statement="Promotion will increase transactions and revenue",
            metrics=["transactions", "revenue"],
            baseline="S0_baseline",
            treatment="S1_promo",
            acceptance_criteria=[
                AcceptanceCriteria(
                    metric="transactions",
                    delta_pct_min=0.05,
                    confidence_min=0.7
                )
            ]
        )
        hypotheses.append(hypothesis)
    
    if 'price' in prompt or 'pricing' in prompt:
        hypothesis = Hypothesis(
            hypothesis_id="H2",
            statement="Price change will affect market share",
            metrics=["transactions", "revenue"],
            baseline="S0_baseline",
            treatment="S1_price_change",
            acceptance_criteria=[
                AcceptanceCriteria(
                    metric="transactions",
                    delta_pct_min=0.02,
                    confidence_min=0.7
                )
            ]
        )
        hypotheses.append(hypothesis)
    
    if 'launch' in prompt or 'new' in prompt or 'menu' in prompt:
        hypothesis = Hypothesis(
            hypothesis_id="H3",
            statement="Menu launch will increase brand transactions",
            metrics=["transactions", "revenue"],
            baseline="S0_baseline",
            treatment="S1_menu_launch",
            acceptance_criteria=[
                AcceptanceCriteria(
                    metric="transactions",
                    delta_pct_min=0.03,
                    confidence_min=0.7
                )
            ]
        )
        hypotheses.append(hypothesis)
    
    # Default hypothesis if none generated
    if not hypotheses:
        hypothesis = Hypothesis(
            hypothesis_id="H1",
            statement="Scenario will affect market outcomes",
            metrics=["transactions", "revenue"],
            baseline="S0_baseline",
            treatment="S1_scenario",
            acceptance_criteria=[
                AcceptanceCriteria(
                    metric="transactions",
                    delta_pct_min=0.01,
                    confidence_min=0.6
                )
            ]
        )
        hypotheses.append(hypothesis)
    
    state.hypotheses = hypotheses
    return state

