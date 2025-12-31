"""
Interpret Query Node

Understands user intent and extracts entities from the query.
"""

import json
import re
from typing import Dict, Any

from ..state import RetrievalState, log_decision
from ..prompts.interpret_query import INTERPRET_QUERY_PROMPT
from adapters.llm.interface import LLMClient


class InterpretQueryNode:
    """
    Node 1: Query Interpreter
    
    Purpose:
    - Parse the incoming query
    - Extract intent and entities
    
    Responsibilities:
    - Classify query intent (sentiment, preference, demographic, behavioral, market)
    - Identify brands, products, demographics, time horizons, attributes
    """
    
    # Intent keywords mapping (fallback if LLM unavailable)
    INTENT_KEYWORDS = {
        "sentiment_analysis": [
            "feel", "feeling", "sentiment", "opinion", "attitude", "emotion",
            "happy", "sad", "angry", "disappointed", "satisfied"
        ],
        "preference_discovery": [
            "prefer", "preference", "like", "favorite", "choose", "would rather",
            "taste", "flavor", "enjoy", "love", "hate"
        ],
        "demographic_comparison": [
            "gen z", "millennial", "boomer", "age", "demographic", "generation",
            "young", "old", "teen", "adult", "senior"
        ],
        "behavioral_evolution": [
            "change", "evolve", "trend", "over time", "historical", "past",
            "now vs", "used to", "shift", "transition"
        ],
        "market_inference": [
            "market", "revenue", "sales", "profit", "financial", "performance",
            "correlate", "relationship", "impact", "affect"
        ],
    }
    
    COMMON_BRANDS = [
        "mcdonalds", "mcd", "burger king", "wendys", "starbucks", "taco bell",
        "kfc", "subway", "dominos", "pizza hut", "chipotle", "panera"
    ]
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize query interpreter.
        
        Args:
            llm_client: Optional LLM client for intent classification
        """
        self.llm_client = llm_client
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute query interpretation.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with intent and entities populated
        """
        query = state["query"]
        
        if self.llm_client:
            # Use LLM for interpretation
            try:
                prompt = INTERPRET_QUERY_PROMPT.format(query=query)
                response = self.llm_client.generate_structured(
                    prompt=prompt,
                    system_prompt="You are a query interpretation system. Always respond with valid JSON.",
                )
                
                state["intent"] = {
                    "primary_intent": response.get("primary_intent", "general_query"),
                    "intent_confidence": response.get("intent_confidence", 0.5),
                    "intent_scores": response.get("intent_scores", {}),
                }
                
                state["entities"] = response.get("entities", {})
                
            except Exception as e:
                # Fallback to rule-based
                state["intent"], state["entities"] = self._rule_based_interpretation(query)
        else:
            # Rule-based interpretation
            state["intent"], state["entities"] = self._rule_based_interpretation(query)
        
        # Log decision
        log_decision(state, "interpret_query", {
            "intent": state["intent"],
            "entities": state["entities"],
        })
        
        return state
    
    def _rule_based_interpretation(self, query: str):
        """Fallback rule-based interpretation"""
        query_lower = query.lower()
        
        # Classify intent
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else "general_query"
        
        intent = {
            "primary_intent": primary_intent,
            "intent_confidence": max(intent_scores.values()) / max(len(self.INTENT_KEYWORDS.get(primary_intent, [])), 1) if intent_scores else 0.0,
            "intent_scores": intent_scores,
        }
        
        # Extract entities
        entities = {
            "brands": self._extract_brands(query_lower),
            "segments": self._extract_demographics(query_lower),
            "time_range": self._extract_time_range(query_lower),
            "metrics": self._extract_metrics(query_lower),
            "keywords": self._extract_keywords(query_lower),
            "attributes": self._extract_attributes(query_lower),
        }
        
        return intent, entities
    
    def _extract_brands(self, query: str) -> list[str]:
        """Extract brand names"""
        brands = []
        for brand in self.COMMON_BRANDS:
            if brand in query:
                brands.append(brand.replace(" ", "_"))
        return brands
    
    def _extract_demographics(self, query: str) -> list[str]:
        """Extract demographic mentions"""
        demo_keywords = ["gen z", "millennial", "boomer", "gen x", "generation", "age"]
        demographics = [demo for demo in demo_keywords if demo in query]
        return demographics
    
    def _extract_time_range(self, query: str):
        """Extract time-related information"""
        time_info = {}
        
        # Look for year mentions
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, query)
        if years:
            time_info["years"] = [int(y) for y in years]
        
        # Look for relative time
        if "recent" in query or "recently" in query:
            time_info["relative"] = "recent"
        if "over time" in query or "historical" in query:
            time_info["relative"] = "historical"
        
        return time_info if time_info else None
    
    def _extract_metrics(self, query: str) -> list[str]:
        """Extract metric mentions"""
        metrics = []
        metric_keywords = ["revenue", "sales", "profit", "market share", "growth"]
        for metric in metric_keywords:
            if metric in query:
                metrics.append(metric)
        return metrics
    
    def _extract_keywords(self, query: str) -> list[str]:
        """Extract important keywords"""
        # Simple keyword extraction (can be enhanced)
        words = query.split()
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = [w for w in words if len(w) > 3 and w.lower() not in stop_words]
        return keywords[:10]  # Limit to top 10
    
    def _extract_attributes(self, query: str) -> list[str]:
        """Extract attribute mentions"""
        attributes = []
        attribute_keywords = ["taste", "price", "health", "quality", "service", "speed", "convenience"]
        for attr in attribute_keywords:
            if attr in query:
                attributes.append(attr)
        return attributes

