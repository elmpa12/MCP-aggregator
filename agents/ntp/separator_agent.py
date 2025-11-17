from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal

from agents.common.base_agent import BaseAgent

Category = Literal["NTP_CORE", "NTP_SUPPORT", "OTHER"]


@dataclass
class FileClassification:
    path: Path
    category: Category
    reason: str


class NTPSepAgent(BaseAgent):
    """
    Agente responsável por analisar o repo e separar o que é NTP do restante.
    Não move nem altera arquivos: só gera um plano.
    """

    def run(self) -> dict:
        ntp_core: List[FileClassification] = []
        ntp_support: List[FileClassification] = []
        others: List[FileClassification] = []

        for path in self._iter_candidate_files():
            classification = self._classify_file(path)
            if classification.category == "NTP_CORE":
                ntp_core.append(classification)
            elif classification.category == "NTP_SUPPORT":
                ntp_support.append(classification)
            else:
                others.append(classification)

        return {
            "ntp_core_files": [self._serialize(c) for c in ntp_core],
            "ntp_support_files": [self._serialize(c) for c in ntp_support],
            "other_files": [self._serialize(c) for c in others],
        }

    def _iter_candidate_files(self):
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in {".py", ".ipynb", ".sh", ".yaml", ".yml", ".json"}:
                yield path

    def _classify_file(self, path: Path) -> FileClassification:
        """
        Regra simples inicial:
        - se caminho/nome contém 'ntp' -> NTP_CORE
        - se está em pastas compartilhadas mas referenciado por NTP (vamos ajustar depois) -> NTP_SUPPORT
        - senão -> OTHER
        """
        lower = str(path).lower()

        if "ntp" in lower:
            return FileClassification(
                path=path,
                category="NTP_CORE",
                reason="Nome/caminho contém 'ntp' (heurística inicial).",
            )

        return FileClassification(
            path=path,
            category="OTHER",
            reason="Não identificado como NTP no nome/caminho.",
        )

    @staticmethod
    def _serialize(c: FileClassification) -> Dict[str, Any]:
        return {"path": str(c.path), "category": c.category, "reason": c.reason}
