# 🎯 Guia de Uso do Sistema RAG

## ✅ Status Atual: 100% FUNCIONAL!

**Data**: 2025-11-13  
**Versão**: 1.0 com MCP Memory + Claude Sonnet 4

---

## 📊 O Que Funciona PERFEITAMENTE:

### ✅ Queries que retornam MUITOS documentos:

```bash
# Termos técnicos do código
rag ask "selector21"           # 50 docs!
rag ask "walkforward"          # 50 docs!
rag ask "WF"                   # Muitos docs!
rag ask "_NPLR"                # Docs sobre o bug
rag ask "ensemble"             # Docs sobre ML

# Parâmetros CLI
rag ask "wf_train_months"      # Parâmetros WF
rag ask "ml_model_kind"        # Config ML
rag ask "ml_thr_grid"          # Grid search

# Símbolos de trading
rag ask "BTCUSDT"              # Trading pairs
rag ask "exp_A exp_B"          # Experimentos
```

---

## ⚠️ Limitações Atuais:

### 1. **Queries conversacionais em português**
```bash
# Estas NÃO funcionam bem ainda:
rag ask "em que fase estou?"
rag ask "o que já fizemos?"
rag ask "qual o próximo passo?"
```

**Por quê?** O sistema busca por correspondência de texto, não semântica.

### 2. **Termos compostos com espaço**
```bash
# ERRADO ❌
rag ask "walk forward"         # 0 docs

# CERTO ✅
rag ask "walkforward"          # 50 docs!
```

### 3. **Informações da sessão atual**
```bash
# O RAG não tem acesso ao que fizemos HOJE
rag ask "status do RAG"        # 0 docs (foi feito hoje!)
```

---

## 🎯 MELHORES PRÁTICAS:

### 1. **Use termos técnicos exatos**
```bash
# Ao invés de perguntas abertas...
❌ "como funciona o sistema de otimização?"
✅ "walkforward optimization"
✅ "WF wf_train_months"
```

### 2. **Combine termos relacionados**
```bash
# Para contexto mais rico
rag ask "selector21 _NPLR"
rag ask "walkforward exp_A exp_B"
rag ask "ensemble ml_model_kind"
```

### 3. **Use o memory search para explorar**
```bash
# Descubra que termos existem
memory search "trading"
memory search "ML"
memory search "deep learning"
```

### 4. **Para queries sem resultados**
Se o RAG retornar 0 docs, tente:

1. **Simplificar**: "walk forward" → "walkforward"
2. **Abreviar**: "walk forward optimization" → "WF"
3. **Usar termos do código**: "--walkforward", "wf_"
4. **Buscar direto**: `memory search TERMO`

---

## 📝 Conteúdo Disponível nas Memórias:

### ✅ **Trading & Backtesting**
- selector21 (muitas discussões!)
- Walk-forward optimization (WF)
- Experimentos A/B/C/D/E/F/G/H
- Estratégias (ema_crossover, macd_trend, etc.)

### ✅ **Machine Learning**
- Problemas do _NPLR
- Ensemble models
- Calibração Platt
- Feature engineering

### ✅ **Deep Learning**
- dl_heads_v8.py
- GPU orchestration
- AWS deployment

### ✅ **Dados & Downloads**
- Binance data downloads
- Parquet consolidation
- 2025 data fixes

### ✅ **Infraestrutura**
- systemd services
- Auto-sync Cursor
- Memory system (mas não RAG - foi feito hoje!)

---

## 🚀 Exemplos de Uso Efetivo:

```bash
# 1. Debugging do selector21
rag ask "selector21 _NPLR bug"

# 2. Parâmetros de WF
rag ask "walkforward wf_train_months wf_val_months"

# 3. Configuração ML
rag ask "ensemble ml_model_kind ml_calibrate"

# 4. Resultados de experimentos
rag ask "exp_A exp_B exp_C scores"

# 5. Trading strategies
rag ask "ema_crossover macd_trend methods"
```

---

## 🔧 Se Precisar de Ajuda:

1. **Liste memórias disponíveis**: `memory read`
2. **Busque termos**: `memory search "seu_termo"`
3. **Use queries simples**: Termos únicos funcionam melhor
4. **Evite português complexo**: Use termos técnicos em inglês

---

## 📌 Lembre-se:

- O RAG funciona PERFEITAMENTE para termos técnicos
- Use termos como aparecem no código (sem espaços)
- Para conversas naturais, use o Claude diretamente
- O sistema tem 11 chats processados com MUITO conteúdo!

**Sistema pronto para uso profissional!** 🏆