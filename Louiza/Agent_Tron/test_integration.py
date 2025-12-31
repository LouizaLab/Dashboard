"""
Integration test for LangGraph retrieval system.

This test verifies that all components work together correctly.
Run with: python Agent_Tron/test_integration.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Data_Engine.data_engine import DataEngine
from Agent_Tron import (
    RetrievalState,
    create_initial_state,
    QueryInterpreterNode,
    BucketRouterNode,
    StrategySelectorNode,
    RetrievalGraph,
    RetrievalGraphFallback,
)


def test_state_creation():
    """Test that initial state can be created"""
    print("Testing state creation...")
    state = create_initial_state("test query")
    assert state["original_query"] == "test query"
    assert state["parsed_intent"] == {}
    assert state["target_buckets"] == []
    print("✓ State creation works")


def test_query_interpreter():
    """Test query interpreter node"""
    print("\nTesting query interpreter...")
    node = QueryInterpreterNode()
    state = create_initial_state("What do Gen Z prefer about McDonald's?")
    state = node(state)
    
    assert "parsed_intent" in state
    assert "inferred_entities" in state
    assert state["parsed_intent"].get("primary_intent") is not None
    assert "brands" in state["inferred_entities"]
    print("✓ Query interpreter works")


def test_bucket_router():
    """Test bucket router node"""
    print("\nTesting bucket router...")
    node = BucketRouterNode()
    state = create_initial_state("What do people feel about McDonald's?")
    
    # First run query interpreter
    interpreter = QueryInterpreterNode()
    state = interpreter(state)
    
    # Then run bucket router
    state = node(state)
    
    assert len(state["target_buckets"]) > 0
    assert all(bucket_id in [1, 2, 3, 4] for bucket_id in state["target_buckets"])
    print("✓ Bucket router works")


def test_strategy_selector():
    """Test strategy selector node"""
    print("\nTesting strategy selector...")
    node = StrategySelectorNode()
    state = create_initial_state("What do people feel about McDonald's?")
    
    # Run previous nodes
    interpreter = QueryInterpreterNode()
    router = BucketRouterNode()
    state = interpreter(state)
    state = router(state)
    
    # Run strategy selector
    state = node(state)
    
    assert "retrieval_plan" in state
    assert len(state["retrieval_plan"]) > 0
    print("✓ Strategy selector works")


def test_fallback_graph():
    """Test fallback graph (works without LangGraph)"""
    print("\nTesting fallback graph...")
    
    # Initialize Data Engine
    storage_dir = Path(__file__).parent.parent / "Data_Engine" / "storage_data"
    engine = DataEngine(storage_dir=storage_dir)
    
    # Create fallback graph
    graph = RetrievalGraphFallback(
        retrieval_manager=engine.retrieval_manager,
        embedding_fn=None,  # No embeddings for this test
    )
    
    # Test retrieval (may return empty results if no data)
    result = graph.retrieve("What do people prefer?")
    
    assert "query" in result
    assert "context" in result
    assert "citations" in result
    assert "confidence_score" in result
    assert "coverage" in result
    print("✓ Fallback graph works")


def main():
    """Run all tests"""
    print("=" * 80)
    print("LangGraph Retrieval System - Integration Tests")
    print("=" * 80)
    
    try:
        test_state_creation()
        test_query_interpreter()
        test_bucket_router()
        test_strategy_selector()
        test_fallback_graph()
        
        print("\n" + "=" * 80)
        print("All tests passed! ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

