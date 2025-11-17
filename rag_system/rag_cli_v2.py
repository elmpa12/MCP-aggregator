#!/usr/bin/env python3
"""
RAG CLI v2 - Interface for Truly Advanced RAG System
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional

# Add necessary paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

# Import the new Advanced RAG (avoid conflicts with packages named 'core')
try:
    from rag_system.core.advanced_rag_v2 import AdvancedRAGv2
    from rag_system.eval.quality_panel import run_quality_suite
except Exception:
    # Fallback if running from within package directory
    from core.advanced_rag_v2 import AdvancedRAGv2
    from eval.quality_panel import run_quality_suite

def print_banner():
    """Print fancy banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                        🚀 ADVANCED RAG v2.0 🚀                              ║
║                                                                              ║
║        Vector Search + Multi-Agent + Semantic Intelligence                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def _load_env_files(paths):
    """Lightweight .env loader to ensure permanent keys are picked up.
    Only sets variables that are not already present in the environment."""
    import os
    for p in paths:
        try:
            p = Path(p)
            if not p.exists():
                continue
            for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

def print_help():
    """Print help message"""
    print("""
📚 COMANDOS DISPONÍVEIS:

  rag ask "sua pergunta"       - Busca inteligente na base de conhecimento
  rag update                   - Atualiza o vector store com novos dados
  rag stats                    - Mostra estatísticas do sistema
  rag eval                     - Roda painel de qualidade (test suite)
  rag distill                  - Gera cartas de conhecimento a partir do Memory
  rag logs                     - Mostra últimos registros de execução
  rag help                     - Mostra esta mensagem

🔍 EXEMPLOS DE USO:

  rag ask "como funciona o walk-forward?"
  rag ask "qual o status da implementação do selector21?"
  rag ask "explique os problemas do _NPLR"
  
💡 DICAS:

  • O sistema agora usa busca SEMÂNTICA real com embeddings
  • Multi-agent paralelo para máxima cobertura
  • Temporal awareness para queries recentes
  • Respostas completas e detalhadas
  • Dica: salve sua chave em /home/scalp/.env (ANTHROPIC_API_KEY=...) para carregamento automático

⚙️  Flags globais:
  --project <nome>            - Nome lógico do projeto (default: scalp)
  --project-root <path>       - Raiz do projeto para ingestão local
  --suite <path>              - Caminho custom de test suite (para 'eval')
  --context-chars <N>         - Limite de contexto (chars) para resposta (default: 120000)
  --top-k <N>                 - Número de documentos pós re‑ranking (default: 40)
    """)

def format_answer(answer: str, confidence: float):
    """Format the answer with nice styling"""
    
    # Confidence color
    if confidence >= 80:
        conf_color = "\033[92m"  # Green
        conf_emoji = "🟢"
    elif confidence >= 50:
        conf_color = "\033[93m"  # Yellow
        conf_emoji = "🟡"
    else:
        conf_color = "\033[91m"  # Red
        conf_emoji = "🔴"
    
    reset = "\033[0m"
    
    # Print formatted answer
    print(f"\n{'─' * 80}")
    print(f"{conf_emoji} RESPOSTA (Confiança: {conf_color}{confidence:.0f}%{reset})")
    print(f"{'─' * 80}\n")
    print(answer)
    print(f"\n{'─' * 80}\n")

def main():
    """Main CLI entry point"""
    
    if len(sys.argv) < 2:
        print_banner()
        print_help()
        sys.exit(0)
    
    # Simple flag parsing for cross-project usage
    project_name = None
    project_root = None
    context_chars = None
    default_top_k = None
    suite_override = None
    filtered_argv = [sys.argv[0]]
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--project="):
            project_name = arg.split("=", 1)[1]
        elif arg == "--project" and i+1 < len(sys.argv):
            project_name = sys.argv[i+1]; i += 1
        elif arg.startswith("--project-root="):
            project_root = arg.split("=", 1)[1]
        elif arg == "--project-root" and i+1 < len(sys.argv):
            project_root = sys.argv[i+1]; i += 1
        elif arg.startswith("--suite="):
            suite_override = arg.split("=", 1)[1]
        elif arg.startswith("--context-chars="):
            context_chars = int(arg.split("=", 1)[1])
        elif arg == "--context-chars" and i+1 < len(sys.argv):
            context_chars = int(sys.argv[i+1]); i += 1
        elif arg.startswith("--top-k="):
            default_top_k = int(arg.split("=", 1)[1])
        elif arg == "--top-k" and i+1 < len(sys.argv):
            default_top_k = int(sys.argv[i+1]); i += 1
        else:
            filtered_argv.append(arg)
        i += 1

    sys.argv = filtered_argv
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "help"
    
    # Initialize RAG system
    try:
        # Ensure permanent keys are picked up before initializing
        _load_env_files([
            "/home/scalp/.env",
            str(current_dir.parent / ".env"),
            "/etc/environment.d/anthropic.conf",
            "/etc/profile.d/anthropic-api-key.sh",
        ])
        # Defaults
        if not project_name:
            project_name = os.environ.get("RAG_PROJECT", "scalp")
        if not project_root:
            project_root = os.environ.get("RAG_PROJECT_ROOT", str(Path.cwd()))
        rag = AdvancedRAGv2(project_name=project_name, project_root=project_root,
                            context_max_chars=context_chars, default_top_k=default_top_k)
    except Exception as e:
        print(f"❌ Erro ao inicializar RAG: {e}")
        print("\n💡 Verifique se:")
        print("  • ANTHROPIC_API_KEY está configurada (sugestão: /home/scalp/.env)")
        print("  • MCP Memory Server está rodando")
        print("  • Dependências instaladas (chromadb, sentence-transformers)")
        print("\n📁 Arquivos lidos automaticamente (se existirem):")
        print("  • /home/scalp/.env")
        print(f"  • {current_dir.parent / '.env'}")
        print("  • /etc/environment.d/anthropic.conf")
        print("  • /etc/profile.d/anthropic-api-key.sh")
        sys.exit(1)
    
    # Handle commands
    if command == "ask":
        if len(sys.argv) < 3:
            print("❌ Uso: rag ask \"sua pergunta\"")
            sys.exit(1)
        
        query = " ".join(sys.argv[2:])
        
        # Process query
        answer, confidence = rag.query(query)
        
        # Format and print answer
        format_answer(answer, confidence)
        
    elif command == "update":
        print("\n🔄 Atualizando vector store...")
        
        try:
            count_mcp = rag.update_vector_store()
            count_local = rag.update_local_knowledge()
            print(f"✅ Vector store atualizado: MCP={count_mcp} chunks, Local={count_local} chunks")
        except Exception as e:
            print(f"❌ Erro ao atualizar: {e}")
            sys.exit(1)
    
    elif command == "stats":
        print_banner()
        
        stats = rag.get_stats()
        
        print("📊 ESTATÍSTICAS DO SISTEMA:\n")
        print(f"  Vector Store:")
        print(f"    • Documentos: {stats['vector_store']['total_documents']}")
        print(f"    • Dimensão embeddings: {stats['vector_store']['embedding_model']}")
        print(f"    • Collection: {stats['vector_store']['collection_name']}")
        print()
        print(f"  Modelos:")
        print(f"    • LLM: {stats['claude_model']}")
        print(f"    • Re-ranker: {stats['reranker_model']}")
        print()
        print(f"  Status:")
        print(f"    • MCP Memory: {'✅ Disponível' if stats['mcp_available'] else '❌ Indisponível'}")
        print(f"    • Vector Search: ✅ Ativo")
        print(f"    • Multi-Agent: ✅ Ativo")
        print()
    
    elif command == "eval":
        # Run quality panel with default suite
        suite_path = Path(suite_override) if suite_override else (current_dir / "eval" / "test_suite.json")
        out_dir = current_dir.parent / "rag_eval_runs"
        try:
            out_file = run_quality_suite(rag, suite_path, out_dir)
            print(f"\n✅ Avaliação concluída. Log salvo em: {out_file}")
            # Also print quick summary
            data = json.loads(out_file.read_text(encoding='utf-8'))
            s = data['summary']
            print("\n📊 RESUMO (0–10):")
            print(f"  • Precisão:      {s['avg_precisao']}")
            print(f"  • Uso contexto:  {s['avg_uso_contexto']}")
            print(f"  • Alucinação:    {s['avg_alucinacao']}")
            print(f"  • Completude:    {s['avg_completude']}")
            # Ranking de prioridades: listar piores casos
            def avg_score(item):
                sc = item['scores']
                return (sc['precisao'] + sc['uso_contexto'] + sc['alucinacao'] + sc['completude']) / 4
            worst = sorted(data['results'], key=avg_score)[:3]
            print("\n🔧 TOP 3 – Onde melhorar primeiro:")
            for i, w in enumerate(worst, start=1):
                print(f"  {i}. {w['question']}  → média {avg_score(w):.2f}")
        except Exception as e:
            print(f"❌ Erro ao rodar avaliação: {e}")
            sys.exit(1)
    
    elif command == "distill":
        try:
            from rag_system.tools.distill_cards import distill_all
        except Exception:
            from tools.distill_cards import distill_all
        n = distill_all()
        print(f"\n✅ Cartas geradas: {n}")
        # Após distilar, atualizar vetor local
        try:
            count_local = rag.update_local_knowledge()
            print(f"✅ Vector store atualizado com {count_local} chunks das cartas")
        except Exception as e:
            print(f"⚠️  Falha ao atualizar vetor com cartas: {e}")

    elif command == "logs":
        logs_file = current_dir.parent / 'logs' / 'rag_runs.jsonl'
        if not logs_file.exists():
            print("ℹ️  Nenhum log encontrado ainda.")
        else:
            lines = logs_file.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
            tail = lines[-10:]
            print("\n📜 Últimos logs (jsonl):\n")
            for ln in tail:
                print(ln)

    elif command == "help":
        print_banner()
        print_help()
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("💡 Use 'rag help' para ver comandos disponíveis")
        sys.exit(1)

if __name__ == "__main__":
    main()
