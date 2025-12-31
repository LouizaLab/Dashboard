# RAG Graph System

Production-grade LangGraph-based RAG (Retrieval-Augmented Generation) system with multi-agent retrieval patterns and Phase-4 ground-truth anchoring integration.

## Overview

This system provides intelligent retrieval across 4 data buckets:
1. **Online datasets** (CSV)
2. **Internal surveys + interviews** (CSV + TXT)
3. **Client financial / foot-traffic** (CSV)
4. **Scraped public reviews/forums** (structured scraped records)

The system uses a multi-agent architecture:
- **Explorer Agent**: Expands queries, generates hypotheses, identifies related attributes
- **Critic Agent**: Validates evidence quality, detects contradictions, identifies missing buckets
- **Synthesizer Agent**: Produces RAG-ready context with citations and confidence scores

## Features

- ✅ **Multi-Agent Search Pattern**: Explorer, Critic, and Synthesizer agents
- ✅ **Confidence → Entropy Mapping**: Information-theoretic uncertainty metrics
- ✅ **Phase-4 Integration**: Ground-truth anchoring for market inference queries
- ✅ **Modular Architecture**: Adapter pattern for LLM, embeddings, and Phase-4 clients
- ✅ **Production-Ready**: Structured logging, error handling, testable design
- ✅ **CLI & API**: Command-line interface and FastAPI endpoint

## Installation

### Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `langgraph>=0.0.40` - Graph orchestration
- `openai>=1.0.0` - LLM provider (optional)
- `requests>=2.31.0` - HTTP client for Phase-4

### Data Engine Setup

Ensure your Data Engine is initialized with indexed data:

```python
from Data_Engine.data_engine import DataEngine
from pathlib import Path

data_engine = DataEngine(storage_dir=Path("Data_Engine/storage_data"))
# ... ingest and index your data ...
```

## Quick Start

### CLI Usage

Basic query:

```bash
python -m rag_graph.cli --query "What do Gen Z prefer about McDonald's?"
```

With Phase-4 anchoring:

```bash
python -m rag_graph.cli \
  --query "How does McDonald's revenue correlate with Gen Z sentiment?" \
  --enable-phase4 \
  --phase4-repo-path /path/to/phase4/repo
```

Output formats:
- `--output json` - JSON output
- `--output pretty` - Human-readable format (default)

### Python API

```python
from Data_Engine.data_engine import DataEngine
from adapters.data_engine_adapter import DataEngineAdapter
from adapters.llm.openai_client import OpenAIClient
from rag_graph.graph import RAGGraph
from pathlib import Path

# Initialize Data Engine
data_engine = DataEngine(storage_dir=Path("Data_Engine/storage_data"))
data_engine_adapter = DataEngineAdapter(data_engine)

# Initialize LLM client
llm_client = OpenAIClient(api_key="your-api-key")

# Create graph
graph = RAGGraph(
    data_engine_adapter=data_engine_adapter,
    llm_client=llm_client,
)

# Execute query
result = graph.invoke("What do Gen Z prefer about McDonald's?")

print(f"Confidence: {result['confidence']:.2f}")
print(f"RAG Context:\n{result['rag_context']}")
```

### FastAPI Endpoint

Start the API server:

```bash
uvicorn rag_graph.api:app --host 0.0.0.0 --port 8000
```

Query endpoint:

```bash
curl -X POST http://localhost:8000/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What do Gen Z prefer about McDonald's?"}'
```

## Configuration

Configuration is managed via environment variables:

### LLM Configuration

```bash
export RAG_LLM_PROVIDER=openai  # or "mock" for testing
export RAG_LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=your-api-key
```

### Phase-4 Configuration

**Subprocess Mode** (runs Phase-4 code locally):

```bash
export RAG_PHASE4_MODE=subprocess
export RAG_PHASE4_REPO_PATH=/path/to/phase4/repo
export RAG_PHASE4_ENTRYPOINT="python -m phase4.anchor"
```

**HTTP Mode** (calls Phase-4 service):

```bash
export RAG_PHASE4_MODE=http
export RAG_PHASE4_URL=http://localhost:8001
export RAG_PHASE4_API_KEY=your-api-key  # optional
```

**Disabled** (default):

```bash
export RAG_PHASE4_MODE=disabled
```

### Retrieval Configuration

```bash
export RAG_TOP_K_BUCKET_1=10
export RAG_TOP_K_BUCKET_2=15
export RAG_TOP_K_BUCKET_3=20
export RAG_TOP_K_BUCKET_4=15
export RAG_MAX_EXPANDED_QUERIES=5
```

## Phase-4 Integration

### Overview

Phase-4 anchoring is an external system that calibrates retrieval results against ground-truth data. The RAG system integrates with Phase-4 through a stable JSON I/O contract.

### Integration Modes

#### 1. Subprocess Mode

Runs Phase-4 code in another repository via subprocess:

```python
from phase4_client.local_subprocess_client import LocalSubprocessClient

anchor_client = LocalSubprocessClient(
    phase4_repo_path="/path/to/phase4/repo",
    entrypoint_command="python -m phase4.anchor",
)
```

**Phase-4 Entrypoint Contract**:

Your Phase-4 entrypoint script should:
1. Accept a JSON file path as command-line argument
2. Read `AnchorRequest` JSON from the file
3. Process the request and write `AnchorResponse` JSON to stdout or a response file

Example Phase-4 entrypoint (`phase4/anchor.py`):

```python
import json
import sys
from phase4_anchoring import GroundTruthAnchoring

def main():
    request_file = sys.argv[1]
    
    with open(request_file, 'r') as f:
        request_data = json.load(f)
    
    # Process request
    # ... your anchoring logic ...
    
    # Build response
    response = {
        "anchored_score": 0.85,
        "calibration_details": {...},
        "updated_confidence": 0.9,
        "notes": [...],
        "warnings": [],
        "success": True,
    }
    
    # Output JSON to stdout
    print(json.dumps(response))

if __name__ == "__main__":
    main()
```

#### 2. HTTP Mode

Calls Phase-4 as a REST API service:

```python
from phase4_client.http_client import HTTPClient

anchor_client = HTTPClient(
    base_url="http://localhost:8001",
    endpoint="/anchor",
    api_key="optional-api-key",
)
```

**HTTP API Contract**:

- **Endpoint**: `POST /anchor`
- **Request Body**: `AnchorRequest` JSON
- **Response**: `AnchorResponse` JSON

Example request:

```json
{
  "query": "How does McDonald's revenue correlate with Gen Z sentiment?",
  "retrieved_evidence_summary": "Survey Evidence:\n- Gen Z prefers...",
  "structured_aggregates": {
    "total_records": 25,
    "buckets_used": [2, 4],
    "confidence": 0.75
  },
  "market_target_variable": "revenue",
  "time_range": {"start": "2023-01-01", "end": "2024-01-01"},
  "brands": ["mcdonalds"],
  "confidence": 0.75
}
```

Example response:

```json
{
  "anchored_score": 0.82,
  "calibration_details": {
    "calibrated_params": {...},
    "validation_metrics": {...}
  },
  "updated_confidence": 0.85,
  "notes": ["Anchoring successful"],
  "warnings": [],
  "success": true
}
```

### When Phase-4 is Called

Phase-4 anchoring is triggered when:
- Intent type is `market_inference` or `behavioral_evolution`
- Query mentions metrics (e.g., "revenue", "sales")
- Query explicitly requests anchoring (e.g., "anchor this to ground truth")

### Schema Definitions

See `phase4_client/schemas.py` for full schema definitions:
- `AnchorRequest`: Input contract
- `AnchorResponse`: Output contract

## Architecture

### Graph Flow

```
START
  ↓
[interpret_query] - Understand intent, extract entities
  ↓
[explorer_agent] - Expand queries, generate hypotheses
  ↓
[plan_retrieval] - Plan retrieval strategies per bucket
  ↓
[retrieve_parallel] - Execute parallel retrieval
  ↓
[critic_agent] - Validate evidence quality
  ↓ (if needs_second_pass)
[retrieve_parallel] - Second retrieval pass (optional)
  ↓
[synthesize_agent] - Generate RAG-ready context
  ↓
[score_entropy] - Compute confidence and entropy
  ↓
[phase4_anchor] - Integrate with Phase-4 (if applicable)
  ↓
END
```

### Node Responsibilities

1. **InterpretQueryNode**: Classifies intent, extracts entities (brands, demographics, time ranges, metrics)
2. **ExplorerAgentNode**: Expands queries with synonyms, identifies competitors, proposes retrieval angles
3. **PlanRetrievalNode**: Determines which buckets to query and strategies per bucket
4. **RetrieveParallelNode**: Executes retrieval from each bucket in parallel
5. **CriticAgentNode**: Validates evidence, detects contradictions, identifies missing buckets
6. **SynthesizeAgentNode**: Produces structured RAG context with citations
7. **ScoreEntropyNode**: Computes confidence scores and entropy metrics
8. **Phase4AnchorNode**: Calls Phase-4 anchoring service if applicable

### Adapters

The system uses adapter pattern for external dependencies:

- **DataEngineAdapter**: Wraps Data Engine for consistent interface
- **LLMClient**: Abstract interface for LLM providers (OpenAI, Mock)
- **AnchorClient**: Abstract interface for Phase-4 clients (Subprocess, HTTP)

## Output Contract

The graph returns a standardized response:

```python
{
    "query": str,
    "intent": {
        "primary_intent": str,
        "intent_confidence": float,
        "intent_scores": dict,
    },
    "entities": {
        "brands": list[str],
        "segments": list[str],
        "time_range": dict | None,
        "metrics": list[str],
        "keywords": list[str],
        "attributes": list[str],
    },
    "rag_context": str,  # RAG-ready context with sections
    "citations": [
        {
            "record_id": str,
            "bucket_id": int,
            "source_name": str,
            "brand": str | None,
            "timestamp": str | None,
        }
    ],
    "confidence": float,  # 0.0-1.0
    "entropy": {
        "binary_entropy": float,
        "bucket_entropy": float,
        "coverage_penalty": float,
        "contradiction_penalty": float,
        "evidence_mass": dict,
        "notes": list[str],
    },
    "coverage": {
        "buckets_used": list[int],
        "counts_by_bucket": dict[int, int],
        "time_span": dict | None,
        "total_records": int,
    },
    "phase4": {
        "anchored_score": float,
        "calibration_details": dict,
        "updated_confidence": float,
        "notes": list[str],
        "warnings": list[str],
        "success": bool,
    },
}
```

## Entropy Metrics

The system computes information-theoretic uncertainty metrics:

- **Binary Entropy**: `H(p) = -p log p - (1-p) log (1-p)` from confidence score
- **Bucket Entropy**: Multi-class entropy over bucket distribution
- **Coverage Penalty**: Penalty for missing expected buckets
- **Evidence Mass**: Distribution metrics (by bucket, time window, sentiment)

## Testing

Run unit tests:

```bash
python -m pytest tests/test_rag_graph.py -v
```

Run with mock LLM:

```bash
export RAG_LLM_PROVIDER=mock
python -m rag_graph.cli --query "Test query"
```

## Troubleshooting

### Phase-4 Integration Issues

**Subprocess mode fails**:
- Check that `RAG_PHASE4_REPO_PATH` points to valid directory
- Verify entrypoint command is correct
- Check Phase-4 entrypoint script accepts JSON file argument

**HTTP mode fails**:
- Verify Phase-4 service is running at `RAG_PHASE4_URL`
- Check API endpoint matches `/anchor`
- Verify request/response JSON format matches schemas

### LLM Issues

**OpenAI API errors**:
- Verify `OPENAI_API_KEY` is set
- Check API quota/rate limits
- System falls back to rule-based interpretation if LLM unavailable

### Retrieval Issues

**No results returned**:
- Check Data Engine has indexed data
- Verify bucket IDs are correct (1-4)
- Check filters aren't too restrictive

## Development

### Adding New Nodes

1. Create node class in `rag_graph/nodes/`
2. Implement `__call__(state: RetrievalState) -> RetrievalState`
3. Add node to `rag_graph/graph.py` workflow
4. Update tests

### Adding New LLM Providers

1. Implement `LLMClient` protocol in `adapters/llm/`
2. Add provider selection logic in `rag_graph/cli.py` and `rag_graph/api.py`
3. Update configuration

### Extending Phase-4 Integration

1. Modify `AnchorRequest`/`AnchorResponse` schemas if needed
2. Update `Phase4AnchorNode` to extract additional data
3. Update Phase-4 entrypoint/service to handle new fields

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

