#!/usr/bin/env python3
"""
Sincroniza memórias do mem0/memory para Serena memories.

Uso:
    python sync_mem0_to_serena.py          # Sincroniza todas
    python sync_mem0_to_serena.py --filter "WF"  # Filtra por palavra-chave
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

from mcp_memory_client import MCPMemoryClient

SERENA_MEMORIES_DIR = Path("/root/.serena/memories")
PROJECT_NAME = "scalp"


def fetch_mem0_entities(filter_keyword: str = None) -> List[Dict[str, Any]]:
    """Busca entidades do mem0 via MCP client."""
    client = MCPMemoryClient()
    
    if filter_keyword:
        result = client.search_nodes(filter_keyword)
    else:
        result = client.read_graph()
    
    if not result or "entities" not in result:
        return []
    
    return result["entities"]


def write_serena_memory(name: str, content: str) -> bool:
    """Escreve memória no Serena via CLI."""
    try:
        # Serena espera chamada via MCP ou CLI especial
        # Por enquanto, vamos criar arquivos JSON diretamente
        memories_dir = SERENA_MEMORIES_DIR / PROJECT_NAME
        memories_dir.mkdir(parents=True, exist_ok=True)
        
        memory_file = memories_dir / f"{name}.json"
        memory_data = {
            "name": name,
            "content": content,
            "source": "mem0_sync"
        }
        
        memory_file.write_text(json.dumps(memory_data, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"❌ Erro ao escrever {name}: {e}")
        return False


def sync_memories(filter_keyword: str = None, limit: int = None) -> int:
    """Sincroniza memórias do mem0 para Serena."""
    print("📥 Buscando memórias do mem0...")
    entities = fetch_mem0_entities(filter_keyword)
    
    if not entities:
        print("⚠️  Nenhuma memória encontrada no mem0")
        return 0
    
    if limit:
        entities = entities[:limit]
    
    print(f"📦 Encontradas {len(entities)} entidade(s)")
    
    synced = 0
    for entity in entities:
        name = entity.get("name", "Unnamed")
        entity_type = entity.get("entityType", "Unknown")
        observations = entity.get("observations", [])
        
        # Criar conteúdo formatado
        content_lines = [
            f"Tipo: {entity_type}",
            "",
            "Observações:",
        ]
        
        for obs in observations[:5]:  # Limitar a 5 observações
            content_lines.append(f"- {obs}")
        
        content = "\n".join(content_lines)
        
        # Nome do arquivo (safe filename)
        safe_name = name.replace("/", "_").replace(" ", "_")[:100]
        
        if write_serena_memory(safe_name, content):
            synced += 1
            print(f"  ✅ {safe_name}")
    
    print(f"\n✅ {synced} memória(s) sincronizada(s) para Serena")
    print(f"📁 Localização: {SERENA_MEMORIES_DIR / PROJECT_NAME}")
    
    return synced


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sincroniza memórias do mem0 para Serena"
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Palavra-chave para filtrar memórias"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limite de memórias para sincronizar"
    )
    
    args = parser.parse_args()
    
    try:
        synced = sync_memories(
            filter_keyword=args.filter,
            limit=args.limit
        )
        return 0 if synced > 0 else 1
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
