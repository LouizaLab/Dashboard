"""
LPM Adapter - Bridges Phase 3-4 simulation from Louiza with recipe simulation system.
This adapter allows us to use the full LPM simulation engine for recipe changes.
"""
import sys
import os
from pathlib import Path

# Add Louiza directory to path if it exists (for reference, but we'll copy what we need)
LOUIZA_PATH = Path(__file__).parent.parent.parent / 'Louiza'
if LOUIZA_PATH.exists():
    sys.path.insert(0, str(LOUIZA_PATH))

import torch
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# We'll create a simplified version that mimics Phase 3-4 behavior
# but works with our PersonaAgent structure


class LPMRecipeSimulator:
    """
    Large Population Model Recipe Simulator
    Uses Phase 3-4 concepts but adapted for recipe changes.
    """
    
    def __init__(self, agents: List[Dict], base_product: Dict, recipe_variant: Dict):
        """
        Initialize LPM simulator for recipe variant.
        
        Args:
            agents: List of agent dicts from PersonaAgent
            base_product: Base product information
            recipe_variant: Recipe variant with changes
        """
        self.agents = agents
        self.base_product = base_product
        self.recipe_variant = recipe_variant
        
        # Initialize agent states (simplified Phase 3-4 style)
        self.agent_states = {}
        self.agent_preferences = {}
        self.initialize_agents()
        
        # Simulation state
        self.time_step = 0
        self.results = []
        
    def initialize_agents(self):
        """Initialize agents with behavioral states (Phase 3-4 style)"""
        for agent in self.agents:
            agent_id = agent['id']
            
            # Initialize behavioral state components (Phase 3-4 style)
            # s_t = [taste, novelty, habit, health, price_sensitivity]
            archetype = agent.get('archetype', 'unknown')
            behavior_params = agent.get('behavior_params_json', {})
            
            # Base state from archetype
            base_state = self._get_archetype_base_state(archetype)
            
            # Add personality variations
            state = {
                'taste': base_state['taste'] + np.random.normal(0, 0.1),
                'novelty': behavior_params.get('novelty_seeking', 0.5) + np.random.normal(0, 0.1),
                'habit': behavior_params.get('brand_loyalty', 0.5) + np.random.normal(0, 0.1),
                'health': behavior_params.get('health_bias', 0.5) + np.random.normal(0, 0.1),
                'price_sensitivity': behavior_params.get('price_sensitivity', 0.5) + np.random.normal(0, 0.1),
            }
            
            # Clip to [0, 1]
            for key in state:
                state[key] = max(0.0, min(1.0, state[key]))
            
            self.agent_states[agent_id] = state
            
            # Initialize baseline preference
            self.agent_preferences[agent_id] = self._compute_baseline_preference(state, agent)
    
    def _get_archetype_base_state(self, archetype: str) -> Dict[str, float]:
        """Get base behavioral state for archetype"""
        archetype_states = {
            'value_seeker': {
                'taste': 0.5,
                'novelty': 0.3,
                'habit': 0.6,
                'health': 0.4,
                'price_sensitivity': 0.9,
            },
            'health_optimizer': {
                'taste': 0.6,
                'novelty': 0.4,
                'habit': 0.5,
                'health': 0.9,
                'price_sensitivity': 0.5,
            },
            'convenience_loyalist': {
                'taste': 0.5,
                'novelty': 0.2,
                'habit': 0.9,
                'health': 0.4,
                'price_sensitivity': 0.5,
            },
            'late_night_craver': {
                'taste': 0.7,
                'novelty': 0.5,
                'habit': 0.6,
                'health': 0.3,
                'price_sensitivity': 0.4,
            },
            'trend_chaser': {
                'taste': 0.7,
                'novelty': 0.9,
                'habit': 0.3,
                'health': 0.5,
                'price_sensitivity': 0.5,
            },
            'family_bundle_buyer': {
                'taste': 0.6,
                'novelty': 0.4,
                'habit': 0.7,
                'health': 0.6,
                'price_sensitivity': 0.7,
            },
            'protein_maximizer': {
                'taste': 0.6,
                'novelty': 0.4,
                'habit': 0.5,
                'health': 0.8,
                'price_sensitivity': 0.5,
            },
        }
        return archetype_states.get(archetype, {
            'taste': 0.5,
            'novelty': 0.5,
            'habit': 0.5,
            'health': 0.5,
            'price_sensitivity': 0.5,
        })
    
    def _compute_baseline_preference(self, state: Dict, agent: Dict) -> float:
        """Compute baseline preference from state (Phase 3-4 style)"""
        # Weighted combination of state components
        base_pref = (
            state['taste'] * 0.4 +
            (1 - state['habit']) * 0.2 +  # Lower habit = more open to change
            state['health'] * 0.2 +
            (1 - state['price_sensitivity']) * 0.2  # Lower price sensitivity = higher preference
        )
        
        # Add some randomness
        base_pref += np.random.normal(0, 0.05)
        return max(0.0, min(1.0, base_pref))
    
    def compute_recipe_impact(self, agent_id: str) -> Dict:
        """
        Compute impact of recipe variant on agent (Phase 3-4 style).
        Returns preference delta and decision.
        """
        state = self.agent_states[agent_id]
        agent = next(a for a in self.agents if a['id'] == agent_id)
        base_pref = self.agent_preferences[agent_id]
        
        # Compute preference delta from recipe changes
        delta = 0.0
        
        # Nutrition impact (Phase 3-4 style - state-dependent)
        nutrition_delta = self.recipe_variant.get('nutrition_delta_json', {})
        
        # Health-conscious agents respond strongly to nutrition changes
        if 'sugar' in nutrition_delta:
            sugar_delta = nutrition_delta['sugar']
            health_weight = state['health']
            if sugar_delta < 0:  # Sugar reduction
                delta += abs(sugar_delta) * 0.3 * health_weight
            else:  # Sugar increase
                delta -= sugar_delta * 0.3 * health_weight
        
        if 'sodium' in nutrition_delta:
            sodium_delta = nutrition_delta['sodium']
            health_weight = state['health']
            if sodium_delta < 0:  # Sodium reduction
                delta += abs(sodium_delta) * 0.25 * health_weight
            else:
                delta -= sodium_delta * 0.25 * health_weight
        
        if 'calories' in nutrition_delta:
            cal_delta = nutrition_delta['calories']
            health_weight = state['health']
            if cal_delta < 0:
                delta += abs(cal_delta) * 0.2 * health_weight
            else:
                delta -= cal_delta * 0.15 * health_weight
        
        # Price impact (Phase 3-4 style - price sensitivity dependent)
        price_delta = self.recipe_variant.get('price_delta', 0.0)
        if price_delta != 0:
            price_impact = -price_delta * state['price_sensitivity'] * 2.0
            delta += price_impact
        
        # Sensory impact (Phase 3-4 style - taste component dependent)
        sensory_delta = self.recipe_variant.get('sensory_delta_json', {})
        taste_component = state['taste']
        
        for attr, change in sensory_delta.items():
            # Positive sensory changes matter more to taste-focused agents
            if change > 0:
                delta += change * taste_component * 0.15
            else:
                delta += change * (1 - taste_component) * 0.1
        
        # Habit inertia reduces impact (Phase 3-4 style)
        habit_strength = state['habit']
        delta *= (1 - habit_strength * 0.4)
        
        # Novelty bias affects response to changes
        novelty_bias = state['novelty']
        if abs(delta) > 0.1:  # Significant change
            delta *= (1 + novelty_bias * 0.2)  # Novelty seekers more responsive
        
        # Compute new preference
        new_preference = base_pref + delta
        new_preference = max(0.0, min(1.0, new_preference))
        
        # Decision (Phase 3-4 style)
        decision = self._make_decision(new_preference, base_pref, state)
        
        return {
            'preference_delta': delta,
            'new_preference': new_preference,
            'base_preference': base_pref,
            'decision': decision,
            'state': state.copy()
        }
    
    def _make_decision(self, new_pref: float, base_pref: float, state: Dict) -> str:
        """Make decision based on preference (Phase 3-4 style)"""
        pref_change = new_pref - base_pref
        
        # High habit = more resistant to change
        habit_threshold = 0.3 + state['habit'] * 0.3
        
        if new_pref < 0.3:
            return 'reject'
        elif new_pref < 0.5:
            return 'substitute'
        elif pref_change < -habit_threshold:
            return 'reduce_frequency'
        elif pref_change > habit_threshold:
            return 'increase_frequency'
        else:
            return 'accept'
    
    def simulate_time_series(self, weeks: int) -> List[Dict]:
        """
        Simulate over time (Phase 3-4 style with state evolution).
        """
        time_series = []
        
        for week in range(weeks):
            week_results = {
                'week': week + 1,
                'acceptance_rate': 0.0,
                'rejection_rate': 0.0,
                'substitution_rate': 0.0,
                'reduce_frequency_rate': 0.0,
                'increase_frequency_rate': 0.0,
                'mean_preference': 0.0,
                'preference_std': 0.0,
                'mean_preference_delta': 0.0,
                'agent_decisions': {}
            }
            
            decisions = {}
            preferences = []
            preference_deltas = []
            
            for agent_id in self.agent_states.keys():
                # Compute impact
                impact = self.compute_recipe_impact(agent_id)
                
                # State evolution over time (Phase 3-4 style)
                # Agents adapt - habit increases, novelty decreases
                adaptation_factor = 1.0 - (week / weeks) * 0.2
                adapted_delta = impact['preference_delta'] * adaptation_factor
                
                # Update state (Phase 3-4 style - gradual adaptation)
                state = self.agent_states[agent_id]
                if impact['decision'] == 'accept':
                    # Successful interaction strengthens habit
                    state['habit'] = min(0.95, state['habit'] + 0.01)
                elif impact['decision'] == 'reject':
                    # Rejection weakens habit
                    state['habit'] = max(0.05, state['habit'] - 0.02)
                
                # Novelty wears off over time
                state['novelty'] = max(0.1, state['novelty'] - 0.005)
                
                # Update preference
                new_pref = impact['base_preference'] + adapted_delta
                new_pref = max(0.0, min(1.0, new_pref))
                self.agent_preferences[agent_id] = new_pref
                
                decisions[agent_id] = impact['decision']
                preferences.append(new_pref)
                preference_deltas.append(adapted_delta)
            
            # Aggregate
            total = len(decisions)
            week_results['acceptance_rate'] = sum(1 for d in decisions.values() if d == 'accept') / total
            week_results['rejection_rate'] = sum(1 for d in decisions.values() if d == 'reject') / total
            week_results['substitution_rate'] = sum(1 for d in decisions.values() if d == 'substitute') / total
            week_results['reduce_frequency_rate'] = sum(1 for d in decisions.values() if d == 'reduce_frequency') / total
            week_results['increase_frequency_rate'] = sum(1 for d in decisions.values() if d == 'increase_frequency') / total
            week_results['mean_preference'] = np.mean(preferences)
            week_results['preference_std'] = np.std(preferences)
            week_results['mean_preference_delta'] = np.mean(preference_deltas)
            week_results['agent_decisions'] = decisions
            
            time_series.append(week_results)
        
        return time_series
    
    def run_simulation(self, weeks: int) -> Dict:
        """
        Run full LPM simulation (Phase 3-4 style).
        """
        print(f"Running LPM simulation for {weeks} weeks with {len(self.agents)} agents...")
        
        # Compute baseline metrics
        baseline_preferences = self.agent_preferences.copy()
        
        # Run time series simulation
        time_series = self.simulate_time_series(weeks)
        
        # Compute final preferences
        final_preferences = self.agent_preferences.copy()
        
        # Aggregate results
        final_week = time_series[-1] if time_series else {}
        
        # Segment breakdown
        segment_breakdown = self._compute_segment_breakdown(final_week)
        
        return {
            'overall_acceptance_rate': final_week.get('acceptance_rate', 0.0),
            'overall_rejection_rate': final_week.get('rejection_rate', 0.0),
            'mean_preference_delta': final_week.get('mean_preference_delta', 0.0),
            'baseline_preferences': baseline_preferences,
            'final_preferences': final_preferences,
            'time_series': time_series,
            'segment_breakdown': segment_breakdown,
            'final_week_metrics': final_week,
            'agent_decisions': final_week.get('agent_decisions', {})
        }
    
    def _compute_segment_breakdown(self, final_week: Dict) -> Dict:
        """Compute segment-level breakdown"""
        segment_breakdown = {}
        decisions = final_week.get('agent_decisions', {})
        
        for agent in self.agents:
            segment_key = f"{agent.get('age_bucket', 'unknown')}_{agent.get('archetype', 'unknown')}"
            
            if segment_key not in segment_breakdown:
                segment_breakdown[segment_key] = {
                    'count': 0,
                    'actions': {'accept': 0, 'reject': 0, 'substitute': 0, 'reduce_frequency': 0, 'increase_frequency': 0},
                    'mean_preference_delta': 0.0,
                    'demographics': {
                        'age_bucket': agent.get('age_bucket', ''),
                        'archetype': agent.get('archetype', ''),
                        'region': agent.get('region', ''),
                    }
                }
            
            segment_breakdown[segment_key]['count'] += 1
            decision = decisions.get(agent['id'], 'accept')
            segment_breakdown[segment_key]['actions'][decision] = \
                segment_breakdown[segment_key]['actions'].get(decision, 0) + 1
            
            # Get preference delta
            impact = self.compute_recipe_impact(agent['id'])
            segment_breakdown[segment_key]['mean_preference_delta'] += impact['preference_delta']
        
        # Normalize
        for segment in segment_breakdown.values():
            if segment['count'] > 0:
                segment['mean_preference_delta'] /= segment['count']
                for action in segment['actions']:
                    segment['actions'][action] /= segment['count']
        
        return segment_breakdown

