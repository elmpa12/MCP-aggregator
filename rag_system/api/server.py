"""
FastAPI server for RAG system
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.advanced_rag import AdvancedRAGSystem, RAGResult

app = FastAPI(title="Advanced RAG API", version="1.0.0")

# Initialize RAG system (singleton)
rag_system = None

@app.on_event("startup")
async def startup():
    global rag_system
    print("🚀 Inicializando RAG System...")
    rag_system = AdvancedRAGSystem()
    print("✅ RAG System pronto!")

class QueryRequest(BaseModel):
    query: str
    include_code: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: list
    confidence: float
    num_docs_retrieved: int
    num_docs_used: int
    query_time_ms: float

@app.post("/api/rag/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Query the RAG system
    
    Example:
        curl -X POST http://localhost:8765/api/rag/query \
            -H "Content-Type: application/json" \
            -d '{"query": "Como funciona o selector21?"}'
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        result = rag_system.query(request.query, include_code=request.include_code)
        
        return QueryResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
            num_docs_retrieved=result.num_docs_retrieved,
            num_docs_used=result.num_docs_used,
            query_time_ms=result.query_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "rag_initialized": rag_system is not None}

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "Advanced RAG API",
        "version": "1.0.0",
        "endpoints": {
            "query": "POST /api/rag/query",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando API Server...")
    print("📍 http://localhost:8765")
    print("📚 Docs: http://localhost:8765/docs")
    uvicorn.run(app, host="0.0.0.0", port=8765)
