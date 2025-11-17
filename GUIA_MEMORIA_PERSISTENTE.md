# 🧠 Guia Completo - Sistema de Memória Persistente

## 📋 Visão Geral

Sistema completo de memória persistente que **nunca perde o contexto** dos seus chats, tanto no CLI quanto no Cursor IDE.

### ✅ O que foi configurado:

- ✅ **CLI (Terminal)**: Comando `memory` para salvar/buscar rapidamente
- ✅ **Cursor IDE**: Integração automática com memory servers
- ✅ **Automação**: Scripts para sincronização contínua
- ✅ **2 Memory Servers**: 
  - `memory` - SQLite simples e rápido
  - `mem0` - Avançado com grafo de conhecimento

---

## 🚀 Como Usar

### 1️⃣ **No Terminal (CLI)**

O comando `memory` está disponível globalmente:

```bash
# Salvar uma nota
memory save "BTC: RSI oversold, MACD bullish, long @ 42850"

# Buscar notas
memory search "BTC"
memory search "oversold"

# Ler tudo
memory read

# Sincronizar conversas do Cursor
memory sync

# Monitorar continuamente (a cada 5 minutos)
memory watch 300
```

**Exemplos práticos para trading:**

```bash
# Análise técnica
memory save "BTCUSDT 1h: RSI=28, MACD cruzando bullish, volume crescendo"

# Resultado de trade
memory save "Trade LONG BTCUSDT: entrada 42850, saída 44100, lucro +2.9%"

# Nota de backtest
memory save "Backtest RSI_MACD_v3: win_rate=62.1%, profit_factor=1.85, sharpe=2.1"

# Buscar depois
memory search "backtest"
memory search "BTCUSDT"
```

---

### 2️⃣ **No Cursor IDE**

O Cursor está configurado para usar 2 memory servers automaticamente.

#### Como salvar durante uma conversa:

```
👤 Você: "Salve na memória: Estratégia RSI + MACD funciona melhor em 
         timeframes 1h e 4h, especialmente em mercados laterais"

🤖 Cursor: [usa automaticamente create_entities do memory server]
          ✅ Informação salva na memória!
```

#### Como buscar informações salvas:

```
👤 Você: "Busque na memória informações sobre MACD"

🤖 Cursor: [usa search_nodes]
          Encontrei estas informações sobre MACD:
          - Estratégia RSI + MACD...
          - Backtest RSI_MACD_v3...
```

#### Recuperar contexto anterior:

```
👤 Você: "Lembra da análise do BTC que salvamos ontem?"

🤖 Cursor: [busca automaticamente na memória]
          Sim, encontrei: "BTC: RSI oversold..."
```

---

### 3️⃣ **Automação - Sincronizar Conversas Automaticamente**

#### Opção A: Sincronização manual (quando quiser)

```bash
cd /home/scalp
source venv/bin/activate
python cursor_memory_auto.py scan
```

#### Opção B: Monitoramento contínuo (recomendado)

```bash
# Monitorar a cada 5 minutos
python cursor_memory_auto.py watch --interval 300

# Em outra sessão terminal, deixar rodando em background
nohup python cursor_memory_auto.py watch --interval 300 > /tmp/memory-sync.log 2>&1 &
```

#### Opção C: Serviço systemd (automático no boot)

```bash
# Criar serviço
sudo tee /etc/systemd/system/cursor-memory-sync.service > /dev/null << 'EOF'
[Unit]
Description=Cursor Memory Auto Sync
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/scalp
Environment=PATH=/home/scalp/venv/bin:/usr/bin:/bin
ExecStart=/home/scalp/venv/bin/python /home/scalp/cursor_memory_auto.py watch --interval 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable cursor-memory-sync.service
sudo systemctl start cursor-memory-sync.service

# Ver status
sudo systemctl status cursor-memory-sync.service

# Ver logs
journalctl -u cursor-memory-sync.service -f
```

---

## 🧪 Testar o Sistema

Execute o script de teste completo:

```bash
cd /home/scalp
./testar_memoria_completa.sh
```

Ele vai verificar:
- ✅ Todas as instalações
- ✅ Comandos CLI
- ✅ Configurações do Cursor
- ✅ Salvar e buscar notas
- ✅ Estrutura de diretórios

---

## 📁 Estrutura de Arquivos

```
/home/scalp/
├── memory/                          # Diretório de dados
│   ├── memory.db                    # SQLite (usado pelo Cursor + CLI)
│   ├── mem0.db                      # Mem0 (grafo de conhecimento)
│   ├── processed_chats.json         # Controle de sincronização
│   └── *.log                        # Logs dos servidores
│
├── memory-cli.sh                    # Script CLI principal ⭐
├── mcp_memory_client.py             # Cliente Python para memory server
├── cursor_memory_auto.py            # Automação de sincronização
├── llm_mcp_config.json5             # Config para mcp-use (CLI)
└── testar_memoria_completa.sh       # Script de testes

/root/.cursor/
└── mcp.json                         # Config do Cursor ✅ (inclui memory + mem0)

/usr/local/bin/
└── memory -> /home/scalp/memory-cli.sh   # Comando global
```

---

## 🔧 Memory Servers Disponíveis

### 1. **memory** (SQLite - Simples e Rápido)

**Ferramentas:**
- `create_entities` - Criar notas/entidades
- `search_nodes` - Buscar por palavra-chave
- `read_graph` - Ler tudo
- `delete_entities` - Deletar
- `add_observations` - Adicionar informações

**Quando usar:** Notas rápidas, contexto de conversas, dados simples

### 2. **mem0** (Grafo de Conhecimento)

**Ferramentas:**
- Mesmas do `memory` +
- `create_relations` - Criar relações entre entidades
- `open_nodes` - Abrir nós específicos

**Quando usar:** Análises complexas, relações entre informações, estrutura de conhecimento

---

## 💡 Casos de Uso - Trading

### 📊 **Durante análises técnicas:**

No Cursor:
```
"Salve na memória: BTCUSDT mostrando divergência bullish no MACD 4h, 
 RSI em 32, suporte forte em $42,800. Setup long válido."
```

No CLI:
```bash
memory save "BTCUSDT: divergência bullish MACD 4h, RSI=32, suporte $42,800"
```

### 💰 **Registrar trades:**

```bash
memory save "Trade #147: LONG BTCUSDT 0.01 @ 42850, TP1: 43500, TP2: 44200, SL: 42200"
memory save "Trade #147 resultado: +2.9%, fechado em TP1"
```

### 📈 **Backtests:**

```bash
memory save "Backtest RSI_MACD_Strategy_v4:
- Período: 2024-01 a 2024-11
- Win Rate: 64.3%
- Profit Factor: 2.12
- Sharpe Ratio: 2.4
- Melhor timeframe: 4h
- Pior em: mercados muito voláteis"
```

### 🔍 **Buscar depois:**

```bash
# Encontrar todos os backtests
memory search "backtest"

# Encontrar análises do BTC
memory search "BTCUSDT"

# Ver divergências
memory search "divergência"

# Ver trades lucrativos
memory search "resultado"
```

---

## 🔍 Comandos Úteis

### Verificar o que está salvo:

```bash
# Ver quantidade de entradas
memory read | grep -c "name"

# Ver últimas 20 linhas
memory read | tail -20

# Exportar tudo para arquivo
memory read > /tmp/memoria_backup_$(date +%Y%m%d).json
```

### Gerenciar banco de dados:

```bash
# Ver tamanho
du -h /home/scalp/memory/*.db

# Backup
cp /home/scalp/memory/memory.db /home/scalp/memory/backup_$(date +%Y%m%d).db

# Ver estrutura SQLite
sqlite3 /home/scalp/memory/memory.db ".schema"
```

### Logs:

```bash
# Logs do memory server (se houver)
tail -f /home/scalp/memory/memory_server.log

# Logs do script de automação (se rodando como serviço)
journalctl -u cursor-memory-sync.service -f
```

---

## 🆘 Troubleshooting

### ❌ "command not found: memory"

```bash
# Recriar o link simbólico
sudo ln -sf /home/scalp/memory-cli.sh /usr/local/bin/memory
```

### ❌ Cursor não mostra ferramentas MCP

1. Feche o Cursor completamente
2. Verifique a config:
```bash
cat /root/.cursor/mcp.json | jq
```
3. Reinicie o Cursor
4. No chat, digite: "Liste as ferramentas MCP disponíveis"

### ❌ Erro ao salvar nota

```bash
# Verificar se o diretório existe
ls -la /home/scalp/memory/

# Verificar permissões
chmod 755 /home/scalp/memory/
chmod 644 /home/scalp/memory/*.db

# Testar cliente diretamente
python /home/scalp/mcp_memory_client.py list-tools
```

### ❌ Sincronização não está funcionando

```bash
# Testar manualmente
python /home/scalp/cursor_memory_auto.py scan

# Ver se há erros
python /home/scalp/cursor_memory_auto.py scan 2>&1 | less

# Verificar diretório de chats do Cursor
ls -la /root/.cursor/chats/
```

---

## 🎯 Resumo de Comandos

| **Ação** | **Comando** |
|----------|-------------|
| Salvar nota | `memory save "texto"` |
| Buscar | `memory search "query"` |
| Ler tudo | `memory read` |
| Sincronizar Cursor | `memory sync` |
| Monitorar contínuo | `memory watch 300` |
| Testar sistema | `./testar_memoria_completa.sh` |
| Ver ajuda | `memory help` |

---

## 📚 Referências

- **Memory Server**: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- **Mem0**: https://github.com/mem0ai/mem0
- **MCP Protocol**: https://modelcontextprotocol.io/

---

## 🎉 Próximos Passos

1. **Testar o sistema:**
```bash
./testar_memoria_completa.sh
```

2. **Salvar sua primeira nota:**
```bash
memory save "Sistema de memória configurado em $(date)"
```

3. **No Cursor, pedir para salvar algo:**
```
"Salve na memória: Sistema configurado e funcionando!"
```

4. **Buscar para confirmar:**
```bash
memory search "configurado"
```

---

**Criado em:** 2025-11-12  
**Versão:** 2.0  
**Status:** ✅ Totalmente funcional
