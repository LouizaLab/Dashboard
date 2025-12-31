"""
Utility functions for RAG graph nodes.
"""

from typing import List, Dict, Any
from datetime import datetime

from Data_Engine.core.schema import DataRecord


def deduplicate_records(records: List[DataRecord]) -> List[DataRecord]:
    """
    Deduplicate records by record_id.
    
    Args:
        records: List of DataRecord objects
        
    Returns:
        Deduplicated list
    """
    seen_ids = set()
    unique_records = []
    for record in records:
        if record.record_id not in seen_ids:
            seen_ids.add(record.record_id)
            unique_records.append(record)
    return unique_records


def rank_records(
    records: List[DataRecord],
    entities: Dict[str, Any],
    intent: Dict[str, Any],
) -> List[DataRecord]:
    """
    Rank records by relevance.
    
    Args:
        records: List of DataRecord objects
        entities: Extracted entities
        intent: Intent classification
        
    Returns:
        Ranked list of records
    """
    def score_record(record: DataRecord) -> float:
        score = 0.0
        
        # Brand match bonus
        if entities.get("brands") and record.brand:
            if record.brand.lower() in [b.lower() for b in entities["brands"]]:
                score += 2.0
        
        # Sentiment score (for sentiment queries)
        intent_type = intent.get("primary_intent", "")
        if intent_type == "sentiment_analysis" and record.sentiment is not None:
            score += abs(record.sentiment)  # Higher absolute sentiment = more informative
        
        # Text content bonus
        text = record.get_text_for_embedding()
        if text:
            score += min(len(text) / 100, 1.0)  # Cap at 1.0
        
        # Recency bonus (if timestamp available)
        if record.timestamp:
            age_days = (datetime.utcnow() - record.timestamp).days
            recency_score = max(0, 1.0 - (age_days / 365))  # Decay over 1 year
            score += recency_score * 0.5
        
        return score
    
    return sorted(records, key=score_record, reverse=True)


def summarize_records_for_prompt(records: List[DataRecord], max_records: int = 10) -> str:
    """
    Create a summary of records for use in prompts.
    
    Args:
        records: List of DataRecord objects
        max_records: Maximum number of records to include
        
    Returns:
        Summary string
    """
    if not records:
        return "No records retrieved."
    
    summary_parts = []
    for i, record in enumerate(records[:max_records], 1):
        text = record.get_text_for_embedding()
        if text:
            text_preview = text[:200] + "..." if len(text) > 200 else text
            summary_parts.append(
                f"[{i}] Bucket {record.bucket_id}, Brand: {record.brand or 'N/A'}, "
                f"Source: {record.source_name}, Text: {text_preview}"
            )
        else:
            summary_parts.append(
                f"[{i}] Bucket {record.bucket_id}, Brand: {record.brand or 'N/A'}, "
                f"Source: {record.source_name}, Structured fields: {list(record.structured_fields.keys())[:3]}"
            )
    
    if len(records) > max_records:
        summary_parts.append(f"... and {len(records) - max_records} more records")
    
    return "\n".join(summary_parts)


def compute_evidence_summary(records: List[DataRecord], retrieved_by_bucket: Dict[int, List[DataRecord]]) -> Dict[str, Any]:
    """
    Compute evidence summary statistics.
    
    Args:
        records: All retrieved records
        retrieved_by_bucket: Records grouped by bucket
        
    Returns:
        Summary dictionary
    """
    counts_by_bucket = {bid: len(recs) for bid, recs in retrieved_by_bucket.items()}
    
    # Time span
    timestamps = [r.timestamp for r in records if r.timestamp]
    time_span = None
    if timestamps:
        min_time = min(timestamps)
        max_time = max(timestamps)
        time_span = {
            "start": min_time.isoformat(),
            "end": max_time.isoformat(),
            "days": (max_time - min_time).days,
        }
    
    # Brand coverage
    brands = list(set(r.brand for r in records if r.brand))
    
    # Sentiment distribution
    sentiments = [r.sentiment for r in records if r.sentiment is not None]
    sentiment_stats = {}
    if sentiments:
        sentiment_stats = {
            "mean": sum(sentiments) / len(sentiments),
            "min": min(sentiments),
            "max": max(sentiments),
            "count": len(sentiments),
        }
    
    return {
        "total_records": len(records),
        "counts_by_bucket": counts_by_bucket,
        "buckets_used": list(retrieved_by_bucket.keys()),
        "time_span": time_span,
        "brands_covered": brands,
        "sentiment_stats": sentiment_stats,
        "sources": list(set(r.source_name for r in records if r.source_name)),
    }

