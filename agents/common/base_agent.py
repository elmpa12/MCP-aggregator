from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Interface base para todos os agentes.

    Cada agente recebe:
    - project_root: raiz do projeto naquele repo
    - config: dict com parâmetros específicos (se precisar)
    """

    def __init__(self, project_root: Path, config: Dict[str, Any] | None = None) -> None:
        self.project_root = project_root
        self.config = config or {}

    @abstractmethod
    def run(self) -> Any:
        """
        Executa a tarefa principal daquele agente.
        Deve retornar um resultado estruturado (manifesto, doc, plano, etc.)
        """
        raise NotImplementedError
