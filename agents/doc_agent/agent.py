from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from agents.common.base_agent import BaseAgent


@dataclass
class FileDoc:
    path: Path
    role: str
    inputs: List[str]
    outputs: List[str]
    deps: List[str]
    risks: List[str]


class DocAgent(BaseAgent):
    """
    Agente responsável por gerar documentação estruturada
    a partir de arquivos de código / scripts.
    """

    def run(self) -> List[FileDoc]:
        files = [p for p in self.project_root.rglob("*.py") if p.is_file()]
        docs: List[FileDoc] = []
        for path in files:
            docs.append(self._document_single_file(path))
        return docs

    def _document_single_file(self, path: Path) -> FileDoc:
        role = self._guess_role(path)
        return FileDoc(
            path=path,
            role=role,
            inputs=[],
            outputs=[],
            deps=[],
            risks=[],
        )

    def _guess_role(self, path: Path) -> str:
        name = path.name.lower()
        if "backtest" in name:
            return "Script de execução de backtest"
        if "train" in name or "treinar" in name:
            return "Script de treino de modelo"
        if "orchestrator" in name:
            return "Orquestrador de pipelines"
        return "Arquivo de código / script (papel ainda não analisado)"

    def to_markdown(self, docs: List[FileDoc]) -> str:
        lines: List[str] = ["# Documentação de arquivos\n"]
        for d in docs:
            lines.append(f"## `{d.path}`")
            lines.append(f"- Papel: {d.role}")
            if d.inputs:
                lines.append(f"- Entradas: {', '.join(d.inputs)}")
            if d.outputs:
                lines.append(f"- Saídas: {', '.join(d.outputs)}")
            if d.deps:
                lines.append(f"- Dependências: {', '.join(d.deps)}")
            if d.risks:
                lines.append(f"- Riscos: {', '.join(d.risks)}")
            lines.append("")
        return "\n".join(lines)
