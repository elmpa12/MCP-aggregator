# Guia: Como Salvar Sessões de Todos os CLIs

## ✅ Métodos de Salvamento por CLI

### 🎯 **Cursor Agent** (Esta sessão atual)

#### Método 1: Script Manual (Recomendado)
```bash
# Salvar com resumo customizado
./save_current_cursor_session.sh "Implementação feature X"

# Salvar sem resumo
./save_current_cursor_session.sh

# Com alias (após configurar)
csave "Bug fix no selector21"
```

#### Método 2: Forçar Sincronização Automática
```bash
# Força processamento imediato de todos os chats
memory sync

# Ou via Python
python /home/scalp/cursor_memory_auto.py scan
```

#### Método 3: Aguardar Auto-Sync
- O serviço `cursor-memory-sync.service` sincroniza **automaticamente** a cada 10 minutos
- Não precisa fazer nada!

---

### 🤖 **Claude CLI**

```bash
# Usar claude-mem (auto-save ao sair)
claude-mem "Sua pergunta"

# Durante conversa: Ctrl+D para terminar
# → Auto-save acontece automaticamente

# Com alias
claude "pergunta"
```

**O que é salvo:**
- Últimas 50 linhas da conversa
- Filtradas para User/Assistant
- Resumo de ~300 caracteres
- Mínimo 100 tokens

---

### 🔥 **Claudex**

```bash
# Usar claudex-mem (auto-save ao sair)
claudex-mem --plan

# Ao terminar ou Ctrl+C
# → Auto-save acontece automaticamente

# Com alias
claudex --implement
cx --plan
```

**O que é salvo:**
- Primeiras 20 + últimas 10 linhas
- Resumo de ~200 caracteres
- Sempre salva (sem filtro de tamanho)

---

## 🚀 Salvamento Manual Rápido

### Durante qualquer conversa:
```bash
# Salvar nota rápida
memory save "Contexto importante desta conversa"

# Com alias
msave "Feature X implementada"
```

### No final da sessão:
```bash
# Cursor Agent
csave "Resumo da sessão"

# Claude/Claudex (já salvam automaticamente ao sair)
# Apenas feche normalmente: Ctrl+D ou exit
```

---

## 📊 Verificar Salvamentos

### Ver último salvamento:
```bash
# Buscar por hoje
memory search "$(date +%Y-%m-%d)"

# Buscar por palavra-chave
memory search "Cursor Agent"
memory search "Claude CLI"
memory search "Claudex"
```

### Ver dashboard:
```bash
memory dashboard
cat /home/scalp/memory_dashboards/latest_memory_report.md
```

### Ver logs brutos:
```bash
# Cursor Agent (última sessão)
find /root/.cursor/chats -name "store.db" -type f -printf '%T@ %p\n' | sort -rn | head -1

# Claude/Claudex (últimos logs)
ls -t /home/scalp/memory/*_session_*.log | head -5
```

---

## 🔄 Fluxo Completo de Salvamento

### Exemplo: Sessão Cursor Agent
```bash
# 1. Durante a conversa (opcional)
memory save "Implementando feature de ML"

# 2. Ao terminar a sessão
csave "ML feature completa + testes"

# 3. Forçar sync completo (opcional)
memory sync

# 4. Verificar
memory search "ML feature"
```

### Exemplo: Claude CLI
```bash
# 1. Iniciar com wrapper
claude-mem

# 2. Conversar normalmente
> User: Help me debug...
> Assistant: [resposta]

# 3. Terminar (Ctrl+D)
# → Auto-save automático!

# 4. Verificar
memory search "debug"
```

---

## ⚙️ Automações Configuradas

| CLI | Auto-Save | Quando | Comando Manual |
|-----|-----------|--------|----------------|
| **Cursor** | ✅ Sim | A cada 10min | `memory sync` |
| **Claude** | ✅ Sim | Ao sair | `claude-mem` |
| **Claudex** | ✅ Sim | Ao sair | `claudex-mem` |

---

## 💡 Dicas e Boas Práticas

### 1. **Salvar Durante Sessões Longas**
```bash
# A cada milestone importante
memory save "Checkpoint: feature X funcionando"
memory save "Bug crítico resolvido"
```

### 2. **Usar Resumos Descritivos**
```bash
# ❌ Ruim
csave "trabalho"

# ✅ Bom
csave "Implementação WalkForward pipeline + validação temporal"
```

### 3. **Sincronizar Antes de Buscar**
```bash
# Garantir dados atualizados
memory sync
serena sync  # Se usar Serena

# Depois buscar
memory search "palavra-chave"
```

### 4. **Backup de Logs Importantes**
```bash
# Copiar log específico
cp /home/scalp/memory/claude_session_20251113_080000.log ~/backups/

# Compactar logs antigos
gzip /home/scalp/memory/*_session_*.log
```

---

## 🐛 Troubleshooting

### Problema: "Conversa não foi salva"
```bash
# Verificar se wrapper foi usado
which claude-mem
which claudex-mem

# Verificar logs
ls -lh /home/scalp/memory/*_session_*.log

# Testar manualmente
echo "teste" | claude-mem
```

### Problema: "Auto-sync não funciona" (Cursor)
```bash
# Ver status do serviço
systemctl status cursor-memory-sync.service

# Ver logs
journalctl -u cursor-memory-sync.service -n 50

# Reiniciar
sudo systemctl restart cursor-memory-sync.service

# Sync manual
memory sync
```

### Problema: "Não acho a conversa"
```bash
# Verificar se foi salva
memory search "palavra-chave-unica-da-conversa"

# Ver todas as memórias recentes
memory dashboard

# Verificar processed chats
cat /home/scalp/memory/processed_chats.json | jq 'keys | length'
```

---

## 📁 Estrutura de Arquivos

```
/home/scalp/
├── save_current_cursor_session.sh       ← Script de save manual
├── .bash_aliases_memory                 ← Aliases (csave, etc)
└── memory/
    ├── cursor_agent_session_*.log       ← Logs Cursor Agent
    ├── claude_session_*.log             ← Logs Claude CLI
    ├── claudex_session_*.log            ← Logs Claudex
    ├── mem0.db                          ← Banco de memória
    └── processed_chats.json             ← Controle de sync

/usr/local/bin/
├── cursor-agent-mem                     ← Wrapper Cursor Agent
├── claude-mem                           ← Wrapper Claude
├── claudex-mem                          ← Wrapper Claudex
└── memory                               ← CLI principal
```

---

## ✅ Checklist Rápido

Antes de terminar uma sessão importante:

- [ ] Conversa tem conteúdo relevante? (>100 tokens)
- [ ] Usado wrapper correto? (`claude-mem`, `claudex-mem`)
- [ ] Salvar nota manual? (`memory save "resumo"`)
- [ ] Para Cursor Agent: usar `csave "resumo"`?
- [ ] Verificar salvamento: `memory search "palavra-chave"`?

---

## 🎉 Resumo

**Todos os CLIs salvam automaticamente!**

- ✅ Cursor → Auto-sync 10min (`memory sync` manual)
- ✅ Claude → Auto-save ao sair (`claude-mem`)
- ✅ Claudex → Auto-save ao sair (`claudex-mem`)
- ✅ Cursor Agent → `csave "resumo"` ou aguardar auto-sync

**Nunca mais perca contexto!** 🧠✨
