"""
Plan Retrieval Node

Plans retrieval strategies for each bucket.
"""

from typing import Dict, Any

from ..state import RetrievalState, log_decision


class PlanRetrievalNode:
    """
    Node 3: Retrieval Planner
    
    Purpose:
    - Decide which buckets to query
    - Define retrieval strategies per bucket
    - Set top_k and filters per bucket
    """
    
    def __init__(self, default_top_k: Dict[int, int] = None):
        """
        Initialize retrieval planner.
        
        Args:
            default_top_k: Default top_k per bucket (default: {1: 10, 2: 15, 3: 20, 4: 15})
        """
        self.default_top_k = default_top_k or {1: 10, 2: 15, 3: 20, 4: 15}
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute retrieval planning.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with retrieval_plan populated
        """
        intent = state["intent"]
        entities = state["entities"]
        exploration_notes = state["exploration_notes"]
        
        # Determine target buckets based on intent and exploration notes
        target_buckets = self._determine_buckets(intent, entities, exploration_notes)
        
        # Build retrieval plan for each bucket
        retrieval_plan = {}
        for bucket_id in target_buckets:
            plan = {
                "strategy": self._get_strategy_for_bucket(bucket_id, intent),
                "filters": self._build_filters(bucket_id, entities),
                "top_k": self._get_top_k_for_bucket(bucket_id, intent),
                "use_semantic": self._should_use_semantic(bucket_id, intent),
            }
            retrieval_plan[bucket_id] = plan
        
        state["retrieval_plan"] = retrieval_plan
        
        # Log decision
        log_decision(state, "plan_retrieval", {
            "target_buckets": target_buckets,
            "plan": retrieval_plan,
        })
        
        return state
    
    def _determine_buckets(
        self,
        intent: Dict[str, Any],
        entities: Dict[str, Any],
        exploration_notes: list[str],
    ) -> list[int]:
        """Determine which buckets to query"""
        intent_type = intent.get("primary_intent", "general_query")
        
        # Base buckets on intent
        if intent_type == "sentiment_analysis" or intent_type == "preference_discovery":
            buckets = [2, 4]  # Surveys and scraped reviews
            if entities.get("demographics"):
                buckets.append(1)  # Online datasets for demographics
        
        elif intent_type == "behavioral_evolution":
            buckets = [2, 4]
            if entities.get("time_range"):
                buckets.append(1)  # Historical data
        
        elif intent_type == "market_inference":
            buckets = [3]  # Financial data primary
            if "sentiment" in str(exploration_notes).lower():
                buckets.extend([2, 4])
        
        elif intent_type == "demographic_comparison":
            buckets = [2]  # Surveys primary
            if entities.get("brands"):
                buckets.append(4)  # Scraped reviews
        
        else:
            # Default: try all buckets
            buckets = [1, 2, 3, 4]
        
        # Check exploration notes for bucket hints
        for note in exploration_notes:
            if "bucket 2" in note.lower() or "survey" in note.lower():
                if 2 not in buckets:
                    buckets.append(2)
            if "bucket 3" in note.lower() or "financial" in note.lower():
                if 3 not in buckets:
                    buckets.append(3)
            if "bucket 4" in note.lower() or "scraped" in note.lower():
                if 4 not in buckets:
                    buckets.append(4)
        
        return sorted(list(set(buckets)))
    
    def _get_strategy_for_bucket(self, bucket_id: int, intent: Dict[str, Any]) -> str:
        """Get retrieval strategy for a bucket"""
        strategies = {
            1: "structured_semantic_hybrid",  # Online datasets
            2: "demographic_semantic",  # Surveys
            3: "time_structured",  # Financial
            4: "semantic_sentiment_brand",  # Scraped
        }
        return strategies.get(bucket_id, "semantic_search")
    
    def _build_filters(self, bucket_id: int, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Build filters for a bucket"""
        filters = {}
        
        # Brand filter
        if entities.get("brands"):
            filters["brand"] = entities["brands"][0]
        
        # Bucket-specific filters
        if bucket_id == 2:  # Surveys
            if entities.get("segments"):
                demo = entities["segments"][0]
                if "gen z" in demo.lower():
                    filters["categorical_fields.generation"] = "Gen Z"
                elif "millennial" in demo.lower():
                    filters["categorical_fields.generation"] = "Millennial"
        
        elif bucket_id == 3:  # Financial
            if entities.get("time_range") and entities["time_range"].get("years"):
                years = entities["time_range"]["years"]
                if len(years) >= 2:
                    filters["time_range"] = {"start": years[0], "end": years[-1]}
                else:
                    filters["time_range"] = {"start": years[0], "end": years[0]}
        
        elif bucket_id == 4:  # Scraped
            # Sentiment filter can be applied later
            pass
        
        return filters
    
    def _get_top_k_for_bucket(self, bucket_id: int, intent: Dict[str, Any]) -> int:
        """Get top_k for a bucket"""
        base_k = self.default_top_k.get(bucket_id, 10)
        
        # Increase for behavioral evolution (need more historical data)
        if intent.get("primary_intent") == "behavioral_evolution":
            base_k = int(base_k * 1.5)
        
        return base_k
    
    def _should_use_semantic(self, bucket_id: int, intent: Dict[str, Any]) -> bool:
        """Determine if semantic search should be used"""
        semantic_buckets = [1, 2, 4]  # Online datasets, surveys, scraped
        return bucket_id in semantic_buckets

