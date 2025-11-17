#!/bin/bash
# Script tmux para uma sala de 6 painéis (3 linhas x 2 colunas)
# Cada CMD pode ser ajustado para o comando do respectivo agente.

SESSION="arena6"

# Comandos de exemplo para cada painel (ajuste conforme necessário)
CMD0="sgpt --chat"        # Painel 0 (topo/esquerda) – coordenador
CMD1="ragcli"             # Painel 1 (topo/direita) – servidor/CLI RAG
CMD2="claude"             # Painel 2 (meio/esquerda) – agente Claude ou outro LLM
CMD3="./ragload.sh"       # Painel 3 (fundo/esquerda) – BotScalp ou script de carga
CMD4="python agent4.py"   # Painel 4 (meio/direita) – outro agente ou serviço
CMD5=""                   # Painel 5 (fundo/direita) – terminal livre

# (Opcional) Finaliza sessão pré-existente com o mesmo nome
# tmux kill-session -t "$SESSION" 2>/dev/null

# Cria nova sessão e define o primeiro painel (0) com CMD0
tmux new-session -d -s "$SESSION" -n "$SESSION" "$CMD0"

# Divide o painel 0 em duas colunas, criando o painel 1 à direita com CMD1
tmux split-window -h -t "$SESSION:0.0" "$CMD1"

# Divide a coluna esquerda em duas linhas: cria o painel 2 (meio-esquerda) com CMD2
tmux split-window -v -t "$SESSION:0.0" "$CMD2"

# Divide novamente a coluna esquerda (painel 0.2) para criar o painel 3 (fundo/esquerda) com CMD3
tmux split-window -v -t "$SESSION:0.2" "$CMD3"

# Divide a coluna direita em duas linhas: cria o painel 4 (meio-direita) com CMD4
tmux split-window -v -t "$SESSION:0.1" "$CMD4"

# Divide novamente a coluna direita (painel 0.4) para criar o painel 5 (fundo/direita) com CMD5
tmux split-window -v -t "$SESSION:0.4" "$CMD5"

# Ativa modo mouse para redimensionar/navegar com o mouse
tmux set-option -g mouse on

# Entra na sessão
tmux attach-session -t "$SESSION"