"""Simple entity graph helper used by Advanced RAG."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Entity:
    name: str
    type: str
    description: str
    documents: List[str]
    depends_on: List[str]
    feeds: List[str]
    tags: List[str]

    def serialize(self) -> str:
        doc_lines = "\n".join(f"- {doc}" for doc in self.documents)
        depends = ", ".join(self.depends_on) or "-"
        feeds = ", ".join(self.feeds) or "-"
        tags = ", ".join(self.tags)
        return (
            f"# Entity: {self.name} ({self.type})\n"
            f"Descrição: {self.description}\n"
            f"Depende de: {depends}\n"
            f"Alimenta: {feeds}\n"
            f"Tags: {tags}\n"
            f"Documentos:\n{doc_lines}\n"
        )


class EntityGraph:
    def __init__(self, config_path: Path) -> None:
        self.entities: List[Entity] = []
        self._load(config_path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        for ent in data.get("entities", []):
            self.entities.append(
                Entity(
                    name=ent.get("name", "unknown"),
                    type=ent.get("type", "node"),
                    description=ent.get("description", ""),
                    documents=ent.get("documents", []),
                    depends_on=ent.get("depends_on", []),
                    feeds=ent.get("feeds", []),
                    tags=ent.get("tags", []),
                )
            )

    def available(self) -> bool:
        return bool(self.entities)

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        if not self.entities:
            return []
        tokens = self._tokenize(query)
        scored: List[tuple[float, Entity]] = []
        for ent in self.entities:
            score = self._score(ent, tokens)
            if score > 0:
                scored.append((score, ent))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: List[Dict] = []
        for score, ent in scored[:limit]:
            results.append(
                {
                    "id": f"entity::{ent.name}",
                    "content": ent.serialize(),
                    "source": "entity_graph",
                    "metadata": {
                        "entity": ent.name,
                        "entity_type": ent.type,
                        "score": round(score, 3),
                    },
                }
            )
        return results

    def _tokenize(self, query: str) -> List[str]:
        tokens = [t for t in re.split(r"[^\w]+", query.lower()) if t]
        return tokens or [query.lower()]

    def _score(self, entity: Entity, tokens: List[str]) -> float:
        score = 0.0
        for token in tokens:
            if token in entity.name.lower():
                score += 2.0
            if token in entity.description.lower():
                score += 1.0
            if token in ",".join(entity.tags).lower():
                score += 1.5
        return score
