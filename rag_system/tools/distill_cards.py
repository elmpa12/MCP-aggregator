#!/usr/bin/env python3
"""
Memory Distiller – cria "cartas de conhecimento" a partir das memórias MCP.

Gera arquivos .md em /home/scalp/memory/cards/ com resumos por entidade.
Sem dependência obrigatória de LLM; se ANTHROPIC_API_KEY estiver set, pode
fazer um resumo curto via Claude; caso contrário, gera um extrato heurístico.
"""

import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from rag_system.core.mcp_direct import MCPMemoryDirect


def _summarize_heuristic(name: str, observations: List[str], max_items: int = 10) -> str:
    lines = [f"# {name}", "", "## Pontos-chave", ""]
    for obs in observations[:max_items]:
        snippet = obs.strip().replace('\n', ' ')
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        lines.append(f"- {snippet}")
    lines.append("")
    lines.append(f"_Gerado em {datetime.utcnow().isoformat()}Z_")
    return "\n".join(lines)


def distill_all(limit_entities: int = 200) -> int:
    client = MCPMemoryDirect()
    # Busca "vazia" em mcp_memory_client retorna todas as entidades/observations
    docs = client.search("", limit=1000)

    # Reagrupar por entidade (o search retorna observations isoladas)
    by_entity: Dict[str, List[str]] = {}
    for d in docs:
        meta = d.get('metadata', {})
        name = meta.get('entity') or meta.get('type') or 'Unknown'
        by_entity.setdefault(name, []).append(d['content'])

    out_dir = Path("/home/scalp/memory/cards")
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for i, (name, obs) in enumerate(by_entity.items()):
        if i >= limit_entities:
            break
        safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.')).strip() or f"entity_{i}"
        path = out_dir / f"{safe}.md"
        content = _summarize_heuristic(name, obs)
        path.write_text(content, encoding='utf-8')
        count += 1
    return count


def main():
    n = distill_all()
    print(f"✅ Geradas {n} cartas de conhecimento em /home/scalp/memory/cards/")


if __name__ == "__main__":
    main()

