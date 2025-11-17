"""Lightweight monitoring helpers for the Advanced RAG pipeline."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class RAGMonitor:
    """Append query runs to jsonl logs and maintain aggregated metrics."""

    def __init__(self, project_name: str, logs_dir: Path) -> None:
        self.project_name = project_name
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / "rag_runs.jsonl"
        self.metrics_file = self.logs_dir / "rag_metrics.json"

    def log_run(self, run_data: Dict[str, Any]) -> None:
        """Append a run entry and update aggregate metrics."""

        entry = {
            "ts": run_data.get("timestamp") or datetime.utcnow().isoformat() + "Z",
            "project": run_data.get("project", self.project_name),
            "query": run_data.get("query", ""),
            "intent": run_data.get("intent", "general"),
            "retrieved": int(run_data.get("retrieved", 0)),
            "reranked": int(run_data.get("reranked", 0)),
            "context_chars": int(run_data.get("context_chars", 0)),
            "confidence": float(run_data.get("confidence", 0.0)),
            "elapsed_sec": float(run_data.get("elapsed_sec", 0.0)),
            "cache_hit": bool(run_data.get("from_cache", False)),
        }

        with self.log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        self._update_metrics(entry)

    # ------------------------------------------------------------------
    def _update_metrics(self, entry: Dict[str, Any]) -> None:
        metrics = self._load_metrics()
        metrics["total_runs"] += 1
        metrics["cache_hits"] += 1 if entry["cache_hit"] else 0
        metrics["sum_confidence"] += entry["confidence"]
        metrics["sum_elapsed_sec"] += entry["elapsed_sec"]
        metrics["sum_context_chars"] += entry["context_chars"]

        total = metrics["total_runs"] or 1
        metrics["avg_confidence"] = round(metrics["sum_confidence"] / total, 2)
        metrics["avg_elapsed_sec"] = round(metrics["sum_elapsed_sec"] / total, 2)
        metrics["avg_context_chars"] = int(metrics["sum_context_chars"] / total)
        metrics["cache_hit_rate"] = round(
            metrics["cache_hits"] / total, 2
        )
        metrics["updated_at"] = datetime.utcnow().isoformat() + "Z"

        self.metrics_file.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_metrics(self) -> Dict[str, Any]:
        if self.metrics_file.exists():
            try:
                data = json.loads(self.metrics_file.read_text(encoding="utf-8"))
                # Ensure required keys exist
                for key in (
                    "total_runs",
                    "cache_hits",
                    "sum_confidence",
                    "sum_elapsed_sec",
                    "sum_context_chars",
                ):
                    data.setdefault(key, 0)
                return data
            except Exception:
                pass

        return {
            "total_runs": 0,
            "cache_hits": 0,
            "sum_confidence": 0.0,
            "sum_elapsed_sec": 0.0,
            "sum_context_chars": 0,
            "avg_confidence": 0.0,
            "avg_elapsed_sec": 0.0,
            "avg_context_chars": 0,
            "cache_hit_rate": 0.0,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

