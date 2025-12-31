# LangGraph Intelligent Retrieval System

A multi-step reasoning graph for retrieval that understands **HOW to search**, not just **WHERE**.

## Overview

This system treats retrieval as a reasoning problem, orchestrating multiple steps to:
1. Understand user intent
2. Decide which data buckets are relevant
3. Select appropriate retrieval strategies
4. Execute parallel retrieval
5. Aggregate evidence intelligently
6. Score confidence and coverage

## Architecture

### Graph Flow

```
Query
  ↓
[Query Interpreter] → Parse intent, extract entities
  ↓
[Bucket Router] → Decide which buckets (1-4) are relevant
  ↓
[Strategy Selector] → Choose HOW to retrieve from each bucket
  ↓
[Parallel Retrievers] → Execute retrieval from each bucket
  ↓
[Evidence Aggregator] → Merge, rank, and balance results
  ↓
[Confidence Scorer] → Estimate confidence and coverage
  ↓
Output (RAG-ready context)
```

### State Schema

The `RetrievalState` flows through all nodes and accumulates:

- **Input**: `original_query`
- **Understanding**: `parsed_intent`, `inferred_entities`
- **Planning**: `target_buckets`, `retrieval_plan`
- **Results**: `retrieved_documents`, `bucket_results`
- **Output**: `aggregated_context`, `citations`, `confidence_score`, `coverage`

## Usage

### Basic Usage

```python
from Data_Engine.data_engine import DataEngine
from Agent_Tron import RetrievalGraph
from sentence_transformers import SentenceTransformer

# Initialize Data Engine
engine = DataEngine(storage_dir=Path("./Data_Engine/storage_data"))

# Set up embeddings
encoder = SentenceTransformer('all-MiniLM-L6-v2')
embedding_fn = lambda text: encoder.encode(text, convert_to_numpy=True)
engine.set_embedding_fn(embedding_fn)

# Create retrieval graph
retrieval_graph = RetrievalGraph(
    retrieval_manager=engine.retrieval_manager,
    embedding_fn=embedding_fn,
)

# Execute retrieval
result = retrieval_graph.retrieve("What do Gen Z prefer about McDonald's?")

# Access results
print(result["context"])  # Aggregated context for RAG
print(result["citations"])  # Citation metadata
print(result["confidence_score"])  # Confidence (0.0-1.0)
print(result["coverage"])  # Coverage report
```

### Output Format

The system returns a structured dictionary:

```python
{
    "query": "What do Gen Z prefer about McDonald's?",
    "context": "=== Surveys & Interviews ===\n[1] ...",
    "citations": [
        {
            "record_id": "...",
            "bucket": 2,
            "source": "survey_2024_q1",
            "brand": "mcdonalds",
            "timestamp": "2024-01-15T10:30:00"
        }
    ],
    "confidence_score": 0.87,
    "coverage": {
        "buckets_used": [2, 4],
        "time_span": "2021–2024",
        "brands_covered": ["mcdonalds"],
        "sources": ["survey_2024_q1", "reddit_reviews"]
    },
    "execution_log": [...],  # Decision log
    "parsed_intent": {...},
    "inferred_entities": {...},
    "target_buckets": [2, 4],
    "num_documents": 25
}
```

## Node Details

### 1. Query Interpreter

**Purpose**: Parse intent and extract entities

**Capabilities**:
- Intent classification (preference discovery, sentiment analysis, demographic comparison, behavioral evolution, market inference)
- Entity extraction (brands, products, demographics, time horizons, attributes)

**Example**:
```python
Query: "What do Gen Z feel about McDonald's?"
Intent: demographic_comparison
Entities: {
    "brands": ["mcdonalds"],
    "demographics": ["gen z"],
    "attributes": []
}
```

### 2. Bucket Router

**Purpose**: Decide which buckets are relevant

**Routing Logic**:
- Sentiment/preference → Bucket 2 (Surveys) + Bucket 4 (Scraped)
- Behavioral evolution → Bucket 2 + 4 + 1 (if historical)
- Market inference → Bucket 3 (Financial) + others
- Demographic comparison → Bucket 2 + 1

### 3. Strategy Selector

**Purpose**: Decide HOW to retrieve from each bucket

**Strategies**:
- **Bucket 1** (Online Datasets): Structured + semantic hybrid
- **Bucket 2** (Surveys): Demographic filters + semantic search
- **Bucket 3** (Financial): Time-windowed + structured filters
- **Bucket 4** (Scraped): Semantic + sentiment + brand matching

### 4. Parallel Retrievers

**Purpose**: Execute retrieval from each bucket

**Features**:
- Parallel execution
- Bucket-specific retrieval logic
- Fallback strategies
- Error handling per bucket

### 5. Evidence Aggregator

**Purpose**: Merge and rank results

**Features**:
- De-duplication by record_id
- Relevance ranking (brand match, sentiment, text content)
- Source balancing (limit per bucket)
- Citation generation

### 6. Confidence Scorer

**Purpose**: Estimate confidence and coverage

**Signals**:
- Number of sources
- Bucket diversity
- Time coverage
- Sentiment consistency
- Sample size (for surveys)

## Intent Types

The system recognizes these intent types:

1. **preference_discovery**: "What do people prefer?"
2. **sentiment_analysis**: "How do people feel about X?"
3. **demographic_comparison**: "What do Gen Z prefer?"
4. **behavioral_evolution**: "How has taste changed over time?"
5. **market_inference**: "Does sentiment correlate with revenue?"

## Extending the System

### Adding Custom Intent Classification

Extend `QueryInterpreterNode.INTENT_KEYWORDS`:

```python
INTENT_KEYWORDS = {
    "custom_intent": ["keyword1", "keyword2"],
    ...
}
```

### Adding Custom Retrieval Strategies

Extend `StrategySelectorNode._get_strategy_for_bucket()`:

```python
def _get_strategy_for_bucket(self, bucket_id: int, intent: str) -> str:
    if bucket_id == 5:  # New bucket
        return "custom_strategy"
    ...
```

### Adding Custom Filters

Extend `StrategySelectorNode._build_filters()`:

```python
def _build_filters(self, bucket_id: int, entities: Dict[str, Any]) -> Dict[str, Any]:
    filters = {}
    if bucket_id == 2:
        # Add custom filter logic
        ...
    return filters
```

## Integration with Agents

This retrieval system is designed to power:

### RAG Pipelines

```python
result = retrieval_graph.retrieve(user_query)
context = result["context"]
citations = result["citations"]

# Use context in LLM prompt
prompt = f"Context: {context}\n\nQuestion: {user_query}"
response = llm.generate(prompt)
```

### Hypothesis Testing Agents

```python
# Test hypothesis: "Gen Z prefers healthier options"
result = retrieval_graph.retrieve("What do Gen Z prefer about fast food?")
# Analyze aggregated_context for health-related mentions
```

### Simulation Agents

```python
# Retrieve behavioral data for simulation
result = retrieval_graph.retrieve("How has preference changed over time?")
# Use time_span and documents for behavioral modeling
```

## Performance Considerations

- **Parallel Retrieval**: Buckets are queried in parallel
- **Result Limiting**: Each bucket returns top-k results (configurable)
- **Source Balancing**: Prevents one bucket from dominating results
- **Caching**: Consider caching embeddings and frequent queries

## Debugging

### Execution Log

Every decision is logged:

```python
result = retrieval_graph.retrieve(query)
for log_entry in result["execution_log"]:
    print(f"{log_entry['node']}: {log_entry['decision']}")
```

### Streaming Execution

Watch the graph execute step-by-step:

```python
for state_update in retrieval_graph.retrieve_stream(query):
    print(state_update)
```

## Future Enhancements

See `TODO.md` for planned enhancements:
- LLM-based intent classification
- Conditional routing (retry with different buckets)
- Multi-agent coordination
- Hypothesis testing agents
- Simulation agents

## Requirements

- `langgraph>=0.0.20`
- `sentence-transformers>=2.2.0` (for semantic search)
- `faiss-cpu>=1.7.4` (for vector search)

Install with:
```bash
pip install langgraph sentence-transformers faiss-cpu
```

