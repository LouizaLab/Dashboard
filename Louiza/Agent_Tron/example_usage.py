"""
Example: LangGraph-based Intelligent Retrieval System

This example demonstrates how to use the LangGraph retrieval system
for agentic RAG, hypothesis testing, and preference discovery.

The system treats retrieval as a multi-step reasoning problem:
1. Understand user intent
2. Route to relevant data buckets
3. Select retrieval strategies
4. Execute parallel retrieval
5. Aggregate evidence
6. Score confidence
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

from Data_Engine.data_engine import DataEngine
from Agent_Tron import RetrievalGraph, RetrievalGraphFallback


def main():
    """Run example queries through the LangGraph retrieval system"""
    
    print("=" * 80)
    print("LangGraph Intelligent Retrieval System - Example")
    print("=" * 80)
    
    # Initialize Data Engine
    print("\n1. Initializing Data Engine...")
    storage_dir = Path("./Data_Engine/storage_data")
    engine = DataEngine(storage_dir=storage_dir)
    
    # Set up embeddings
    print("2. Setting up embeddings...")
    try:
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_fn = lambda text: encoder.encode(text, convert_to_numpy=True)
        engine.set_embedding_fn(embedding_fn)
        print("   ✓ Embeddings ready!")
    except Exception as e:
        print(f"   ⚠ Could not set up embeddings: {e}")
        print("   Continuing without semantic search...")
        embedding_fn = None
    
    # Initialize LangGraph retrieval system
    print("\n3. Initializing LangGraph retrieval system...")
    try:
        retrieval_graph = RetrievalGraph(
            retrieval_manager=engine.retrieval_manager,
            embedding_fn=embedding_fn,
        )
        print("   ✓ LangGraph retrieval system ready!")
    except ImportError:
        print("   ⚠ LangGraph not installed, using fallback implementation...")
        retrieval_graph = RetrievalGraphFallback(
            retrieval_manager=engine.retrieval_manager,
            embedding_fn=embedding_fn,
        )
    
    # Example queries
    example_queries = [
        {
            "query": "What do people feel about McDonald's?",
            "description": "Sentiment analysis query - should route to Bucket 2 (Surveys) and Bucket 4 (Scraped)",
        },
        {
            "query": "What do Gen Z prefer about fast food?",
            "description": "Demographic preference query - should route to Bucket 2 (Surveys) and Bucket 1 (Online datasets)",
        },
        {
            "query": "How has taste preference changed over time?",
            "description": "Behavioral evolution query - should route to multiple buckets with time filtering",
        },
        {
            "query": "Does sentiment correlate with revenue for burger chains?",
            "description": "Market inference query - should route to Bucket 3 (Financial) + sentiment buckets",
        },
    ]
    
    # Execute queries
    print("\n" + "=" * 80)
    print("4. Executing Example Queries")
    print("=" * 80)
    
    for i, example in enumerate(example_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {example['query']}")
        print(f"Description: {example['description']}")
        print(f"{'='*80}\n")
        
        try:
            result = retrieval_graph.retrieve(example['query'])
            
            # Display results
            print("📊 RETRIEVAL RESULTS")
            print("-" * 80)
            print(f"Intent: {result['parsed_intent'].get('primary_intent', 'N/A')}")
            print(f"Target Buckets: {result['target_buckets']}")
            print(f"Documents Retrieved: {result['num_documents']}")
            print(f"Confidence Score: {result['confidence_score']:.2f}")
            
            print(f"\n📈 COVERAGE")
            print("-" * 80)
            coverage = result['coverage']
            print(f"Buckets Used: {coverage.get('buckets_used', [])}")
            print(f"Time Span: {coverage.get('time_span', 'N/A')}")
            print(f"Brands Covered: {coverage.get('brands_covered', [])}")
            print(f"Sources: {len(coverage.get('sources', []))} unique sources")
            
            print(f"\n📝 CONTEXT (Preview)")
            print("-" * 80)
            context_preview = result['context'][:500] + "..." if len(result['context']) > 500 else result['context']
            print(context_preview)
            
            print(f"\n📚 CITATIONS (First 3)")
            print("-" * 80)
            for citation in result['citations'][:3]:
                print(f"  - Bucket {citation['bucket']}: {citation['source']} (ID: {citation['record_id'][:8]}...)")
            
            print(f"\n🔍 EXECUTION LOG (Decisions Made)")
            print("-" * 80)
            for log_entry in result['execution_log']:
                print(f"  [{log_entry['node']}] {log_entry.get('decision', {})}")
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Example Complete!")
    print("=" * 80)
    
    print("\n💡 NEXT STEPS:")
    print("-" * 80)
    print("1. Extend QueryInterpreterNode with LLM-based intent classification")
    print("2. Add conditional routing (e.g., if no results, try different buckets)")
    print("3. Implement hypothesis testing agents that use this retrieval system")
    print("4. Add multi-agent coordination for complex queries")
    print("5. Integrate with simulation agents for behavioral modeling")


if __name__ == "__main__":
    main()

