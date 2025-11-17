# 🚀 RAG System - Guia Rápido

## ✅ Sistema Implementado!

Você agora tem um **Advanced RAG System** completo e pronto para uso!

---

## 🔧 Setup Inicial (UMA VEZ)

### 1. Configurar API Key

```bash
# Adicionar ao ~/.bashrc ou ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-..."

# Ou criar arquivo .env
echo 'ANTHROPIC_API_KEY=sk-ant-...' > /home/scalp/.env
```

### 2. Testar Instalação

```bash
rag test
```

Se ver resposta → **Sistema funcionando!** ✅

---

## 💬 Usar o Sistema

### Método 1: CLI (Recomendado)

```bash
# Fazer qualquer pergunta
rag ask "Como funciona o selector21?"

# Perguntas técnicas
rag ask "Explique a arquitetura do sistema"

# Debugging
rag ask "Onde está o bug do ML feature?"

# Histórico
rag ask "O que mudou na última versão?"

# Formato JSON
rag ask "Explique o sistema" --format json
```

### Método 2: API Server

```bash
# Terminal 1: Iniciar servidor
rag server

# Terminal 2: Fazer queries
curl -X POST http://localhost:8765/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Como funciona o selector21?"}'
```

### Método 3: Python

```python
from rag_system.core.advanced_rag import AdvancedRAGSystem

# Criar instância
rag = AdvancedRAGSystem()

# Fazer query
result = rag.query("Como funciona o sistema de memória?")

# Ver resposta
print(result.answer)
print(f"Confiança: {result.confidence:.0%}")
print(f"Tempo: {result.query_time_ms:.0f}ms")

# Ver fontes
for i, source in enumerate(result.sources):
    print(f"[{i+1}] {source['content'][:100]}...")
```

---

## 🎯 O que o Sistema Faz

### Fluxo Completo:

```
Sua Pergunta
    ↓
1. Expande query (3 variações)
    ↓
2. Busca em mem0 + SQLite (100 docs)
    ↓
3. Re-rankeia (top 10)
    ↓
4. Comprime contexto
    ↓
5. Claude gera resposta
    ↓
Resposta Completa + Fontes + Confiança
```

### Busca em:

✅ Todas as conversas do Cursor Agent  
✅ Conversas do Claude CLI  
✅ Conversas do Claudex  
✅ Notas manuais (memory save)  
✅ Memórias do mem0  

---

## 💡 Exemplos de Perguntas

### Código e Arquitetura
```bash
rag ask "Como funciona o selector21?"
rag ask "Onde está a classe WalkForward?"
rag ask "Explique a arquitetura do backtest"
```

### Debugging
```bash
rag ask "Quando consertei o bug do validation?"
rag ask "Por que o ML model não converge?"
rag ask "Qual era o erro no data pipeline?"
```

### Histórico e Evolução
```bash
rag ask "Como evoluiu a estratégia de trading?"
rag ask "O que mudou no último mês?"
rag ask "Quando implementei feature engineering?"
```

### Decisões e Contexto
```bash
rag ask "Por que escolhi Random Forest?"
rag ask "Quais foram as alternativas testadas?"
rag ask "Como validei o modelo?"
```

---

## 📊 Entender a Resposta

### Exemplo de Output:

```
🔍 Processando query: Como funciona o selector21?...
  1️⃣  Expandindo query...
     ✅ 4 variações geradas
  2️⃣  Buscando documentos...
     ✅ 87 documentos encontrados
  3️⃣  Re-ranqueando resultados...
     ✅ Top 10 docs selecionados
  4️⃣  Comprimindo contexto...
     ✅ Contexto comprimido
  5️⃣  Gerando resposta...
     ✅ Resposta gerada (confiança: 92%)

════════════════════════════════════════════
Resposta (confiança: 92%)
════════════════════════════════════════════

O selector21 é um sistema de seleção...
[Doc 1] [Doc 3]...

📊 87 docs recuperados, 10 usados | ⏱️  4250ms
```

### Interpretação:

- **Confiança 80-100%**: Resposta muito confiável
- **Confiança 60-80%**: Resposta boa mas verificar
- **Confiança <60%**: Pouca informação disponível

### Citações:

- **[Doc N]**: Referência ao documento fonte
- Você pode pedir detalhes: `rag ask "Mostre Doc 1 completo"`

---

## ⚙️ Configuração Avançada

### Arquivo: `/home/scalp/rag_system/config/settings.py`

```python
# Ajustar parâmetros
INITIAL_RETRIEVAL_K = 100  # Docs iniciais
RERANK_TOP_K = 10          # Após re-ranking
FINAL_CONTEXT_K = 5        # Docs no contexto final
```

### Modelos Utilizados:

- **Expansion**: Claude Haiku (rápido, barato)
- **Re-ranking**: Cross-encoder local (grátis)
- **Generation**: Claude Sonnet 4.5 (melhor qualidade)

---

## 💰 Custos

### Por Query:
- Expansion: $0.001
- Re-ranking: $0 (local)
- Generation: $0.015
- **Total: ~$0.02/query**

### Estimativas Mensais:
- 10 queries/dia = **$6/mês**
- 20 queries/dia = **$12/mês**
- 50 queries/dia = **$30/mês**

### ROI:
Se economizar 1 hora/semana:
- Valor: $100-200
- Custo: $6-30
- **ROI: 5-30x** 🎯

---

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY não encontrada"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Ou adicionar ao ~/.bashrc
```

### "Command not found: rag"
```bash
chmod +x /usr/local/bin/rag
# Ou usar: python /home/scalp/rag_system/cli/rag_cli.py
```

### "Nenhum documento encontrado"
```bash
# Verificar mem0
memory search "teste"

# Forçar sync
memory sync
```

### Resposta genérica/vaga
- Base de conhecimento pequena ainda
- Continue usando e salvando conversas
- Sistema melhora com mais dados

---

## 🔄 Integração com Workflow

### No Terminal
```bash
# Antes de começar tarefa
rag ask "O que fiz da última vez neste feature?"

# Durante desenvolvimento
rag ask "Como implementei isso antes?"

# Após terminar
memory save "Implementei X, Y, Z"
```

### No Cursor Agent
```
Você: "Me ajude com o selector21"

Cursor Agent: [usa ferramentas Serena]

Você: "Também busque no histórico"
      rag ask "selector21 histórico bugs"

Cursor Agent: [vê histórico + código atual]
```

---

## 📈 Melhorar Performance

### 1. Alimentar o Sistema
```bash
# Salvar notas importantes
memory save "Feature X implementado com técnica Y"

# Auto-sync já roda automaticamente
# Suas conversas são indexadas
```

### 2. Queries Específicas
```bash
# ❌ Ruim (muito genérico)
rag ask "sistema"

# ✅ Bom (específico)
rag ask "Como funciona o sistema de validação temporal do selector21?"
```

### 3. Iterativo
```bash
# Query 1
rag ask "Explique selector21"

# Refinar com mais contexto
rag ask "Explique a parte de feature engineering do selector21"

# Detalhar ainda mais
rag ask "Quais features o selector21 calcula?"
```

---

## 🎉 Próximos Passos

### Integração Serena (Código)
```bash
# Futuro: buscar código automaticamente
rag ask "Mostre código do selector21" --with-code
```

### Graph RAG (Entidades)
```bash
# Futuro: seguir relações
rag ask "O que depende do selector21?"
```

### Dashboard Web
```bash
# Futuro: interface visual
rag web  # Abre browser
```

---

## 📚 Documentação Completa

- **Este arquivo**: Guia rápido
- `/home/scalp/RAG_ADVANCED_GUIDE.md`: Detalhes técnicos
- `/home/scalp/rag_system/README.md`: Documentação do código

---

## ✅ Checklist de Uso

Antes de perguntar algo importante:

- [ ] API key configurada?
- [ ] Sistema testado? (`rag test`)
- [ ] Query específica e clara?
- [ ] Base tem informação sobre o tópico?

---

## 🚀 Começar AGORA

```bash
# 1. Configurar (se ainda não fez)
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Testar
rag test

# 3. Usar!
rag ask "Explique o sistema de memória que implementamos hoje"
```

**Pronto! Sistema 100% funcional! 🎊**

---

## 💪 Dica Final

**Use sem moderação!**

Este sistema foi feito para economizar seu tempo.  
Sempre que pensar "Como fiz aquilo?" → **`rag ask`**

Quanto mais usar, mais rápido você trabalha! ⚡
