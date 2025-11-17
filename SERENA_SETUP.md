# Serena - Configuração e Uso

## ✅ Status da Instalação

- **Serena instalado**: via `uvx` (sem precisar clonar repo)
- **Projeto indexado**: 428 arquivos Python/TypeScript
- **Contexto customizado**: `trading-bot` (foco em backtesting e estratégias)
- **Integração MCP**: Configurado no Cursor (`/root/.cursor/mcp.json`)

---

## 📋 Arquivos de Configuração

### 1. Projeto Principal
```
/home/scalp/.serena/project.yml
```
- Linguagens: Python, TypeScript
- Encoding: UTF-8
- Respeita `.gitignore`: ✅
- Read-only: ❌

### 2. Contexto Customizado
```
/root/.serena/contexts/trading-bot.yml
```
**Prompt do contexto:**
> Expert em trading systems, foco em backtesting, market microstructure analysis e walk-forward optimization. Sempre usa ferramentas simbólicas (LSP) antes de modificar código.

### 3. Cache de Símbolos LSP
```
/home/scalp/.serena/cache/python/document_symbols_cache_v23-06-25.pkl
/home/scalp/.serena/cache/typescript/document_symbols_cache_v23-06-25.pkl
```

---

## 🔗 Integração com Memórias mem0

### Sincronizar Memórias do mem0 para Serena
```bash
# Sincronizar todas as memórias
serena sync

# Filtrar por palavra-chave
serena sync --filter "WF"

# Limitar quantidade
serena sync --limit 10
```

**O que acontece:**
- Busca entidades do mem0 via MCP
- Converte para formato de memórias do Serena
- Salva em `/root/.serena/memories/scalp/`
- Serena pode usar `read_memory` / `list_memories` para acessar

**Quando sincronizar:**
- Após fazer mudanças importantes no sistema
- Antes de pedir ao Serena para "lembrar" de algo específico
- Semanalmente para manter sincronizado

---

## 🚀 Comandos Principais

### Iniciar Servidor MCP (STDIO)
```bash
uvx --from git+https://github.com/oraios/serena serena start-mcp-server \
  --project /home/scalp \
  --context trading-bot \
  --mode interactive \
  --mode editing \
  --transport stdio
```

### Re-indexar Projeto (após mudanças grandes)
```bash
cd /home/scalp
uvx --from git+https://github.com/oraios/serena serena project index /home/scalp
```

### Health Check do Projeto
```bash
uvx --from git+https://github.com/oraios/serena serena project health-check /home/scalp
```

### Listar Ferramentas Disponíveis
```bash
uvx --from git+https://github.com/oraios/serena serena tools list
```

### Gerenciar Contextos
```bash
# Listar contextos
uvx --from git+https://github.com/oraios/serena serena context list

# Editar contexto customizado
uvx --from git+https://github.com/oraios/serena serena context edit trading-bot
```

---

## 🔧 Integração com Cursor

O Serena está configurado em `/root/.cursor/mcp.json`:

```json
{
  "serena": {
    "command": "/root/.local/bin/uvx",
    "args": [
      "--from", "git+https://github.com/oraios/serena",
      "serena", "start-mcp-server",
      "--project", "/home/scalp",
      "--context", "trading-bot",
      "--mode", "interactive",
      "--mode", "editing",
      "--transport", "stdio"
    ]
  }
}
```

**Para ativar:**
1. Reinicie o Cursor completamente
2. Abra o chat (Cmd/Ctrl+L)
3. Pergunte: "Liste as ferramentas MCP disponíveis"
4. Você verá: `serena` com ~27 ferramentas

---

## 🛠️ Ferramentas Principais do Serena

### Navegação de Código (LSP-based)
- `find_symbol`: Busca global de símbolos (classes, funções, etc.)
- `find_referencing_symbols`: Encontra onde um símbolo é usado
- `get_symbols_overview`: Overview de símbolos em um arquivo

### Edição de Código
- `replace_symbol_body`: Substitui definição de uma função/classe
- `insert_after_symbol` / `insert_before_symbol`: Inserção precisa
- `rename_symbol`: Refatoração segura (renomeia em toda base)

### Contexto e Memória
- `write_memory`: Salva nota para futuras conversas
- `read_memory` / `list_memories`: Recupera notas salvas
- `onboarding`: Analisa estrutura do projeto (primeira vez)

### Análise e Busca
- `search_for_pattern`: Busca por regex no projeto
- `find_file`: Localiza arquivos por nome
- `execute_shell_command`: Executa comandos (pytest, etc.)

---

## 💡 Exemplos de Uso no Cursor

### 1. Encontrar onde `RSIStrategy` é usado
```
Usuário: "Use find_symbol para localizar a classe RSIStrategy"
Cursor: [retorna definição completa com caminho e linha]

Usuário: "Agora encontre todas as referências a RSIStrategy"
Cursor: [usa find_referencing_symbols, lista todos os imports/usos]
```

### 2. Refatorar uma função
```
Usuário: "Use get_symbols_overview em backtest_integration.py"
Cursor: [lista funções: run_backtest, calculate_metrics, etc.]

Usuário: "Substitua o corpo da função run_backtest para adicionar logging detalhado"
Cursor: [usa replace_symbol_body com novo código]
```

### 3. Buscar padrões no código
```
Usuário: "Busque todas as ocorrências de 'TODO' nos arquivos Python"
Cursor: [usa search_for_pattern com regex TODO.*]
```

### 4. Salvar decisões importantes
```
Usuário: "Salve na memória: RSI oversold threshold mudado de 30 para 25 após análise de sensibilidade"
Cursor: [usa write_memory, cria nota permanente no projeto]
```

---

## 📊 Dashboard Web (opcional)

Quando o servidor MCP está rodando, acesse:
```
http://127.0.0.1:24282/dashboard/index.html
```

Mostra:
- Ferramentas ativas
- Projeto carregado
- Modos ativos (interactive, editing)
- Logs em tempo real

---

## 🔄 Atualizar Serena

```bash
# uvx sempre busca a versão mais recente do GitHub
uvx --from git+https://github.com/oraios/serena serena --help
```

Não precisa reinstalar, `uvx` gerencia cache automaticamente.

---

## 🐛 Troubleshooting

### Problema: "Language server timeout"
**Solução:** Re-indexe o projeto
```bash
uvx --from git+https://github.com/oraios/serena serena project index /home/scalp
```

### Problema: Serena não aparece no Cursor
**Solução:**
1. Verifique `/root/.cursor/mcp.json` (sem erros de sintaxe)
2. Reinicie Cursor **completamente** (feche todas as janelas)
3. Verifique logs: `/root/.serena/logs/`

### Problema: "Symbol not found"
**Solução:** O LSP pode não ter indexado o arquivo ainda
```bash
# Indexar arquivo específico
uvx --from git+https://github.com/oraios/serena serena project index-file /home/scalp/core/strategy.py
```

### Problema: Edições não aplicando
**Solução:** Reinicie o language server
```
Usuário no Cursor: "Use restart_language_server"
```

---

## 📚 Documentação Oficial

- GitHub: https://github.com/oraios/serena
- Discord: (verificar no repo)
- CLI Help: `uvx --from git+https://github.com/oraios/serena serena --help`

---

## 🎯 Próximos Passos Sugeridos

1. **Teste no Cursor**: Reinicie e peça para listar ferramentas MCP
2. **Primeiro onboarding**: No Cursor, pergunte "Faça onboarding do projeto"
3. **Experimente navegação simbólica**: "Encontre a função calculate_sharpe_ratio"
4. **Salve uma memória**: "Salve na memória: iniciando uso do Serena em 2025-11-13"

---

**Status:** ✅ Serena 100% configurado e pronto para uso!
