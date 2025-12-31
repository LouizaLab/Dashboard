"""
LLM Client Interface

Protocol/interface for LLM providers.
"""

from typing import Protocol, List, Dict, Any, Optional


class LLMClient(Protocol):
    """
    Protocol for LLM clients.
    
    All LLM implementations must provide these methods.
    """
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text
        """
        ...
    
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            response_format: Optional schema for structured output
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Dictionary with structured output
        """
        ...
    
    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate text for multiple prompts.
        
        Args:
            prompts: List of user prompts
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific arguments
            
        Returns:
            List of generated texts
        """
        ...

