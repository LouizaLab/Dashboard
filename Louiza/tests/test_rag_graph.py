"""
Tests for RAG Graph System

Unit tests and integration tests for the RAG graph.
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from Data_Engine.core.schema import DataRecord
from adapters.data_engine_adapter import DataEngineAdapter
from adapters.llm.mock_client import MockLLMClient
from phase4_client.schemas import AnchorRequest, AnchorResponse
from rag_graph.graph import RAGGraph
from rag_graph.state import create_initial_state
from metrics.entropy import binary_entropy, bucket_entropy


class TestEntropyMetrics(unittest.TestCase):
    """Test entropy metric functions"""
    
    def test_binary_entropy(self):
        """Test binary entropy calculation"""
        # Maximum entropy at p=0.5
        self.assertAlmostEqual(binary_entropy(0.5), 1.0, places=2)
        
        # Zero entropy at extremes
        self.assertEqual(binary_entropy(0.0), 0.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        
        # Entropy increases towards 0.5
        self.assertGreater(binary_entropy(0.3), binary_entropy(0.2))
    
    def test_bucket_entropy(self):
        """Test bucket entropy calculation"""
        # Create test records
        records = [
            DataRecord(bucket_id=1, source_name="test1"),
            DataRecord(bucket_id=1, source_name="test2"),
            DataRecord(bucket_id=2, source_name="test3"),
        ]
        
        entropy = bucket_entropy(records)
        self.assertGreater(entropy, 0.0)
        self.assertLess(entropy, 2.0)  # Max entropy for 2 buckets is log2(2) = 1
        
        # Single bucket should have zero entropy
        single_bucket_records = [
            DataRecord(bucket_id=1, source_name="test1"),
            DataRecord(bucket_id=1, source_name="test2"),
        ]
        self.assertEqual(bucket_entropy(single_bucket_records), 0.0)


class TestRAGGraph(unittest.TestCase):
    """Test RAG graph integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock Data Engine
        self.mock_data_engine = Mock()
        self.mock_data_engine.retrieval_manager = Mock()
        self.mock_data_engine.embedding_fn = None
        
        # Create adapter
        self.data_engine_adapter = DataEngineAdapter(self.mock_data_engine)
        
        # Mock LLM client
        self.llm_client = MockLLMClient()
        
        # Create graph
        self.graph = RAGGraph(
            data_engine_adapter=self.data_engine_adapter,
            llm_client=self.llm_client,
            anchor_client=None,
        )
    
    def test_graph_initialization(self):
        """Test graph initializes correctly"""
        self.assertIsNotNone(self.graph)
        self.assertIsNotNone(self.graph.graph)
    
    def test_query_execution(self):
        """Test query execution (with mocked retrieval)"""
        # Mock retrieval to return empty results
        self.data_engine_adapter.hybrid_query = Mock(return_value=[])
        self.data_engine_adapter.query_structured = Mock(return_value=[])
        
        result = self.graph.invoke("What do Gen Z prefer about McDonald's?")
        
        self.assertEqual(result["query"], "What do Gen Z prefer about McDonald's?")
        self.assertIn("intent", result)
        self.assertIn("entities", result)
        self.assertIn("rag_context", result)
        self.assertIn("confidence", result)
        self.assertIn("entropy", result)
        self.assertIn("coverage", result)
        self.assertIn("phase4", result)


class TestPhase4Client(unittest.TestCase):
    """Test Phase-4 client integration"""
    
    def test_anchor_request_creation(self):
        """Test AnchorRequest creation"""
        request = AnchorRequest(
            query="Test query",
            retrieved_evidence_summary="Test evidence",
            structured_aggregates={"count": 10},
            market_target_variable="revenue",
        )
        
        self.assertEqual(request.query, "Test query")
        self.assertEqual(request.market_target_variable, "revenue")
    
    def test_anchor_response_serialization(self):
        """Test AnchorResponse serialization"""
        response = AnchorResponse(
            anchored_score=0.85,
            calibration_details={"param1": 0.5},
            updated_confidence=0.9,
            notes=["Test note"],
            warnings=[],
        )
        
        response_dict = response.to_dict()
        self.assertEqual(response_dict["anchored_score"], 0.85)
        self.assertEqual(response_dict["updated_confidence"], 0.9)
        
        # Test deserialization
        restored = AnchorResponse.from_dict(response_dict)
        self.assertEqual(restored.anchored_score, 0.85)


if __name__ == "__main__":
    unittest.main()

