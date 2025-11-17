"""Configuration settings for RAG system"""
import os
from pathlib import Path

class Settings:
    """RAG System Settings"""
    
    # Paths
    PROJECT_ROOT = Path("/home/scalp")
    MEM0_DB_PATH = PROJECT_ROOT / "memory" / "mem0.db"
    CACHE_DIR = PROJECT_ROOT / ".rag_cache"
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Models
    RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL = "claude-3-5-sonnet-20241022"
    LLM_MINI_MODEL = "claude-3-5-haiku-20241022"
    
    # Retrieval Parameters
    INITIAL_RETRIEVAL_K = 100
    RERANK_TOP_K = 10
    FINAL_CONTEXT_K = 5
    NUM_QUERY_VARIATIONS = 3
    MAX_CONTEXT_TOKENS = 8000
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8765

settings = Settings()
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
