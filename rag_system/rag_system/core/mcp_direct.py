"""
Direct MCP Memory Client for RAG
Uses existing mcp_memory_client.py exactly like memory-cli.sh does
"""

import json
import subprocess
import sys
import asyncio
from typing import List, Dict
from pathlib import Path


class MCPMemoryDirect:
    """Direct access to MCP Memory via mcp_memory_client.py"""
    
    def __init__(self):
        self.python_path = "/home/scalp/venv/bin/python"
        self.client_path = "/home/scalp/mcp_memory_client.py"
        
    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search memories using mcp_memory_client.py (same as memory CLI)
        
        Returns list of documents with content
        """
        try:
            # Call exactly like memory-cli.sh does
            result = subprocess.run(
                [self.python_path, self.client_path, "search", json.dumps({"query": query})],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"  ⚠️  MCP client returned error code: {result.returncode}")
                return []
            
            # Parse output - procurar pelo JSON final
            output = result.stdout
            
            # Remove ANSI codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean = ansi_escape.sub('', output)
            
            # Procurar pelo bloco JSON (começa com "✅ Resultados")
            if '✅' in clean:
                json_start = clean.find('{', clean.find('✅'))
                if json_start != -1:
                    json_str = clean[json_start:]
                    
                    try:
                        data = json.loads(json_str)
                        
                        # Extract documents from entities
                        docs = []
                        if 'entities' in data:
                            for entity in data['entities'][:limit]:
                                observations = entity.get('observations', [])
                                ent_name = entity.get('name', '')
                                ent_type = entity.get('entityType', '')
                                # Timestamps if available
                                ent_created = entity.get('createdAt') or entity.get('created_at')
                                ent_updated = entity.get('updatedAt') or entity.get('updated_at')
                                for obs in observations:
                                    if len(obs.strip()) > 100:
                                        docs.append({
                                            'content': obs,
                                            'score': 1.0,
                                            'metadata': {
                                                'entity': ent_name,
                                                'type': ent_type,
                                                'createdAt': ent_created,
                                                'updatedAt': ent_updated
                                            }
                                        })
                        
                        return docs[:limit]
                    except json.JSONDecodeError:
                        # JSON está truncado - extrair manualmente via regex
                        return self._extract_via_regex(clean, limit)
            
            return []
            
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  MCP search timeout (output muito grande)")
            # Timeout significa que encontrou mas output é muito grande
            # Tentar parsear o que conseguiu
            return []
        except Exception as e:
            print(f"  ⚠️  MCP search error: {e}")
            return []
    
    def _extract_via_regex(self, text: str, limit: int) -> List[Dict]:
        """Extract observations directly via regex when JSON is too large"""
        import re
        
        docs = []
        
        # Pattern: "observations": [ "conteúdo" ]
        # Capturar conteúdo entre aspas dentro de observations
        pattern = r'"observations":\s*\[\s*"((?:[^"\\]|\\.)*)"\s*(?:,|])'
        
        matches = re.findall(pattern, text[:500000])  # Limitar a 500KB para performance
        
        for match in matches[:limit]:
            # Decodificar escapes JSON
            content = match.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            
            if len(content) > 100:
                docs.append({
                    'content': content,
                    'score': 1.0,
                    'metadata': {'source': 'regex_extraction'}
                })
        
        return docs
    
    async def search_async(self, query: str, limit: int = 50) -> List[Dict]:
        """Async version of search to avoid blocking ThreadPoolExecutor."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.python_path, self.client_path, "search", 
                json.dumps({"query": query}),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            
            if proc.returncode != 0:
                return []
            
            output = stdout.decode('utf-8', errors='ignore')
            
            # Remove ANSI codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean = ansi_escape.sub('', output)
            
            # Procurar pelo bloco JSON
            if '✅' in clean:
                json_start = clean.find('{', clean.find('✅'))
                if json_start != -1:
                    json_str = clean[json_start:]
                    
                    try:
                        data = json.loads(json_str)
                        docs = []
                        if 'entities' in data:
                            for entity in data['entities'][:limit]:
                                observations = entity.get('observations', [])
                                ent_name = entity.get('name', '')
                                ent_type = entity.get('entityType', '')
                                ent_created = entity.get('createdAt') or entity.get('created_at')
                                ent_updated = entity.get('updatedAt') or entity.get('updated_at')
                                for obs in observations:
                                    if len(obs.strip()) > 100:
                                        docs.append({
                                            'content': obs,
                                            'score': 1.0,
                                            'metadata': {
                                                'entity': ent_name,
                                                'type': ent_type,
                                                'createdAt': ent_created,
                                                'updatedAt': ent_updated
                                            }
                                        })
                        return docs[:limit]
                    except json.JSONDecodeError:
                        return self._extract_via_regex(clean, limit)
            return []
        except asyncio.TimeoutError:
            return []
        except Exception:
            return []


# Test if running directly
if __name__ == "__main__":
    print("🧪 Testando MCPMemoryDirect...\n")
    
    client = MCPMemoryDirect()
    results = client.search("selector21", limit=3)
    
    print(f"✅ Encontrados: {len(results)} documentos\n")
    
    for i, doc in enumerate(results[:2]):
        print(f"[Doc {i+1}]")
        print(f"  Score: {doc.get('score', 0.0)}")
        print(f"  Preview: {doc['content'][:200]}...")
        print()
