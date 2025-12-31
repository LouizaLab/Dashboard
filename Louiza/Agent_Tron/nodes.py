"""
LangGraph Nodes for Intelligent Retrieval

Each node represents a step in the retrieval reasoning process:
1. Query Interpreter - Understand intent and extract entities
2. Bucket Router - Decide which buckets are relevant
3. Strategy Selector - Decide HOW to retrieve from each bucket
4. Parallel Retrievers - Execute retrieval from each bucket
5. Evidence Aggregator - Merge and rank results
6. Confidence Scorer - Estimate confidence and coverage
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from .state import RetrievalState, log_decision
from Data_Engine.core.schema import DataRecord
from Data_Engine.retrieval.retrieval_manager import RetrievalManager


class QueryInterpreterNode:
    """
    Node 1: Query Interpreter
    
    Purpose:
    - Parse the incoming query
    - Extract intent and entities
    
    Responsibilities:
    - Classify query intent (preference discovery, sentiment analysis, etc.)
    - Identify brands, products, demographics, time horizons, attributes
    """
    
    # Intent keywords mapping
    INTENT_KEYWORDS = {
        "preference_discovery": [
            "prefer", "preference", "like", "favorite", "choose", "would rather",
            "taste", "flavor", "enjoy", "love", "hate"
        ],
        "sentiment_analysis": [
            "feel", "feeling", "sentiment", "opinion", "attitude", "emotion",
            "happy", "sad", "angry", "disappointed", "satisfied"
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
    
    # Common brand names (can be extended)
    COMMON_BRANDS = [
        "mcdonalds", "mcd", "burger king", "wendys", "starbucks", "taco bell",
        "kfc", "subway", "dominos", "pizza hut", "chipotle", "panera"
    ]
    
    # Demographic keywords
    DEMOGRAPHIC_KEYWORDS = [
        "gen z", "millennial", "boomer", "gen x", "gen y", "generation",
        "age", "young", "old", "teen", "adult", "senior", "college", "student"
    ]
    
    # Time keywords
    TIME_KEYWORDS = [
        "recent", "recently", "last year", "past year", "2024", "2023", "2022",
        "over time", "historical", "trend", "since", "during", "after", "before"
    ]
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute query interpretation.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with parsed_intent and inferred_entities
        """
        query = state["original_query"].lower()
        
        # Classify intent
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                intent_scores[intent] = score
        
        # Primary intent is the one with highest score
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else "general_query"
        
        parsed_intent = {
            "primary_intent": primary_intent,
            "intent_scores": intent_scores,
            "confidence": max(intent_scores.values()) / max(len(self.INTENT_KEYWORDS.get(primary_intent, [])), 1) if intent_scores else 0.0,
        }
        
        # Extract entities
        inferred_entities = {
            "brands": self._extract_brands(query),
            "products": self._extract_products(query),
            "demographics": self._extract_demographics(query),
            "time_horizon": self._extract_time_horizon(query),
            "attributes": self._extract_attributes(query),
        }
        
        # Update state
        state["parsed_intent"] = parsed_intent
        state["inferred_entities"] = inferred_entities
        
        # Log decision
        log_decision(state, "query_interpreter", {
            "intent": parsed_intent,
            "entities": inferred_entities,
        })
        
        return state
    
    def _extract_brands(self, query: str) -> List[str]:
        """Extract brand names from query"""
        brands = []
        for brand in self.COMMON_BRANDS:
            if brand in query:
                brands.append(brand.replace(" ", "_"))
        return brands
    
    def _extract_products(self, query: str) -> List[str]:
        """Extract product mentions"""
        product_keywords = ["burger", "fries", "coffee", "pizza", "sandwich", "salad", "breakfast", "lunch", "dinner"]
        products = [kw for kw in product_keywords if kw in query]
        return products
    
    def _extract_demographics(self, query: str) -> List[str]:
        """Extract demographic mentions"""
        demographics = []
        for demo in self.DEMOGRAPHIC_KEYWORDS:
            if demo in query:
                demographics.append(demo)
        return demographics
    
    def _extract_time_horizon(self, query: str) -> Optional[Dict[str, Any]]:
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
    
    def _extract_attributes(self, query: str) -> List[str]:
        """Extract attribute mentions (taste, price, health, etc.)"""
        attributes = []
        attribute_keywords = ["taste", "price", "health", "quality", "service", "speed", "convenience"]
        for attr in attribute_keywords:
            if attr in query:
                attributes.append(attr)
        return attributes


class BucketRouterNode:
    """
    Node 2: Bucket Router
    
    Purpose:
    - Decide which buckets are relevant for the query
    
    Routing logic:
    - Sentiment/preference queries → Bucket 2 (Surveys) + Bucket 4 (Scraped)
    - Behavioral evolution → Bucket 2 + Bucket 4 + Bucket 1 (if historical data)
    - Financial/market queries → Bucket 3 (Financial) + others
    - Demographic queries → Bucket 2 + Bucket 1
    """
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute bucket routing.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with target_buckets populated
        """
        intent = state["parsed_intent"].get("primary_intent", "general_query")
        entities = state["inferred_entities"]
        
        target_buckets = []
        
        # Routing logic based on intent
        if intent == "sentiment_analysis" or intent == "preference_discovery":
            # Sentiment and preferences come from surveys and scraped reviews
            target_buckets = [2, 4]
            if entities.get("demographics"):
                # Add online datasets if demographic comparison
                target_buckets.append(1)
        
        elif intent == "behavioral_evolution":
            # Need historical data from multiple sources
            target_buckets = [2, 4]
            if entities.get("time_horizon"):
                target_buckets.append(1)  # Online datasets may have historical data
        
        elif intent == "market_inference":
            # Financial data is primary, but also need context from other buckets
            target_buckets = [3]
            if "sentiment" in state["original_query"].lower() or "feel" in state["original_query"].lower():
                target_buckets.extend([2, 4])
        
        elif intent == "demographic_comparison":
            # Surveys are primary for demographics
            target_buckets = [2]
            if entities.get("brands"):
                target_buckets.append(4)  # Scraped reviews may have demographic signals
        
        else:
            # Default: try all buckets
            target_buckets = [1, 2, 3, 4]
        
        # Remove duplicates and sort
        target_buckets = sorted(list(set(target_buckets)))
        
        state["target_buckets"] = target_buckets
        
        # Log decision
        log_decision(state, "bucket_router", {
            "intent": intent,
            "selected_buckets": target_buckets,
            "reasoning": f"Selected buckets based on intent: {intent}",
        })
        
        return state


class StrategySelectorNode:
    """
    Node 3: Retrieval Strategy Selector
    
    Purpose:
    - Decide HOW to retrieve from each bucket
    
    Strategies:
    - Bucket 1 (Online Datasets): Structured filters + semantic search
    - Bucket 2 (Surveys): Demographic filters + semantic search on free-text
    - Bucket 3 (Financial): Time-windowed + structured filters
    - Bucket 4 (Scraped): Semantic search + sentiment threshold + brand match
    """
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute strategy selection.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with retrieval_plan populated
        """
        target_buckets = state["target_buckets"]
        entities = state["inferred_entities"]
        intent = state["parsed_intent"].get("primary_intent", "general_query")
        
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
        log_decision(state, "strategy_selector", {
            "plan": retrieval_plan,
        })
        
        return state
    
    def _get_strategy_for_bucket(self, bucket_id: int, intent: str) -> str:
        """Get retrieval strategy for a bucket"""
        strategies = {
            1: "structured_semantic_hybrid",  # Online datasets: structured + semantic
            2: "demographic_semantic",  # Surveys: filter by demo + semantic search
            3: "time_structured",  # Financial: time-windowed + structured
            4: "semantic_sentiment_brand",  # Scraped: semantic + sentiment + brand
        }
        return strategies.get(bucket_id, "semantic_search")
    
    def _build_filters(self, bucket_id: int, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Build filters for a bucket based on entities"""
        filters = {}
        
        # Brand filter (applies to all buckets)
        if entities.get("brands"):
            filters["brand"] = entities["brands"][0]  # Use first brand
        
        # Bucket-specific filters
        if bucket_id == 2:  # Surveys
            if entities.get("demographics"):
                # Map demographic keywords to categorical fields
                demo = entities["demographics"][0]
                if "gen z" in demo.lower():
                    filters["categorical_fields.generation"] = "Gen Z"
                elif "millennial" in demo.lower():
                    filters["categorical_fields.generation"] = "Millennial"
        
        elif bucket_id == 3:  # Financial
            if entities.get("time_horizon"):
                time_info = entities["time_horizon"]
                if "years" in time_info:
                    # Set time range (approximate)
                    years = time_info["years"]
                    if len(years) >= 2:
                        filters["time_range"] = {"start": years[0], "end": years[-1]}
                    else:
                        filters["time_range"] = {"start": years[0], "end": years[0]}
        
        elif bucket_id == 4:  # Scraped
            # Sentiment threshold for sentiment queries
            if entities.get("brands"):
                filters["min_sentiment"] = None  # Can be set based on query
        
        return filters
    
    def _get_top_k_for_bucket(self, bucket_id: int, intent: str) -> int:
        """Get number of results to retrieve per bucket"""
        # More results for complex queries
        base_k = {
            1: 10,  # Online datasets
            2: 15,  # Surveys (need more for statistical significance)
            3: 20,  # Financial (time series data)
            4: 15,  # Scraped reviews
        }.get(bucket_id, 10)
        
        # Increase for behavioral evolution (need more historical data)
        if intent == "behavioral_evolution":
            base_k = int(base_k * 1.5)
        
        return base_k
    
    def _should_use_semantic(self, bucket_id: int, intent: str) -> bool:
        """Determine if semantic search should be used"""
        # Semantic search is useful for text-heavy queries
        semantic_buckets = [1, 2, 4]  # Online datasets, surveys, scraped
        return bucket_id in semantic_buckets


class ParallelRetrieversNode:
    """
    Node 4: Parallel Retrievers
    
    Purpose:
    - Execute retrieval from each bucket in parallel
    
    Each retriever uses the existing Data Engine APIs
    and returns DataRecord objects.
    """
    
    def __init__(self, retrieval_manager: RetrievalManager, embedding_fn=None):
        """
        Initialize parallel retrievers.
        
        Args:
            retrieval_manager: RetrievalManager instance
            embedding_fn: Optional embedding function for semantic search
        """
        self.retrieval_manager = retrieval_manager
        self.embedding_fn = embedding_fn
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute parallel retrieval.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with retrieved_documents and bucket_results populated
        """
        retrieval_plan = state["retrieval_plan"]
        query = state["original_query"]
        bucket_results = {}
        all_documents = []
        
        # Execute retrieval for each bucket
        for bucket_id, plan in retrieval_plan.items():
            try:
                documents = self._retrieve_from_bucket(
                    bucket_id=bucket_id,
                    query=query,
                    plan=plan,
                )
                bucket_results[bucket_id] = documents
                all_documents.extend(documents)
            except Exception as e:
                # Log error but continue with other buckets
                log_decision(state, "parallel_retrievers", {
                    "bucket_id": bucket_id,
                    "error": str(e),
                })
                bucket_results[bucket_id] = []
        
        state["bucket_results"] = bucket_results
        state["retrieved_documents"] = all_documents
        
        # Log decision
        log_decision(state, "parallel_retrievers", {
            "results_per_bucket": {bid: len(docs) for bid, docs in bucket_results.items()},
            "total_documents": len(all_documents),
        })
        
        return state
    
    def _retrieve_from_bucket(
        self,
        bucket_id: int,
        query: str,
        plan: Dict[str, Any],
    ) -> List[DataRecord]:
        """Retrieve documents from a specific bucket"""
        filters = plan.get("filters", {})
        top_k = plan.get("top_k", 10)
        use_semantic = plan.get("use_semantic", False)
        
        # Remove time_range from filters (handle separately)
        time_range = filters.pop("time_range", None)
        min_sentiment = filters.pop("min_sentiment", None)
        
        documents = []
        
        # Apply time range filter if specified
        if time_range and bucket_id == 3:
            start_time = datetime(time_range["start"], 1, 1)
            end_time = datetime(time_range["end"], 12, 31)
            time_filtered = self.retrieval_manager.query_by_time_range(
                start_time=start_time,
                end_time=end_time,
                limit=top_k * 2,  # Get more for additional filtering
            )
            # Apply other filters
            for record in time_filtered:
                if self._matches_filters(record, filters):
                    documents.append(record)
                    if len(documents) >= top_k:
                        break
        else:
            # Use semantic search if available and requested
            if use_semantic and self.embedding_fn:
                try:
                    documents = self.retrieval_manager.query_by_text(
                        prompt=query,
                        embedding_fn=self.embedding_fn,
                        filters=filters,
                        top_k=top_k,
                    )
                except Exception:
                    # Fallback to structured query
                    documents = self.retrieval_manager.query_by_filters(
                        filters={**filters, "bucket_id": bucket_id},
                        limit=top_k,
                    )
            else:
                # Structured query only
                filters["bucket_id"] = bucket_id
                documents = self.retrieval_manager.query_by_filters(
                    filters=filters,
                    limit=top_k,
                )
        
        # Apply sentiment filter if specified
        if min_sentiment is not None:
            documents = [d for d in documents if d.sentiment and d.sentiment >= min_sentiment]
        
        return documents[:top_k]
    
    def _matches_filters(self, record: DataRecord, filters: Dict[str, Any]) -> bool:
        """Check if record matches filters"""
        for key, value in filters.items():
            if key == "brand" and record.brand != value:
                return False
            elif key.startswith("categorical_fields."):
                field_name = key.replace("categorical_fields.", "")
                if record.categorical_fields.get(field_name) != value:
                    return False
        return True


class EvidenceAggregatorNode:
    """
    Node 5: Evidence Aggregator
    
    Purpose:
    - Merge retrieved results into a coherent context
    
    Responsibilities:
    - De-duplicate records
    - Rank by relevance
    - Balance sources (avoid dominance by one bucket)
    - Preserve metadata for traceability
    """
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute evidence aggregation.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with aggregated_context and citations populated
        """
        bucket_results = state["bucket_results"]
        all_documents = state["retrieved_documents"]
        
        # De-duplicate by record_id
        seen_ids = set()
        unique_documents = []
        for doc in all_documents:
            if doc.record_id not in seen_ids:
                seen_ids.add(doc.record_id)
                unique_documents.append(doc)
        
        # Rank documents (simple relevance scoring)
        ranked_documents = self._rank_documents(unique_documents, state)
        
        # Balance sources (limit per bucket)
        balanced_documents = self._balance_sources(ranked_documents, bucket_results)
        
        # Generate aggregated context
        aggregated_context = self._generate_context(balanced_documents, state)
        
        # Generate citations
        citations = self._generate_citations(balanced_documents)
        
        state["retrieved_documents"] = balanced_documents
        state["aggregated_context"] = aggregated_context
        state["citations"] = citations
        
        # Log decision
        log_decision(state, "evidence_aggregator", {
            "unique_documents": len(unique_documents),
            "final_documents": len(balanced_documents),
            "citations_count": len(citations),
        })
        
        return state
    
    def _rank_documents(self, documents: List[DataRecord], state: RetrievalState) -> List[DataRecord]:
        """Rank documents by relevance"""
        # Simple ranking: prioritize records with:
        # 1. Matching brand (if specified)
        # 2. Sentiment scores (for sentiment queries)
        # 3. More text content
        
        entities = state.get("inferred_entities", {})
        intent = state.get("parsed_intent", {}).get("primary_intent", "")
        
        def score_doc(doc: DataRecord) -> float:
            score = 0.0
            
            # Brand match bonus
            if entities.get("brands") and doc.brand:
                if doc.brand.lower() in [b.lower() for b in entities["brands"]]:
                    score += 2.0
            
            # Sentiment score (for sentiment queries)
            if intent == "sentiment_analysis" and doc.sentiment is not None:
                score += abs(doc.sentiment)  # Higher absolute sentiment = more informative
            
            # Text content bonus
            text = doc.get_text_for_embedding()
            if text:
                score += min(len(text) / 100, 1.0)  # Cap at 1.0
            
            return score
        
        # Sort by score (descending)
        ranked = sorted(documents, key=score_doc, reverse=True)
        return ranked
    
    def _balance_sources(
        self,
        documents: List[DataRecord],
        bucket_results: Dict[int, List[DataRecord]],
    ) -> List[DataRecord]:
        """Balance documents across buckets to avoid dominance"""
        # Group by bucket
        by_bucket = {}
        for doc in documents:
            bucket_id = doc.bucket_id
            if bucket_id not in by_bucket:
                by_bucket[bucket_id] = []
            by_bucket[bucket_id].append(doc)
        
        # Limit per bucket (max 10 per bucket, but prioritize top results)
        max_per_bucket = 10
        balanced = []
        
        # Take top N from each bucket
        for bucket_id in sorted(by_bucket.keys()):
            bucket_docs = by_bucket[bucket_id][:max_per_bucket]
            balanced.extend(bucket_docs)
        
        return balanced
    
    def _generate_context(self, documents: List[DataRecord], state: RetrievalState) -> str:
        """Generate aggregated context string"""
        context_parts = []
        
        # Group by bucket for organization
        by_bucket = {}
        for doc in documents:
            bucket_id = doc.bucket_id
            if bucket_id not in by_bucket:
                by_bucket[bucket_id] = []
            by_bucket[bucket_id].append(doc)
        
        bucket_names = {
            1: "Online Datasets",
            2: "Surveys & Interviews",
            3: "Financial Data",
            4: "Scraped Public Data",
        }
        
        for bucket_id in sorted(by_bucket.keys()):
            bucket_docs = by_bucket[bucket_id]
            context_parts.append(f"\n=== {bucket_names.get(bucket_id, f'Bucket {bucket_id}')} ===")
            
            for i, doc in enumerate(bucket_docs[:5], 1):  # Limit to top 5 per bucket in context
                text = doc.get_text_for_embedding()
                if text:
                    # Truncate long text
                    if len(text) > 500:
                        text = text[:500] + "..."
                    context_parts.append(f"\n[{i}] {text}")
                
                # Add structured fields if relevant
                if doc.structured_fields:
                    key_fields = {k: v for k, v in list(doc.structured_fields.items())[:3]}
                    if key_fields:
                        context_parts.append(f"    Fields: {key_fields}")
        
        return "\n".join(context_parts)
    
    def _generate_citations(self, documents: List[DataRecord]) -> List[Dict[str, Any]]:
        """Generate citation metadata"""
        citations = []
        for doc in documents:
            citation = {
                "record_id": doc.record_id,
                "bucket": doc.bucket_id,
                "source": doc.source_name,
                "brand": doc.brand,
                "timestamp": doc.timestamp.isoformat() if doc.timestamp else None,
            }
            citations.append(citation)
        return citations


class ConfidenceScorerNode:
    """
    Node 6: Confidence & Coverage Scorer
    
    Purpose:
    - Estimate confidence in retrieved evidence
    
    Signals:
    - Number of sources
    - Bucket diversity
    - Time coverage
    - Sentiment consistency
    - Sample size (for surveys)
    """
    
    def __call__(self, state: RetrievalState) -> RetrievalState:
        """
        Execute confidence scoring.
        
        Args:
            state: Current retrieval state
            
        Returns:
            Updated state with confidence_score and coverage populated
        """
        documents = state["retrieved_documents"]
        bucket_results = state["bucket_results"]
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(documents, bucket_results, state)
        
        # Calculate coverage
        coverage = self._calculate_coverage(documents, bucket_results)
        
        state["confidence_score"] = confidence_score
        state["coverage"] = coverage
        state["end_time"] = datetime.utcnow()
        
        # Log decision
        log_decision(state, "confidence_scorer", {
            "confidence_score": confidence_score,
            "coverage": coverage,
        })
        
        return state
    
    def _calculate_confidence(
        self,
        documents: List[DataRecord],
        bucket_results: Dict[int, List[DataRecord]],
        state: RetrievalState,
    ) -> float:
        """Calculate overall confidence score (0.0-1.0)"""
        if not documents:
            return 0.0
        
        score = 0.0
        
        # Number of sources (more = better, but with diminishing returns)
        num_sources = len(documents)
        score += min(num_sources / 20, 0.3)  # Max 0.3 for source count
        
        # Bucket diversity (more buckets = better)
        num_buckets = len(bucket_results)
        score += min(num_buckets / 4, 0.2)  # Max 0.2 for bucket diversity
        
        # Time coverage (if time-related query)
        entities = state.get("inferred_entities", {})
        if entities.get("time_horizon"):
            timestamps = [d.timestamp for d in documents if d.timestamp]
            if timestamps:
                time_span = (max(timestamps) - min(timestamps)).days
                score += min(time_span / 365, 0.2)  # Max 0.2 for time coverage
        
        # Sentiment consistency (for sentiment queries)
        intent = state.get("parsed_intent", {}).get("primary_intent", "")
        if intent == "sentiment_analysis":
            sentiments = [d.sentiment for d in documents if d.sentiment is not None]
            if sentiments:
                # Consistency = low variance
                if len(sentiments) > 1:
                    variance = np.var(sentiments)
                    consistency = 1.0 / (1.0 + variance)  # Inverse variance
                    score += consistency * 0.2  # Max 0.2 for consistency
        
        # Sample size bonus (for surveys)
        survey_docs = [d for d in documents if d.bucket_id == 2]
        if survey_docs:
            score += min(len(survey_docs) / 15, 0.1)  # Max 0.1 for survey sample size
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_coverage(
        self,
        documents: List[DataRecord],
        bucket_results: Dict[int, List[DataRecord]],
    ) -> Dict[str, Any]:
        """Calculate coverage report"""
        buckets_used = list(bucket_results.keys())
        
        # Time span
        timestamps = [d.timestamp for d in documents if d.timestamp]
        time_span = None
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_span = f"{min_time.year}-{max_time.year}" if min_time.year != max_time.year else str(min_time.year)
        
        # Brand coverage
        brands = list(set(d.brand for d in documents if d.brand))
        
        coverage = {
            "buckets_used": buckets_used,
            "num_documents": len(documents),
            "time_span": time_span,
            "brands_covered": brands,
            "sources": list(set(d.source_name for d in documents)),
        }
        
        return coverage

