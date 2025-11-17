# 🔄 Guia de Salvamento Automático de Contexto

## 📋 Visão Geral

Este guia mostra como configurar salvamento **100% automático** de todo o contexto de suas conversas e comandos, sem precisar fazer nada manualmente.

---

## ✅ O que Já Está Funcionando

### 1. **Cursor IDE** (Automático por padrão)

O Cursor **já salva automaticamente** tudo que é importante:

- ✅ Conversas no chat
- ✅ Decisões técnicas
- ✅ Código gerado/discutido
- ✅ Contexto entre sessões

**Você não precisa fazer nada!** O memory server já está ativo no Cursor.

---

## 🚀 Configurações Adicionais Opcionais

### Opção 1: Sincronização Periódica Manual

Para quando você quiser sincronizar conversas manualmente:

```bash
# Uma vez
memory sync

# Monitoramento contínuo (a cada 5 minutos)
memory watch 300

# Em background
nohup memory watch 300 > /tmp/memory-sync.log 2>&1 &
```

---

### Opção 2: Serviço Systemd (Recomendado para servidores) ⭐

**Instala uma vez e esquece!** Sincroniza automaticamente sempre.

#### Instalar:

```bash
sudo bash /home/scalp/instalar_servico_memoria.sh
```

Isso vai:
- ✅ Criar serviço systemd
- ✅ Configurar para iniciar no boot
- ✅ Sincronizar a cada 5 minutos automaticamente
- ✅ Reiniciar automaticamente se falhar

#### Gerenciar o serviço:

```bash
# Ver status
sudo systemctl status cursor-memory-sync

# Ver logs em tempo real
sudo journalctl -u cursor-memory-sync -f

# Parar
sudo systemctl stop cursor-memory-sync

# Iniciar
sudo systemctl start cursor-memory-sync

# Reiniciar
sudo systemctl restart cursor-memory-sync

# Desabilitar
sudo systemctl disable cursor-memory-sync
```

---

### Opção 3: Hook Bash Automático

Salva contexto **automaticamente** após comandos importantes (git commit, tests, etc).

#### Instalar:

```bash
bash /home/scalp/instalar_hook_auto.sh
```

#### Ativar (após instalar):

```bash
source ~/.bashrc
```

Ou simplesmente abra um novo terminal.

#### Como funciona:

O hook detecta comandos importantes e salva automaticamente:

```bash
# Você executa
git commit -m "Fix bug"

# Hook salva automaticamente:
# "Auto-save: git commit -m 'Fix bug' (exit: 0) @ 2025-11-12 16:45:30"

# Buscar depois
memory search "Auto-save"
```

#### Comandos que acionam salvamento:

- `git commit`
- `git merge`
- `git rebase`
- `python.*test`
- `pytest`
- `npm test`
- `cargo test`
- `make.*test`

#### Desinstalar hook:

```bash
sed -i '/# MEMORY AUTO-SAVE HOOK/,/# END MEMORY AUTO-SAVE HOOK/d' ~/.bashrc
```

---

## 🎯 Setup Recomendado (Completo)

Para **zero perda de contexto**, instale tudo:

```bash
# 1. Serviço systemd (sincronização periódica)
sudo bash /home/scalp/instalar_servico_memoria.sh

# 2. Hook bash (salvamento após comandos)
bash /home/scalp/instalar_hook_auto.sh
source ~/.bashrc
```

Com esse setup:

- ✅ Cursor salva conversas automaticamente (já ativo)
- ✅ Arquivos de chat sincronizados a cada 5 minutos
- ✅ Comandos importantes salvos automaticamente
- ✅ Zero intervenção manual necessária
- ✅ Contexto **NUNCA** perdido

---

## 📊 Comparação das Opções

| Método | Quando salva | O que salva | Automático? | Requer instalação? |
|--------|--------------|-------------|-------------|---------------------|
| **Cursor nativo** | Sempre | Conversas | ✅ SIM | ❌ JÁ ATIVO |
| **memory sync** | Manual | Chats Cursor | ❌ Manual | ❌ Não |
| **memory watch** | A cada 5min | Chats Cursor | ✅ Após iniciar | ❌ Não |
| **Systemd service** | A cada 5min | Chats Cursor | ✅ SIM | ✅ Uma vez |
| **Hook bash** | Após comandos | Outputs CLI | ✅ SIM | ✅ Uma vez |

---

## 🧪 Testar Configuração

### Testar Cursor (já funciona):

1. Abra o Cursor (Cmd/Ctrl + L)
2. Digite: "Salve na memória: teste de salvamento automático"
3. Digite: "Busque na memória: teste de salvamento"
4. ✅ Deve encontrar!

### Testar serviço systemd:

```bash
# Ver se está rodando
sudo systemctl status cursor-memory-sync

# Ver logs
sudo journalctl -u cursor-memory-sync -f

# Deve mostrar sincronizações a cada 5 minutos
```

### Testar hook bash:

```bash
# Executar comando que aciona hook
git commit -m "test" --allow-empty

# Buscar salvamento automático
memory search "Auto-save"

# Deve aparecer o commit que você fez
```

---

## 🔍 Verificar o que Está Sendo Salvo

```bash
# Ver últimas entradas
memory read | tail -50

# Ver quantas entradas
memory read | grep -c '"name"'

# Buscar por tipo
memory search "Auto-save"        # Salvamentos do hook
memory search "CLI_Note"         # Notas manuais do CLI
memory search "ImportedChat"     # Chats importados
memory search "CursorConversation"  # Conversas do Cursor (se usando sync)
```

---

## 💡 Dicas de Uso

### Para máxima cobertura:

```bash
# 1. Instalar ambos
sudo bash /home/scalp/instalar_servico_memoria.sh
bash /home/scalp/instalar_hook_auto.sh
source ~/.bashrc

# 2. Verificar que estão ativos
sudo systemctl status cursor-memory-sync
grep "MEMORY AUTO-SAVE HOOK" ~/.bashrc

# 3. Testar
git commit -m "test" --allow-empty
memory search "Auto-save"
```

### Para servidores remotos:

```bash
# Usar apenas systemd (mais leve)
sudo bash /home/scalp/instalar_servico_memoria.sh

# Hook bash pode gerar muitas escritas
```

### Para desenvolvimento local:

```bash
# Usar ambos para máxima captura
sudo bash /home/scalp/instalar_servico_memoria.sh
bash /home/scalp/instalar_hook_auto.sh
```

---

## 🆘 Troubleshooting

### Serviço não está rodando:

```bash
# Ver erro
sudo journalctl -u cursor-memory-sync -n 50

# Reiniciar
sudo systemctl restart cursor-memory-sync

# Verificar se venv existe
ls -la /home/scalp/venv/bin/python
```

### Hook não está salvando:

```bash
# Verificar se está instalado
grep "MEMORY AUTO-SAVE HOOK" ~/.bashrc

# Recarregar
source ~/.bashrc

# Testar manualmente
memory save "teste manual"

# Ver se comando memory funciona
which memory
```

### Cursor não está salvando:

```bash
# Verificar config
cat /root/.cursor/mcp.json | grep memory

# Reiniciar Cursor completamente
# No chat do Cursor, pedir: "Liste ferramentas MCP"
# Deve aparecer: create_entities, search_nodes, etc.
```

---

## 🗑️ Desinstalar

### Remover serviço systemd:

```bash
sudo systemctl stop cursor-memory-sync
sudo systemctl disable cursor-memory-sync
sudo rm /etc/systemd/system/cursor-memory-sync.service
sudo systemctl daemon-reload
```

### Remover hook bash:

```bash
sed -i '/# MEMORY AUTO-SAVE HOOK/,/# END MEMORY AUTO-SAVE HOOK/d' ~/.bashrc
```

---

## 📚 Resumo

**Estado atual:**
- ✅ Cursor: salvamento automático ATIVO
- ⚙️ Systemd: opcional (instalar se quiser)
- ⚙️ Hook bash: opcional (instalar se quiser)

**Para setup completo:**
```bash
sudo bash /home/scalp/instalar_servico_memoria.sh
bash /home/scalp/instalar_hook_auto.sh
source ~/.bashrc
```

**Resultado:**
- 🎯 Zero perda de contexto
- 🤖 Tudo automático
- 🔍 Busca instantânea
- 💾 Memória infinita

---

**Criado em:** 2025-11-12  
**Scripts:** `/home/scalp/instalar_*.sh`  
**Status:** ✅ Pronto para usar
