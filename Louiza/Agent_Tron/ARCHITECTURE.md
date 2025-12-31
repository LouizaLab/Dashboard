# LangGraph Retrieval System - Architecture

## Design Philosophy

**"Retrieval is a GRAPH, not a function."**

This system treats retrieval as a multi-step reasoning problem where each step makes intelligent decisions about:
- **WHAT** to retrieve
- **WHERE** to retrieve from
- **HOW** to retrieve
- **HOW MUCH** evidence is enough

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    RetrievalGraph                           │
│  (LangGraph State Machine Orchestrator)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      RetrievalState               │
        │  (Shared state across nodes)      │
        └───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Node 1     │    │   Node 2     │    │   Node 3     │
│  Interpreter │───▶│    Router    │───▶│   Strategy   │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Parallel Retrievers          │
        │  (Bucket 1, 2, 3, 4)              │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Evidence Aggregator          │
        │  (Rank, Balance, Merge)           │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Confidence Scorer            │
        │  (Score & Coverage Report)         │
        └───────────────────────────────────┘
```

## State Flow

### Initial State
```python
{
    "original_query": "What do Gen Z prefer?",
    "parsed_intent": {},
    "inferred_entities": {},
    "target_buckets": [],
    "retrieval_plan": {},
    "retrieved_documents": [],
    "aggregated_context": "",
    "confidence_score": 0.0,
    ...
}
```

### After Query Interpreter
```python
{
    "parsed_intent": {
        "primary_intent": "demographic_comparison",
        "intent_scores": {...},
        "confidence": 0.85
    },
    "inferred_entities": {
        "brands": ["mcdonalds"],
        "demographics": ["gen z"],
        "attributes": []
    },
    ...
}
```

### After Bucket Router
```python
{
    "target_buckets": [2, 4],  # Surveys + Scraped
    ...
}
```

### After Strategy Selector
```python
{
    "retrieval_plan": {
        2: {
            "strategy": "demographic_semantic",
            "filters": {"categorical_fields.generation": "Gen Z"},
            "top_k": 15,
            "use_semantic": True
        },
        4: {
            "strategy": "semantic_sentiment_brand",
            "filters": {"brand": "mcdonalds"},
            "top_k": 15,
            "use_semantic": True
        }
    },
    ...
}
```

### After Parallel Retrievers
```python
{
    "retrieved_documents": [DataRecord, ...],
    "bucket_results": {
        2: [DataRecord, ...],
        4: [DataRecord, ...]
    },
    ...
}
```

### After Evidence Aggregator
```python
{
    "aggregated_context": "=== Surveys & Interviews ===\n[1] ...",
    "citations": [
        {"record_id": "...", "bucket": 2, ...},
        ...
    ],
    ...
}
```

### Final State
```python
{
    "confidence_score": 0.87,
    "coverage": {
        "buckets_used": [2, 4],
        "time_span": "2021–2024",
        "brands_covered": ["mcdonalds"]
    },
    ...
}
```

## Node Responsibilities

### 1. Query Interpreter
**Input**: Natural language query  
**Output**: Parsed intent + extracted entities

**Key Logic**:
- Keyword-based intent classification
- Entity extraction (brands, demographics, time, attributes)
- Confidence scoring for intent

**Extensibility**:
- Can be replaced with LLM-based classification
- Can add NER models for better entity extraction

### 2. Bucket Router
**Input**: Parsed intent + entities  
**Output**: List of target buckets

**Routing Rules**:
- Sentiment → Bucket 2 + 4
- Demographics → Bucket 2 + 1
- Market → Bucket 3 + others
- Evolution → Multiple buckets with time filtering

**Extensibility**:
- Can add conditional routing
- Can add retry logic

### 3. Strategy Selector
**Input**: Target buckets + entities  
**Output**: Retrieval plan per bucket

**Strategies**:
- **Bucket 1**: Structured + semantic hybrid
- **Bucket 2**: Demographic filters + semantic
- **Bucket 3**: Time-windowed + structured
- **Bucket 4**: Semantic + sentiment + brand

**Extensibility**:
- Can add custom strategies per bucket
- Can adjust top_k dynamically

### 4. Parallel Retrievers
**Input**: Retrieval plan  
**Output**: Retrieved documents per bucket

**Execution**:
- Parallel retrieval from each bucket
- Bucket-specific retrieval logic
- Error handling per bucket
- Fallback strategies

**Extensibility**:
- Can add caching
- Can add query expansion
- Can add result pre-filtering

### 5. Evidence Aggregator
**Input**: Retrieved documents  
**Output**: Aggregated context + citations

**Operations**:
- De-duplication
- Relevance ranking
- Source balancing
- Context generation

**Extensibility**:
- Can add advanced re-ranking
- Can add LLM-based summarization
- Can add citation formatting

### 6. Confidence Scorer
**Input**: Aggregated documents  
**Output**: Confidence score + coverage report

**Signals**:
- Source count
- Bucket diversity
- Time coverage
- Sentiment consistency
- Sample size

**Extensibility**:
- Can add ML-based confidence models
- Can add user feedback integration

## Integration Points

### With Data Engine
```python
retrieval_graph = RetrievalGraph(
    retrieval_manager=engine.retrieval_manager,
    embedding_fn=embedding_fn,
)
```

### With RAG Pipelines
```python
result = retrieval_graph.retrieve(query)
context = result["context"]
citations = result["citations"]
# Use in LLM prompt
```

### With Agents
```python
# Hypothesis testing agent
agent = HypothesisTestingAgent(retrieval_graph)
hypothesis_result = agent.test("Gen Z prefers healthier options")

# Simulation agent
sim_agent = SimulationAgent(retrieval_graph)
simulation = sim_agent.simulate("preference_evolution", years=5)
```

## Error Handling

### Per-Node Errors
- Each node logs errors to `execution_log`
- Errors don't stop graph execution
- Fallback strategies available

### Missing Data
- Empty results handled gracefully
- Confidence score reflects data availability
- Coverage report shows gaps

### Missing Dependencies
- Fallback implementation if LangGraph unavailable
- Graceful degradation if embeddings unavailable
- Structured queries work without semantic search

## Performance Considerations

### Parallelism
- Buckets queried in parallel
- No blocking between buckets

### Result Limiting
- Configurable top_k per bucket
- Prevents excessive retrieval
- Balances sources

### Caching Opportunities
- Query embeddings
- Intent classification
- Retrieval results (with TTL)

## Observability

### Execution Log
Every decision is logged:
```python
{
    "node": "bucket_router",
    "timestamp": "2024-01-15T10:30:00",
    "decision": {
        "selected_buckets": [2, 4],
        "reasoning": "..."
    }
}
```

### Streaming
Watch graph execute step-by-step:
```python
for state_update in graph.retrieve_stream(query):
    print(state_update)
```

## Future Enhancements

See `TODO.md` for detailed enhancement plans:
1. LLM-based intent classification
2. Conditional routing & retry logic
3. Multi-agent coordination
4. Hypothesis testing agents
5. Simulation agents

## Design Decisions

### Why LangGraph?
- Explicit state management
- Observable execution
- Easy to extend
- Production-ready

### Why Keyword-Based Intent?
- No external dependencies
- Fast execution
- Predictable behavior
- Easy to debug

### Why Parallel Retrieval?
- Better performance
- Independent bucket queries
- Fault tolerance

### Why Source Balancing?
- Prevents one bucket from dominating
- Ensures diverse evidence
- Better for RAG

## Testing Strategy

1. **Unit Tests**: Each node tested independently
2. **Integration Tests**: Full graph execution
3. **End-to-End Tests**: Real queries with real data
4. **Performance Tests**: Latency and throughput

## Deployment Considerations

### Dependencies
- LangGraph (required)
- Sentence Transformers (optional, for semantic search)
- FAISS (optional, for vector search)

### Scaling
- Stateless nodes (can scale horizontally)
- Caching layer recommended
- Consider async execution for high throughput

### Monitoring
- Track query latency
- Monitor confidence scores
- Alert on low coverage
- Log execution traces

