"""
CLI for RAG Graph System

Provides command-line interface for running queries.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from Data_Engine.data_engine import DataEngine
from adapters.data_engine_adapter import DataEngineAdapter
from adapters.llm.openai_client import OpenAIClient
from adapters.llm.mock_client import MockLLMClient
from phase4_client.local_subprocess_client import LocalSubprocessClient
from phase4_client.http_client import HTTPClient
from phase4_client.schemas import create_disabled_response
from .graph import RAGGraph
from .config import get_config


def create_llm_client(config) -> object:
    """Create LLM client based on config"""
    if config.llm_provider == "mock":
        return MockLLMClient()
    
    elif config.llm_provider == "openai":
        api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not set. Using mock LLM client.", file=sys.stderr)
            return MockLLMClient()
        
        return OpenAIClient(api_key=api_key, model=config.llm_model)
    
    else:
        print(f"Warning: Unknown LLM provider '{config.llm_provider}'. Using mock.", file=sys.stderr)
        return MockLLMClient()


def create_anchor_client(config) -> object:
    """Create Phase-4 anchor client based on config"""
    if config.phase4_mode == "disabled":
        return None
    
    elif config.phase4_mode == "subprocess":
        if not config.phase4_repo_path:
            print("Warning: PHASE4_REPO_PATH not set. Phase-4 anchoring disabled.", file=sys.stderr)
            return None
        
        return LocalSubprocessClient(
            phase4_repo_path=config.phase4_repo_path,
            entrypoint_command=config.phase4_entrypoint,
        )
    
    elif config.phase4_mode == "http":
        if not config.phase4_url:
            print("Warning: PHASE4_URL not set. Phase-4 anchoring disabled.", file=sys.stderr)
            return None
        
        return HTTPClient(
            base_url=config.phase4_url,
            api_key=config.phase4_api_key,
        )
    
    else:
        print(f"Warning: Unknown Phase-4 mode '{config.phase4_mode}'. Phase-4 disabled.", file=sys.stderr)
        return None


def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(description="RAG Graph Query System")
    parser.add_argument("--query", "-q", required=True, help="Query string")
    parser.add_argument("--data-engine-path", default="Data_Engine/storage_data", help="Data Engine storage path")
    parser.add_argument("--enable-phase4", action="store_true", help="Enable Phase-4 anchoring")
    parser.add_argument("--phase4-repo-path", help="Path to Phase-4 repository")
    parser.add_argument("--phase4-url", help="Phase-4 HTTP service URL")
    parser.add_argument("--output", "-o", choices=["json", "pretty"], default="pretty", help="Output format")
    parser.add_argument("--llm-provider", choices=["openai", "mock"], default="openai", help="LLM provider")
    
    args = parser.parse_args()
    
    # Load config
    config = get_config()
    
    # Override config with CLI args
    if args.enable_phase4:
        config.phase4_mode = "subprocess" if args.phase4_repo_path else "http"
    if args.phase4_repo_path:
        config.phase4_repo_path = args.phase4_repo_path
    if args.phase4_url:
        config.phase4_url = args.phase4_url
    if args.llm_provider:
        config.llm_provider = args.llm_provider
    
    # Initialize Data Engine
    print("Initializing Data Engine...", file=sys.stderr)
    data_engine = DataEngine(storage_dir=Path(args.data_engine_path))
    data_engine_adapter = DataEngineAdapter(data_engine)
    
    # Initialize LLM client
    print("Initializing LLM client...", file=sys.stderr)
    llm_client = create_llm_client(config)
    
    # Initialize Phase-4 client
    anchor_client = None
    if args.enable_phase4 or config.phase4_mode != "disabled":
        print("Initializing Phase-4 client...", file=sys.stderr)
        anchor_client = create_anchor_client(config)
    
    # Create graph
    print("Creating RAG graph...", file=sys.stderr)
    graph = RAGGraph(
        data_engine_adapter=data_engine_adapter,
        llm_client=llm_client,
        anchor_client=anchor_client,
    )
    
    # Execute query
    print(f"Executing query: {args.query}", file=sys.stderr)
    result = graph.invoke(args.query)
    
    # Output results
    if args.output == "json":
        print(json.dumps(result, indent=2, default=str))
    else:
        # Pretty print
        print("\n" + "=" * 60)
        print("RAG QUERY RESULTS")
        print("=" * 60)
        print(f"\nQuery: {result['query']}")
        print(f"\nIntent: {result['intent'].get('primary_intent', 'unknown')} (confidence: {result['intent'].get('intent_confidence', 0.0):.2f})")
        print(f"\nEntities: {json.dumps(result['entities'], indent=2)}")
        print(f"\nConfidence: {result['confidence']:.2f}")
        print(f"\nEntropy:")
        print(f"  Binary Entropy: {result['entropy'].get('binary_entropy', 0.0):.3f}")
        print(f"  Bucket Entropy: {result['entropy'].get('bucket_entropy', 0.0):.3f}")
        print(f"\nCoverage:")
        print(f"  Buckets Used: {result['coverage'].get('buckets_used', [])}")
        print(f"  Total Records: {result['coverage'].get('total_records', 0)}")
        print(f"\nRAG Context:\n{result['rag_context']}")
        print(f"\nCitations: {len(result['citations'])} records")
        if result['phase4'].get('success'):
            print(f"\nPhase-4 Anchoring:")
            print(f"  Anchored Score: {result['phase4'].get('anchored_score', 0.0):.2f}")
            print(f"  Updated Confidence: {result['phase4'].get('updated_confidence', 0.0):.2f}")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    import os
    main()

