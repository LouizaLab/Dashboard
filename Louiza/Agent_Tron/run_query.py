"""
Simple script to run queries through the LangGraph retrieval system.

Usage:
    python Agent_Tron/run_query.py "What do people feel about McDonald's?"
    
Or run interactively:
    python Agent_Tron/run_query.py
"""

import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Data_Engine.data_engine import DataEngine
from Agent_Tron import RetrievalGraph, RetrievalGraphFallback


def setup_retrieval_system():
    """Initialize the retrieval system"""
    print("=" * 80)
    print("Initializing LangGraph Retrieval System")
    print("=" * 80)
    
    # Initialize Data Engine
    print("\n1. Loading Data Engine...")
    storage_dir = Path(__file__).parent.parent / "Data_Engine" / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    print(f"   ✓ Data Engine loaded from: {storage_dir}")
    
    # Set up embeddings
    print("\n2. Setting up embeddings...")
    embedding_fn = None
    try:
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_fn = lambda text: encoder.encode(text, convert_to_numpy=True)
        engine.set_embedding_fn(embedding_fn)
        print("   ✓ Embeddings ready (semantic search enabled)")
    except Exception as e:
        print(f"   ⚠ Could not set up embeddings: {e}")
        print("   Continuing without semantic search (structured queries only)")
    
    # Initialize LangGraph retrieval system
    print("\n3. Initializing retrieval graph...")
    try:
        retrieval_graph = RetrievalGraph(
            retrieval_manager=engine.retrieval_manager,
            embedding_fn=embedding_fn,
        )
        print("   ✓ LangGraph retrieval system ready!")
        return retrieval_graph
    except ImportError:
        print("   ⚠ LangGraph not installed, using fallback implementation...")
        retrieval_graph = RetrievalGraphFallback(
            retrieval_manager=engine.retrieval_manager,
            embedding_fn=embedding_fn,
        )
        print("   ✓ Fallback retrieval system ready!")
        return retrieval_graph


def display_results(result, query):
    """Display retrieval results in a readable format"""
    print("\n" + "=" * 80)
    print("RETRIEVAL RESULTS")
    print("=" * 80)
    
    print(f"\n📝 Query: {query}")
    print(f"🎯 Intent: {result['parsed_intent'].get('primary_intent', 'N/A')}")
    print(f"📦 Target Buckets: {result['target_buckets']}")
    print(f"📊 Documents Retrieved: {result['num_documents']}")
    print(f"🎲 Confidence Score: {result['confidence_score']:.2%}")
    
    # Coverage
    print(f"\n📈 COVERAGE REPORT")
    print("-" * 80)
    coverage = result['coverage']
    print(f"   Buckets Used: {coverage.get('buckets_used', [])}")
    print(f"   Time Span: {coverage.get('time_span', 'N/A')}")
    print(f"   Brands Covered: {coverage.get('brands_covered', [])}")
    print(f"   Sources: {len(coverage.get('sources', []))} unique sources")
    
    # Context preview
    print(f"\n📄 AGGREGATED CONTEXT")
    print("-" * 80)
    context = result['context']
    if context:
        # Show first 1000 characters
        preview = context[:1000] + "..." if len(context) > 1000 else context
        print(preview)
    else:
        print("   (No context generated - no documents retrieved)")
    
    # Citations
    print(f"\n📚 CITATIONS ({len(result['citations'])} total)")
    print("-" * 80)
    for i, citation in enumerate(result['citations'][:5], 1):  # Show first 5
        print(f"   {i}. Bucket {citation['bucket']}: {citation['source']}")
        print(f"      Record ID: {citation['record_id'][:8]}...")
        if citation.get('brand'):
            print(f"      Brand: {citation['brand']}")
        if citation.get('timestamp'):
            print(f"      Timestamp: {citation['timestamp']}")
    
    if len(result['citations']) > 5:
        print(f"   ... and {len(result['citations']) - 5} more citations")
    
    # Execution log
    print(f"\n🔍 EXECUTION LOG (Step-by-step decisions)")
    print("-" * 80)
    for log_entry in result['execution_log']:
        node_name = log_entry['node']
        decision = log_entry.get('decision', {})
        print(f"   [{node_name}]")
        if isinstance(decision, dict):
            for key, value in list(decision.items())[:3]:  # Show first 3 keys
                if isinstance(value, (str, int, float, list)):
                    print(f"      {key}: {value}")
        print()


def run_query(retrieval_graph, query):
    """Execute a query and display results"""
    print("\n" + "=" * 80)
    print(f"EXECUTING QUERY")
    print("=" * 80)
    print(f"Query: {query}")
    print()
    
    try:
        result = retrieval_graph.retrieve(query)
        display_results(result, query)
        return result
    except Exception as e:
        print(f"\n❌ Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return None


def interactive_mode(retrieval_graph):
    """Run in interactive mode"""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Enter queries (or 'quit' to exit)")
    print()
    
    while True:
        try:
            query = input("Query: ").strip()
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            run_query(retrieval_graph, query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


def main():
    """Main entry point"""
    # Setup
    retrieval_graph = setup_retrieval_system()
    
    # Check if query provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_query(retrieval_graph, query)
    else:
        # Interactive mode
        interactive_mode(retrieval_graph)


if __name__ == "__main__":
    main()

