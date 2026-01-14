"""
Django-friendly client for Agent-Tron API
"""

import requests
from typing import Dict, List, Optional, Any

try:
    from django.conf import settings
except ImportError:
    # Django not available, use defaults
    class Settings:
        AGENT_TRON_URL = 'http://localhost:8001'
        AGENT_TRON_TIMEOUT = 30
    settings = Settings()


class AgentTronClient:
    """
    Django client for Agent-Tron API
    
    Usage:
        from agent_tron.django_integration.client import AgentTronClient
        
        client = AgentTronClient()
        response = client.get_persona_decision(...)
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize client
        
        Args:
            base_url: Agent-Tron API base URL. Defaults to AGENT_TRON_URL from settings,
                     or 'http://localhost:8001' if not set.
        """
        self.base_url = base_url or getattr(
            settings, 
            'AGENT_TRON_URL', 
            'http://localhost:8001'
        )
        self.timeout = getattr(settings, 'AGENT_TRON_TIMEOUT', 30)
    
    def get_persona_decision(
        self,
        request_id: str,
        hypothesis: str,
        persona: Dict,
        context: Dict,
        question_type: str = "preference",
        num_samples: int = 1,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Get decision for a single persona
        
        Args:
            request_id: Unique request identifier
            hypothesis: Hypothesis/question to answer
            persona: Persona dict with agent_id, archetype, demographics, psychographics
            context: Context dict with time_of_day, location, etc.
            question_type: One of "comparison", "what_if", "forecast", "preference"
            num_samples: Number of samples to draw (default: 1)
            seed: Optional random seed for determinism
        
        Returns:
            PersonaDecisionResponse as dict
        
        Raises:
            requests.RequestException: If API call fails
        """
        request_data = {
            "request_id": request_id,
            "hypothesis": hypothesis,
            "question_type": question_type,
            "persona": persona,
            "context": context,
            "num_samples": num_samples
        }
        
        if seed is not None:
            request_data["seed"] = seed
        
        response = requests.post(
            f"{self.base_url}/agent_tron/persona_decision",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_batch_decisions(
        self,
        request_id: str,
        hypothesis: str,
        personas: List[Dict],
        context: Dict,
        question_type: str = "comparison",
        seed: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Get decisions for multiple personas
        
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
        request_data = {
            "request_id": request_id,
            "hypothesis": hypothesis,
            "question_type": question_type,
            "personas": personas,
            "context": context
        }
        
        if seed is not None:
            request_data["seed"] = seed
        
        response = requests.post(
            f"{self.base_url}/agent_tron/batch_decisions",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def aggregate_responses(self, responses: List[Dict]) -> Dict:
        """
        Aggregate multiple responses into executive summary
        
        Args:
            responses: List of PersonaDecisionResponse dicts
        
        Returns:
            AggregateResponse as dict
        """
        response = requests.post(
            f"{self.base_url}/agent_tron/aggregate",
            json=responses,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


# Singleton instance (optional, for convenience)
_client_instance: Optional[AgentTronClient] = None


def get_client() -> AgentTronClient:
    """Get singleton Agent-Tron client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = AgentTronClient()
    return _client_instance

