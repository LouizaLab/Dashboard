"""
Agent Registry - Manages agent instantiation and state.

Creates agents from personas and maintains batched state.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ibde.state import AgentState
from pme.persona_schema import Persona, PersonaSet
from common.seeds import SeedManager


@dataclass
class Agent:
    """Single agent representation."""
    agent_id: int
    persona: Persona
    state: AgentState
    region_id: str
    channel_id: Optional[str] = None
    cohort_id: Optional[str] = None


class AgentRegistry:
    """
    Registry for managing agents in batched form.
    
    Maintains:
    - Agent states (owned by IBDE)
    - Persona mappings
    - Static features (region, channel, cohort)
    """
    
    def __init__(
        self,
        personaset: PersonaSet,
        num_agents: int,
        regions: List[str],
        channels: Optional[List[str]] = None,
        num_brands: Optional[int] = None,
        seed: int = 42
    ):
        """
        Initialize agent registry.
        
        Args:
            personaset: PersonaSet to sample from
            num_agents: Total number of agents to create
            regions: List of region IDs
            channels: Optional list of channel IDs
            num_brands: Number of brands (required for brand_loyalty initialization)
            seed: Random seed for agent initialization
        """
        self.personaset = personaset
        self.num_agents = num_agents
        self.regions = regions
        self.channels = channels or []
        self.num_brands = num_brands
        self.seed_manager = SeedManager(base_seed=seed)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Create batched structures
        self.state_batch = [agent.state for agent in self.agents]
        self.persona_batch = [agent.persona for agent in self.agents]
        self.persona_idx = [self._get_persona_index(agent.persona) for agent in self.agents]
        self.region_idx = [regions.index(agent.region_id) for agent in self.agents]
        self.channel_idx = [channels.index(agent.channel_id) if agent.channel_id and agent.channel_id in channels else -1 for agent in self.agents]
    
    def _initialize_agents(self) -> List[Agent]:
        """Initialize agents from personas."""
        active_personas = self.personaset.get_active_personas()
        
        if len(active_personas) == 0:
            raise ValueError("PersonaSet must have at least one active persona")
        
        # Sample agents according to persona weights
        rng = self.seed_manager.get_rng("agent_sampling")
        persona_weights = [p.population_weight.global_weight for p in active_personas]
        persona_indices = rng.choice(
            len(active_personas),
            size=self.num_agents,
            p=persona_weights
        )
        
        # Sample regions uniformly (can be made more sophisticated)
        region_indices = rng.choice(len(self.regions), size=self.num_agents)
        
        # Sample channels if available
        channel_indices = None
        if self.channels:
            channel_indices = rng.choice(len(self.channels), size=self.num_agents)
        
        agents = []
        for i in range(self.num_agents):
            persona = active_personas[persona_indices[i]]
            region_id = self.regions[region_indices[i]]
            channel_id = self.channels[channel_indices[i]] if channel_indices is not None else None
            
            # Initialize state from persona priors
            state = self._initialize_state_from_persona(persona, agent_id=i)
            
            agent = Agent(
                agent_id=i,
                persona=persona,
                state=state,
                region_id=region_id,
                channel_id=channel_id
            )
            agents.append(agent)
        
        return agents
    
    def _initialize_state_from_persona(self, persona: Persona, agent_id: int) -> AgentState:
        """Initialize agent state from persona priors."""
        rng = self.seed_manager.get_rng("state_initialization", index=agent_id)
        
        # Sample taste embedding from prior
        taste_mean = np.array(persona.state_priors.taste_embedding.mean)
        taste_cov = np.array(persona.state_priors.taste_embedding.cov)
        
        # Sample from multivariate normal
        taste_embedding = rng.multivariate_normal(taste_mean, taste_cov)
        
        # Initialize brand loyalty (uniform initially, will evolve)
        num_brands = self.num_brands
        if num_brands is None:
            raise ValueError("num_brands must be provided to AgentRegistry.__init__()")
        brand_loyalty = rng.uniform(0.1, 0.3, size=num_brands)
        brand_loyalty = brand_loyalty / brand_loyalty.sum()  # Normalize
        
        # Initialize other state components
        habit_strength = persona.behavioral_params.habit_strength
        reference_price = 1.0  # Will be updated from environment
        attention = 1.0
        
        return AgentState(
            taste_embedding=taste_embedding.tolist(),
            brand_loyalty=brand_loyalty.tolist(),
            habit_strength=habit_strength,
            reference_price=reference_price,
            attention=attention
        )
    
    def _get_persona_index(self, persona: Persona) -> int:
        """Get index of persona in PersonaSet."""
        for i, p in enumerate(self.personaset.personas):
            if p.persona_id == persona.persona_id:
                return i
        raise ValueError(f"Persona {persona.persona_id} not found in PersonaSet")
    
    def update_states(self, new_states: List[AgentState]):
        """Update agent states (called after IBDE step)."""
        if len(new_states) != len(self.agents):
            raise ValueError(f"State batch size mismatch: {len(new_states)} vs {len(self.agents)}")
        
        for i, new_state in enumerate(new_states):
            self.agents[i].state = new_state
        
        self.state_batch = new_states
    
    def get_agent_by_id(self, agent_id: int) -> Agent:
        """Get agent by ID."""
        return self.agents[agent_id]
    
    def get_persona_by_agent_id(self, agent_id: int) -> Persona:
        """Get persona for an agent."""
        return self.agents[agent_id].persona

