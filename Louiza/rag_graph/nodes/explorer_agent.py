"""
Explorer Agent Node

Expands queries and generates retrieval hypotheses.
"""

import json
from typing import Dict, Any

from ..state import RetrievalState, log_decision
from ..prompts.explorer_agent import EXPLORER_PROMPT
from adapters.llm.interface import LLMClient


class ExplorerAgentNode:
    """
    Node 2: Explorer Agent
    
    Purpose:
    - Expand queries with synonyms and related terms
    - Identify related attributes and competitors
    - Propose retrieval angles/hypotheses
    """
    
    def __init__(self, llm_client: LLMClient = None, max_expanded_queries: int = 5):
        """
        Initialize explorer agent.
        
        Args:
            llm_client: Optional LLM client for query expansion
            max_expanded_queries: Maximum number of expanded queries to generate
        """
        self.llm_client = llm_client
        self.max_expanded_queries = max_expanded_queries
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute query expansion.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with expanded_queries and exploration_notes
        """
        query = state["query"]
        intent = state["intent"]
        entities = state["entities"]
        
        if self.llm_client:
            # Use LLM for expansion
            try:
                prompt = EXPLORER_PROMPT.format(
                    query=query,
                    intent=intent,
                    entities=entities,
                )
                response = self.llm_client.generate_structured(
                    prompt=prompt,
                    system_prompt="You are an Explorer agent. Always respond with valid JSON.",
                )
                
                expanded_queries = response.get("expanded_queries", [])
                exploration_notes = response.get("exploration_notes", [])
                
                # Limit expanded queries
                state["expanded_queries"] = expanded_queries[:self.max_expanded_queries]
                state["exploration_notes"] = exploration_notes
                
            except Exception as e:
                # Fallback to rule-based expansion
                state["expanded_queries"], state["exploration_notes"] = self._rule_based_expansion(query, intent, entities)
        else:
            # Rule-based expansion
            state["expanded_queries"], state["exploration_notes"] = self._rule_based_expansion(query, intent, entities)
        
        # Log decision
        log_decision(state, "explorer_agent", {
            "expanded_queries": state["expanded_queries"],
            "exploration_notes": state["exploration_notes"],
        })
        
        return state
    
    def _rule_based_expansion(
        self,
        query: str,
        intent: Dict[str, Any],
        entities: Dict[str, Any],
    ):
        """Fallback rule-based query expansion"""
        expanded_queries = [query]  # Always include original
        
        intent_type = intent.get("primary_intent", "")
        
        # Add intent-specific expansions
        if intent_type == "preference_discovery":
            expanded_queries.extend([
                f"{query} preferences",
                f"{query} taste preferences",
            ])
        elif intent_type == "sentiment_analysis":
            expanded_queries.extend([
                f"{query} sentiment",
                f"{query} opinions",
            ])
        
        # Add brand-specific expansions
        if entities.get("brands"):
            brand = entities["brands"][0]
            expanded_queries.append(f"{brand} {query}")
        
        # Generate exploration notes
        exploration_notes = []
        
        if intent_type in ["sentiment_analysis", "preference_discovery"]:
            exploration_notes.append("Look for survey evidence in bucket 2")
            exploration_notes.append("Look for scraped sentiment shifts in bucket 4")
        
        if intent_type == "market_inference":
            exploration_notes.append("Look for financial correlation in bucket 3")
            if entities.get("metrics"):
                exploration_notes.append(f"Focus on {entities['metrics'][0]} metric")
        
        if entities.get("segments"):
            exploration_notes.append(f"Filter by demographic segments: {', '.join(entities['segments'])}")
        
        return expanded_queries[:self.max_expanded_queries], exploration_notes

