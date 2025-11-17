"""
Advanced RAG System v2 - Truly Advanced with Vector Search
Implements all components of a state-of-the-art RAG system
"""

import os
import time
import json
import fnmatch
import glob
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Core components
from .vector_store import VectorStore
from .mcp_direct import MCPMemoryDirect

# LLM for query expansion and generation
from anthropic import Anthropic

# Cross-encoder for re-ranking
from sentence_transformers import CrossEncoder

# For multi-agent orchestration
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from enum import Enum

from rag_system.config.settings import settings
from rag_system.utils.cache import QueryCache
from rag_system.utils.monitoring import RAGMonitor
from rag_system.utils.serena_code_index import SerenaCodeIndex
from rag_system.utils.keyword_retriever import KeywordRetriever
from rag_system.utils.entity_graph import EntityGraph
from rag_system.utils.feedback_loop import BotScalpBrain
from rag_system.utils.tracing import get_tracer  # Phase 3
from rag_system.utils.ast_chunker import ASTChunker  # Phase 4

class AgentType(Enum):
    """Types of specialized agents"""
    MEMORY = "memory"  # Search in conversation history
    CODE = "code"      # Search in codebase
    VECTOR = "vector"  # Semantic vector search
    RECENT = "recent"  # Recent/temporal search
    KEYWORD = "keyword"
    GRAPH = "graph"

class AdvancedRAGv2:
    """
    Truly Advanced RAG System with:
    - Vector embeddings & semantic search
    - Intelligent chunking
    - Hybrid search (vector + keyword)
    - Multi-agent architecture
    - Temporal awareness
    - Parallel orchestration
    """
    
    def __init__(self,
                 project_name: str = "scalp",
                 project_root: Optional[str] = None,
                 context_max_chars: Optional[int] = None,
                 default_top_k: Optional[int] = None):
        """Initialize all RAG components
        Args:
            project_name: Logical project identifier (affects vector DB namespace)
            project_root: Filesystem path to project root for local ingestion
        """
        print("\n🚀 Initializing Advanced RAG v2...")
        self.project_name = project_name
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # Tuning knobs
        self.context_max_chars = int(os.getenv('RAG_CONTEXT_CHARS', context_max_chars or 120000))
        self.default_top_k = int(os.getenv('RAG_TOP_K', default_top_k or 40))
        
        # 1. Vector Store (NEW!)
        persist = f"/home/scalp/rag_system/chroma_db/{self.project_name}"
        collection = f"{self.project_name}_knowledge"
        self.vector_store = VectorStore(persist_dir=persist, collection_name=collection)
        
        # 2. MCP Memory Client (existing)
        self.mcp_client = MCPMemoryDirect()
        
        # 3. LLM for intelligence
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set!")
        self.claude = Anthropic(api_key=api_key)
        # Model selection with safe defaults (allow env override)
        self.model_fast = os.getenv('ANTHROPIC_MODEL_FAST', 'claude-3-5-haiku-20241022')
        self.model_main = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')
        
        # 4. Cross-encoder for re-ranking
        print("  📊 Loading cross-encoder...")
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # 5. Cache + monitoring
        cache_dir = settings.CACHE_DIR / self.project_name
        cache_ttl = int(os.getenv('RAG_CACHE_TTL', '900'))
        cache_cap = int(os.getenv('RAG_CACHE_MAX_ENTRIES', '256'))
        disable_cache = os.getenv('RAG_DISABLE_CACHE', '0') == '1'
        self.cache: Optional[QueryCache] = None if disable_cache else QueryCache(
            cache_dir=cache_dir,
            ttl_seconds=cache_ttl,
            max_entries=cache_cap,
        )
        logs_dir = Path(__file__).resolve().parent.parent / 'logs'
        self.monitor = RAGMonitor(project_name=self.project_name, logs_dir=logs_dir)

        self.serena_index: Optional[SerenaCodeIndex]
        try:
            self.serena_index = SerenaCodeIndex(project_root=self.project_root)
            if self.serena_index.available():
                print("  🧭 Serena code index ready")
        except Exception as exc:
            print(f"  ⚠️  Serena index unavailable: {exc}")
            self.serena_index = None

        self.keyword_retriever = KeywordRetriever(self.project_root)
        config_dir = Path(__file__).resolve().parent.parent / 'config'
        self.entity_graph = EntityGraph(config_dir / 'entity_graph.json')

        self.intent_cache_policy = {
            'status': int(os.getenv('RAG_CACHE_TTL_STATUS', '180')),
            'general': int(os.getenv('RAG_CACHE_TTL_GENERAL', '600')),
            'explain': int(os.getenv('RAG_CACHE_TTL_EXPLAIN', '600')),
            'code': int(os.getenv('RAG_CACHE_TTL_CODE', '90')),
        }

        # Initialize BotScalp Brain for intelligent tracking
        self.brain = BotScalpBrain()
        self.auto_save_enabled = os.getenv('RAG_AUTO_SAVE', '1') == '1'
        
        # Phase 3: Tracing system
        self.tracer = get_tracer(project_name=self.project_name)
        
        # Phase 4: AST-based chunking
        self.ast_chunker = ASTChunker(max_chunk_size=1500)
        
        print("  ✅ Advanced RAG v2 initialized!\n")
    
    def _build_cache_key(self, query: str, processed_query: Dict, strategy: Dict) -> Optional[str]:
        """Generate cache key - now with semantic similarity support."""
        if not self.cache:
            return None
        
        # Normalize query for better cache hits
        normalized_query = query.strip().lower()
        # Remove punctuation and extra spaces
        import re
        normalized_query = re.sub(r'[^\w\s]', '', normalized_query)
        normalized_query = re.sub(r'\s+', ' ', normalized_query)
        
        key_parts = {
            'project': self.project_name,
            'query': normalized_query,
            'intent': processed_query.get('intent', 'general'),
            'top_k': strategy.get('top_k'),
            'context_max': self.context_max_chars,
            'vector': strategy.get('use_vector', True),
            'memory': strategy.get('use_memory', True),
            'recent': strategy.get('use_recent', False),
        }
        return self.cache.make_key(**key_parts)

    def _display_pipeline_stats(
        self,
        retrieved: int,
        reranked: int,
        context_chars: int,
        confidence: float,
        elapsed: float,
        *,
        from_cache: bool = False,
    ) -> None:
        """Pretty-print pipeline stats (works for live and cached responses)."""
        print(f"\n{'='*80}")
        print("📊 Pipeline Stats:" + (" (cache)" if from_cache else ""))
        print(f"  • Retrieved: {retrieved} documents")
        print(f"  • Re-ranked: {reranked} documents")
        print(f"  • Context: {context_chars} chars")
        print(f"  • Confidence: {confidence:.0f}%")
        print(f"  • Time: {elapsed:.2f}s")
        if from_cache:
            print("  • Source: disk cache")
        print(f"{'='*80}\n")

    # ============= STAGE 1: INTELLIGENT QUERY PROCESSING =============
    
    def process_query(self, query: str) -> Dict:
        """
        Advanced query processing with multiple extraction strategies
        
        Returns:
            Dict with processed query components
        """
        print(f"\n🧠 Processing query: {query}")
        
        # Extract multiple query representations in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.extract_concepts, query): 'concepts',
                executor.submit(self.expand_query, query): 'expansions',
                executor.submit(self.extract_temporal, query): 'temporal',
                executor.submit(self.classify_intent, query): 'intent'
            }
            
            results = {}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"  ⚠️  Failed to extract {key}: {e}")
                    results[key] = None
        
        return {
            'original': query,
            'concepts': results.get('concepts', []),
            'expansions': results.get('expansions', []),
            'temporal': results.get('temporal', {}),
            'intent': results.get('intent', 'general')
        }
    
    def extract_concepts(self, query: str) -> List[str]:
        """Extract key concepts for vector search"""
        try:
            prompt = f"""
            Extract key technical concepts and terms from this query.
            Focus on nouns, technical terms, and important keywords.
            
            Query: "{query}"
            
            Return only the concepts, one per line, max 5.
            """
            
            response = self.claude.messages.create(
                model=self.model_fast,
                max_tokens=100,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            concepts = response.content[0].text.strip().split('\n')
            return [c.strip() for c in concepts if c.strip()][:5]
        except Exception:
            return []
    
    def expand_query(self, query: str) -> List[str]:
        """Expand query with variations"""
        try:
            prompt = f"""
            Generate search variations for: "{query}"
            Include synonyms, related terms, and different phrasings.
            Return max 3 variations, one per line.
            """
            
            response = self.claude.messages.create(
                model=self.model_fast,
                max_tokens=100,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            expansions = response.content[0].text.strip().split('\n')
            return [e.strip() for e in expansions if e.strip()][:3]
        except Exception:
            return []
    
    def extract_temporal(self, query: str) -> Dict:
        """Extract temporal context from query"""
        temporal_keywords = {
            'hoje': 0, 'ontem': 1, 'anteontem': 2,
            'semana': 7, 'mês': 30, 'recente': 7,
            'último': 3, 'nova': 3, 'atual': 1
        }
        
        query_lower = query.lower()
        for keyword, days in temporal_keywords.items():
            if keyword in query_lower:
                return {
                    'has_temporal': True,
                    'days_back': days,
                    'keyword': keyword
                }
        
        return {'has_temporal': False}
    
    def classify_intent(self, query: str) -> str:
        """Classify query intent to route to appropriate agent"""
        query_lower = query.lower()
        
        # Code-related
        if any(word in query_lower for word in ['código', 'função', 'classe', 'implementação', 'bug', 'erro']):
            return 'code'
        
        # Configuration/setup
        if any(word in query_lower for word in ['configurar', 'setup', 'instalar', 'config']):
            return 'config'
        
        # Learning/explanation
        if any(word in query_lower for word in ['como', 'porque', 'explique', 'entender', 'funciona']):
            return 'explain'
        
        # Status/progress
        if any(word in query_lower for word in ['status', 'progresso', 'fase', 'andamento']):
            return 'status'
        
        return 'general'
    
    # ============= STAGE 2: MULTI-AGENT RETRIEVAL =============
    
    def multi_agent_retrieval(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        """
        Parallel multi-agent retrieval with different strategies
        """
        print("\n🤖 Multi-agent retrieval starting...")
        
        all_documents = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Launch parallel agents based on query analysis
            futures = []
            
            # Decide which agents to use
            use_vector = True
            use_memory = True
            use_recent = processed_query['temporal']['has_temporal']
            use_code = processed_query.get('intent') == 'code'
            if strategy:
                use_vector = strategy.get('use_vector', use_vector)
                use_memory = strategy.get('use_memory', use_memory)
                use_recent = strategy.get('use_recent', use_recent)
                use_code = strategy.get('use_code', use_code)
                use_keywords = strategy.get('use_keywords', True)
                use_graph = strategy.get('use_graph', False)
            else:
                use_keywords = True
                use_graph = False

            if use_vector:
                futures.append(executor.submit(self._vector_agent, processed_query, strategy))

            if use_memory:
                futures.append(executor.submit(self._memory_agent, processed_query, strategy))
            
            if use_recent:
                futures.append(executor.submit(self._temporal_agent, processed_query, strategy))

            if use_code:
                futures.append(executor.submit(self._code_agent, processed_query, strategy))

            if use_keywords:
                futures.append(executor.submit(self._keyword_agent, processed_query, strategy))

            if use_graph:
                futures.append(executor.submit(self._graph_agent, processed_query, strategy))
            
            # Collect results from all agents
            for future in as_completed(futures):
                try:
                    docs = future.result()
                    if docs:
                        all_documents.extend(docs)
                        print(f"  ✅ Agent returned {len(docs)} documents")
                except Exception as e:
                    print(f"  ⚠️  Agent failed: {e}")
        
        # Deduplicate documents
        seen = set()
        unique_docs = []
        for doc in all_documents:
            doc_hash = hash(doc['content'][:200])
            if doc_hash not in seen:
                seen.add(doc_hash)
                unique_docs.append(doc)
        
        print(f"  📚 Total unique documents: {len(unique_docs)}")
        return unique_docs
    
    def _vector_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        """Agent for vector/semantic search with dynamic budget"""
        print("  🔍 Vector agent searching...")
        
        # Combine all query variations
        all_queries = [processed_query['original']] + \
                     processed_query['concepts'] + \
                     processed_query['expansions']
        
        all_results = []
        n_results = 10
        if strategy:
            n_results = int(strategy.get('vector_n_results', n_results))
        
        # Dynamic budget: stop early if we have enough high-quality docs
        quality_threshold = 0.8
        quality_budget = 30  # Stop if we have 30+ docs with score > 0.8
        
        for q in all_queries:
            results = self.vector_store.search(q, n_results=n_results)
            all_results.extend(results)
            
            # Early stopping: check if budget met
            high_quality = sum(1 for doc in all_results if doc.get('score', 0) > quality_threshold)
            if high_quality >= quality_budget:
                print(f"  ⚡ Early stop: {high_quality} high-quality docs found")
                break
        
        return all_results
    
    def _memory_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        """Agent for MCP memory search"""
        print("  🧠 Memory agent searching...")
        
        all_results = []
        
        # Search with original
        limit = 20
        if strategy:
            limit = int(strategy.get('memory_limit', limit))
        results = self.mcp_client.search(processed_query['original'], limit=limit)
        all_results.extend(results)
        
        # Search with concepts
        per_concept = min(3, len(processed_query['concepts']))
        if strategy:
            per_concept = int(strategy.get('memory_concepts', per_concept))
        for concept in processed_query['concepts'][:per_concept]:
            results = self.mcp_client.search(concept, limit=max(5, limit//2))
            all_results.extend(results)
        
        return all_results
    
    def _temporal_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        """Agent for temporal/recency-aware search with AGGRESSIVE weighting for trading.
        Phase 3 Enhancement: Trading context changes rapidly - recent info is CRITICAL.
        """
        print("  ⏰ Temporal agent searching (aggressive trading mode)...")
        
        # Search baseline
        results = self.mcp_client.search(processed_query['original'], limit=30)
        
        # AGGRESSIVE temporal weighting for trading context
        from datetime import datetime, timezone
        import math
        now = datetime.now(timezone.utc)
        
        # Shorter half-life for trading (3 days instead of 7)
        half_life_days = int(strategy.get('half_life_days', 3)) if strategy else 3
        
        for doc in results:
            ts_str = doc.get('metadata', {}).get('updatedAt') or doc.get('metadata', {}).get('createdAt')
            boost = 1.0
            
            if ts_str:
                try:
                    if isinstance(ts_str, (int, float)):
                        dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
                    
                    age_days = max(0.0, (now - dt).total_seconds() / 86400.0)
                    
                    # AGGRESSIVE exponential decay
                    if age_days <= 1:  # Last 24h
                        boost = 3.0  # 3x boost!
                    elif age_days <= 3:  # Last 3 days
                        boost = 2.0  # 2x boost
                    elif age_days <= 7:  # Last week
                        boost = 1.5
                    else:  # Older than 1 week
                        boost = 1.0 + math.exp(-age_days / half_life_days)
                    
                    # Extra boost for backtest results (always want latest)
                    if doc.get('metadata', {}).get('doc_type') == 'backtest_result':
                        boost *= 1.3
                    
                except Exception:
                    boost = 1.1
            else:
                boost = 1.0  # No timestamp = older doc
            
            doc['temporal_boost'] = boost
        
        return results

    def _code_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        """Agent that searches the local codebase for relevant snippets"""
        print("  🧩 Code agent searching...")
        limit = int(strategy.get('code_limit', 20)) if strategy else 20
        queries = [processed_query.get('original', '')]
        queries.extend(processed_query.get('concepts', []))
        queries.extend(processed_query.get('expansions', []))

        if self.serena_index and self.serena_index.available():
            return self.serena_index.search(queries, limit=limit)

        # Fallback scan (only if Serena cache is inaccessible)
        import re

        patterns = [pat for pat in queries if pat]
        if not patterns:
            return []

        root = self.project_root
        exts = {'.py', '.ts', '.tsx', '.md'}
        results: List[Dict] = []
        scanned = 0
        for path in root.rglob('*'):
            if scanned >= 400 or len(results) >= limit:
                break
            if not path.is_file() or path.suffix not in exts:
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if any(re.search(re.escape(pat), text, re.IGNORECASE) for pat in patterns):
                snippet = '\n'.join(text.splitlines()[:200])
                rel = str(path.relative_to(self.project_root))
                results.append({
                    'id': f'code::{rel}',
                    'content': f"# File: {rel}\n{snippet}",
                    'source': 'code_fallback',
                    'metadata': {'path': rel}
                })
                scanned += 1
        return results

    def _keyword_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        print("  🧾 Keyword agent searching...")
        if not self.keyword_retriever:
            return []
        limit = int(strategy.get('keyword_limit', 12)) if strategy else 12
        return self.keyword_retriever.search(processed_query.get('original', ''), limit=limit)

    def _graph_agent(self, processed_query: Dict, strategy: Optional[Dict] = None) -> List[Dict]:
        if not self.entity_graph or not self.entity_graph.available():
            return []
        print("  🌐 Graph agent searching...")
        limit = int(strategy.get('graph_limit', 5)) if strategy else 5
        return self.entity_graph.search(processed_query.get('original', ''), limit=limit)
    
    # ============= STAGE 3: INTELLIGENT RE-RANKING =============
    
    def rerank_documents(self, query: str, documents: List[Dict], top_k: int = 30) -> List[Dict]:
        """
        Two-stage re-ranking: quick filter first, then cross-encoder on best candidates
        """
        if not documents:
            return []
        
        print(f"\n📊 Re-ranking {len(documents)} documents...")
        
        # STAGE 1: Quick filter by existing scores (vector similarity, etc.)
        # Sort by score if available, otherwise keep order
        quick_sorted = sorted(
            documents, 
            key=lambda x: x.get('score', 0) + x.get('vector_score', 0), 
            reverse=True
        )
        
        # Only use cross-encoder on top candidates (60% reduction)
        candidates_limit = min(len(quick_sorted), max(50, top_k * 2))
        candidates = quick_sorted[:candidates_limit]
        
        print(f"  🔍 Stage 1: Filtered to top {len(candidates)} candidates")
        
        # STAGE 2: Prepare for cross-encoder
        pairs = [[query, doc['content'][:1000]] for doc in candidates]
        
        # Get cross-encoder scores
        ce_scores = self.reranker.predict(pairs)
        
        print(f"  🎯 Stage 2: Cross-encoder evaluated {len(candidates)} docs")
        
        # Combine multiple signals
        for i, doc in enumerate(candidates):
            # Base score from cross-encoder
            final_score = float(ce_scores[i])
            
            # Boost for vector similarity
            if 'vector_score' in doc:
                final_score += doc['vector_score'] * 0.2
            
            # Boost for temporal relevance
            if 'temporal_boost' in doc:
                final_score *= float(doc['temporal_boost'])
            
            # Boost for exact match
            if query.lower() in doc['content'].lower():
                final_score *= 1.2
            
            doc['final_score'] = final_score
        
        # Sort by final score
        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return candidates[:top_k]
    
    # ============= STAGE 4: CONTEXT COMPRESSION =============
    
    def compress_context(self, documents: List[Dict], max_chars: int = 120000) -> str:
        """
        Intelligent context compression with chunk priority
        """
        if not documents:
            return ""
        
        print(f"\n📦 Compressing {len(documents)} documents...")
        
        context_parts = []
        current_size = 0
        
        for i, doc in enumerate(documents):
            content = doc['content']
            
            # Priority content (first and highest scoring docs)
            if i < 10 or doc.get('final_score', 0) > 0.8:
                # Include full content for top docs
                if current_size + len(content) <= max_chars:
                    context_parts.append(f"[Doc {i+1}] (Score: {doc.get('final_score', 0):.2f})\n{content}\n")
                    current_size += len(content)
                else:
                    # Truncate if needed
                    remaining = max_chars - current_size
                    if remaining > 500:
                        context_parts.append(f"[Doc {i+1}] (Score: {doc.get('final_score', 0):.2f})\n{content[:remaining]}... [truncated]\n")
                        current_size += remaining
                    break
            else:
                # For lower priority, include summary only
                # include a larger snippet to keep fidelity
                summary = content[:1500] if len(content) > 1500 else content
                if current_size + len(summary) <= max_chars:
                    context_parts.append(f"[Doc {i+1}] (Summary)\n{summary}...\n")
                    current_size += len(summary)
                else:
                    break
        
        print(f"  ✅ Compressed to {current_size} chars from {sum(len(d['content']) for d in documents)} chars")
        return '\n'.join(context_parts)
    
    # ============= STAGE 5: ANSWER GENERATION =============
    
    def generate_answer(self, query: str, context: str, metadata: Dict) -> str:
        """
        Generates answer using Chain-of-Thought reasoning for better quality.
        Phase 3 Enhancement: Structured reasoning before answering.
        """
        if not context:
            return "❌ Não encontrei informações relevantes na base de conhecimento."
        
        print("\n✨ Generating answer with Chain-of-Thought...")
        
        # Chain-of-Thought prompt for better reasoning
        prompt = f"""
        Você é um assistente expert em trading e desenvolvimento de sistemas BotScalp.
        
        ANÁLISE DO CONTEXTO:
        - Query: {query}
        - Intent: {metadata.get('intent', 'general')}
        - Conceitos-chave: {', '.join(metadata.get('concepts', []))}
        - Documentos encontrados: {metadata.get('total_docs', 0)} → {metadata.get('reranked_docs', 0)} após re-ranking
        
        DOCUMENTOS RELEVANTES:
        {context}
        
        INSTRUÇÕES CHAIN-OF-THOUGHT:
        
        1. ANÁLISE (raciocine primeiro, não mostre ao usuário):
           - O que a pergunta está realmente pedindo?
           - Quais documentos são mais relevantes?
           - Há informações conflitantes?
           - Preciso de contexto adicional sobre trading/ML?
        
        2. SÍNTESE:
           - Combine informações de múltiplas fontes
           - Priorize informações mais recentes (trading muda rápido!)
           - Se for sobre backtest: foque em métricas, parâmetros, resultados
           - Se for sobre código: inclua exemplos completos e funcionais
           - Se for sobre estratégia: explique a lógica de trading
        
        3. RESPOSTA ESTRUTURADA:
           - Comece com resumo executivo (2-3 linhas)
           - Organize em seções claras com emojis
           - Cite [Doc N] para rastreabilidade
           - Inclua TODOS os comandos, código, e configurações
           - Adicione warnings se informação incompleta
        
        PERGUNTA: {query}
        
        RESPOSTA DETALHADA (pule a seção de análise, vá direto para síntese):
        """
        
        response = self.claude.messages.create(
            model=self.model_main,
            max_tokens=8000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    # ============= MAIN QUERY INTERFACE =============
    
    def query(self, user_query: str) -> Tuple[str, float]:
        """
        Main query interface - orchestrates the entire RAG pipeline
        Phase 3: Added detailed tracing
        """
        start_time = time.time()
        
        # Phase 3: Start trace
        _ = self.tracer.start_trace(
            operation='rag_query',
            query=user_query,
            metadata={'project': self.project_name}
        )

        print(f"\n{'='*80}")
        print("🚀 ADVANCED RAG v2 - Processing Query")
        print(f"{'='*80}")

        # Stage 1: Process Query
        with self.tracer.span('query_processing', {'query_length': len(user_query)}):
            processed_query = self.process_query(user_query)
        metadata = {
            'intent': processed_query.get('intent', 'general'),
            'concepts': processed_query.get('concepts', []),
            'total_docs': 0,
            'reranked_docs': 0,
        }

        # Decide retrieval strategy (adaptive)
        strategy = self._decide_retrieval_strategy(processed_query)

        # Cache lookup (if enabled)
        cache_key = self._build_cache_key(user_query, processed_query, strategy)
        cached_payload = self.cache.get(cache_key) if cache_key else None
        if cached_payload:
            cache_elapsed = time.time() - start_time
            print("\n⚡ Cache hit — reutilizando resposta anterior.")
            self._display_pipeline_stats(
                cached_payload.get('retrieved', 0),
                cached_payload.get('reranked', 0),
                cached_payload.get('context_chars', 0),
                cached_payload.get('confidence', 0.0),
                cache_elapsed,
                from_cache=True,
            )
            log_entry = dict(cached_payload)
            log_entry.update({
                'query': user_query,
                'intent': metadata['intent'],
                'elapsed_sec': round(cache_elapsed, 2),
                'from_cache': True,
                'project': self.project_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'cache_ttl': cached_payload.get('cache_ttl'),
            })
            self.monitor.log_run(log_entry)
            return cached_payload['answer'], cached_payload['confidence']

        # Optional: no retrieval if obvious
        if strategy.get('mode') == 'none':
            answer = self.generate_answer(user_query, context="", metadata={'intent': processed_query['intent']})
            confidence = 50.0
            elapsed = time.time() - start_time
            cache_ttl = self._cache_ttl_for_intent(metadata['intent'])
            stats = {
                'query': user_query,
                'intent': metadata['intent'],
                'retrieved': 0,
                'reranked': 0,
                'context_chars': 0,
                'confidence': confidence,
                'elapsed_sec': round(elapsed, 2),
                'from_cache': False,
                'answer': answer,
                'project': self.project_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'cache_ttl': cache_ttl,
            }
            if cache_key:
                self.cache.set(cache_key, stats, ttl=cache_ttl)
            self.monitor.log_run(stats)
            self._display_pipeline_stats(0, 0, 0, confidence, elapsed, from_cache=False)
            return answer, confidence

        # Stage 2: Retrieval (Parallel), with optional query planning
        with self.tracer.span('multi_agent_retrieval', {'strategy': strategy}):
            if strategy.get('use_planning'):
                print("\n🗺️  Query planning enabled. Decompondo em subperguntas...")
                subqs = self._plan_query(user_query)
                documents = []
                for i, sq in enumerate(subqs, start=1):
                    print(f"  🔹 Subpergunta {i}: {sq}")
                    pq = self.process_query(sq)
                    docs_sq = self.multi_agent_retrieval(pq, strategy)
                    documents.extend(docs_sq)
            else:
                documents = self.multi_agent_retrieval(processed_query, strategy)

        if not documents:
            elapsed = time.time() - start_time
            cache_ttl = self._cache_ttl_for_intent(metadata['intent'])
            no_data_stats = {
                'query': user_query,
                'intent': metadata['intent'],
                'retrieved': 0,
                'reranked': 0,
                'context_chars': 0,
                'confidence': 0.0,
                'elapsed_sec': round(elapsed, 2),
                'from_cache': False,
                'answer': "❌ Não encontrei informações relevantes na base de conhecimento.",
                'project': self.project_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'cache_ttl': cache_ttl,
            }
            if cache_key:
                self.cache.set(cache_key, no_data_stats, ttl=cache_ttl)
            self.monitor.log_run(no_data_stats)
            self._display_pipeline_stats(0, 0, 0, 0.0, elapsed, from_cache=False)
            return no_data_stats['answer'], 0.0

        # Stage 3: Re-ranking
        reranked_docs = self.rerank_documents(user_query, documents, top_k=strategy.get('top_k', self.default_top_k))

        # Stage 4: Context Compression
        compressed_context = self.compress_context(reranked_docs, max_chars=self.context_max_chars)

        # Stage 5: Answer Generation
        metadata.update({
            'total_docs': len(documents),
            'reranked_docs': len(reranked_docs),
        })

        answer = self.generate_answer(user_query, compressed_context, metadata)

        # Calculate confidence
        confidence = min(100, len(reranked_docs) * 2.0)

        elapsed = time.time() - start_time

        self._display_pipeline_stats(len(documents), len(reranked_docs), len(compressed_context), confidence, elapsed)

        cache_ttl = self._cache_ttl_for_intent(metadata['intent'])
        run_payload = {
            'query': user_query,
            'intent': metadata['intent'],
            'retrieved': len(documents),
            'reranked': len(reranked_docs),
            'context_chars': len(compressed_context),
            'confidence': confidence,
            'elapsed_sec': round(elapsed, 2),
            'from_cache': False,
            'answer': answer,
            'project': self.project_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'cache_ttl': cache_ttl,
        }
        
        # Auto-save chat interaction to Brain
        if self.auto_save_enabled:
            self._auto_save_interaction(user_query, answer, run_payload)
        
        if cache_key:
            self.cache.set(cache_key, run_payload, ttl=cache_ttl)
        self.monitor.log_run(run_payload)
        
        # Phase 3: End trace with results
        self.tracer.end_trace(result=run_payload)
        
        return answer, confidence
    
    def _auto_save_interaction(self, query: str, answer: str, metadata: Dict):
        """Auto-save chat interaction to Brain's memory system."""
        try:
            # Record interaction in Brain
            self.brain.record_interaction(
                query=query,
                response={
                    'answer': answer[:500],  # Save summary only
                    'confidence': metadata.get('confidence', 0),
                    'context_id': metadata.get('intent', 'general'),
                    'sources': metadata.get('reranked', 0)
                },
                feedback=None  # Will be updated if user provides feedback
            )
            
            # Also save to session logs for RAG ingestion
            session_log_dir = Path("/home/scalp/chat_orchestrator/session_logs")
            session_log_dir.mkdir(parents=True, exist_ok=True)
            
            context_id = metadata.get('intent', 'general')
            session_file = session_log_dir / f"{context_id}" / f"{self.project_name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            log_entry = {
                'timestamp': metadata.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                'query': query,
                'answer_preview': answer[:200] + "..." if len(answer) > 200 else answer,
                'confidence': metadata.get('confidence', 0),
                'retrieved': metadata.get('retrieved', 0),
                'reranked': metadata.get('reranked', 0),
                'elapsed': metadata.get('elapsed_sec', 0),
                'from_cache': metadata.get('from_cache', False)
            }
            
            with open(session_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
            
            print(f"  💾 Auto-saved to: {session_file.name}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to auto-save interaction: {e}")

    def _decide_retrieval_strategy(self, processed_query: Dict) -> Dict:
        """Decide retrieval mode, agents, and top_k dynamically"""
        intent = processed_query.get('intent', 'general')
        q = processed_query.get('original', '')
        qlen = len(q)
        is_objective = any(x in q.lower() for x in ['onde', 'qual arquivo', 'linha', 'parâmetro', 'flag', 'comando'])
        strategy = {
            'mode': 'hybrid',
            'use_vector': True,
            'use_memory': True,
            'use_recent': processed_query['temporal'].get('has_temporal', False),
            'use_code': intent == 'code',
            'use_keywords': intent != 'code',
            'use_graph': intent in {'status', 'explain', 'general'},
            'top_k': 20,
            'vector_n_results': 10,
            'memory_limit': 20,
            'memory_concepts': 3,
        }
        # Intent-based adjustments
        if intent == 'code':
            strategy.update({'use_code': True, 'top_k': 15, 'vector_n_results': 15, 'memory_limit': 10})
        elif intent in ('status', 'config'):
            strategy.update({'top_k': 15, 'vector_n_results': 8, 'memory_limit': 15})
        elif intent == 'explain':
            strategy.update({'top_k': max(self.default_top_k, 50), 'vector_n_results': 15, 'memory_limit': 30})

        # Objective vs open-ended
        if is_objective:
            strategy['top_k'] = min(strategy['top_k'], 12)
            strategy['vector_n_results'] = min(strategy['vector_n_results'], 8)
            strategy['use_keywords'] = True
            strategy['use_graph'] = False
        else:
            if qlen > 120:
                strategy['top_k'] = max(strategy['top_k'], max(self.default_top_k, 50))
                strategy['vector_n_results'] = max(strategy['vector_n_results'], 18)

        # None retrieval heuristic (very short explainer not specific to repo)
        generic_terms = ['o que é', 'defina', 'definição de']
        if intent == 'explain' and any(t in q.lower() for t in generic_terms) and not any(k in q.lower() for k in ['selector21', 'botscalp', 'mcp', 'rag']):
            strategy['mode'] = 'none'
            strategy['use_vector'] = False
            strategy['use_memory'] = False
            strategy['use_code'] = False
            strategy['use_keywords'] = False
            strategy['use_graph'] = False

        # Enable planning for complex/system questions
        planning_triggers = ['pipeline', 'fluxo', 'passos', 'decompor', 'entender', 'descrever', 'inteiro']
        strategy['use_planning'] = (len(q) > 160) or any(t in q.lower() for t in planning_triggers)

        return strategy

    def _plan_query(self, query: str) -> List[str]:
        """Decompose a complex question into sub-questions (max 3)."""
        try:
            prompt = f"""
            Decompose the following question into 2-3 concise sub-questions that help answer it step-by-step.
            Return only the sub-questions, one per line.

            Question: "{query}"
            """
            response = self.claude.messages.create(
                model=self.model_fast,
                max_tokens=120,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            subs = [s.strip() for s in response.content[0].text.strip().split('\n') if s.strip()]
            return subs[:3] if subs else [query]
        except Exception:
            return [query]
    
    # ============= MAINTENANCE FUNCTIONS =============
    
    def update_vector_store(self):
        """Update vector store with latest MCP memories"""
        print("\n🔄 Updating vector store from MCP...")
        count = self.vector_store.update_from_mcp(self.mcp_client)
        print(f"✅ Updated {count} chunks in vector store")
        return count

    def update_local_knowledge(self) -> int:
        """Update vector store with important local knowledge files (Serena/Project docs)."""
        print("\n📚 Updating vector store from local knowledge files...")
        # Load .ragconfig.json if present in project root
        config_path = self.project_root / ".ragconfig.json"
        metadata_rules: List[Dict] = []
        cron_hint: Optional[str] = None
        globs: List[str]
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding='utf-8'))
                globs = data.get("ingest_globs", [])
                metadata_rules = data.get("metadata_rules", [])
                cron_hint = data.get("cron_hint")
            except Exception as e:
                print(f"⚠️  Failed to read .ragconfig.json: {e}")
                globs = []
        else:
            # Fallback curated set relative to project root
            globs = [
                "SESSION_MEMORY.md",
                "SESSION_PROGRESS.md",
                "SESSION_RECOVERY.md",
                "VALIDATED_SETUPS.md",
                "RAG_ADVANCED_GUIDE.md",
                "RAG_QUICKSTART.md",
                "rag_system/README.md",
                "docs/**/*.md",
            ]

        documents: List[Dict] = []
        paths = self._expand_globs(globs)
        for path in paths:
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if len(text.strip()) < 80:
                continue
            metadata = self._metadata_for_path(path, metadata_rules)
            metadata.update({
                'path': str(path.relative_to(self.project_root)),
                'source': 'local_file',
                'doc_type': metadata.get('doc_type', 'file'),
                'component': self._infer_component(path),
                'modified_ts': int(path.stat().st_mtime),
                'priority': metadata.get('priority', 0.5),
            })
            headline = text.splitlines()[0][:160] if text.splitlines() else ''
            if headline:
                metadata['headline'] = headline
            documents.append({'content': text, 'metadata': metadata})

        if not documents:
            print("  ⚠️  No documents matched ingestion globs")
            return 0

        try:
            added = self.vector_store.add_documents(documents)
            print(f"✅ Added {added} chunks from {len(documents)} local files")
            if cron_hint:
                print(f"  ⏰ Cron hint: {cron_hint}")
            return added
        except Exception as e:
            print(f"⚠️  Failed to add local knowledge: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            'vector_store': self.vector_store.get_stats(),
            'mcp_available': True,
            'claude_model': self.model_main,
            'reranker_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2'
        }

    def _cache_ttl_for_intent(self, intent: str) -> int:
        if not self.cache:
            return 0
        ttl = self.intent_cache_policy.get(intent)
        if ttl is None or ttl < 0:
            return self.cache.default_ttl
        return ttl

    def _expand_globs(self, patterns: List[str]) -> List[Path]:
        paths: List[Path] = []
        seen = set()
        for pattern in patterns:
            base = pattern if pattern.startswith('/') else str(self.project_root / pattern)
            for match in glob.glob(base, recursive=True):
                path = Path(match)
                if not path.is_file():
                    continue
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                paths.append(path)
        return paths

    def _metadata_for_path(self, path: Path, rules: List[Dict]) -> Dict:
        rel = str(path.relative_to(self.project_root))
        meta: Dict = {}
        for rule in rules:
            pattern = rule.get('pattern')
            if not pattern:
                continue
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(str(path), pattern):
                meta.update(rule.get('metadata', {}))
        return meta

    def _infer_component(self, path: Path) -> str:
        parts = list(path.relative_to(self.project_root).parts)
        if not parts:
            return 'root'
        if parts[0] in {'core', 'rag_system', 'docs', 'evolution'}:
            return "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        return parts[0]

    async def batch_query(self, queries: List[str], parallel: bool = True) -> List[Dict]:
        """Processar múltiplas queries em batch para otimizar throughput."""
        if parallel and len(queries) > 1:
            # Usar ThreadPoolExecutor para queries paralelas
            with ThreadPoolExecutor(max_workers=min(len(queries), 10)) as executor:
                futures = [executor.submit(self.query, q) for q in queries]
                return [f.result() for f in futures]
        else:
            return [self.query(q) for q in queries]

    def create_specialized_indexes(self):
        """Criar índices especializados para queries frequentes do trading."""
        # Índice para estratégias
        self.strategy_index = self.vector_store.create_index(
            filter={"doc_type": "strategy"},
            metric="cosine"
        )
        
        # Índice para resultados de backtest
        self.backtest_index = self.vector_store.create_index(
            filter={"doc_type": "backtest_result"},
            metric="cosine"
        )
        
        # Índice temporal para análises históricas
        self.temporal_index = self.vector_store.create_index(
            order_by="timestamp",
            partition_by="context_id"
        )
