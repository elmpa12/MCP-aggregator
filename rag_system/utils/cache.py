"""Simple on-disk cache for Advanced RAG queries."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class QueryCache:
    """Small JSON-based cache for RAG query responses."""

    def __init__(
        self,
        cache_dir: Path,
        ttl_seconds: int = 900,
        max_entries: int = 256,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = max(0, int(ttl_seconds))
        self.max_entries = max(0, int(max_entries))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def make_key(self, **parts: Any) -> str:
        """Build a deterministic hash key based on the provided parts."""

        normalized = json.dumps(parts, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached payload if not expired."""

        path = self._entry_path(key)
        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink(missing_ok=True)
            return None

        ts = raw.get("ts", 0)
        ttl = raw.get("ttl", self.default_ttl)
        if ttl and (time.time() - ts) > ttl:
            path.unlink(missing_ok=True)
            return None

        return raw.get("payload")

    def set(self, key: str, payload: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Persist payload under key with timestamp and prune old entries."""

        if not self.max_entries:
            return

        record = {
            "ts": time.time(),
            "ttl": ttl if ttl is not None else self.default_ttl,
            "payload": payload,
        }

        path = self._entry_path(key)
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        self._prune()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _prune(self) -> None:
        files = sorted(
            self.cache_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for stale in files[self.max_entries :]:
            stale.unlink(missing_ok=True)
