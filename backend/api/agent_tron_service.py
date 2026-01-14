"""
Agent-Tron Django Service Integration

This module provides integration between Django views and Agent-Tron core functionality.
Agent-Tron samples from the LPM (Large Population Model) to provide grounded decisions
for persona agents.

🚨 CRITICAL: All persona decisions MUST go through Agent-Tron LPM sampling.

NOTE: This now calls Django views directly instead of HTTP requests to a FastAPI server.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)

# Add project root to path for Agent-Tron imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent_tron.core.handler import DecisionHandler
from agent_tron.schemas.request import (
    PersonaDecisionRequest, Persona, Demographics, Psychographics, Context, Constraints
)
from agent_tron.schemas.response import PersonaDecisionResponse
from agent_tron.aggregation.aggregate import aggregate_responses


class AgentTronService:
    """
    Service layer for interacting with Agent-Tron Django views.
    
    Agent-Tron provides:
    - LPM-based decision sampling
    - Population priors and conditioned distributions
    - Uncertainty metrics (entropy, confidence)
    - Phase 4 ground truth evidence
    
    NOTE: Now uses Django views directly instead of HTTP requests.
    """
    
    def __init__(self):
        """Initialize Agent-Tron service with settings."""
        self.enabled = getattr(settings, 'AGENT_TRON_ENABLED', True)
        self._handler: Optional[DecisionHandler] = None
    
    def _get_handler(self) -> DecisionHandler:
        """Get or create DecisionHandler instance."""
        if self._handler is None:
            logger.info("Initializing Agent-Tron DecisionHandler...")
            self._handler = DecisionHandler()
            logger.info("✓ Agent-Tron DecisionHandler initialized")
        return self._handler
    
    def _check_health(self) -> bool:
        """Check if Agent-Tron is available."""
        if not self.enabled:
            return False
        try:
            # Just check if handler can be initialized
            handler = self._get_handler()
            return handler is not None
        except Exception as e:
            logger.warning(f"Agent-Tron health check failed: {e}")
            return False
    
    def get_persona_decision(
        self,
        agent_id: str,
        hypothesis: str,
        persona: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        question_type: str = "preference",
        num_samples: int = 1,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get LPM-sampled decision for a persona agent.
        
        Args:
            agent_id: Unique agent identifier
            hypothesis: Hypothesis/question to answer
            persona: Persona dict with archetype, demographics, psychographics
            context: Context dict (time_of_day, location, region, etc.)
            question_type: One of "comparison", "what_if", "forecast", "preference"
            num_samples: Number of samples to draw from LPM (default: 1)
            seed: Optional random seed for determinism
        
        Returns:
            PersonaDecisionResponse dict with:
            - sampled_decision: Primary decision sample
            - sampled_responses: List of additional samples (if num_samples > 1)
            - population_prior: Base distribution
            - conditioned_distribution: Persona-conditioned distribution
            - uncertainty: Entropy and confidence metrics
            - ground_truth_evidence: Phase 4 evidence references
        
        Raises:
            RuntimeError: If Agent-Tron is disabled or unavailable
        """
        if not self.enabled:
            logger.warning("Agent-Tron is disabled. Set AGENT_TRON_ENABLED=True in settings.")
            raise RuntimeError("Agent-Tron is disabled. Set AGENT_TRON_ENABLED=True in settings.")
        
        # Check health
        if not self._check_health():
            error_msg = (
                "Agent-Tron is not available. "
                "Please check that Agent-Tron is enabled and dependencies are installed."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            logger.info(
                f"Calling Agent-Tron for agent {agent_id} "
                f"with hypothesis: {hypothesis[:100]}..."
            )
            
            # Build PersonaDecisionRequest
            request_id = f"django_{agent_id}_{hypothesis[:50].replace(' ', '_')}"
            
            # Convert persona dict to Pydantic model
            persona_model = Persona(
                agent_id=persona.get('agent_id', agent_id),
                archetype=persona['archetype'],
                demographics=Demographics(**persona['demographics']),
                psychographics=Psychographics(**persona.get('psychographics', {})),
                traits=persona.get('traits', {})
            )
            
            # Build context and constraints
            context_model = Context(**(context or {}))
            constraints_model = Constraints()
            
            # Build request
            agent_request = PersonaDecisionRequest(
                request_id=request_id,
                hypothesis=hypothesis,
                question_type=question_type,
                persona=persona_model,
                context=context_model,
                constraints=constraints_model,
                seed=seed,
                num_samples=num_samples
            )
            
            # Process request directly (no HTTP)
            handler = self._get_handler()
            response = handler.process_request(agent_request)
            
            # Convert to dict
            result = response.dict()
            
            logger.info(
                f"Agent-Tron returned decision: {response.sampled_decision.choice} "
                f"with confidence {response.uncertainty.confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Agent-Tron decision failed: {e}", exc_info=True)
            raise RuntimeError(f"Agent-Tron decision failed: {str(e)}")
    
    def get_batch_decisions(
        self,
        request_id: str,
        hypothesis: str,
        personas: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        question_type: str = "preference",
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get LPM-sampled decisions for multiple personas.
        
        Args:
            request_id: Unique request identifier
            hypothesis: Hypothesis/question
            personas: List of persona dicts
            context: Shared context
            question_type: Question type
            seed: Optional seed
        
        Returns:
            List of PersonaDecisionResponse dicts
        """
        if not self.enabled:
            raise RuntimeError("Agent-Tron is disabled.")
        
        if not self._check_health():
            raise RuntimeError("Agent-Tron is not available.")
        
        try:
            logger.info(f"Calling Agent-Tron batch for {len(personas)} personas")
            
            handler = self._get_handler()
            responses = []
            
            for persona_dict in personas:
                # Convert persona dict to Pydantic model
                persona_model = Persona(
                    agent_id=persona_dict.get('agent_id', ''),
                    archetype=persona_dict['archetype'],
                    demographics=Demographics(**persona_dict['demographics']),
                    psychographics=Psychographics(**persona_dict.get('psychographics', {})),
                    traits=persona_dict.get('traits', {})
                )
                
                # Build individual request
                individual_request = PersonaDecisionRequest(
                    request_id=f"{request_id}_{persona_model.agent_id}",
                    hypothesis=hypothesis,
                    question_type=question_type,
                    persona=persona_model,
                    context=Context(**(context or {})),
                    constraints=Constraints(),
                    seed=seed
                )
                
                response = handler.process_request(individual_request)
                responses.append(response.dict())
            
            logger.info(f"Agent-Tron batch: processed {len(responses)} personas")
            
            return responses
            
        except Exception as e:
            logger.error(f"Agent-Tron batch failed: {e}", exc_info=True)
            raise RuntimeError(f"Agent-Tron batch request failed: {str(e)}")
    
    def aggregate_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple Agent-Tron responses into executive summary.
        
        Args:
            responses: List of PersonaDecisionResponse dicts
        
        Returns:
            AggregateResponse dict with preference breakdown, segment insights, etc.
        """
        if not self.enabled:
            raise RuntimeError("Agent-Tron is disabled.")
        
        if not self._check_health():
            raise RuntimeError("Agent-Tron is not available.")
        
        try:
            # Convert dicts to Pydantic models
            response_models = [PersonaDecisionResponse(**r) for r in responses]
            
            # Aggregate
            aggregated = aggregate_responses(response_models)
            
            # Convert to dict
            return aggregated.dict()
            
        except Exception as e:
            logger.error(f"Agent-Tron aggregation failed: {e}", exc_info=True)
            raise RuntimeError(f"Agent-Tron aggregation failed: {str(e)}")


# Singleton instance
_service_instance: Optional[AgentTronService] = None


def get_agent_tron_service() -> AgentTronService:
    """Get singleton Agent-Tron service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AgentTronService()
    return _service_instance


def persona_agent_to_agent_tron_persona(agent) -> Dict[str, Any]:
    """
    Convert Django PersonaAgent model to Agent-Tron Persona format.
    
    Args:
        agent: PersonaAgent Django model instance
    
    Returns:
        Persona dict for Agent-Tron API
    """
    behavior_params = agent.behavior_params_json or {}
    
    return {
        "agent_id": str(agent.id),
        "archetype": agent.archetype,
        "demographics": {
            "age_bucket": agent.age_bucket,
            "gender": agent.gender,
            "region": agent.region,
            "income": agent.income
        },
        "psychographics": {
            "price_sensitivity": behavior_params.get('price_sensitivity', 0.5),
            "novelty_seeking": behavior_params.get('novelty_seeking', 0.5),
            "health_consciousness": behavior_params.get('health_bias', 0.5),
            "brand_loyalty": behavior_params.get('brand_loyalty', 0.5)
        },
        "traits": behavior_params  # Pass through any additional traits
    }
