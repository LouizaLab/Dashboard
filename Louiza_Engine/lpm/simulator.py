"""
LPM Simulator - Main simulation runtime.

Executes the timestep loop, samples actions, and aggregates outcomes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import json

from lpm.agent_registry import AgentRegistry
from lpm.environment import EnvironmentManager, EnvironmentState
from ibde.state import EnvironmentInputs, Logits
from ibde.ibde_step import ibde_step_batched
from pme.persona_schema import PersonaSet
from data_engine.loaders import DataLoader
from common.seeds import SeedManager
from common.versioning import hash_scenario_config


class Aggregator:
    """Streaming aggregator for simulation metrics."""
    
    def __init__(self, brand_ids: List[str], regions: List[str], persona_ids: List[str]):
        """Initialize aggregator."""
        self.brand_ids = brand_ids
        self.regions = regions
        self.persona_ids = persona_ids
        
        # Counters keyed by (week_id, brand_id, region_id, persona_id)
        self.transactions = {}  # (week_id, brand_id, region_id, persona_id) -> count
        self.revenue = {}  # (week_id, brand_id, region_id, persona_id) -> sum
        
    def record_event(
        self,
        week_id: int,
        brand_idx: int,
        region_idx: int,
        persona_idx: int,
        price: float
    ):
        """Record a purchase event."""
        brand_id = self.brand_ids[brand_idx]
        region_id = self.regions[region_idx]
        persona_id = self.persona_ids[persona_idx]
        
        key = (week_id, brand_id, region_id, persona_id)
        
        self.transactions[key] = self.transactions.get(key, 0) + 1
        self.revenue[key] = self.revenue.get(key, 0.0) + price
    
    def get_aggregates(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get aggregated metrics.
        
        Returns:
            Tuple of (simulated_metrics, persona_contributions)
        """
        # Build simulated_metrics table
        metrics_rows = []
        for (week_id, brand_id, region_id, persona_id), count in self.transactions.items():
            rev = self.revenue.get((week_id, brand_id, region_id, persona_id), 0.0)
            metrics_rows.append({
                "week_id": week_id,
                "brand_id": brand_id,
                "region_id": region_id,
                "transactions_sim": count,
                "revenue_sim": rev
            })
        
        simulated_metrics = pd.DataFrame(metrics_rows)
        
        # Aggregate across personas for total metrics
        if len(simulated_metrics) > 0:
            simulated_metrics = simulated_metrics.groupby(
                ["week_id", "brand_id", "region_id"]
            ).agg({
                "transactions_sim": "sum",
                "revenue_sim": "sum"
            }).reset_index()
        
        # Build persona_contributions table
        persona_rows = []
        for (week_id, brand_id, region_id, persona_id), count in self.transactions.items():
            rev = self.revenue.get((week_id, brand_id, region_id, persona_id), 0.0)
            persona_rows.append({
                "week_id": week_id,
                "brand_id": brand_id,
                "region_id": region_id,
                "persona_id": persona_id,
                "transactions_sim": count,
                "revenue_sim": rev
            })
        
        persona_contributions = pd.DataFrame(persona_rows)
        
        return simulated_metrics, persona_contributions


class LPMSimulator:
    """
    Large Population Model Simulator.
    
    Executes the simulation loop: IBDE → sampling → aggregation.
    """
    
    def __init__(
        self,
        personaset: PersonaSet,
        data_loader: DataLoader,
        scenario_config: Dict[str, Any],
        num_agents: int = 10000,
        seed: int = 42
    ):
        """
        Initialize simulator.
        
        Args:
            personaset: PersonaSet to use
            data_loader: DataLoader for environment schedules
            scenario_config: Scenario configuration
            num_agents: Number of agents
            seed: Random seed
        """
        self.personaset = personaset
        self.data_loader = data_loader
        self.scenario_config = scenario_config
        self.num_agents = num_agents
        self.seed = seed
        self.seed_manager = SeedManager(base_seed=seed)
        
        # Get brand and region lists
        self.brand_ids = self._get_brand_ids()
        self.regions = self._get_regions()
        
        # Initialize agent registry (pass num_brands for brand_loyalty initialization)
        self.agent_registry = AgentRegistry(
            personaset=personaset,
            num_agents=num_agents,
            regions=self.regions,
            num_brands=len(self.brand_ids),
            seed=seed
        )
        
        # Initialize aggregator
        persona_ids = [p.persona_id for p in personaset.personas]
        self.aggregator = Aggregator(
            brand_ids=self.brand_ids,
            regions=self.regions,
            persona_ids=persona_ids
        )
    
    def _get_brand_ids(self) -> List[str]:
        """Get brand IDs from data."""
        brands_df = self.data_loader.load_brands()
        return brands_df["brand_id"].tolist()
    
    def _get_regions(self) -> List[str]:
        """Get region IDs from data."""
        regions_df = self.data_loader.load_regions()
        return regions_df["region_id"].tolist()
    
    def run(
        self,
        start_week: int,
        num_weeks: int,
        output_dir: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Run simulation.
        
        Args:
            start_week: Starting week ID
            num_weeks: Number of weeks to simulate
            output_dir: Optional output directory for results
            
        Returns:
            Dictionary with simulated_metrics and persona_contributions DataFrames
        """
        timestep = 0
        
        for week_offset in range(num_weeks):
            week_id = start_week + week_offset
            
            # Process each week (simplified: one timestep per week)
            self._simulate_week(week_id, timestep)
            timestep += 1
        
        # Get aggregated results
        simulated_metrics, persona_contributions = self.aggregator.get_aggregates()
        
        results = {
            "simulated_metrics": simulated_metrics,
            "persona_contributions": persona_contributions
        }
        
        # Save if output directory provided
        if output_dir:
            self._save_results(results, output_dir)
        
        return results
    
    def _simulate_week(self, week_id: int, timestep: int):
        """Simulate one week."""
        # Group agents by region for environment lookup
        agents_by_region = {}
        for agent in self.agent_registry.agents:
            region_id = agent.region_id
            if region_id not in agents_by_region:
                agents_by_region[region_id] = []
            agents_by_region[region_id].append(agent)
        
        # Process each region
        for region_id, region_agents in agents_by_region.items():
            # Get environment for this region
            env_manager = EnvironmentManager(
                data_loader=self.data_loader,
                region_id=region_id,
                brand_ids=self.brand_ids,
                scenario_config=self.scenario_config
            )
            env_state = env_manager.get_environment(week_id, timestep)
            
            # Convert to EnvironmentInputs for IBDE
            env_inputs = EnvironmentInputs(
                prices=env_state.prices.tolist(),
                availability=env_state.availability.tolist(),
                promotions=env_state.promotions.tolist(),
                ads=env_state.ads.tolist(),
                context=env_state.context
            )
            
            # Prepare batches for this region
            state_batch = [agent.state for agent in region_agents]
            persona_batch = [agent.persona for agent in region_agents]
            env_batch = [env_inputs] * len(region_agents)
            
            # Call IBDE (batched)
            next_states, logits_batch, _ = ibde_step_batched(
                state_batch=state_batch,
                env_batch=env_batch,
                persona_batch=persona_batch,
                timestep=timestep,
                return_diagnostics=False
            )
            
            # Update states
            for i, agent in enumerate(region_agents):
                agent.state = next_states[i]
            
            # Sample actions (LPM owns randomness)
            actions = self._sample_actions(logits_batch, region_agents, timestep)
            
            # Record events and aggregate
            for i, agent in enumerate(region_agents):
                action = actions[i]
                if action is not None and action >= 0:  # Valid purchase
                    brand_idx = action
                    region_idx = self.regions.index(region_id)
                    persona_idx = self.agent_registry.persona_idx[agent.agent_id]
                    price = env_state.prices[brand_idx]
                    
                    self.aggregator.record_event(
                        week_id=week_id,
                        brand_idx=brand_idx,
                        region_idx=region_idx,
                        persona_idx=persona_idx,
                        price=price
                    )
                    
                    # Update agent state (record last choice)
                    agent.state.memory.last_choice = brand_idx
                    agent.state.schedule.last_purchase_day = timestep
    
    def _sample_actions(
        self,
        logits_batch: List[Logits],
        agents: List,
        timestep: int
    ) -> List[Optional[int]]:
        """
        Sample actions from logits (LPM owns randomness).
        
        Uses softmax sampling with temperature.
        """
        actions = []
        rng = self.seed_manager.get_rng("action_sampling", index=timestep)
        
        for i, logits in enumerate(logits_batch):
            purchase_logits = np.array(logits.purchase_logits)
            no_purchase_logit = logits.no_purchase_logit
            
            # Combine purchase and no-purchase logits
            all_logits = np.concatenate([purchase_logits, [no_purchase_logit]])
            
            # Softmax
            exp_logits = np.exp(all_logits - np.max(all_logits))  # Numerical stability
            probs = exp_logits / exp_logits.sum()
            
            # Sample
            action = rng.choice(len(all_logits), p=probs)
            
            # Map to brand index (or None for no purchase)
            if action < len(purchase_logits):
                actions.append(action)
            else:
                actions.append(None)
        
        return actions
    
    def _save_results(self, results: Dict[str, pd.DataFrame], output_dir: str):
        """Save simulation results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save DataFrames
        results["simulated_metrics"].to_csv(
            output_path / "simulated_metrics_brand_week_region.csv",
            index=False
        )
        results["persona_contributions"].to_csv(
            output_path / "persona_contributions.csv",
            index=False
        )
        
        # Save metadata
        metadata = {
            "persona_version": self.personaset.version,
            "data_version": self.personaset.data_version,
            "scenario_hash": hash_scenario_config(self.scenario_config),
            "seed": self.seed,
            "num_agents": self.num_agents,
            "created_at": datetime.now().isoformat()
        }
        
        with open(output_path / "run_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

