"""
Retrieve Parallel Node

Executes parallel retrieval from multiple buckets.
"""

from typing import Dict, Any, List
from datetime import datetime

from ..state import RetrievalState, log_decision
from ..utils import deduplicate_records, rank_records
from Data_Engine.core.schema import DataRecord
from adapters.data_engine_adapter import DataEngineAdapter


class RetrieveParallelNode:
    """
    Node 4: Parallel Retriever
    
    Purpose:
    - Execute retrieval for each bucket
    - Merge and deduplicate results
    - Rank by relevance
    """
    
    def __init__(self, data_engine_adapter: DataEngineAdapter):
        """
        Initialize parallel retriever.
        
        Args:
            data_engine_adapter: DataEngineAdapter instance
        """
        self.data_engine = data_engine_adapter
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute parallel retrieval.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with retrieved and retrieved_by_bucket populated
        """
        retrieval_plan = state["retrieval_plan"]
        query = state["query"]
        expanded_queries = state["expanded_queries"] or [query]
        entities = state["entities"]
        intent = state["intent"]
        
        bucket_results = {}
        all_records = []
        
        # Execute retrieval for each bucket
        for bucket_id, plan in retrieval_plan.items():
            try:
                records = self._retrieve_from_bucket(
                    bucket_id=bucket_id,
                    queries=expanded_queries,
                    plan=plan,
                    entities=entities,
                )
                bucket_results[bucket_id] = records
                all_records.extend(records)
            except Exception as e:
                # Log error but continue with other buckets
                log_decision(state, "retrieve_parallel", {
                    "bucket_id": bucket_id,
                    "error": str(e),
                })
                bucket_results[bucket_id] = []
        
        # Deduplicate
        unique_records = deduplicate_records(all_records)
        
        # Rank by relevance
        ranked_records = rank_records(unique_records, entities, intent)
        
        state["retrieved"] = ranked_records
        state["retrieved_by_bucket"] = bucket_results
        
        # Increment retrieval pass count
        state["retrieval_pass_count"] = state.get("retrieval_pass_count", 0) + 1
        
        # Log decision
        log_decision(state, "retrieve_parallel", {
            "results_per_bucket": {bid: len(recs) for bid, recs in bucket_results.items()},
            "total_unique": len(ranked_records),
            "pass_count": state["retrieval_pass_count"],
        })
        
        return state
    
    def _retrieve_from_bucket(
        self,
        bucket_id: int,
        queries: List[str],
        plan: Dict[str, Any],
        entities: Dict[str, Any],
    ) -> List[DataRecord]:
        """Retrieve documents from a specific bucket"""
        filters = plan.get("filters", {}).copy()
        top_k = plan.get("top_k", 10)
        use_semantic = plan.get("use_semantic", False)
        strategy = plan.get("strategy", "semantic_search")
        
        # Remove special filters
        time_range = filters.pop("time_range", None)
        
        all_records = []
        
        # Execute retrieval for each expanded query
        for query_text in queries:
            try:
                if use_semantic and strategy != "time_structured":
                    # Use hybrid query
                    records = self.data_engine.hybrid_query(
                        query_text=query_text,
                        filters=filters,
                        top_k=top_k,
                        bucket_ids=[bucket_id],
                    )
                else:
                    # Use structured query
                    records = self.data_engine.query_structured(
                        filters={**filters, "bucket_id": bucket_id},
                        top_k=top_k,
                    )
                
                all_records.extend(records)
                
            except Exception as e:
                # Fallback to structured query
                try:
                    records = self.data_engine.query_structured(
                        filters={**filters, "bucket_id": bucket_id},
                        top_k=top_k,
                    )
                    all_records.extend(records)
                except Exception:
                    pass
        
        # Apply time range filter if specified
        if time_range and bucket_id == 3:
            filtered_records = []
            start_year = time_range.get("start")
            end_year = time_range.get("end")
            
            for record in all_records:
                if record.timestamp:
                    record_year = record.timestamp.year
                    if start_year <= record_year <= end_year:
                        filtered_records.append(record)
            
            all_records = filtered_records
        
        # Deduplicate and limit
        unique_records = deduplicate_records(all_records)
        
        return unique_records[:top_k]

