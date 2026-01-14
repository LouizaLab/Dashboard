"""
Phase 3: Large Population Model (LPM)
Agent, Environment, and Population Simulator
"""

import torch
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

@dataclass
class Agent:
    """Represents a single agent in the population"""
    agent_id: int
    segment_id: str
    z_segment: torch.Tensor  # Segment embedding
    s_t: torch.Tensor  # Current behavioral state
    personality: Dict[str, float]  # Personality parameters
    interaction_count: int = 0
    
    def __post_init__(self):
        """Initialize agent state"""
        if self.s_t is None:
            raise ValueError("State must be initialized")
    
    def get_state_components(self, state_model):
        """Extract state components"""
        return state_model.get_components(self.s_t)


class Environment:
    """Manages products, contexts, and environment state"""
    
    def __init__(self, 
                 products_df: pd.DataFrame,
                 contexts_df: pd.DataFrame,
                 product_embeddings: Dict[str, np.ndarray],
                 context_embeddings: Dict[str, np.ndarray],
                 seed: int = 42,
                 enable_dynamic_prices: bool = True,
                 enable_new_launches: bool = True,
                 enable_macro_context: bool = True):
        self.products_df = products_df.copy()
        self.contexts_df = contexts_df
        self.product_embeddings = product_embeddings.copy()
        self.context_embeddings = context_embeddings
        
        np.random.seed(seed)
        random.seed(seed)
        
        # Product catalog (can change over time)
        self.all_products_df = products_df.copy()  # Master catalog
        
        # Start with subset of products available (for new launches to matter)
        if enable_new_launches:
            # Start with 70% of products available
            n_start = max(1, int(len(products_df) * 0.7))
            self.available_products_df = products_df.sample(n=n_start, random_state=seed).copy()
        else:
            self.available_products_df = products_df.copy()
        
        self.product_ids = self.available_products_df['product_id'].tolist()
        self.product_categories = products_df.set_index('product_id')['category'].to_dict()
        self.product_prices = products_df.set_index('product_id')['price'].to_dict()
        
        # Track product launches
        self.product_launch_dates = {}  # product_id -> launch_date
        self.enable_new_launches = enable_new_launches
        
        # Price dynamics
        self.enable_dynamic_prices = enable_dynamic_prices
        self.base_prices = self.product_prices.copy()
        self.price_history = []  # Track price changes
        
        # Context pool
        self.context_ids = contexts_df['context_id'].tolist()
        
        # Time management
        self.current_time = None
        self.time_step = 0
        
        # Macro context
        self.enable_macro_context = enable_macro_context
        self.macro_context = {
            'season': 'winter',  # winter, spring, summer, fall
            'inflation_regime': 'normal',  # low, normal, high
            'market_sentiment': 0.5  # 0-1 scale
        }
    
    def get_product_embedding(self, product_id: str) -> torch.Tensor:
        """Get product embedding"""
        if product_id in self.product_embeddings:
            return torch.FloatTensor(self.product_embeddings[product_id])
        else:
            # Fallback: find similar product
            return torch.FloatTensor(list(self.product_embeddings.values())[0])
    
    def get_context_embedding(self, context_id: str) -> torch.Tensor:
        """Get context embedding"""
        if context_id in self.context_embeddings:
            return torch.FloatTensor(self.context_embeddings[context_id])
        else:
            return torch.FloatTensor(list(self.context_embeddings.values())[0])
    
    def sample_product(self, 
                      agent_state: Optional[torch.Tensor] = None,
                      intent_scores: Optional[Dict[str, float]] = None,
                      exploration_rate: float = 0.1,
                      social_influence: Optional[Dict[str, float]] = None) -> str:
        """
        Sample a product for an agent
        Args:
            agent_state: Current agent state (for intent-based sampling)
            intent_scores: Pre-computed intent scores for products
            exploration_rate: Probability of random exploration
            social_influence: Optional dict of product_id -> popularity weight from neighbors
        """
        # Get available products (respects new launches)
        available_products = self.available_products_df['product_id'].tolist()
        
        if np.random.random() < exploration_rate:
            # Exploration: random product from available
            return np.random.choice(available_products)
        
        # Combine intent scores with social influence
        if intent_scores is not None:
            combined_scores = intent_scores.copy()
            
            # Add social influence if provided
            if social_influence is not None:
                for product_id, social_weight in social_influence.items():
                    if product_id in combined_scores:
                        # Blend intent with social influence (weighted average)
                        combined_scores[product_id] = 0.7 * combined_scores[product_id] + 0.3 * social_weight
            
            # Filter to available products only
            available_scores = {pid: score for pid, score in combined_scores.items() if pid in available_products}
            
            if len(available_scores) > 0:
                products = list(available_scores.keys())
                scores = np.array([available_scores[p] for p in products])
                # Normalize to probabilities
                scores = np.maximum(scores, 0.0)  # Ensure non-negative
                if scores.sum() > 0:
                    probs = scores / scores.sum()
                    return np.random.choice(products, p=probs)
        
        # Fallback: random from available
        return np.random.choice(available_products)
    
    def sample_context(self, 
                      time_of_day: Optional[str] = None,
                      hour: Optional[int] = None,
                      macro_context: Optional[Dict] = None) -> str:
        """
        Sample a context, optionally matching time of day and macro context
        """
        if time_of_day is not None:
            # Filter contexts by time of day
            matching_contexts = self.contexts_df[
                self.contexts_df['time_of_day'] == time_of_day
            ]['context_id'].tolist()
            if matching_contexts:
                context_id = np.random.choice(matching_contexts)
                
                # Adjust price in context based on macro context
                if macro_context and 'inflation_regime' in macro_context:
                    # This would modify the context embedding, but for now we just return it
                    # In a full implementation, we'd adjust the price_shown in the context
                    pass
                
                return context_id
        
        # Random context
        return np.random.choice(self.context_ids)
    
    def get_macro_context(self) -> Dict:
        """Get current macro context"""
        return self.macro_context.copy()
    
    def get_time_context(self, current_time: datetime) -> Dict[str, any]:
        """Get time-based context information"""
        hour = current_time.hour
        
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'late_night'
        
        return {
            'hour': hour,
            'time_of_day': time_of_day,
            'day_of_week': current_time.weekday()
        }
    
    def update_macro_context(self):
        """Update macro context based on current time"""
        if not self.enable_macro_context or self.current_time is None:
            return
        
        month = self.current_time.month
        # Determine season
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'fall'
        
        self.macro_context['season'] = season
        
        # Simulate inflation regime (can be made more sophisticated)
        # For now, random walk with higher probability
        current_inflation = self.macro_context['inflation_regime']
        if np.random.random() < 0.2:  # 20% chance to change (increased from 10%)
            regimes = ['low', 'normal', 'high']
            current_idx = regimes.index(current_inflation) if current_inflation in regimes else 1
            # Random walk
            if np.random.random() < 0.5 and current_idx > 0:
                self.macro_context['inflation_regime'] = regimes[current_idx - 1]
            elif np.random.random() < 0.5 and current_idx < len(regimes) - 1:
                self.macro_context['inflation_regime'] = regimes[current_idx + 1]
    
    def launch_new_products(self, n_new: int = 1):
        """Launch new products (add to available catalog)"""
        if not self.enable_new_launches:
            return
        
        # Find products not yet launched
        available_ids = set(self.available_products_df['product_id'].tolist())
        all_ids = set(self.all_products_df['product_id'].tolist())
        unlaunched = list(all_ids - available_ids)
        
        if len(unlaunched) == 0:
            return  # All products already launched
        
        # Launch n_new products
        to_launch = np.random.choice(unlaunched, size=min(n_new, len(unlaunched)), replace=False)
        
        for product_id in to_launch:
            product = self.all_products_df[self.all_products_df['product_id'] == product_id].iloc[0]
            self.available_products_df = pd.concat([self.available_products_df, pd.DataFrame([product])], ignore_index=True)
            self.product_ids.append(product_id)
            self.product_launch_dates[product_id] = self.current_time
        
        if len(to_launch) > 0:
            print(f"  Launched {len(to_launch)} new products: {list(to_launch)}")
    
    def update_prices(self, volatility: float = 0.02):
        """Update product prices (simulate price changes)"""
        if not self.enable_dynamic_prices:
            return
        
        # Update prices based on inflation regime
        inflation_multiplier = {
            'low': 0.99,  # Prices decrease slightly
            'normal': 1.0,  # Prices stable
            'high': 1.01  # Prices increase
        }
        
        base_mult = inflation_multiplier.get(self.macro_context['inflation_regime'], 1.0)
        
        # Add random volatility
        for product_id in self.product_ids:
            if product_id in self.base_prices:
                # Random walk with drift
                change = np.random.normal(0, volatility)
                new_price = self.base_prices[product_id] * base_mult * (1 + change)
                self.product_prices[product_id] = max(0.5, new_price)  # Floor price
        
        # Record price change
        if self.current_time:
            self.price_history.append({
                'date': self.current_time,
                'inflation_regime': self.macro_context['inflation_regime'],
                'mean_price': np.mean(list(self.product_prices.values()))
            })
    
    def get_product_price(self, product_id: str) -> float:
        """Get current price for a product"""
        return self.product_prices.get(product_id, 2.5)  # Default price
    
    def advance_time(self, days: int = 1):
        """Advance simulation time"""
        if self.current_time is None:
            self.current_time = datetime(2024, 1, 1)
        else:
            self.current_time += timedelta(days=days)
        self.time_step += days
        
        # Update macro context
        self.update_macro_context()
        
        # Update prices periodically
        if self.enable_dynamic_prices and self.time_step % 7 == 0 and self.time_step > 0:  # Weekly price updates
            self.update_prices()
        
        # Launch new products periodically
        if self.enable_new_launches and self.time_step % 10 == 0 and self.time_step > 0:
            # Launch 1-2 new products every 10 days
            n_new = np.random.randint(1, 3)
            self.launch_new_products(n_new)


class PopulationSimulator:
    """
    Simulates a population of agents interacting with products over time
    """
    
    def __init__(self,
                 phase2_model,
                 phase1_models,
                 environment: Environment,
                 device: str = 'cpu',
                 enable_social_influence: bool = True,
                 state_init_noise: float = 0.1):
        self.phase2_model = phase2_model
        self.phase1_models = phase1_models
        self.environment = environment
        self.device = device
        self.enable_social_influence = enable_social_influence
        self.state_init_noise = state_init_noise
        
        self.agents: List[Agent] = []
        self.results: List[Dict] = []
        
        # Move model to device
        self.phase2_model = self.phase2_model.to(device)
        self.phase2_model.eval()
    
    def initialize_agent_state(self, z_segment: torch.Tensor) -> torch.Tensor:
        """
        Initialize agent state probabilistically: s_0 ~ p(s_0 | segment)
        Adds noise to deterministic initialization for variance
        """
        with torch.no_grad():
            # Deterministic base state
            s_0_base = self.phase2_model.initialize_state(z_segment.unsqueeze(0).to(self.device))
            s_0_base = s_0_base[0].cpu()
            
            # Add noise for probabilistic initialization
            if self.state_init_noise > 0:
                noise = torch.randn_like(s_0_base) * self.state_init_noise
                s_0 = s_0_base + noise
                # Renormalize
                s_0 = torch.nn.functional.normalize(s_0, p=2, dim=0)
            else:
                s_0 = s_0_base
            
            return s_0
    
    def initialize_agents(self, 
                        segments_df: pd.DataFrame,
                        n_agents: int = 10,
                        segment_distribution: Optional[Dict[str, float]] = None):
        """
        Initialize agents from segments with probabilistic state initialization
        Args:
            segments_df: DataFrame with segment information
            n_agents: Number of agents to create
            segment_distribution: Optional distribution of segments (default: uniform)
        """
        self.agents = []
        
        # Get segment embeddings (will be set externally)
        # This method is kept for compatibility but actual initialization happens in simulate_phase3.py
        
        # Determine segment distribution
        if segment_distribution is None:
            segment_ids = segments_df['segment_id'].tolist()
            segment_distribution = {sid: 1.0 / len(segment_ids) for sid in segment_ids}
        
        print(f"Agent initialization will be handled by main simulation script")
    
    def _encode_segment(self, segment_row) -> torch.Tensor:
        """Encode segment using Phase 1 model"""
        # This will be handled in the main simulation script
        # For now, return placeholder - actual encoding done in simulate_phase3.py
        return torch.zeros(64)  # Placeholder
    
    def compute_social_influence(self) -> Dict[str, float]:
        """
        Compute social influence: popularity of products among neighbors
        Returns dict of product_id -> popularity weight
        """
        if not self.enable_social_influence or len(self.agents) < 2:
            return {}
        
        # Count recent product choices (last N interactions)
        product_counts = {}
        recent_results = self.results[-len(self.agents)*5:] if len(self.results) > 0 else []
        
        for result in recent_results:
            product_id = result.get('product_id')
            if product_id:
                product_counts[product_id] = product_counts.get(product_id, 0) + 1
        
        # Normalize to weights
        total = sum(product_counts.values())
        if total > 0:
            social_weights = {pid: count / total for pid, count in product_counts.items()}
        else:
            social_weights = {}
        
        return social_weights
    
    def simulate_step(self, 
                     use_intent_sampling: bool = True,
                     sample_outcomes: bool = False) -> List[Dict]:
        """
        Simulate one time step for all agents
        Returns list of interactions
        """
        step_results = []
        
        # Get time context and macro context
        time_info = self.environment.get_time_context(self.environment.current_time)
        macro_context = self.environment.get_macro_context()
        
        # Compute social influence
        social_influence = self.compute_social_influence() if self.enable_social_influence else None
        
        # Batch process agents for efficiency
        batch_size = len(self.agents)
        if batch_size == 0:
            return step_results
        
        # Prepare batch data
        z_segments = torch.stack([agent.z_segment for agent in self.agents]).to(self.device)
        s_t_batch = torch.stack([agent.s_t for agent in self.agents]).to(self.device)
        
        # Sample products and contexts for each agent
        product_ids = []
        context_ids = []
        z_products_batch = []
        z_contexts_batch = []
        
        # Get available products (respects new launches)
        available_products = self.environment.available_products_df['product_id'].tolist()
        
        for i, agent in enumerate(self.agents):
            # Sample product
            if use_intent_sampling:
                # Pre-compute intent scores for available products
                intent_scores = {}
                products_to_score = available_products[:min(15, len(available_products))]  # Limit for efficiency
                
                for pid in products_to_score:
                    z_product = self.environment.get_product_embedding(pid).to(self.device)
                    z_context = self.environment.get_context_embedding(
                        self.environment.sample_context(time_info['time_of_day'], macro_context=macro_context)
                    ).to(self.device)
                    
                    with torch.no_grad():
                        intent = self.phase2_model.predict_intent(
                            agent.s_t.unsqueeze(0).to(self.device),
                            z_product.unsqueeze(0),
                            z_context.unsqueeze(0)
                        )
                        intent_scores[pid] = intent.item()
                
                # Apply social influence if enabled
                agent_social_influence = None
                if social_influence and agent.personality.get('social_susceptibility', 0) > 0:
                    # Weight social influence by agent's susceptibility
                    agent_social_influence = {
                        pid: weight * agent.personality['social_susceptibility']
                        for pid, weight in social_influence.items()
                    }
                
                product_id = self.environment.sample_product(
                    agent_state=agent.s_t,
                    intent_scores=intent_scores,
                    exploration_rate=agent.personality['exploration_rate'],
                    social_influence=agent_social_influence
                )
            else:
                product_id = self.environment.sample_product()
            
            # Sample context with macro context
            context_id = self.environment.sample_context(
                time_info['time_of_day'],
                macro_context=macro_context
            )
            
            product_ids.append(product_id)
            context_ids.append(context_id)
            
            z_products_batch.append(self.environment.get_product_embedding(product_id))
            z_contexts_batch.append(self.environment.get_context_embedding(context_id))
        
        # Batch process
        z_products_batch = torch.stack(z_products_batch).to(self.device)
        z_contexts_batch = torch.stack(z_contexts_batch).to(self.device)
        
        # Predict intent for all agents
        with torch.no_grad():
            intent_batch = self.phase2_model.predict_intent(
                s_t_batch, z_products_batch, z_contexts_batch
            )
        
        # Update states
        with torch.no_grad():
            # Use predicted intent for state update
            s_t_next_batch = self.phase2_model.update_state(
                s_t_batch, z_products_batch, z_contexts_batch, intent_batch
            )
        
        # Process results and update agents
        for i, agent in enumerate(self.agents):
            intent_value = intent_batch[i].item()
            
            # Sample outcome if requested
            if sample_outcomes:
                outcome = 1 if np.random.random() < intent_value else 0
            else:
                outcome = intent_value
            
            # Update agent state
            agent.s_t = s_t_next_batch[i].cpu()
            agent.interaction_count += 1
            
            # Get current price
            current_price = self.environment.get_product_price(product_ids[i])
            
            # Record interaction
            interaction = {
                'agent_id': agent.agent_id,
                'segment_id': agent.segment_id,
                'timestamp': self.environment.current_time,
                'time_step': self.environment.time_step,
                'product_id': product_ids[i],
                'context_id': context_ids[i],
                'intent_value': intent_value,
                'outcome': outcome,
                'product_category': self.environment.product_categories.get(product_ids[i], 'unknown'),
                'price': current_price,
                'season': macro_context.get('season', 'unknown'),
                'inflation_regime': macro_context.get('inflation_regime', 'unknown')
            }
            step_results.append(interaction)
        
        self.results.extend(step_results)
        return step_results
    
    def simulate(self, 
                n_days: int = 30,
                interactions_per_day: int = 1,
                use_intent_sampling: bool = True,
                sample_outcomes: bool = False):
        """
        Run simulation for specified number of days
        """
        print(f"Starting simulation: {n_days} days, {interactions_per_day} interactions/day")
        
        # Initialize time
        self.environment.current_time = datetime(2024, 1, 1)
        self.environment.time_step = 0
        
        total_steps = n_days * interactions_per_day
        
        for day in range(n_days):
            for interaction in range(interactions_per_day):
                step_results = self.simulate_step(
                    use_intent_sampling=use_intent_sampling,
                    sample_outcomes=sample_outcomes
                )
                
                if (day * interactions_per_day + interaction + 1) % 10 == 0:
                    print(f"  Completed {day * interactions_per_day + interaction + 1}/{total_steps} steps")
            
            # Advance time
            self.environment.advance_time(days=1)
        
        print(f"Simulation complete: {len(self.results)} interactions recorded")
        return self.results
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame"""
        if not self.results:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.results)
        return df
    
    def get_aggregate_statistics(self) -> Dict:
        """Compute aggregate statistics"""
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        stats = {
            'total_interactions': len(df),
            'unique_agents': df['agent_id'].nunique(),
            'unique_products': df['product_id'].nunique(),
            'mean_intent': df['intent_value'].mean(),
            'intent_by_category': df.groupby('product_category')['intent_value'].mean().to_dict(),
            'intent_by_segment': df.groupby('segment_id')['intent_value'].mean().to_dict(),
            'interactions_per_agent': df.groupby('agent_id').size().to_dict()
        }
        
        return stats

