# LangGraph Retrieval System - TODO & Future Enhancements

This document outlines planned enhancements and extensions for the LangGraph retrieval system.

## High Priority

### 1. LLM-Based Intent Classification
**Status**: Not Started  
**Priority**: High

Replace keyword-based intent classification with LLM-based classification for better accuracy.

**Implementation**:
- Add `LLMQueryInterpreterNode` that uses an LLM (OpenAI, Anthropic, etc.)
- Prompt: "Classify this query into one of: preference_discovery, sentiment_analysis, demographic_comparison, behavioral_evolution, market_inference"
- Extract entities using LLM with structured output
- Fallback to keyword-based if LLM unavailable

**Files to Modify**:
- `nodes.py`: Add `LLMQueryInterpreterNode`
- `graph.py`: Make interpreter node configurable

---

### 2. Conditional Routing & Retry Logic
**Status**: Not Started  
**Priority**: High

Add conditional edges to retry retrieval with different buckets if initial results are insufficient.

**Implementation**:
- Add conditional edge after `parallel_retrievers`
- Check if `len(retrieved_documents) < threshold`
- If insufficient, route to `bucket_router` with expanded bucket list
- Limit retries to prevent infinite loops

**Graph Modification**:
```python
workflow.add_conditional_edges(
    "parallel_retrievers",
    should_retry,
    {
        "retry": "bucket_router",
        "continue": "evidence_aggregator"
    }
)
```

---

### 3. Multi-Agent Coordination
**Status**: Not Started  
**Priority**: Medium

Enable multiple agents to coordinate retrieval for complex queries.

**Use Cases**:
- Agent 1: Retrieve sentiment data
- Agent 2: Retrieve financial data
- Agent 3: Correlate results

**Implementation**:
- Create `MultiAgentRetrievalGraph` that spawns sub-graphs per agent
- Add coordination node that merges results
- Support agent-specific retrieval strategies

---

## Medium Priority

### 4. Hypothesis Testing Agents
**Status**: Not Started  
**Priority**: Medium

Create agents that use retrieval to test behavioral hypotheses.

**Example Hypotheses**:
- "Gen Z prefers healthier options"
- "Sentiment correlates with revenue"
- "Taste preferences have shifted toward plant-based"

**Implementation**:
- Create `HypothesisTestingAgent` class
- Use retrieval graph to gather evidence
- Statistical analysis of retrieved documents
- Generate hypothesis test results

**Files to Create**:
- `agents/hypothesis_testing.py`

---

### 5. Simulation Agents
**Status**: Not Started  
**Priority**: Medium

Create agents that use retrieved data for behavioral simulation.

**Use Cases**:
- Simulate consumer behavior over time
- Model preference shifts
- Predict market responses

**Implementation**:
- Create `SimulationAgent` class
- Use retrieval graph to gather historical data
- Feed data into simulation model
- Return simulation results

**Files to Create**:
- `agents/simulation.py`

---

### 6. Advanced Entity Extraction
**Status**: Not Started  
**Priority**: Medium

Improve entity extraction with NER models and structured parsing.

**Enhancements**:
- Use spaCy or similar for NER
- Extract product names, locations, dates
- Parse complex time expressions ("last 3 years", "Q1 2024")
- Extract numerical ranges

**Files to Modify**:
- `nodes.py`: Enhance `QueryInterpreterNode._extract_*` methods

---

### 7. Dynamic Top-K Selection
**Status**: Not Started  
**Priority**: Medium

Automatically adjust `top_k` based on query complexity and available data.

**Logic**:
- Simple queries → lower top_k
- Complex queries → higher top_k
- Check data availability before retrieval
- Adjust based on confidence requirements

**Files to Modify**:
- `nodes.py`: `StrategySelectorNode._get_top_k_for_bucket()`

---

## Low Priority

### 8. Caching Layer
**Status**: Not Started  
**Priority**: Low

Add caching for frequent queries and embeddings.

**Implementation**:
- Cache query embeddings
- Cache retrieval results (with TTL)
- Cache intent classification results
- Use Redis or in-memory cache

**Files to Create**:
- `cache.py`

---

### 9. Query Expansion
**Status**: Not Started  
**Priority**: Low

Expand queries with synonyms and related terms for better retrieval.

**Implementation**:
- Use word embeddings to find synonyms
- Expand entity mentions
- Generate query variations
- Retrieve from multiple query variations

**Files to Create**:
- `query_expansion.py`

---

### 10. Result Re-ranking
**Status**: Not Started  
**Priority**: Low

Add advanced re-ranking using cross-encoders or LLM-based scoring.

**Implementation**:
- Use cross-encoder models (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- LLM-based relevance scoring
- Learn-to-rank models
- User feedback integration

**Files to Create**:
- `reranking.py`

---

### 11. Multi-Modal Retrieval
**Status**: Not Started  
**Priority**: Low

Extend to support image and other media retrieval.

**Implementation**:
- Add image embedding support
- Multi-modal query understanding
- Cross-modal retrieval (text → image, image → text)

**Files to Create**:
- `multimodal_retrieval.py`

---

### 12. Observability & Monitoring
**Status**: Not Started  
**Priority**: Low

Add comprehensive logging, metrics, and tracing.

**Metrics**:
- Query latency per node
- Retrieval success rate per bucket
- Confidence score distribution
- Coverage metrics

**Implementation**:
- Integrate with OpenTelemetry
- Add Prometheus metrics
- Structured logging
- Performance profiling

**Files to Create**:
- `observability.py`

---

## Research & Exploration

### 13. Reinforcement Learning for Routing
**Status**: Research  
**Priority**: Research

Use RL to learn optimal bucket routing strategies.

**Approach**:
- Define routing as MDP
- Reward based on retrieval quality
- Learn routing policy
- A/B test against rule-based routing

---

### 14. Graph Neural Networks for Ranking
**Status**: Research  
**Priority**: Research

Use GNNs to model relationships between documents for better ranking.

**Approach**:
- Build document graph (similarity edges)
- Use GNN to propagate relevance signals
- Rank based on graph structure

---

## Integration Points

### External Systems

1. **LLM Providers**
   - OpenAI GPT-4
   - Anthropic Claude
   - Local LLMs (Llama, Mistral)

2. **Vector Databases**
   - Pinecone
   - Weaviate
   - Qdrant
   - Chroma

3. **Agent Frameworks**
   - LangChain
   - AutoGen
   - CrewAI

4. **Monitoring**
   - LangSmith
   - Weights & Biases
   - MLflow

---

## Notes

- All enhancements should maintain backward compatibility
- Add comprehensive tests for new features
- Update documentation as features are added
- Consider performance implications of each enhancement

