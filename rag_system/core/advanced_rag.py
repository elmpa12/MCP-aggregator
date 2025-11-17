"""
Advanced RAG System - Core Implementation
Integrates: mem0 + Serena + Claude for intelligent retrieval
"""

import json
import sqlite3
import subprocess
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from sentence_transformers import CrossEncoder
import anthropic
import hashlib
import time

@dataclass
class RAGResult:
    """Result from RAG query"""
    answer: str
    sources: List[Dict]
    confidence: float
    num_docs_retrieved: int
    num_docs_used: int
    query_time_ms: float

class AdvancedRAGSystem:
    """
    Advanced Retrieval-Augmented Generation System
    
    Features:
    - Multi-query expansion
    - Hybrid search (vector + keyword)
    - Cross-encoder re-ranking
    - Contextual compression
    - Source citations
    - Confidence scoring
    """
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.anthropic_key = anthropic_api_key or self._get_api_key()
        self.claude = anthropic.Anthropic(api_key=self.anthropic_key)
        
        # Load re-ranker model
        print("📥 Carregando modelo de re-ranking...")
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Re-ranker carregado!")
        
        # Paths
        self.project_root = Path("/home/scalp")
        self.memory_cli = "/usr/local/bin/memory"
        
        # Cache
        self.cache_dir = Path("/home/scalp/.rag_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_api_key(self) -> str:
        """Get Anthropic API key from environment"""
        import os
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada. Configure: export ANTHROPIC_API_KEY='sk-...'")
        return key
    
    def query(self, user_query: str, include_code: bool = True) -> RAGResult:
        """
        Main RAG query method
        
        Args:
            user_query: User's question
            include_code: Whether to search code via Serena
            
        Returns:
            RAGResult with answer and metadata
        """
        start_time = time.time()
        
        print(f"\n🔍 Processando query: {user_query[:80]}...")
        
        # 1. Extract key concepts for semantic search
        print("  1️⃣  Extraindo conceitos-chave...")
        key_concepts = self.extract_key_concepts(user_query)
        if key_concepts:
            print(f"     📌 Conceitos: {', '.join(key_concepts)}")
        
        # 2. Query Expansion
        print("  2️⃣  Expandindo query...")
        expanded_queries = self.expand_query(user_query)
        
        # Combine: original + expanded + key concepts
        all_queries = [user_query] + expanded_queries + key_concepts
        # Remove duplicates while preserving order
        seen = set()
        all_queries = [q for q in all_queries if not (q in seen or seen.add(q))]
        
        print(f"     ✅ {len(all_queries)} variações totais")
        
        # 3. Hybrid Retrieval with semantic understanding
        print("  3️⃣  Buscando documentos (semântico + literal)...")
        docs = self.hybrid_retrieval(all_queries)
        print(f"     ✅ {len(docs)} documentos encontrados")
        
        if not docs:
            return RAGResult(
                answer="Não encontrei informações relevantes na base de conhecimento.",
                sources=[],
                confidence=0.0,
                num_docs_retrieved=0,
                num_docs_used=0,
                query_time_ms=0
            )
        
        # 4. Re-ranking - Aumentar para pegar MAIS documentos
        print("  4️⃣  Re-ranqueando resultados...")
        # Pegar até 30 docs para ter conhecimento completo
        top_k = min(30, len(docs))  # Pega até 30 ou todos se menos
        reranked_docs = self.rerank(user_query, docs, top_k=top_k)
        print(f"     ✅ Top {len(reranked_docs)} docs selecionados")
        
        # 5. Contextual Compression
        print("  5️⃣  Comprimindo contexto...")
        compressed_context = self.compress_context(user_query, reranked_docs)
        print(f"     ✅ Contexto comprimido")
        
        # 6. Generate Answer
        print("  6️⃣  Gerando resposta...")
        answer, confidence = self.generate_answer(user_query, compressed_context, reranked_docs)
        print(f"     ✅ Resposta gerada (confiança: {confidence:.1%})")
        
        query_time = (time.time() - start_time) * 1000
        
        return RAGResult(
            answer=answer,
            sources=[{"id": doc["id"], "content": doc["content"][:200]} for doc in reranked_docs[:5]],
            confidence=confidence,
            num_docs_retrieved=len(docs),
            num_docs_used=len(reranked_docs),
            query_time_ms=query_time
        )
    
    def extract_key_concepts(self, query: str) -> List[str]:
        """Extract key technical concepts from natural language query"""
        try:
            prompt = f"""
            Extract ONLY the key technical terms and concepts from this question.
            Focus on code terms, parameters, and technical concepts.
            
            Question: "{query}"
            
            Return ONLY the key terms, one per line, no explanations.
            Examples of good terms: walkforward, WF, selector21, _NPLR, ml_model_kind
            
            IMPORTANT: 
            - For "walk forward" or "walk-forward" return: walkforward
            - For compound terms, try both together and separate
            - Include common abbreviations (WF for walk-forward)
            - Return maximum 5 terms
            """
            
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            concepts = response.content[0].text.strip().split('\n')
            return [c.strip() for c in concepts if c.strip()][:5]
        except Exception as e:
            print(f"  ⚠️  Concept extraction failed: {e}")
            return []
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query into multiple variations
        
        Uses Claude Haiku for fast query expansion
        """
        prompt = f"""Generate {3} different variations of this query for better information retrieval.
The variations should capture different aspects and phrasings of the same question.

Original query: {query}

Return ONLY the variations, one per line, without numbering or explanations."""
        
        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            variations = message.content[0].text.strip().split('\n')
            variations = [v.strip() for v in variations if v.strip()]
            
            # Include original query
            return [query] + variations[:3]
        except Exception as e:
            print(f"  ⚠️  Query expansion failed: {e}")
            return [query]
    
    def hybrid_retrieval(self, queries: List[str]) -> List[Dict]:
        """
        Hybrid retrieval: Vector (mem0) + Keyword (SQLite FTS)
        
        Returns unique documents from both sources
        """
        all_docs = []
        seen_ids = set()
        
        for query in queries:
            # Vector search via mem0
            vector_docs = self._vector_search(query, limit=50)
            
            # Keyword search via SQLite FTS
            keyword_docs = self._keyword_search(query, limit=50)
            
            # Merge and deduplicate
            for doc in vector_docs + keyword_docs:
                doc_id = doc.get("id", hashlib.md5(doc["content"].encode()).hexdigest())
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    doc["id"] = doc_id
                    all_docs.append(doc)
        
        return all_docs
    
    def _vector_search(self, query: str, limit: int = 50) -> List[Dict]:
        """Search mem0 using direct MCP client"""
        try:
            # Use direct MCP client (no CLI parsing needed)
            from .mcp_direct import MCPMemoryDirect
            
            client = MCPMemoryDirect()
            docs = client.search(query, limit=limit)
            
            # Convert format if needed
            formatted_docs = []
            for doc in docs:
                formatted_docs.append({
                    "content": doc.get('content', ''),
                    "source": "mcp_direct",
                    "metadata": doc.get('metadata', {})
                })
            
            return formatted_docs[:limit]
            
        except Exception as e:
            print(f"  ⚠️  Vector search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _keyword_search(self, query: str, limit: int = 50) -> List[Dict]:
        """Search SQLite database with FTS - DISABLED (usando MCP Memory)"""
        # MCP Memory já faz busca híbrida via CLI
        # Não precisamos de keyword search separado
        return []
    
    def rerank(self, query: str, docs: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Re-rank documents using cross-encoder
        
        Cross-encoder provides more accurate relevance scores
        """
        if not docs:
            return []
        
        # Prepare pairs for cross-encoder
        pairs = [(query, doc["content"][:512]) for doc in docs]  # Limit to 512 chars
        
        # Get relevance scores
        scores = self.reranker.predict(pairs)
        
        # Sort by score
        docs_with_scores = list(zip(docs, scores))
        docs_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return [doc for doc, score in docs_with_scores[:top_k]]
    
    def compress_context(self, query: str, docs: List[Dict]) -> str:
        """
        Compress context to fit in token window
        
        Strategy: INCLUIR O MÁXIMO DE CONTEÚDO POSSÍVEL
        """
        max_total_chars = 50000  # Aumentar MUITO o limite para ter TODO conteúdo
        compressed_docs = []
        total_chars = 0
        
        for i, doc in enumerate(docs):
            content = doc["content"]
            doc_text = f"[Doc {i+1}]\n{content}\n"
            
            # Adiciona documento completo se couber
            if total_chars + len(doc_text) < max_total_chars:
                compressed_docs.append(doc_text)
                total_chars += len(doc_text)
            else:
                # Se não cabe completo, pega o que couber
                remaining = max_total_chars - total_chars
                if remaining > 500:  # Só adiciona se for útil
                    truncated = content[:remaining]
                    compressed_docs.append(f"[Doc {i+1}]\n{truncated}\n[...TRUNCADO...]")
                    total_chars += len(truncated)
                break
        
        print(f"     📚 Contexto total: {total_chars} caracteres de {len(docs)} docs")
        return "\n---\n\n".join(compressed_docs)
    
    def generate_answer(
        self, 
        query: str, 
        context: str, 
        source_docs: List[Dict]
    ) -> Tuple[str, float]:
        """
        Generate final answer using Claude
        
        Returns: (answer, confidence_score)
        """
        prompt = f"""You are an expert assistant helping a developer with their trading bot project.

Context from knowledge base:
{context}

User Question: {query}

INSTRUÇÕES IMPORTANTES - FORNEÇA TODO O CONHECIMENTO:
1. INCLUA ABSOLUTAMENTE TUDO que encontrou nos documentos
2. Seja EXTREMAMENTE DETALHADO - não resuma NADA
3. Liste TODOS os detalhes técnicos, parâmetros, configurações
4. Se houver código/comandos, MOSTRE COMPLETOS
5. Se houver valores/números, LISTE TODOS
6. Se houver múltiplas variações, MOSTRE TODAS
7. Cite TODOS os documentos relevantes [Doc 1], [Doc 2], etc
8. Organize por tópicos mas seja EXAUSTIVO em cada um
9. NUNCA omita informação por parecer repetitiva ou longa
10. Quanto MAIS COMPLETO, MELHOR

Answer:"""
        
        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = message.content[0].text
            
            # Calculate confidence based on answer quality
            confidence = self._calculate_confidence(answer, source_docs)
            
            return answer, confidence
        except Exception as e:
            return f"Erro ao gerar resposta: {e}", 0.0
    
    def _calculate_confidence(self, answer: str, docs: List[Dict]) -> float:
        """Calculate confidence score based on answer characteristics"""
        confidence = 0.5  # Base confidence
        
        # Has citations
        if "[Doc" in answer:
            confidence += 0.2
        
        # Sufficient length
        if len(answer) > 200:
            confidence += 0.1
        
        # Not too vague
        if "não tenho informação" not in answer.lower():
            confidence += 0.1
        
        # Has code or technical details
        if any(word in answer for word in ["def ", "class ", "import ", "```"]):
            confidence += 0.1
        
        return min(confidence, 1.0)


# Quick test function
def test_rag():
    """Test RAG system"""
    print("🧪 Testando RAG System...")
    
    rag = AdvancedRAGSystem()
    
    # Test query
    result = rag.query("Como funciona o sistema de memória?")
    
    print("\n" + "="*80)
    print("📊 RESULTADO:")
    print("="*80)
    print(f"\n{result.answer}\n")
    print(f"Confiança: {result.confidence:.1%}")
    print(f"Docs recuperados: {result.num_docs_retrieved}")
    print(f"Docs utilizados: {result.num_docs_used}")
    print(f"Tempo: {result.query_time_ms:.0f}ms")
    print("="*80)


if __name__ == "__main__":
    test_rag()
