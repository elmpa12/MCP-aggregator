"""Lightweight reader for Serena's symbol caches (code navigation)."""

from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class SerenaSymbol:
    """Convenience container for a Serena symbol entry."""

    name: str
    full_name: str
    kind: int
    file_path: Path
    relative_path: str
    start_line: int
    end_line: int

    @property
    def name_lower(self) -> str:
        return self.name.lower()

    @property
    def full_name_lower(self) -> str:
        return self.full_name.lower()

    @property
    def path_lower(self) -> str:
        return self.relative_path.lower()


class SerenaCodeIndex:
    """Loads Serena's cached LSP symbols for fast code retrieval."""

    def __init__(
        self,
        project_root: Path,
        cache_root: Optional[Path] = None,
        max_symbols: Optional[int] = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.cache_root = cache_root or Path.home() / ".serena" / "cache"
        self.symbols: List[SerenaSymbol] = []
        self._loaded = False
        self.max_symbols = max_symbols
        self._load_caches()

    # ------------------------------------------------------------------
    def available(self) -> bool:
        return self._loaded and bool(self.symbols)

    def search(self, queries: Sequence[str], limit: int = 20) -> List[Dict]:
        if not self.available() or not queries:
            return []

        tokens = self._tokenize(queries)
        if not tokens:
            return []

        scored: List[Tuple[float, SerenaSymbol]] = []
        for sym in self.symbols:
            score = self._score_symbol(sym, tokens)
            if score > 0:
                scored.append((score, sym))

        scored.sort(key=lambda item: item[0], reverse=True)

        results: List[Dict] = []
        for score, sym in scored[:limit]:
            snippet = self._read_snippet(sym)
            if not snippet:
                continue
            results.append(
                {
                    "id": f"serena::{sym.relative_path}:{sym.start_line + 1}",
                    "content": snippet,
                    "source": "serena_code",
                    "metadata": {
                        "path": sym.relative_path,
                        "start_line": sym.start_line + 1,
                        "end_line": sym.end_line + 1,
                        "symbol": sym.full_name,
                        "score": round(score, 3),
                    },
                }
            )

        return results

    # ------------------------------------------------------------------
    def _load_caches(self) -> None:
        if not self.cache_root.exists():
            self._loaded = True
            return

        cache_files = sorted(self.cache_root.rglob("document_symbols_cache_*.pkl"))
        if not cache_files:
            self._loaded = True
            return

        for cache_path in cache_files:
            try:
                with cache_path.open("rb") as fh:
                    data = pickle.load(fh)
            except Exception:
                continue

            for _, payload in data.items():
                if not isinstance(payload, tuple) or len(payload) < 2:
                    continue
                symbols = payload[1]
                for symbol in symbols:
                    self._collect_symbol(symbol, parent_stack=[])
                    if self.max_symbols and len(self.symbols) >= self.max_symbols:
                        self._loaded = True
                        return

        self._loaded = True

    def _collect_symbol(self, symbol: Dict, parent_stack: List[str]) -> None:
        name = symbol.get("name")
        loc = symbol.get("location") or {}
        rel_path = loc.get("relativePath")
        abs_path = loc.get("absolutePath")
        rng = symbol.get("range") or {}
        start = rng.get("start", {})
        end = rng.get("end", {})

        if not (name and rel_path and abs_path):
            # Some nodes (e.g. variables) may miss proper location info
            pass
        else:
            entry = SerenaSymbol(
                name=name,
                full_name="/".join(parent_stack + [name]) if parent_stack else name,
                kind=int(symbol.get("kind", 0)),
                file_path=Path(abs_path),
                relative_path=rel_path,
                start_line=int(start.get("line", 0)),
                end_line=int(end.get("line", start.get("line", 0))),
            )
            self.symbols.append(entry)

        for child in symbol.get("children", []) or []:
            self._collect_symbol(child, parent_stack + [name] if name else parent_stack)

    # ------------------------------------------------------------------
    def _tokenize(self, queries: Sequence[str]) -> List[str]:
        tokens: List[str] = []
        splitter = re.compile(r"[^a-zA-Z0-9_]+")
        for query in queries:
            if not query:
                continue
            parts = [p for p in splitter.split(query.lower()) if p]
            tokens.extend(parts)
        # Deduplicate preserving order
        seen = set()
        unique = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique.append(token)
        return unique

    def _score_symbol(self, symbol: SerenaSymbol, tokens: Iterable[str]) -> float:
        score = 0.0
        for token in tokens:
            if token in symbol.name_lower:
                score += 3.0
            elif token in symbol.full_name_lower:
                score += 2.0
            elif token in symbol.path_lower:
                score += 1.0
        return score

    def _read_snippet(self, symbol: SerenaSymbol, context_lines: int = 8) -> Optional[str]:
        try:
            text = symbol.file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        lines = text.splitlines()
        start = max(0, symbol.start_line - context_lines)
        end = min(len(lines), symbol.end_line + context_lines + 1)

        snippet_lines = lines[start:end]
        header = f"# File: {symbol.relative_path}:{start + 1}-{end}\n"
        body = "\n".join(snippet_lines)
        return f"{header}{body}"
