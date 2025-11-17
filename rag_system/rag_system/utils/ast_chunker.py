"""
AST-based intelligent chunking for Python and TypeScript
Phase 4 Enhancement: Semantic code boundaries instead of arbitrary character splits
"""

from __future__ import annotations

import ast
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class ASTChunker:
    """
    Chunks code files using AST to preserve semantic boundaries.
    Much better than naive character-based chunking!
    """
    
    def __init__(self, max_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size
    
    def chunk_python(self, code: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Chunk Python code by functions, classes, and top-level statements"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback to line-based chunking
            return self._fallback_chunk(code, metadata, language='python')
        
        chunks = []
        lines = code.splitlines(keepends=True)
        
        for node in ast.iter_child_nodes(tree):
            chunk_meta = {**(metadata or {})}
            
            if isinstance(node, ast.FunctionDef):
                # Function definition
                start_line = node.lineno - 1
                end_line = node.end_lineno if node.end_lineno else start_line + 1
                chunk_code = ''.join(lines[start_line:end_line])
                
                chunk_meta.update({
                    'chunk_type': 'function',
                    'symbol_name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno
                })
                
                # Include decorators if present
                if node.decorator_list:
                    decorator_start = node.decorator_list[0].lineno - 1
                    chunk_code = ''.join(lines[decorator_start:end_line])
                    chunk_meta['line_start'] = decorator_start + 1
                
                chunks.append({
                    'content': chunk_code,
                    'metadata': chunk_meta
                })
            
            elif isinstance(node, ast.ClassDef):
                # Class definition - may need to split if large
                start_line = node.lineno - 1
                end_line = node.end_lineno if node.end_lineno else start_line + 1
                chunk_code = ''.join(lines[start_line:end_line])
                
                # If class is too large, chunk by methods
                if len(chunk_code) > self.max_chunk_size:
                    chunks.extend(self._chunk_class(node, lines, metadata))
                else:
                    chunk_meta.update({
                        'chunk_type': 'class',
                        'symbol_name': node.name,
                        'line_start': node.lineno,
                        'line_end': node.end_lineno or node.lineno
                    })
                    
                    chunks.append({
                        'content': chunk_code,
                        'metadata': chunk_meta
                    })
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # Group imports together
                pass  # Handled separately
            
            else:
                # Other top-level statements (assignments, etc.)
                start_line = node.lineno - 1
                end_line = node.end_lineno if node.end_lineno else start_line + 1
                chunk_code = ''.join(lines[start_line:end_line])
                
                if len(chunk_code.strip()) > 20:  # Skip trivial statements
                    chunk_meta.update({
                        'chunk_type': 'statement',
                        'line_start': node.lineno,
                        'line_end': node.end_lineno or node.lineno
                    })
                    
                    chunks.append({
                        'content': chunk_code,
                        'metadata': chunk_meta
                    })
        
        # Add imports as first chunk
        imports = self._extract_imports(tree, lines)
        if imports:
            chunks.insert(0, {
                'content': imports,
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': 'imports',
                    'line_start': 1
                }
            })
        
        return chunks
    
    def _chunk_class(self, class_node: ast.ClassDef, lines: List[str], 
                     metadata: Optional[Dict]) -> List[Dict]:
        """Split large class into chunks by methods"""
        chunks = []
        
        # Class header with docstring
        start_line = class_node.lineno - 1
        
        # Find first method
        first_method_line = None
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                first_method_line = item.lineno - 1
                break
        
        if first_method_line:
            header = ''.join(lines[start_line:first_method_line])
            chunks.append({
                'content': header,
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': 'class_header',
                    'symbol_name': class_node.name,
                    'line_start': class_node.lineno
                }
            })
        
        # Each method as separate chunk
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_start = node.lineno - 1
                method_end = node.end_lineno if node.end_lineno else method_start + 1
                method_code = ''.join(lines[method_start:method_end])
                
                chunks.append({
                    'content': method_code,
                    'metadata': {
                        **(metadata or {}),
                        'chunk_type': 'method',
                        'symbol_name': f"{class_node.name}.{node.name}",
                        'class_name': class_node.name,
                        'method_name': node.name,
                        'line_start': node.lineno,
                        'line_end': node.end_lineno or node.lineno
                    }
                })
        
        return chunks
    
    def _extract_imports(self, tree: ast.AST, lines: List[str]) -> str:
        """Extract all import statements"""
        import_lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if hasattr(node, 'lineno'):
                    import_lines.append(node.lineno - 1)
        
        if not import_lines:
            return ""
        
        # Get contiguous import block
        import_lines.sort()
        start = import_lines[0]
        end = import_lines[-1] + 1
        
        return ''.join(lines[start:end])
    
    def _fallback_chunk(self, code: str, metadata: Optional[Dict], 
                        language: str) -> List[Dict]:
        """Fallback to simple line-based chunking"""
        lines = code.splitlines(keepends=True)
        chunks = []
        
        chunk_lines = []
        chunk_size = 0
        
        for line in lines:
            chunk_lines.append(line)
            chunk_size += len(line)
            
            if chunk_size >= self.max_chunk_size:
                chunks.append({
                    'content': ''.join(chunk_lines),
                    'metadata': {
                        **(metadata or {}),
                        'chunk_type': 'fallback',
                        'language': language
                    }
                })
                chunk_lines = []
                chunk_size = 0
        
        # Add remaining
        if chunk_lines:
            chunks.append({
                'content': ''.join(chunk_lines),
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': 'fallback',
                    'language': language
                }
            })
        
        return chunks
    
    def chunk_file(self, file_path: Path) -> List[Dict]:
        """Chunk a file based on its extension"""
        suffix = file_path.suffix.lower()
        
        try:
            code = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return []
        
        metadata = {
            'path': str(file_path),
            'language': suffix[1:] if suffix else 'unknown'
        }
        
        if suffix == '.py':
            return self.chunk_python(code, metadata)
        # TypeScript support can be added here with a TS parser
        # elif suffix in ('.ts', '.tsx'):
        #     return self.chunk_typescript(code, metadata)
        else:
            # Fallback for non-Python files
            return self._fallback_chunk(code, metadata, suffix[1:])
