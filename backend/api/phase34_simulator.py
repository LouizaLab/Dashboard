"""
Phase 3-4 Recipe Simulation Engine
Integrates real Phase 3-4 LPM models for recipe simulation.
"""
import sys
import os
from pathlib import Path
import torch
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# Add Louiza directory to path
LOUIZA_PATH = Path(__file__).parent.parent.parent / 'Louiza'
if LOUIZA_PATH.exists():
    sys.path.insert(0, str(LOUIZA_PATH))

try:
    from models_phase3 import Agent, Environment, PopulationSimulator
except ImportError:
    Agent = None
    Environment = None
    PopulationSimulator = None

from .phase34_model_loader import get_model_loader
from .recipe_simulation_engine import compute_entropy_metrics, assess_approval


class Phase34RecipeSimulator:
    """
    Recipe simulation using real Phase 3-4 LPM models.
    """
    
    def __init__(self, 
                 agents: List[Dict],
                 base_product: Dict,
                 recipe_variant: Dict,
                 device: str = 'cpu'):
        """
        Initialize Phase 3-4 recipe simulator.
        
        Args:
            agents: List of agent dicts from PersonaAgent
            base_product: Base product information
            recipe_variant: Recipe variant with changes
            device: Device to run models on
        """
        self.agents = agents
        self.base_product = base_product
        self.recipe_variant = recipe_variant
        self.device = device
        
        # Initialize agent_id_mapping before it's used
        self.agent_id_mapping = {}
        
        # Load models
        try:
            self.model_loader = get_model_loader(device=device)
            success, error = self.model_loader.load_models()
            if not success:
                raise RuntimeError(f"Failed to load Phase 1-2 models: {error}")
            
            self.phase1_models = self.model_loader.get_phase1_models()
            self.phase2_model = self.model_loader.get_phase2_model()
        except Exception as e:
            import traceback
            error_msg = f"Model loading failed: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise RuntimeError(error_msg)
        
        # Initialize environment and simulator
        try:
            self.environment = None
            self.simulator = None
            self._initialize_environment()
            self._initialize_simulator()
        except Exception as e:
            import traceback
            error_msg = f"Simulator initialization failed: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise RuntimeError(error_msg)
    
    def _initialize_environment(self):
        """Initialize Phase 3 Environment with products"""
        if Environment is None:
            raise RuntimeError("Phase 3 Environment not available")
        
        # Create products DataFrame
        products_data = []
        
        # Base product
        base_product_id = self.base_product.get('id', 'base_product')
        base_product_name = self.base_product.get('name', 'Base Product')
        
        # Get base product nutrition (defaults)
        nutrition_delta = self.recipe_variant.get('nutrition_delta_json', {})
        base_nutrition = {
            'sugar': nutrition_delta.get('sugar', 0) + 10,  # Assume base had 10g sugar
            'calories': nutrition_delta.get('calories', 0) + 200,
            'protein': nutrition_delta.get('protein', 0) + 5,
            'caffeine': nutrition_delta.get('caffeine', 0) + 0
        }
        
        # Base product (original, before changes)
        base_price = 5.0
        products_data.append({
            'product_id': base_product_id,
            'category': 'food',
            'ingredients': self._get_ingredients_string(variant=False),
            'sensory_tags': self._get_sensory_tags_string(variant=False),
            'sugar_g': base_nutrition['sugar'],
            'caffeine_mg': base_nutrition['caffeine'],
            'calories': base_nutrition['calories'],
            'protein_g': base_nutrition['protein'],
            'description': base_product_name,
            'price': base_price
        })
        
        # Variant product (with changes) - this is what we're testing
        variant_product_id = f"{base_product_id}_variant"
        variant_nutrition = {
            'sugar': base_nutrition['sugar'] + nutrition_delta.get('sugar', 0),
            'calories': base_nutrition['calories'] + nutrition_delta.get('calories', 0),
            'protein': base_nutrition['protein'] + nutrition_delta.get('protein', 0),
            'caffeine': base_nutrition['caffeine'] + nutrition_delta.get('caffeine', 0)
        }
        variant_price = base_price + self.recipe_variant.get('price_delta', 0.0)
        
        products_data.append({
            'product_id': variant_product_id,
            'category': 'food',
            'ingredients': self._get_ingredients_string(variant=True),
            'sensory_tags': self._get_sensory_tags_string(variant=True),
            'sugar_g': variant_nutrition['sugar'],
            'caffeine_mg': variant_nutrition['caffeine'],
            'calories': variant_nutrition['calories'],
            'protein_g': variant_nutrition['protein'],
            'description': f"{base_product_name} (Modified)",
            'price': variant_price
        })
        
        print(f"Created products:")
        print(f"  Base: {base_product_id} - Price: ${base_price:.2f}, Sugar: {base_nutrition['sugar']}g")
        print(f"  Variant: {variant_product_id} - Price: ${variant_price:.2f}, Sugar: {variant_nutrition['sugar']}g")
        print(f"  Price delta: ${variant_price - base_price:.2f}")
        print(f"  Nutrition delta: Sugar={nutrition_delta.get('sugar', 0):.1f}g, Calories={nutrition_delta.get('calories', 0):.1f}")
        
        products_df = pd.DataFrame(products_data)
        
        # Create contexts DataFrame (simplified)
        contexts_data = []
        time_of_days = ['morning', 'afternoon', 'evening', 'late_night']
        locations = ['home', 'work', 'restaurant', 'outdoor']
        occasions = ['breakfast', 'lunch', 'dinner', 'snack']
        
        for i, (tod, loc, occ) in enumerate(zip(time_of_days, locations, occasions)):
            contexts_data.append({
                'context_id': f'ctx_{i}',
                'time_of_day': tod,
                'location': loc,
                'occasion': occ,
                'price_shown': 5.0
            })
        
        contexts_df = pd.DataFrame(contexts_data)
        
        # Encode products and contexts
        product_embeddings = {}
        context_embeddings = {}
        
        for _, product in products_df.iterrows():
            product_data = {
                'ingredients': product['ingredients'],
                'sensory_tags': product['sensory_tags'],
                'nutrition': {
                    'sugar': product['sugar_g'],
                    'caffeine': product['caffeine_mg'],
                    'calories': product['calories'],
                    'protein': product['protein_g']
                },
                'description': product['description']
            }
            product_embeddings[product['product_id']] = self.model_loader.encode_product(product_data)
        
        # Encode contexts (simplified)
        for _, context in contexts_df.iterrows():
            # Create context embedding manually
            time_ids = torch.LongTensor([[time_of_days.index(context['time_of_day'])]]).to(self.device)
            location_ids = torch.LongTensor([[locations.index(context['location'])]]).to(self.device)
            occasion_ids = torch.LongTensor([[occasions.index(context['occasion'])]]).to(self.device)
            price = torch.FloatTensor([[context['price_shown']]]).to(self.device)
            
            with torch.no_grad():
                z_context = self.phase1_models['context'](time_ids, location_ids, occasion_ids, price)
                context_embeddings[context['context_id']] = z_context.cpu().numpy()[0]
        
        # Create environment
        self.environment = Environment(
            products_df=products_df,
            contexts_df=contexts_df,
            product_embeddings=product_embeddings,
            context_embeddings=context_embeddings,
            enable_dynamic_prices=False,
            enable_new_launches=False,
            enable_macro_context=False
        )
        
        self.variant_product_id = variant_product_id
        self.base_product_id = base_product_id
    
    def _get_ingredients_string(self, variant=False):
        """Get ingredients string for product"""
        ingredient_changes = self.recipe_variant.get('ingredient_changes_json', {})
        
        if variant:
            added = ingredient_changes.get('added', [])
            removed = ingredient_changes.get('removed', [])
            substituted = ingredient_changes.get('substituted', {})
            
            # Simplified: return base ingredients with changes
            base_ingredients = ['flour', 'sugar', 'butter', 'eggs']
            ingredients = [ing for ing in base_ingredients if ing not in removed]
            ingredients.extend(added)
            for old, new in substituted.items():
                if old in ingredients:
                    ingredients.remove(old)
                    ingredients.append(new)
        else:
            ingredients = ['flour', 'sugar', 'butter', 'eggs']
        
        return ','.join(ingredients[:10])
    
    def _get_sensory_tags_string(self, variant=False):
        """Get sensory tags string for product"""
        sensory_delta = self.recipe_variant.get('sensory_delta_json', {})
        
        base_tags = ['sweet', 'creamy', 'rich']
        if variant:
            # Add/modify tags based on sensory delta
            if sensory_delta.get('sweetness', 0) > 0.1:
                base_tags.append('very_sweet')
            if sensory_delta.get('saltiness', 0) > 0.1:
                base_tags.append('salty')
        
        return ','.join(base_tags[:8])
    
    def _initialize_simulator(self):
        """Initialize Phase 3 PopulationSimulator"""
        if PopulationSimulator is None:
            raise RuntimeError("Phase 3 PopulationSimulator not available")
        
        # Create segments DataFrame from agents
        segments_data = []
        segment_map = {}
        
        for agent in self.agents:
            segment_key = f"{agent.get('age_bucket', '25-34')}_{agent.get('archetype', 'value_seeker')}"
            if segment_key not in segment_map:
                segment_map[segment_key] = {
                    'segment_id': segment_key,
                    'age_bucket': agent.get('age_bucket', '25-34'),
                    'region': agent.get('region', 'West'),
                    'psychographic': agent.get('archetype', 'value_seeker')
                }
                segments_data.append(segment_map[segment_key])
        
        segments_df = pd.DataFrame(segments_data)
        
        # Create simulator
        self.simulator = PopulationSimulator(
            phase2_model=self.phase2_model,
            phase1_models=self.phase1_models,
            environment=self.environment,
            device=self.device,
            enable_social_influence=True,
            state_init_noise=0.1
        )
        
        # Initialize agents manually (Phase 3 style)
        # First, encode all segments
        segment_embeddings = {}
        for _, segment_row in segments_df.iterrows():
            segment_data = {
                'age_bucket': segment_row['age_bucket'],
                'region': segment_row['region'],
                'psychographic': segment_row['psychographic']
            }
            z_segment_vec = self.model_loader.encode_segment(segment_data)
            segment_embeddings[segment_row['segment_id']] = z_segment_vec
        
        # Create agents with proper segment embeddings
        self.simulator.agents = []
        agent_id_counter = 0
        
        for agent_data in self.agents:
            segment_key = f"{agent_data.get('age_bucket', '25-34')}_{agent_data.get('archetype', 'value_seeker')}"
            
            # Get segment embedding
            if segment_key in segment_embeddings:
                z_segment_vec = segment_embeddings[segment_key]
            else:
                # Fallback: encode on the fly
                segment_data = {
                    'age_bucket': agent_data.get('age_bucket', '25-34'),
                    'region': agent_data.get('region', 'West'),
                    'psychographic': agent_data.get('archetype', 'value_seeker')
                }
                z_segment_vec = self.model_loader.encode_segment(segment_data)
            
            z_segment = torch.FloatTensor(z_segment_vec).to(self.device)
            
            # Initialize state
            with torch.no_grad():
                s_0 = self.phase2_model.initialize_state(z_segment.unsqueeze(0))
                s_0 = s_0[0].cpu()
            
            # Create personality from behavior params
            behavior_params = agent_data.get('behavior_params_json', {})
            personality = {
                'exploration_rate': behavior_params.get('novelty_seeking', 0.5),
                'social_susceptibility': behavior_params.get('social_influence', 0.5),
                'price_sensitivity': behavior_params.get('price_sensitivity', 0.5)
            }
            
            # Create Phase 3 Agent
            phase3_agent = Agent(
                agent_id=agent_id_counter,
                segment_id=segment_key,
                z_segment=z_segment.cpu(),
                s_t=s_0,
                personality=personality,
                interaction_count=0
            )
            
            self.simulator.agents.append(phase3_agent)
            
            # Map PersonaAgent ID to Phase 3 Agent ID
            self.agent_id_mapping[str(agent_data['id'])] = agent_id_counter
            agent_id_counter += 1
    
    def run_simulation(self, time_horizon_weeks: int = 12) -> Dict:
        """
        Run Phase 3-4 simulation for recipe variant.
        
        Args:
            time_horizon_weeks: Number of weeks to simulate
        
        Returns:
            Dict with simulation results
        """
        print(f"Running Phase 3-4 simulation with {len(self.agents)} agents for {time_horizon_weeks} weeks...")
        
        # Get baseline preferences (before recipe change)
        # Use the agent's actual segment data
        baseline_preferences = {}
        for i, agent in enumerate(self.simulator.agents):
            if i < len(self.agents):
                # Get corresponding PersonaAgent data
                persona_agent = self.agents[i]
                segment_data = {
                    'age_bucket': persona_agent.get('age_bucket', '25-34'),
                    'region': persona_agent.get('region', 'West'),
                    'psychographic': persona_agent.get('archetype', 'value_seeker')
                }
            else:
                segment_data = {
                    'age_bucket': '25-34',
                    'region': 'West',
                    'psychographic': 'value_seeker'
                }
            
            # Encode segment
            z_segment_vec = self.model_loader.encode_segment(segment_data)
            z_segment = torch.FloatTensor(z_segment_vec).unsqueeze(0).to(self.device)
            
            # Get base product embedding
            base_product_data = {
                'ingredients': self._get_ingredients_string(variant=False),
                'sensory_tags': self._get_sensory_tags_string(variant=False),
                'nutrition': {
                    'sugar': 10,
                    'caffeine': 0,
                    'calories': 200,
                    'protein': 5
                },
                'description': self.base_product.get('name', 'Base Product')
            }
            z_product_vec = self.model_loader.encode_product(base_product_data)
            z_product = torch.FloatTensor(z_product_vec).unsqueeze(0).to(self.device)
            
            # Get default context
            time_ids = torch.LongTensor([[0]]).to(self.device)  # morning
            location_ids = torch.LongTensor([[0]]).to(self.device)  # home
            occasion_ids = torch.LongTensor([[0]]).to(self.device)  # breakfast
            price = torch.FloatTensor([[5.0]]).to(self.device)
            
            with torch.no_grad():
                z_context = self.phase1_models['context'](time_ids, location_ids, occasion_ids, price)
                s_0 = self.phase2_model.initialize_state(z_segment)
                # Predict baseline intent
                baseline_intent = self.phase2_model.predict_intent(s_0, z_product, z_context)
                baseline_preferences[agent.agent_id] = baseline_intent[0].item()
        
        # Run simulation focusing on variant product
        # Modify environment to prioritize variant product
        original_product_ids = self.environment.product_ids.copy()
        original_available_products = self.environment.available_products_df.copy()
        
        # Set only variant and base products as available
        self.environment.product_ids = [self.variant_product_id, self.base_product_id]
        variant_base_df = self.environment.products_df[
            self.environment.products_df['product_id'].isin([self.variant_product_id, self.base_product_id])
        ]
        self.environment.available_products_df = variant_base_df.copy()
        
        print(f"Running Phase 3 simulation with {len(self.simulator.agents)} agents")
        print(f"Variant product ID: {self.variant_product_id}")
        print(f"Base product ID: {self.base_product_id}")
        print(f"Available products: {self.environment.product_ids}")
        
        # Run simulation
        n_days = time_horizon_weeks * 7
        # Increase interactions per day to see more state evolution
        # Phase 2 model uses residual connections (slow state changes), so we need more interactions
        interactions_per_day = 3  # Increased to see more dynamics
        results = self.simulator.simulate(
            n_days=n_days,
            interactions_per_day=interactions_per_day,
            use_intent_sampling=True,
            sample_outcomes=False
        )
        
        print(f"Simulation completed. Total interactions: {len(results)}")
        
        # Debug: Check if agent states are actually changing over time
        print(f"\n=== Agent State Evolution Check ===")
        sample_agent_ids = list(self.agent_id_mapping.values())[:5]  # Check first 5 agents
        for phase3_agent_id in sample_agent_ids:
            if phase3_agent_id < len(self.simulator.agents):
                agent = self.simulator.agents[phase3_agent_id]
                # Get agent's interactions with variant product
                agent_results = [r for r in results if r.get('agent_id') == phase3_agent_id and r.get('product_id') == self.variant_product_id]
                if len(agent_results) > 10:
                    # Compare first 10% vs last 10% of interactions
                    early_count = max(1, len(agent_results) // 10)
                    late_count = max(1, len(agent_results) // 10)
                    early_intent = np.mean([r['intent_value'] for r in agent_results[:early_count]])
                    late_intent = np.mean([r['intent_value'] for r in agent_results[-late_count:]])
                    state_change = late_intent - early_intent
                    print(f"Agent {phase3_agent_id}: Early={early_intent:.3f}, Late={late_intent:.3f}, Change={state_change:+.3f}")
        print("=" * 40)
        
        # Restore original product list
        self.environment.product_ids = original_product_ids
        self.environment.available_products_df = original_available_products
        
        # Process results
        if not results or len(results) == 0:
            print("WARNING: No simulation results returned!")
            # Return empty results structure
            return {
                'overall_acceptance_rate': 0.0,
                'overall_rejection_rate': 0.0,
                'mean_preference_delta': 0.0,
                'baseline_preferences': {},
                'preference_deltas': {},
                'final_preferences': {},
                'time_series': [],
                'segment_breakdown': {},
                'actions': {},
                'final_week_metrics': {}
            }
        
        results_df = pd.DataFrame(results)
        print(f"Results DataFrame shape: {results_df.shape}")
        print(f"Columns in results: {list(results_df.columns)}")
        print(f"Product IDs in results: {results_df['product_id'].unique() if 'product_id' in results_df.columns else 'N/A'}")
        
        # Ensure we have a 'day' column for time series aggregation
        # Phase 3 uses 'time_step' which is already in days
        if 'time_step' in results_df.columns and 'day' not in results_df.columns:
            results_df['day'] = results_df['time_step']
        
        # Filter results for variant product
        variant_results = results_df[results_df['product_id'] == self.variant_product_id].copy()
        print(f"Variant product interactions: {len(variant_results)}")
        
        # Also get base product results for comparison
        base_results = results_df[results_df['product_id'] == self.base_product_id].copy()
        print(f"Base product interactions: {len(base_results)}")
        
        # Compute baseline preferences FIRST (before computing variant metrics)
        baseline_preferences = {}
        for agent_id, phase3_agent_id in self.agent_id_mapping.items():
            if phase3_agent_id < len(self.simulator.agents):
                agent = self.simulator.agents[phase3_agent_id]
                # Get agent's baseline preference for base product using initial state
                base_product_data = {
                    'ingredients': self._get_ingredients_string(variant=False),
                    'sensory_tags': self._get_sensory_tags_string(variant=False),
                    'nutrition': {
                        'sugar': self.environment.products_df[self.environment.products_df['product_id'] == self.base_product_id]['sugar_g'].iloc[0],
                        'caffeine': self.environment.products_df[self.environment.products_df['product_id'] == self.base_product_id]['caffeine_mg'].iloc[0],
                        'calories': self.environment.products_df[self.environment.products_df['product_id'] == self.base_product_id]['calories'].iloc[0],
                        'protein': self.environment.products_df[self.environment.products_df['product_id'] == self.base_product_id]['protein_g'].iloc[0]
                    },
                    'description': self.base_product.get('name', 'Base Product')
                }
                z_product_vec = self.model_loader.encode_product(base_product_data)
                z_product = torch.FloatTensor(z_product_vec).unsqueeze(0).to(self.device)
                
                # Use initial agent state for baseline
                z_segment = agent.z_segment.unsqueeze(0).to(self.device)
                with torch.no_grad():
                    s_0 = self.phase2_model.initialize_state(z_segment)
                    # Get default context
                    context_id_for_baseline = self.environment.context_ids[0]
                    z_context = self.environment.get_context_embedding(context_id_for_baseline)
                    z_context = torch.FloatTensor(z_context).unsqueeze(0).to(self.device)
                    baseline_intent = self.phase2_model.predict_intent(s_0, z_product, z_context)
                    baseline_preferences[phase3_agent_id] = baseline_intent[0].item()
        
        # Compute metrics from actual Phase 3 results
        if len(variant_results) > 0:
            # Use actual intent values from Phase 3 simulation
            intent_values = variant_results['intent_value'].values
            
            # Debug: Print intent value distribution
            print(f"Intent value stats: min={intent_values.min():.3f}, max={intent_values.max():.3f}, mean={intent_values.mean():.3f}, median={np.median(intent_values):.3f}")
            print(f"Intent value distribution: <0.3: {(intent_values < 0.3).sum()}, 0.3-0.5: {((intent_values >= 0.3) & (intent_values < 0.5)).sum()}, 0.5-0.7: {((intent_values >= 0.5) & (intent_values < 0.7)).sum()}, >=0.7: {(intent_values >= 0.7).sum()}")
            
            # Compute acceptance/rejection relative to baseline preferences
            # For each interaction, compare variant intent to agent's baseline
            variant_with_baseline = []
            for _, row in variant_results.iterrows():
                agent_id = row['agent_id']
                variant_intent = row['intent_value']
                baseline_intent = baseline_preferences.get(agent_id, 0.5)
                variant_with_baseline.append({
                    'variant_intent': variant_intent,
                    'baseline_intent': baseline_intent,
                    'delta': variant_intent - baseline_intent
                })
            
            variant_with_baseline_df = pd.DataFrame(variant_with_baseline)
            
            # Acceptance: variant intent > baseline AND variant intent > 0.55
            # Rejection: variant intent < baseline OR variant intent < 0.45
            overall_acceptance_rate = ((variant_with_baseline_df['variant_intent'] > variant_with_baseline_df['baseline_intent']) & 
                                      (variant_with_baseline_df['variant_intent'] > 0.55)).mean()
            overall_rejection_rate = ((variant_with_baseline_df['variant_intent'] < variant_with_baseline_df['baseline_intent']) | 
                                     (variant_with_baseline_df['variant_intent'] < 0.45)).mean()
            mean_preference = float(intent_values.mean())
            mean_delta = float(variant_with_baseline_df['delta'].mean())
            
            print(f"Variant product - Mean intent: {mean_preference:.3f}, Mean delta vs baseline: {mean_delta:.3f}")
            print(f"Acceptance (variant > baseline & >0.55): {overall_acceptance_rate:.3f}")
            print(f"Rejection (variant < baseline or <0.45): {overall_rejection_rate:.3f}")
        else:
            print("WARNING: No variant product interactions found!")
            # If no variant interactions, check if agents preferred base product
            if len(base_results) > 0:
                # Agents preferred base product - this is rejection of variant
                overall_acceptance_rate = 0.0
                overall_rejection_rate = 1.0
                mean_preference = 0.3  # Low preference since they chose base instead
            else:
                overall_acceptance_rate = 0.0
                overall_rejection_rate = 0.0
                mean_preference = 0.5
        
        # Compute preference deltas from actual Phase 3 agent interactions
        preference_deltas = {}
        final_preferences = {}
        
        # Get final agent states from simulator (more accurate than just last interaction)
        for agent_id, phase3_agent_id in self.agent_id_mapping.items():
            if phase3_agent_id < len(self.simulator.agents):
                agent = self.simulator.agents[phase3_agent_id]
                
                # Get agent's interactions with variant product
                agent_variant_results = variant_results[variant_results['agent_id'] == phase3_agent_id]
                
                if len(agent_variant_results) > 0:
                    # Use mean intent across all interactions (more stable)
                    final_pref = float(agent_variant_results['intent_value'].mean())
                    baseline_pref = baseline_preferences.get(phase3_agent_id, 0.5)
                    preference_deltas[agent_id] = final_pref - baseline_pref
                    final_preferences[agent_id] = final_pref
                else:
                    # Agent didn't interact with variant - check if they interacted with base
                    agent_base_results = base_results[base_results['agent_id'] == phase3_agent_id]
                    if len(agent_base_results) > 0:
                        # Agent preferred base product - negative delta
                        baseline_pref = baseline_preferences.get(phase3_agent_id, 0.5)
                        preference_deltas[agent_id] = -0.2  # Negative preference delta
                        final_preferences[agent_id] = max(0.0, baseline_pref - 0.2)
                    else:
                        # No interactions - use baseline
                        preference_deltas[agent_id] = 0.0
                        final_preferences[agent_id] = baseline_preferences.get(phase3_agent_id, 0.5)
            else:
                preference_deltas[agent_id] = 0.0
                final_preferences[agent_id] = baseline_preferences.get(phase3_agent_id, 0.5)
        
        print(f"Computed preference deltas for {len(preference_deltas)} agents")
        print(f"Mean preference delta: {np.mean(list(preference_deltas.values())):.3f}")
        
        # Time series aggregation (by week) - using REAL Phase 3 time_step data
        time_series = []
        
        # Ensure we have 'day' column from time_step (Phase 3 uses time_step which increments per day)
        if 'day' not in variant_results.columns:
            if 'time_step' in variant_results.columns:
                # time_step is already in days (increments by 1 per day in Phase 3)
                variant_results['day'] = variant_results['time_step'].astype(int)
            else:
                # Last resort: estimate from index
                variant_results['day'] = (variant_results.index * time_horizon_weeks * 7) // len(variant_results)
        
        # Debug: Print time_step range
        if 'time_step' in variant_results.columns:
            print(f"Time step range: {variant_results['time_step'].min()} to {variant_results['time_step'].max()}")
            print(f"Day range: {variant_results['day'].min()} to {variant_results['day'].max()}")
        
        for week in range(time_horizon_weeks):
            week_start_day = week * 7
            week_end_day = (week + 1) * 7
            
            # Filter interactions for this week using actual time_step/day from Phase 3
            week_results = variant_results[
                (variant_results['day'] >= week_start_day) & 
                (variant_results['day'] < week_end_day)
            ]
            
            if len(week_results) > 0:
                # Use REAL intent values from Phase 3 interactions for this week
                week_intent_values = week_results['intent_value'].values
                
                # CRITICAL: Track agent state evolution over time
                # Get agent states at the END of this week (from Phase 3 simulator)
                week_agent_states = {}
                for agent_id, phase3_agent_id in self.agent_id_mapping.items():
                    if phase3_agent_id < len(self.simulator.agents):
                        agent = self.simulator.agents[phase3_agent_id]
                        # Get agent's interactions up to this week
                        agent_week_results = week_results[week_results['agent_id'] == phase3_agent_id]
                        if len(agent_week_results) > 0:
                            # Use the LAST interaction's intent (reflects current state)
                            week_agent_states[agent_id] = agent_week_results['intent_value'].iloc[-1]
                
                # Compute metrics from actual Phase 3 data (no artificial fluctuations)
                mean_pref = float(week_intent_values.mean())
                pref_std = float(week_intent_values.std()) if len(week_intent_values) > 1 else 0.0
                
                # Track preference evolution: compare early vs late interactions in the week
                # This captures state changes DURING the week
                if len(week_results) > 10:
                    early_half = week_results.iloc[:len(week_results)//2]['intent_value'].mean()
                    late_half = week_results.iloc[len(week_results)//2:]['intent_value'].mean()
                    preference_trend = float(late_half - early_half)  # Positive = increasing, Negative = decreasing
                else:
                    preference_trend = 0.0
                
                # Compare against baseline for this week's interactions
                week_with_baseline = []
                for _, row in week_results.iterrows():
                    agent_id = row['agent_id']
                    variant_intent = row['intent_value']
                    baseline_intent = baseline_preferences.get(agent_id, 0.5)
                    week_with_baseline.append({
                        'variant_intent': variant_intent,
                        'baseline_intent': baseline_intent,
                        'delta': variant_intent - baseline_intent
                    })
                
                week_with_baseline_df = pd.DataFrame(week_with_baseline)
                
                # Acceptance/rejection relative to baseline
                acceptance_rate = ((week_with_baseline_df['variant_intent'] > week_with_baseline_df['baseline_intent']) & 
                                  (week_with_baseline_df['variant_intent'] > 0.55)).mean()
                rejection_rate = ((week_with_baseline_df['variant_intent'] < week_with_baseline_df['baseline_intent']) | 
                                 (week_with_baseline_df['variant_intent'] < 0.45)).mean()
                mean_delta = float(week_with_baseline_df['delta'].mean())
                
                time_series.append({
                    'week': week + 1,
                    'acceptance_rate': float(acceptance_rate),
                    'rejection_rate': float(rejection_rate),
                    'mean_preference': mean_pref,  # REAL mean from Phase 3 interactions
                    'preference_std': pref_std,    # REAL std from Phase 3 interactions
                    'mean_preference_delta': mean_delta,  # REAL delta vs baseline
                    'preference_trend': preference_trend,  # Change within week (early vs late)
                    'interaction_count': len(week_results)  # Track number of interactions
                })
                
                print(f"Week {week + 1}: {len(week_results)} interactions, mean_pref={mean_pref:.3f} (trend={preference_trend:+.3f}), mean_delta={mean_delta:.3f}, acceptance={acceptance_rate:.3f}")
            else:
                # No interactions this week - use previous week's values or baseline
                if len(time_series) > 0:
                    # Carry forward last known values (agents haven't interacted yet)
                    last_week = time_series[-1]
                    time_series.append({
                        'week': week + 1,
                        'acceptance_rate': last_week['acceptance_rate'],
                        'rejection_rate': last_week['rejection_rate'],
                        'mean_preference': last_week['mean_preference'],
                        'preference_std': last_week['preference_std'],
                        'interaction_count': 0
                    })
                else:
                    # First week with no data - use neutral baseline
                    time_series.append({
                        'week': week + 1,
                        'acceptance_rate': 0.0,
                        'rejection_rate': 0.0,
                        'mean_preference': 0.5,
                        'preference_std': 0.0,
                        'interaction_count': 0
                    })
        
        # Segment breakdown
        segment_breakdown = {}
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
                        'region': agent.get('region', '')
                    }
                }
            
            segment_breakdown[segment_key]['count'] += 1
            agent_id = str(agent['id'])
            delta = preference_deltas.get(agent_id, 0.0)
            segment_breakdown[segment_key]['mean_preference_delta'] += delta
            
            # Determine action based on preference
            final_pref = final_preferences.get(agent_id, 0.5)
            if final_pref < 0.3:
                action = 'reject'
            elif final_pref < 0.5:
                action = 'substitute'
            elif final_pref < 0.6:
                action = 'reduce_frequency'
            elif final_pref >= 0.8:
                action = 'increase_frequency'
            else:
                action = 'accept'
            
            segment_breakdown[segment_key]['actions'][action] += 1
        
        # Normalize segment breakdown
        for segment in segment_breakdown.values():
            if segment['count'] > 0:
                segment['mean_preference_delta'] /= segment['count']
                for action in segment['actions']:
                    segment['actions'][action] /= segment['count']
        
        # Actions dict
        actions = {}
        for agent_id, phase3_agent_id in self.agent_id_mapping.items():
            final_pref = final_preferences.get(agent_id, 0.5)
            if final_pref < 0.3:
                actions[agent_id] = 'reject'
            elif final_pref < 0.5:
                actions[agent_id] = 'substitute'
            elif final_pref < 0.6:
                actions[agent_id] = 'reduce_frequency'
            elif final_pref >= 0.8:
                actions[agent_id] = 'increase_frequency'
            else:
                actions[agent_id] = 'accept'
        
        return {
            'overall_acceptance_rate': float(overall_acceptance_rate),
            'overall_rejection_rate': float(overall_rejection_rate),
            'mean_preference_delta': float(np.mean(list(preference_deltas.values()))),
            'baseline_preferences': {k: float(v) for k, v in baseline_preferences.items()},
            'preference_deltas': {k: float(v) for k, v in preference_deltas.items()},
            'final_preferences': {k: float(v) for k, v in final_preferences.items()},
            'time_series': time_series,
            'segment_breakdown': segment_breakdown,
            'actions': actions,
            'final_week_metrics': time_series[-1] if time_series else {}
        }

