"""
Node E: ScenarioBuilder

Converts hypotheses into executable scenario specs for LPM.
"""

from reasoning.state import ReasoningState, ScenarioSpec, Intervention


def scenario_builder(state: ReasoningState) -> ReasoningState:
    """
    Build scenario specifications from hypotheses.
    
    Creates baseline scenario and counterfactual scenarios.
    """
    scenarios = []
    
    # Always create baseline scenario
    baseline = ScenarioSpec(
        scenario_id="S0_baseline",
        kind="baseline",
        time_horizon_weeks=state.request.constraints.time_horizon_weeks,
        scope={
            "regions": state.request.constraints.regions or [],
            "brands": state.request.constraints.brands or [],
            "channels": state.request.constraints.channels or []
        },
        interventions=[]
    )
    scenarios.append(baseline)
    
    # Create counterfactual scenarios based on hypotheses
    prompt = state.request.user_prompt.lower()
    
    # Scenario 1: Promo
    if 'promo' in prompt or 'promotion' in prompt:
        interventions = []
        brand_id = state.request.constraints.brands[0] if state.request.constraints.brands else "BRAND_01"
        region_id = state.request.constraints.regions[0] if state.request.constraints.regions else None
        
        interventions.append(Intervention(
            type="promo",
            brand_id=brand_id,
            region_id=region_id,
            intensity=0.7,
            start_week=3,
            end_week=6
        ))
        
        scenario = ScenarioSpec(
            scenario_id="S1_promo",
            kind="counterfactual",
            time_horizon_weeks=state.request.constraints.time_horizon_weeks,
            scope={
                "regions": state.request.constraints.regions or [],
                "brands": state.request.constraints.brands or [],
                "channels": state.request.constraints.channels or []
            },
            interventions=interventions
        )
        scenarios.append(scenario)
    
    # Scenario 2: Price change
    if 'price' in prompt or 'pricing' in prompt:
        interventions = []
        brand_id = state.request.constraints.brands[0] if state.request.constraints.brands else "BRAND_01"
        region_id = state.request.constraints.regions[0] if state.request.constraints.regions else None
        
        # Determine price direction
        delta_pct = -0.05 if 'reduce' in prompt or 'lower' in prompt or 'decrease' in prompt else 0.05
        
        interventions.append(Intervention(
            type="price_change",
            brand_id=brand_id,
            region_id=region_id,
            delta_pct=delta_pct,
            start_week=3
        ))
        
        scenario = ScenarioSpec(
            scenario_id="S1_price_change",
            kind="counterfactual",
            time_horizon_weeks=state.request.constraints.time_horizon_weeks,
            scope={
                "regions": state.request.constraints.regions or [],
                "brands": state.request.constraints.brands or [],
                "channels": state.request.constraints.channels or []
            },
            interventions=interventions
        )
        scenarios.append(scenario)
    
    # Scenario 3: Menu launch
    if 'launch' in prompt or 'new' in prompt or 'menu' in prompt:
        interventions = []
        brand_id = state.request.constraints.brands[0] if state.request.constraints.brands else "BRAND_01"
        
        interventions.append(Intervention(
            type="menu_launch",
            brand_id=brand_id,
            item_id="new_item_001",
            start_week=3
        ))
        
        scenario = ScenarioSpec(
            scenario_id="S1_menu_launch",
            kind="counterfactual",
            time_horizon_weeks=state.request.constraints.time_horizon_weeks,
            scope={
                "regions": state.request.constraints.regions or [],
                "brands": state.request.constraints.brands or [],
                "channels": state.request.constraints.channels or []
            },
            interventions=interventions
        )
        scenarios.append(scenario)
    
    # Default scenario if none created
    if len(scenarios) == 1:  # Only baseline
        scenario = ScenarioSpec(
            scenario_id="S1_scenario",
            kind="counterfactual",
            time_horizon_weeks=state.request.constraints.time_horizon_weeks,
            scope={
                "regions": state.request.constraints.regions or [],
                "brands": state.request.constraints.brands or [],
                "channels": state.request.constraints.channels or []
            },
            interventions=[
                Intervention(
                    type="promo",
                    brand_id=state.request.constraints.brands[0] if state.request.constraints.brands else "BRAND_01",
                    intensity=0.5,
                    start_week=2,
                    end_week=4
                )
            ]
        )
        scenarios.append(scenario)
    
    state.scenario_specs = scenarios
    return state

