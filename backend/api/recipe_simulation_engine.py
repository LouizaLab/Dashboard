"""
Recipe Simulation Engine
Extends LPM to simulate recipe changes and compute regulatory readiness metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import math

# Note: This is a standalone implementation that doesn't depend on Louiza directory
# It uses simplified agent models based on the PersonaAgent structure


class RecipeSimulationAgent:
    """
    Extended agent for recipe simulation with taste memory, habit inertia, etc.
    Based on PersonaAgent but with additional state for recipe changes.
    """
    
    def __init__(self, agent_id: str, segment_id: str, archetype: str,
                 taste_profile: List[str], behavior_params: Dict,
                 demographics: Dict):
        self.agent_id = agent_id
        self.segment_id = segment_id
        self.archetype = archetype
        self.taste_profile = taste_profile
        self.behavior_params = behavior_params
        self.demographics = demographics
        
        # Extended state for recipe simulation
        self.taste_memory = {}  # product_id -> last preference
        self.habit_inertia = 0.5  # 0-1, how resistant to change
        self.sensory_sensitivity = self._compute_sensory_sensitivity()
        self.price_sensitivity = behavior_params.get('price_sensitivity', 0.5)
        self.health_sensitivity = behavior_params.get('health_bias', 0.5)
        self.brand_loyalty = behavior_params.get('brand_loyalty', 0.5)
        self.novelty_bias = behavior_params.get('novelty_seeking', 0.5)
        
        # Regulatory risk flags
        self.sugar_conscious = 'sugar' in str(taste_profile).lower() or archetype == 'health_optimizer'
        self.sodium_conscious = 'sodium' in str(taste_profile).lower() or archetype == 'health_optimizer'
        self.calorie_conscious = archetype in ['health_optimizer', 'protein_maximizer']
        
        # Current state
        self.current_preference = 0.5  # Baseline preference
        self.interaction_count = 0
    
    def _compute_sensory_sensitivity(self) -> Dict[str, float]:
        """Compute sensitivity to different sensory attributes."""
        base_sensitivity = {
            'sweetness': 0.5,
            'saltiness': 0.5,
            'texture': 0.5,
            'heat': 0.5,
            'aroma': 0.5
        }
        
        # Adjust based on archetype
        if self.archetype == 'health_optimizer':
            base_sensitivity['sweetness'] = 0.3  # Less tolerant of high sugar
            base_sensitivity['saltiness'] = 0.3  # Less tolerant of high sodium
        elif self.archetype == 'late_night_craver':
            base_sensitivity['heat'] = 0.7  # More tolerant of spicy
        elif self.archetype == 'trend_chaser':
            base_sensitivity['aroma'] = 0.8  # More sensitive to aroma
        
        return base_sensitivity
    
    def compute_preference_delta(self, recipe_variant: Dict, base_product: Dict) -> float:
        """
        Compute preference change due to recipe variant.
        Returns delta in preference (can be negative).
        """
        delta = 0.0
        
        # Nutrition changes
        nutrition_delta = recipe_variant.get('nutrition_delta_json', {})
        
        # Sugar change
        if 'sugar' in nutrition_delta:
            sugar_delta = nutrition_delta['sugar']
            if self.sugar_conscious:
                delta -= abs(sugar_delta) * 0.3  # Negative impact
            else:
                delta += sugar_delta * 0.1  # Slight positive if increase
        
        # Sodium change
        if 'sodium' in nutrition_delta:
            sodium_delta = nutrition_delta['sodium']
            if self.sodium_conscious:
                delta -= abs(sodium_delta) * 0.3
            else:
                delta += sodium_delta * 0.05
        
        # Calories change
        if 'calories' in nutrition_delta:
            cal_delta = nutrition_delta['calories']
            if self.calorie_conscious:
                delta -= abs(cal_delta) * 0.2 if cal_delta > 0 else cal_delta * 0.1
            else:
                delta += cal_delta * 0.05 if cal_delta < 0 else 0
        
        # Sensory changes
        sensory_delta = recipe_variant.get('sensory_delta_json', {})
        for attr, change in sensory_delta.items():
            sensitivity = self.sensory_sensitivity.get(attr, 0.5)
            # Preference change based on sensitivity and direction
            if attr in ['sweetness', 'saltiness'] and self.health_sensitivity > 0.7:
                delta -= abs(change) * sensitivity * 0.2
            else:
                delta += change * sensitivity * 0.1
        
        # Price change
        price_delta = recipe_variant.get('price_delta', 0.0)
        if price_delta != 0:
            price_impact = -price_delta * self.price_sensitivity * 2.0  # Negative for price increase
            delta += price_impact
        
        # Ingredient changes
        ingredient_changes = recipe_variant.get('ingredient_changes_json', {})
        removed = ingredient_changes.get('removed', [])
        added = ingredient_changes.get('added', [])
        
        # Check if removed ingredients were liked
        for ingredient in removed:
            if ingredient.lower() in str(self.taste_profile).lower():
                delta -= 0.15  # Negative impact
        
        # Check if added ingredients align with preferences
        for ingredient in added:
            if ingredient.lower() in str(self.taste_profile).lower():
                delta += 0.1  # Positive impact
        
        # Habit inertia reduces impact of changes
        delta *= (1 - self.habit_inertia * 0.5)
        
        return delta
    
    def decide_action(self, preference_delta: float, base_preference: float) -> str:
        """
        Decide action: Accept, Reject, Substitute, Reduce Frequency, Increase Frequency
        """
        new_preference = base_preference + preference_delta
        new_preference = max(0.0, min(1.0, new_preference))
        
        if new_preference < 0.3:
            return 'reject'
        elif new_preference < 0.5:
            return 'substitute'
        elif new_preference < 0.6:
            return 'reduce_frequency'
        elif new_preference >= 0.8:
            return 'increase_frequency'
        else:
            return 'accept'
    
    def update_state(self, action: str, preference_delta: float):
        """Update agent state after interaction."""
        self.interaction_count += 1
        
        # Update habit inertia (becomes more resistant over time)
        if action == 'accept':
            self.habit_inertia = min(0.9, self.habit_inertia + 0.01)
        elif action == 'reject':
            self.habit_inertia = max(0.1, self.habit_inertia - 0.05)
        
        # Update current preference
        self.current_preference += preference_delta * 0.1  # Gradual update
        self.current_preference = max(0.0, min(1.0, self.current_preference))


class RecipeSimulationEngine:
    """
    Main simulation engine for recipe changes.
    Runs LPM simulation and computes regulatory readiness metrics.
    """
    
    def __init__(self, agents: List[Dict], base_product: Dict):
        """
        Initialize simulation engine.
        
        Args:
            agents: List of agent dicts (from PersonaAgent queryset)
            base_product: Base product information
        """
        self.base_product = base_product
        self.agents = [
            RecipeSimulationAgent(
                agent_id=str(agent['id']),
                segment_id=agent.get('segment_id', 'unknown'),
                archetype=agent.get('archetype', 'unknown'),
                taste_profile=agent.get('taste_profile_json', []),
                behavior_params=agent.get('behavior_params_json', {}),
                demographics={
                    'age_bucket': agent.get('age_bucket', ''),
                    'region': agent.get('region', ''),
                    'gender': agent.get('gender', ''),
                    'income': agent.get('income', '')
                }
            )
            for agent in agents
        ]
        
        self.results = []
        self.time_steps = []
    
    def run_simulation(self, recipe_variant: Dict, time_horizon_weeks: int = 12) -> Dict:
        """
        Run simulation for recipe variant.
        
        Returns:
            Dict with simulation results
        """
        print(f"Running simulation with {len(self.agents)} agents for {time_horizon_weeks} weeks...")
        
        # Compute baseline preferences
        baseline_preferences = self._compute_baseline_preferences()
        
        # Compute preference deltas for recipe variant
        preference_deltas = {}
        actions = {}
        
        for agent in self.agents:
            delta = agent.compute_preference_delta(recipe_variant, self.base_product)
            preference_deltas[agent.agent_id] = delta
            
            base_pref = baseline_preferences.get(agent.agent_id, 0.5)
            action = agent.decide_action(delta, base_pref)
            actions[agent.agent_id] = action
        
        # Simulate over time
        time_series_results = self._simulate_time_series(
            recipe_variant, preference_deltas, actions, time_horizon_weeks
        )
        
        # Aggregate results
        results = self._aggregate_results(baseline_preferences, preference_deltas, actions, time_series_results)
        
        return results
    
    def _compute_baseline_preferences(self) -> Dict[str, float]:
        """Compute baseline preferences for all agents."""
        preferences = {}
        
        for agent in self.agents:
            # Base preference from archetype and behavior params
            base = 0.5
            
            # Adjust based on archetype
            if agent.archetype == 'convenience_loyalist':
                base = 0.7  # Higher baseline loyalty
            elif agent.archetype == 'value_seeker':
                base = 0.6
            elif agent.archetype == 'health_optimizer':
                base = 0.5  # Neutral baseline
            
            # Add some randomness
            base += np.random.normal(0, 0.1)
            base = max(0.0, min(1.0, base))
            
            preferences[agent.agent_id] = base
            agent.current_preference = base
        
        return preferences
    
    def _simulate_time_series(self, recipe_variant: Dict, preference_deltas: Dict,
                              initial_actions: Dict, weeks: int) -> List[Dict]:
        """Simulate preference evolution over time."""
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
                'actions': {}
            }
            
            actions_this_week = {}
            preferences_this_week = []
            
            for agent in self.agents:
                # Update agent state
                delta = preference_deltas[agent.agent_id]
                
                # Over time, agents may adapt (reduce impact of change)
                adaptation_factor = 1.0 - (week / weeks) * 0.3  # Gradually adapt
                adapted_delta = delta * adaptation_factor
                
                base_pref = agent.current_preference
                action = agent.decide_action(adapted_delta, base_pref)
                actions_this_week[agent.agent_id] = action
                
                agent.update_state(action, adapted_delta)
                preferences_this_week.append(agent.current_preference)
            
            # Compute rates
            total = len(self.agents)
            week_results['acceptance_rate'] = sum(1 for a in actions_this_week.values() if a == 'accept') / total
            week_results['rejection_rate'] = sum(1 for a in actions_this_week.values() if a == 'reject') / total
            week_results['substitution_rate'] = sum(1 for a in actions_this_week.values() if a == 'substitute') / total
            week_results['reduce_frequency_rate'] = sum(1 for a in actions_this_week.values() if a == 'reduce_frequency') / total
            week_results['increase_frequency_rate'] = sum(1 for a in actions_this_week.values() if a == 'increase_frequency') / total
            week_results['mean_preference'] = np.mean(preferences_this_week)
            week_results['preference_std'] = np.std(preferences_this_week)
            week_results['actions'] = actions_this_week
            
            time_series.append(week_results)
        
        return time_series
    
    def _aggregate_results(self, baseline_preferences: Dict, preference_deltas: Dict,
                          actions: Dict, time_series: List[Dict]) -> Dict:
        """Aggregate simulation results."""
        # Segment-level breakdown
        segment_breakdown = {}
        for agent in self.agents:
            segment_key = f"{agent.demographics['age_bucket']}_{agent.archetype}"
            if segment_key not in segment_breakdown:
                segment_breakdown[segment_key] = {
                    'count': 0,
                    'actions': {'accept': 0, 'reject': 0, 'substitute': 0, 'reduce_frequency': 0, 'increase_frequency': 0},
                    'mean_preference_delta': 0.0,
                    'demographics': agent.demographics
                }
            
            segment_breakdown[segment_key]['count'] += 1
            action = actions.get(agent.agent_id, 'accept')
            segment_breakdown[segment_key]['actions'][action] = segment_breakdown[segment_key]['actions'].get(action, 0) + 1
            segment_breakdown[segment_key]['mean_preference_delta'] += preference_deltas.get(agent.agent_id, 0.0)
        
        # Normalize
        for segment in segment_breakdown.values():
            if segment['count'] > 0:
                segment['mean_preference_delta'] /= segment['count']
                for action in segment['actions']:
                    segment['actions'][action] /= segment['count']
        
        # Overall metrics
        overall_acceptance = sum(1 for a in actions.values() if a == 'accept') / len(actions) if actions else 0.0
        overall_rejection = sum(1 for a in actions.values() if a == 'reject') / len(actions) if actions else 0.0
        mean_preference_delta = np.mean(list(preference_deltas.values())) if preference_deltas else 0.0
        
        # Final week metrics
        final_week = time_series[-1] if time_series else {}
        
        return {
            'overall_acceptance_rate': overall_acceptance,
            'overall_rejection_rate': overall_rejection,
            'mean_preference_delta': mean_preference_delta,
            'segment_breakdown': segment_breakdown,
            'time_series': time_series,
            'final_week_metrics': final_week,
            'baseline_preferences': baseline_preferences,
            'preference_deltas': preference_deltas,
            'actions': actions
        }


def compute_entropy_metrics(baseline_preferences: Dict, post_change_preferences: Dict) -> Dict:
    """
    Compute entropy metrics for decision clarity.
    
    Entropy measures uncertainty/agreement in population.
    Lower entropy = more agreement = higher confidence.
    """
    # Convert to arrays
    baseline_values = np.array(list(baseline_preferences.values()))
    post_values = np.array(list(post_change_preferences.values()))
    
    # Compute entropy using histogram
    def compute_entropy(values, bins=20):
        hist, _ = np.histogram(values, bins=bins, range=(0, 1))
        hist = hist[hist > 0]  # Remove zeros
        probs = hist / hist.sum()
        entropy = -np.sum(probs * np.log2(probs))
        return entropy
    
    baseline_entropy = compute_entropy(baseline_values)
    post_entropy = compute_entropy(post_values)
    entropy_delta = post_entropy - baseline_entropy
    
    # Confidence score (inverse of entropy, normalized)
    max_entropy = np.log2(20)  # Using 20 bins as default
    confidence = 1.0 - (post_entropy / max_entropy) if max_entropy > 0 else 0.5
    confidence = max(0.0, min(1.0, confidence))
    
    return {
        'baseline_entropy': float(baseline_entropy),
        'post_change_entropy': float(post_entropy),
        'entropy_delta': float(entropy_delta),
        'confidence_score': float(confidence)
    }


def assess_approval(simulation_results: Dict, approval_personas: List[Dict]) -> Dict:
    """
    Assess approval by different personas based on their thresholds.
    """
    assessments = {}
    
    overall_acceptance = simulation_results.get('overall_acceptance_rate', 0.0)
    mean_preference_delta = simulation_results.get('mean_preference_delta', 0.0)
    
    for persona in approval_personas:
        persona_id = persona.get('id')
        thresholds = {
            'taste_acceptance': persona.get('taste_acceptance_threshold', 0.6),
            'price_sensitivity': persona.get('price_sensitivity_threshold', 0.5),
            'health_acceptance': persona.get('health_acceptance_threshold', 0.5),
            'cannibalization_risk': persona.get('cannibalization_risk_threshold', 0.3),
            'demographic_coverage': persona.get('demographic_coverage_threshold', 0.5),
            'substitution_risk': persona.get('substitution_risk_threshold', 0.4),
        }
        
        # Check thresholds
        approved = True
        reasons = []
        
        if overall_acceptance < thresholds['taste_acceptance']:
            approved = False
            reasons.append(f"Taste acceptance ({overall_acceptance:.2%}) below threshold ({thresholds['taste_acceptance']:.2%})")
        
        # Check demographic coverage
        segment_breakdown = simulation_results.get('segment_breakdown', {})
        positive_segments = sum(1 for s in segment_breakdown.values() 
                               if s.get('mean_preference_delta', 0) > 0)
        total_segments = len(segment_breakdown)
        demographic_coverage = positive_segments / total_segments if total_segments > 0 else 0.0
        
        if demographic_coverage < thresholds['demographic_coverage']:
            approved = False
            reasons.append(f"Demographic coverage ({demographic_coverage:.2%}) below threshold ({thresholds['demographic_coverage']:.2%})")
        
        # Substitution risk (from substitution rate)
        substitution_rate = sum(1 for a in simulation_results.get('actions', {}).values() 
                               if a == 'substitute') / len(simulation_results.get('actions', {})) \
                           if simulation_results.get('actions') else 0.0
        
        if substitution_rate > thresholds['substitution_risk']:
            approved = False
            reasons.append(f"Substitution risk ({substitution_rate:.2%}) above threshold ({thresholds['substitution_risk']:.2%})")
        
        assessments[str(persona_id)] = {
            'approved': approved,
            'reasons': reasons,
            'risk_level': 'low' if approved else 'high',
            'confidence': 0.8 if approved else 0.4
        }
    
    return assessments

