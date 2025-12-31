"""
Configuration for RAG Graph System

Uses environment variables for configuration management.
"""

import os
from typing import Optional


class RAGConfig:
    """Configuration for RAG graph system"""
    
    def __init__(self):
        # Phase-4 Configuration
        self.phase4_mode = os.getenv("RAG_PHASE4_MODE", "disabled")
        self.phase4_repo_path = os.getenv("RAG_PHASE4_REPO_PATH")
        self.phase4_entrypoint = os.getenv("RAG_PHASE4_ENTRYPOINT", "python -m phase4.anchor")
        self.phase4_url = os.getenv("RAG_PHASE4_URL")
        self.phase4_api_key = os.getenv("RAG_PHASE4_API_KEY")
        
        # Retrieval Configuration
        self.top_k_bucket_1 = int(os.getenv("RAG_TOP_K_BUCKET_1", "10"))
        self.top_k_bucket_2 = int(os.getenv("RAG_TOP_K_BUCKET_2", "15"))
        self.top_k_bucket_3 = int(os.getenv("RAG_TOP_K_BUCKET_3", "20"))
        self.top_k_bucket_4 = int(os.getenv("RAG_TOP_K_BUCKET_4", "15"))
        self.max_expanded_queries = int(os.getenv("RAG_MAX_EXPANDED_QUERIES", "5"))
        
        # LLM Configuration
        self.llm_provider = os.getenv("RAG_LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("RAG_LLM_MODEL", "gpt-4o-mini")
        self.openai_api_key = os.getenv("RAG_OPENAI_API_KEY")


def get_config() -> RAGConfig:
    """Get configuration from environment variables"""
    return RAGConfig()

