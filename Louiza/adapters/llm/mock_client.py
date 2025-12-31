"""
Mock LLM Client for Testing

Provides a mock implementation that returns predictable responses.
"""

from typing import List, Dict, Any, Optional
import json

from .interface import LLMClient


class MockLLMClient:
    """
    Mock LLM client for testing.
    
    Returns predictable responses based on prompt patterns.
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """
        Initialize mock client.
        
        Args:
            responses: Optional dict mapping prompt patterns to responses
        """
        self.responses = responses or {}
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate mock text."""
        # Check for exact match
        if prompt in self.responses:
            return self.responses[prompt]
        
        # Check for pattern match
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return response
        
        # Default responses based on prompt content
        prompt_lower = prompt.lower()
        
        if "intent" in prompt_lower or "classify" in prompt_lower:
            return json.dumps({
                "primary_intent": "preference_discovery",
                "confidence": 0.85,
                "intent_scores": {"preference_discovery": 0.85}
            })
        
        if "expand" in prompt_lower or "synonym" in prompt_lower:
            return json.dumps({
                "expanded_queries": ["taste preferences", "flavor preferences", "food preferences"],
                "related_attributes": ["taste", "flavor", "quality"],
                "competitors": []
            })
        
        if "critique" in prompt_lower or "critic" in prompt_lower:
            return json.dumps({
                "critique_notes": ["Sample size is adequate", "Good bucket coverage"],
                "contradictions": [],
                "coverage_report": {"buckets_used": [2, 4], "missing_buckets": []}
            })
        
        if "synthesize" in prompt_lower or "context" in prompt_lower:
            return "Survey Evidence:\n- Users prefer taste over price\n\nPublic Sentiment Evidence:\n- Positive sentiment towards brand X"
        
        # Default response
        return "Mock LLM response"
    
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock structured output."""
        response_text = self.generate(prompt, system_prompt=system_prompt, **kwargs)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"response": response_text}
    
    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """Generate mock text for multiple prompts."""
        return [self.generate(p, system_prompt=system_prompt, **kwargs) for p in prompts]

