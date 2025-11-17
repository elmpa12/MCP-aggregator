# 🤖 RAG Avançado - Guia Completo

## 📚 O que é RAG?

**RAG = Retrieval-Augmented Generation**

É uma técnica que combina:
1. **Retrieval** (Busca): Encontrar informações relevantes em sua base de conhecimento
2. **Augmented** (Aumentado): Enriquecer o prompt do LLM com esse contexto
3. **Generation** (Geração): LLM gera resposta baseada no contexto recuperado

### 💡 Analogia Simples:

**Sem RAG:**
- Você: "Claude, como funciona o selector21?"
- Claude: "Não sei, não tenho contexto sobre seu código"

**Com RAG:**
- Você: "Claude, como funciona o selector21?"
- Sistema busca: [3 conversas relevantes + código]
- Sistema monta prompt: "Context: [conversas]... User: como funciona selector21?"
- Claude: "Baseado no contexto, o selector21 funciona assim..."

---

## 🎯 Seu Sistema Atual vs RAG Completo

### ✅ O que você JÁ TEM (RAG Parcial):

| Componente | Status | Descrição |
|------------|--------|-----------|
| **Armazenamento** | ✅ Pronto | mem0 + SQLite |
| **Embeddings** | ✅ Pronto | Busca semântica vetorial |
| **Retrieval** | ✅ Pronto | `memory search` |
| **Auto-indexação** | ✅ Pronto | Auto-sync 10min |

### ❌ O que FALTA para RAG Avançado:

| Componente | Status | Descrição |
|------------|--------|-----------|
| **Query Expansion** | ❌ Falta | Gerar variações da pergunta |
| **Hybrid Search** | ❌ Falta | Vetorial + Keyword (BM25) |
| **Re-ranking** | ❌ Falta | Reordenar por relevância real |
| **Compression** | ❌ Falta | Remover partes irrelevantes |
| **Prompt Builder** | ❌ Falta | Montar prompt estruturado |
| **LLM Integration** | ❌ Falta | Auto-chamada Claude/GPT |

---

## 🚀 Features do RAG Avançado

### 1. 🎯 Retrieval Sofisticado

#### a) **Hybrid Search** (Busca Híbrida)

Combina 2 métodos:
- **Vetorial**: Busca por similaridade semântica (embeddings)
- **Keyword**: Busca por palavras exatas (BM25, SQLite FTS)

**Exemplo:**
```python
# Busca vetorial
vector_results = mem0.search("selector21 implementação")  # Top 50

# Busca keyword
keyword_results = sqlite_fts.search("selector21")  # Top 50

# Merge e dedup
final_results = merge_and_deduplicate(vector_results, keyword_results)  # Top 100
```

**Vantagem:** Pega tanto matches semânticos quanto exatos

#### b) **Multi-Query**

Gera variações da pergunta para melhor cobertura:

**Query original:** "Como funciona selector21?"

**Variações geradas:**
- "Arquitetura do selector21"
- "Implementação do selector21"
- "Como selector21 seleciona estratégias"
- "Bugs e fixes do selector21"

```python
from openai import OpenAI

def expand_query(query: str) -> list[str]:
    prompt = f"""Gere 4 variações desta pergunta para buscar em documentação técnica:
    
    Query: {query}
    
    Retorne apenas as 4 queries, uma por linha."""
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.split('\n')
```

#### c) **HyDE** (Hypothetical Document Embeddings)

Técnica avançada:
1. LLM gera resposta hipotética (mesmo sem saber resposta real)
2. Usa resposta hipotética para buscar docs similares
3. Mais efetivo que buscar com query direta

**Exemplo:**
```python
# 1. Gerar documento hipotético
hypothetical_doc = llm.generate(
    "Escreva uma explicação técnica sobre como o selector21 funciona"
)
# Resultado: "O selector21 é um sistema que usa ML para..."

# 2. Buscar docs similares ao documento hipotético
results = vector_search(hypothetical_doc)
# Encontra: documentos reais que falam sobre selector21
```

**Por que funciona?** Documentos tendem a ser similares entre si, então buscar por um "documento fake" encontra documentos reais.

---

### 2. 🔝 Re-Ranking

**Problema:** Busca vetorial inicial é rápida mas imprecisa

**Solução:** Re-ranker (cross-encoder)

**Fluxo:**
```
1. Busca inicial (vetorial): 100 docs (rápida, ~70% precisão)
2. Re-rank (cross-encoder): Top 10 (lenta, ~95% precisão)
```

**Implementação:**
```python
from sentence_transformers import CrossEncoder

# 1. Busca inicial (rápida)
initial_results = vector_search(query, top_k=100)

# 2. Re-rank (precisa)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
pairs = [(query, doc.content) for doc in initial_results]
scores = reranker.predict(pairs)

# 3. Reordenar por score
sorted_results = sorted(
    zip(initial_results, scores),
    key=lambda x: x[1],
    reverse=True
)[:10]  # Top 10
```

**Diferença:**
- **Bi-encoder** (vetorial): Compara embeddings pré-calculados (rápido)
- **Cross-encoder** (re-rank): Avalia query + doc juntos (preciso)

---

### 3. 🧩 Chunking Inteligente

**Problema:** Como dividir documentos grandes?

**Estratégias:**

#### a) Fixed-size chunking (Simples)
```python
chunk_size = 500  # tokens
overlap = 50      # tokens de overlap

chunks = split_into_chunks(document, chunk_size, overlap)
```

#### b) Semantic chunking (Inteligente)
```python
# Quebra em frases naturais
# Agrupa frases semanticamente similares
chunks = semantic_split(document)
```

#### c) Document hierarchy (Melhor)
```python
{
    "section": "Implementação selector21",
    "subsection": "Feature Engineering",
    "content": "...",
    "metadata": {
        "file": "selector.py",
        "function": "engineer_features",
        "lines": "45-120"
    }
}
```

**Seu caso:** Conversas já são "chunks" naturais! ✅

---

### 4. 🔗 Contextual Compression

**Problema:** Contexto muito grande → custo alto + perde foco

**Solução:** Comprimir mantendo só o relevante

```python
def compress_context(docs: list, query: str) -> str:
    compressed = []
    
    for doc in docs:
        # LLM extrai apenas partes relevantes para query
        relevant_parts = llm.extract_relevant(doc, query)
        compressed.append(relevant_parts)
    
    return "\n\n".join(compressed)

# Exemplo
original = "5000 tokens"  # 3 conversas completas
compressed = "1500 tokens"  # Apenas partes relevantes
# Economia: 70% tokens = $$$
```

---

### 5. 🎭 Multi-Hop Reasoning

**Problema:** Perguntas complexas precisam múltiplas buscas

**Exemplo:**
```
Query: "Compare selector21 atual com versão anterior"

→ Busca 1: "selector21 implementação atual"
   Resultado: [Docs sobre versão atual]

→ Busca 2: "selector21 versão anterior histórico"
   Resultado: [Docs sobre versão antiga]

→ Busca 3: "diferenças mudanças selector21"
   Resultado: [Docs sobre o que mudou]

→ LLM sintetiza: Comparação completa
```

**Implementação:**
```python
def multi_hop_rag(query: str, max_hops: int = 3):
    context = []
    current_query = query
    
    for hop in range(max_hops):
        # 1. Buscar
        results = search(current_query)
        context.extend(results)
        
        # 2. LLM decide: precisa mais informação?
        needs_more = llm.needs_more_context(query, context)
        if not needs_more:
            break
        
        # 3. Gerar próxima query
        current_query = llm.generate_followup_query(query, context)
    
    # 4. Resposta final
    return llm.generate_answer(query, context)
```

---

### 6. 🌳 Graph RAG

**Usa grafo de conhecimento para navegação inteligente**

**Você já tem a base!** mem0 armazena:
- Entidades (nodes)
- Relações (edges)

**Como usar:**
```python
# Query: "O que mudou no selector21?"

# 1. Encontrar entidade
entity = graph.find_entity("selector21")

# 2. Traversal no grafo
related = graph.get_related(
    entity,
    relations=["modified_by", "references", "replaced"]
)

# 3. Buscar contexto de cada node
docs = [retrieve_context(node) for node in related]

# 4. LLM sintetiza
answer = llm.generate(query, docs)
```

**Vantagem:** Segue relações estruturadas, não apenas similaridade

---

### 7. 🎨 Self-RAG

**LLM decide automaticamente:**
- Quando buscar mais info
- Se resposta está boa
- Se precisa iterar

```python
def self_rag(query: str):
    # 1. LLM tenta responder
    initial_answer = llm.generate(query, context=[])
    
    # 2. LLM avalia própria resposta
    confidence = llm.evaluate_confidence(initial_answer)
    
    if confidence < 0.7:
        # 3. Buscar mais contexto
        context = search(query)
        
        # 4. Tentar novamente
        better_answer = llm.generate(query, context)
        
        # 5. Verificar fontes
        is_grounded = llm.check_grounding(better_answer, context)
        
        if is_grounded:
            return better_answer
        else:
            return "Não encontrei informação suficiente"
    
    return initial_answer
```

---

## 📊 Arquitetura Completa para Seu Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. USER QUERY                                │
│            "Como funciona o selector21?"                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 2. QUERY PROCESSOR                              │
│  • Expand query (GPT-4 mini): 4 variações                      │
│  • Extract entities: ["selector21"]                            │
│  • Generate embeddings                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 3. HYBRID RETRIEVAL                             │
│  ┌─────────────────────┐     ┌─────────────────────┐          │
│  │  Vector Search      │     │  Keyword Search     │          │
│  │  (mem0 embeddings)  │     │  (SQLite FTS5)      │          │
│  │  Top 50 docs        │     │  Top 50 docs        │          │
│  └──────────┬──────────┘     └──────────┬──────────┘          │
│             │                           │                      │
│             └─────────┬─────────────────┘                      │
│                       │                                        │
│              ┌────────▼─────────┐                             │
│              │  Merge + Dedup   │                             │
│              │  100 unique docs │                             │
│              └────────┬─────────┘                             │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. RE-RANKER                                 │
│  • Cross-encoder model (local)                                 │
│  • Score each doc vs query                                     │
│  • Sort by relevance score                                     │
│  • Keep top 10                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              5. CONTEXTUAL COMPRESSION                          │
│  • LLM extracts relevant parts                                 │
│  • Removes noise and irrelevant info                           │
│  • Reduces tokens: 5000 → 1500                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 6. PROMPT BUILDER                               │
│  System: Você é expert em trading bots Python                  │
│                                                                  │
│  Context (from memory):                                         │
│  [Doc1] selector21 implementação inicial...                    │
│  [Doc2] refatoração para ML-based selection...                 │
│  [Doc3] bug fix na validação temporal...                       │
│                                                                  │
│  User: Como funciona o selector21?                             │
│                                                                  │
│  Instructions: Responda APENAS baseado no Context.             │
│  Cite as fontes. Se não souber, diga.                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   7. LLM GENERATION                             │
│  • Claude Sonnet 4.5                                           │
│  • Generates answer from context                               │
│  • Cites sources                                               │
│  • Flags uncertainties                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   8. FINAL RESPONSE                             │
│                                                                  │
│  O selector21 funciona através de 3 componentes principais:    │
│                                                                  │
│  1. **Feature Engineering** [1]: Calcula 47 features...        │
│  2. **ML Scoring** [2]: Random Forest treinado com...         │
│  3. **Validation** [3]: Walk-forward temporal...              │
│                                                                  │
│  Sources:                                                       │
│  [1] Conversa 2025-10-15: Implementação inicial               │
│  [2] Conversa 2025-11-03: Refatoração ML                      │
│  [3] Conversa 2025-11-10: Bug fix validação                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementação Prática

### Opção 1: Framework Pronto (Mais Rápido)

#### **LangChain** (Recomendado)
```python
pip install langchain chromadb anthropic

# Código mínimo
from langchain.vectorstores import Chroma
from langchain.llms import Anthropic
from langchain.chains import RetrievalQA

# 1. Setup
vectorstore = Chroma(persist_directory="/home/scalp/memory/chroma")
llm = Anthropic(model="claude-sonnet-4")

# 2. Create RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
    return_source_documents=True
)

# 3. Query
result = qa_chain("Como funciona o selector21?")
print(result["result"])
print("Sources:", result["source_documents"])
```

#### **LlamaIndex** (Mais focado em RAG)
```python
pip install llama-index

from llama_index import (
    VectorStoreIndex,
    ServiceContext,
    StorageContext,
    load_index_from_storage
)

# 1. Setup
storage_context = StorageContext.from_defaults(
    persist_dir="/home/scalp/memory/llama_index"
)
index = load_index_from_storage(storage_context)

# 2. Create query engine (RAG automático!)
query_engine = index.as_query_engine(
    similarity_top_k=10,
    response_mode="tree_summarize"
)

# 3. Query
response = query_engine.query("Como funciona o selector21?")
print(response)
```

---

### Opção 2: Custom (Mais Controle)

```python
# rag_system.py
import anthropic
from sentence_transformers import CrossEncoder
from typing import List, Dict

class AdvancedRAG:
    def __init__(self):
        self.claude = anthropic.Anthropic()
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
    def query(self, user_query: str) -> Dict:
        # 1. Query Expansion
        expanded_queries = self.expand_query(user_query)
        
        # 2. Hybrid Search
        vector_results = self.vector_search(expanded_queries)
        keyword_results = self.keyword_search(user_query)
        all_results = self.merge_results(vector_results, keyword_results)
        
        # 3. Re-rank
        reranked = self.rerank(user_query, all_results, top_k=10)
        
        # 4. Compress
        compressed = self.compress_context(user_query, reranked)
        
        # 5. Build Prompt
        prompt = self.build_prompt(user_query, compressed)
        
        # 6. Generate
        response = self.generate(prompt)
        
        return {
            "answer": response,
            "sources": [doc["metadata"] for doc in reranked],
            "num_docs_retrieved": len(all_results),
            "num_docs_used": len(reranked)
        }
    
    def expand_query(self, query: str) -> List[str]:
        prompt = f"""Generate 3 variations of this query for better retrieval:

Query: {query}

Return only the 3 queries, one per line."""
        
        message = self.claude.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.split('\n')
    
    def vector_search(self, queries: List[str]) -> List[Dict]:
        # Busca em mem0 para cada query
        # Implementar com seu sistema atual
        pass
    
    def keyword_search(self, query: str) -> List[Dict]:
        # SQLite FTS5
        # SELECT * FROM docs WHERE content MATCH ?
        pass
    
    def rerank(self, query: str, docs: List[Dict], top_k: int) -> List[Dict]:
        pairs = [(query, doc["content"]) for doc in docs]
        scores = self.reranker.predict(pairs)
        
        ranked = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [doc for doc, score in ranked[:top_k]]
    
    def compress_context(self, query: str, docs: List[Dict]) -> str:
        # Opcional: usar LLM para comprimir
        # Por ora, apenas truncar
        max_tokens = 3000
        compressed = []
        
        for doc in docs:
            compressed.append(doc["content"][:500])  # Primeiros 500 chars
        
        return "\n\n---\n\n".join(compressed)
    
    def build_prompt(self, query: str, context: str) -> str:
        return f"""You are an expert assistant for a trading bot developer.

Context from previous conversations and code:
{context}

User Question: {query}

Instructions:
- Answer ONLY based on the Context provided
- Cite sources using [N] notation
- If you don't know, say "I don't have enough information"
- Be technical and precise

Answer:"""
    
    def generate(self, prompt: str) -> str:
        message = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text

# Uso
rag = AdvancedRAG()
result = rag.query("Como funciona o selector21?")
print(result["answer"])
print("\nSources:", result["sources"])
```

---

## 💰 Custo vs Benefício

### RAG Básico (você tem):
- **Custo:** $0/mês
- **Setup:** Pronto!
- **Precisão:** ~70%
- **Uso:** Manual (você lê e interpreta)

### RAG Avançado:
- **Custo:** $5-20/mês (depende do uso)
- **Setup:** 2-4 dias dev
- **Precisão:** ~90-95%
- **Uso:** Automático (LLM responde diretamente)

#### Breakdown de Custos:

| Componente | Modelo | Custo/query |
|------------|--------|-------------|
| Query Expansion | GPT-4o mini | $0.001 |
| Re-ranker | Local (grátis) | $0 |
| Compression | Claude Haiku | $0.002 |
| Generation | Claude Sonnet | $0.015 |
| **Total** | | **$0.018/query** |

**Estimativa:**
- 50 queries/dia = $0.90/dia = **$27/mês**
- 20 queries/dia = $0.36/dia = **$11/mês**
- 5 queries/dia = $0.09/dia = **$2.70/mês**

### Vale a pena?

**Para trading bot:** SIM! 💯

**Por quê?**
- ✅ 1 bug evitado = economiza 2-4 horas
- ✅ 1 estratégia otimizada = potencial $$$
- ✅ Conhecimento sempre acessível
- ✅ Time-to-market mais rápido
- ✅ Onboarding de novos devs facilitado

**ROI:** Se economizar 1 hora/semana = ~$100-200 valor/hora = **ROI 10-40x**

---

## 🎯 Quando Usar RAG Avançado?

### ✅ Use RAG Avançado quando:
- Base de conhecimento grande (>1000 docs)
- Queries complexas (multi-hop)
- Precisão crítica (decisões de $$$)
- Respostas longas e detalhadas
- Citação de fontes obrigatória
- Múltiplos usuários (time)

### ⚠️ RAG Básico suficiente quando:
- Base pequena (<100 docs)
- Queries simples (lookup)
- Você valida manualmente
- Respostas curtas
- Apenas exploração pessoal

### Para seu caso (Trading Bot):
**→ RAG Avançado faz sentido!** ✅

**Justificativa:**
- ✅ Muitas conversas técnicas (>100)
- ✅ Código complexo (Python + ML)
- ✅ Decisões críticas (dinheiro real)
- ✅ Histórico de bugs/fixes importante
- ✅ Evolução contínua de estratégias
- ✅ Documentação viva necessária

---

## 🚀 Próximos Passos

### Fase 1: Setup Básico (1-2 dias)
1. ✅ Instalar framework (LangChain ou LlamaIndex)
2. ✅ Integrar com mem0 existente
3. ✅ Testar query simples
4. ✅ Validar respostas

### Fase 2: Features Avançadas (2-3 dias)
1. ✅ Implementar hybrid search
2. ✅ Adicionar re-ranker
3. ✅ Query expansion
4. ✅ Contextual compression

### Fase 3: Produção (1-2 dias)
1. ✅ API REST endpoint
2. ✅ CLI interface
3. ✅ Logging e monitoring
4. ✅ Caching de resultados

### Fase 4: Otimização (contínuo)
1. ✅ Tuning de parâmetros
2. ✅ A/B testing de prompts
3. ✅ Feedback loop
4. ✅ Métricas de qualidade

---

## 📚 Recursos Adicionais

### Papers importantes:
- **RAG**: https://arxiv.org/abs/2005.11401
- **HyDE**: https://arxiv.org/abs/2212.10496
- **Self-RAG**: https://arxiv.org/abs/2310.11511

### Frameworks:
- **LangChain**: https://python.langchain.com/
- **LlamaIndex**: https://www.llamaindex.ai/
- **Haystack**: https://haystack.deepset.ai/

### Modelos úteis:
- **Embeddings**: `text-embedding-3-large` (OpenAI)
- **Re-ranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **LLM**: Claude Sonnet 4.5, GPT-4

---

## 🎉 Resumo

**RAG = Transformar sua memória passiva em assistente ativo!**

### Seu sistema ATUAL:
```
📚 Biblioteca → Você busca → Você lê → Você interpreta
```

### Com RAG AVANÇADO:
```
🤖 Bibliotecário Expert → Busca + Resume + Responde automaticamente
```

**É o próximo nível natural do seu sistema profissional!** 🚀

---

**Quer implementar? Posso ajudar com código específico para seu caso!** 💪
