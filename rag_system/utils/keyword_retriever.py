"""Very small keyword retriever that shells out to ripgrep."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List


class KeywordRetriever:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        token = self._select_token(query)
        if not token:
            return []
        try:
            cmd = [
                "rg",
                "--json",
                "-n",
                "-m",
                str(limit * 3),
                "--no-heading",
                token,
                str(self.project_root),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return []
        results: List[Dict] = []
        for line in proc.stdout.splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("type") != "match":
                continue
            data = payload.get("data", {})
            path = data.get("path", {}).get("text")
            line_number = data.get("line_number")
            line_text = data.get("lines", {}).get("text", "").strip()
            if not path or not line_text:
                continue
            snippet = f"# File: {Path(path).relative_to(self.project_root)}:{line_number}\n{line_text}"
            results.append(
                {
                    "id": f"keyword::{path}:{line_number}",
                    "content": snippet,
                    "metadata": {
                        "path": str(Path(path).relative_to(self.project_root)),
                        "line": line_number,
                        "source": "keyword",
                    },
                    "score": 0.6,
                }
            )
            if len(results) >= limit:
                break
        return results

    def _select_token(self, query: str) -> str | None:
        tokens = [t for t in re.split(r"[^A-Za-z0-9_]+", query) if len(t) > 3]
        tokens.sort(key=len, reverse=True)
        return tokens[0] if tokens else None
