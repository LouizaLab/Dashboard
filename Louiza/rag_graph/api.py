"""
FastAPI endpoint for RAG Graph System

Provides REST API for running queries.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes
    class FastAPI:
        pass
    class HTTPException(Exception):
        pass
    class BaseModel:
        pass

from Data_Engine.data_engine import DataEngine
from adapters.data_engine_adapter import DataEngineAdapter
from adapters.llm.openai_client import OpenAIClient
from adapters.llm.mock_client import MockLLMClient
from phase4_client.local_subprocess_client import LocalSubprocessClient
from phase4_client.http_client import HTTPClient
from .graph import RAGGraph
from .config import get_config


app = FastAPI(title="RAG Graph API", version="1.0.0")

# Global graph instance (initialized on startup)
rag_graph: Optional[RAGGraph] = None


class QueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str
    client_id: Optional[str] = None
    enable_phase4: bool = False


class QueryResponse(BaseModel):
    """Response model for RAG query"""
    query: str
    intent: Dict[str, Any]
    entities: Dict[str, Any]
    rag_context: str
    citations: list[Dict[str, Any]]
    confidence: float
    entropy: Dict[str, Any]
    coverage: Dict[str, Any]
    phase4: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize RAG graph on startup"""
    global rag_graph
    
    if not FASTAPI_AVAILABLE:
        return
    
    config = get_config()
    
    # Initialize Data Engine
    data_engine = DataEngine(storage_dir=Path("Data_Engine/storage_data"))
    data_engine_adapter = DataEngineAdapter(data_engine)
    
    # Initialize LLM client
    if config.llm_provider == "mock":
        llm_client = MockLLMClient()
    else:
        api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            llm_client = OpenAIClient(api_key=api_key, model=config.llm_model)
        else:
            llm_client = MockLLMClient()
    
    # Initialize Phase-4 client
    anchor_client = None
    if config.phase4_mode == "subprocess" and config.phase4_repo_path:
        anchor_client = LocalSubprocessClient(
            phase4_repo_path=config.phase4_repo_path,
            entrypoint_command=config.phase4_entrypoint,
        )
    elif config.phase4_mode == "http" and config.phase4_url:
        anchor_client = HTTPClient(
            base_url=config.phase4_url,
            api_key=config.phase4_api_key,
        )
    
    # Create graph
    rag_graph = RAGGraph(
        data_engine_adapter=data_engine_adapter,
        llm_client=llm_client,
        anchor_client=anchor_client,
    )


@app.post("/rag_query", response_model=QueryResponse)
async def rag_query(request: QueryRequest) -> QueryResponse:
    """
    Execute RAG query.
    
    Args:
        request: QueryRequest with query string and optional parameters
        
    Returns:
        QueryResponse with retrieval results
    """
    if not rag_graph:
        raise HTTPException(status_code=503, detail="RAG graph not initialized")
    
    try:
        result = rag_graph.invoke(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "graph_initialized": rag_graph is not None}

