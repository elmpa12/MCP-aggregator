# 🧠 RAG Usage Policy for Agents

## 🎯 Objetivo
Garantir que todo agente utilize o **Advanced RAG v2** como fonte primária de contexto e somente recorra ao Serena quando precisar navegar/editar código com precisão cirúrgica.

## ✅ Fluxo Recomendado
1. **Perguntas gerais, status, histórico, arquitetura, decisões** → sempre execute:
   ```bash
   rag ask "sua pergunta"
   ```
2. **Precisa de códigos específicos ou refactors** → use Serena *depois* de entender o contexto pelo RAG.
3. **Atualize o contexto antes de grandes mudanças**:
   ```bash
   rag update          # sincroniza memórias + arquivos
   rag distill         # gera cartas/resumos das sessões
   ```

## 🚦 Regras
- 📚 **RAG primeiro**: não abra Serena para "lembrar" algo – faça uma consulta ao RAG.
- 🧩 **Serena**: use apenas para localizar símbolos, editar ou aplicar refactors. Cite no commit que a decisão veio do RAG.
- 🔄 **Após mudanças grandes**: rode `rag update` para manter embeddings frescos.
- 🧪 **Antes de deploys**: pergunte ao RAG *"O que foi feito recentemente em <área>?"* para revisar riscos.

## 🔍 Exemplos
```bash
rag ask "Qual o status do selector21?"
rag ask "Quais aprendizados estão em SESSION_PROGRESS.md?"
rag ask "Onde está documentado o auto_evolution_system?"
```

## 🧰 Alias (sugestão)
Adicione no shell:
```bash
alias ragask='python rag_system/rag_cli_v2.py ask'
```

## 📎 Onde Documentar
- Cite este arquivo em `.claude-config`, PROMPTs ou memórias compartilhadas.
- Resuma a política em novos PRs para educar outros agentes.

**Resumo**: RAG = memória institucional; Serena = bisturi de código. Use na ordem certa. ✅
