from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from agents.common.base_agent import BaseAgent


@dataclass
class MoveAction:
    src: Path
    dst: Path
    reason: str


@dataclass
class ExecutionPlan:
    base_dir: Path
    moves: List[MoveAction]

    def pretty(self) -> str:
        lines = ["Plano de execução:\n"]
        for m in self.moves:
            lines.append(f"- {m.src} -> {m.dst}  ({m.reason})")
        return "\n".join(lines)


class ExecutorAgent(BaseAgent):
    """
    Agente que aplica um plano de reorganização
    (mover arquivos para uma nova estrutura).
    """

    def run(self) -> Dict[str, List[Dict[str, str]]]:
        manifest_path = self.config.get("manifest_path")
        if not manifest_path:
            raise ValueError("manifest_path não fornecido na config.")

        manifest = self._load_manifest(Path(manifest_path))
        plan = self.build_plan_from_manifest(manifest)

        dry_run = self.config.get("dry_run", True)
        self.execute_plan(plan, dry_run=dry_run)

        return {
            "moves": [
                {
                    "src": str(m.src),
                    "dst": str(m.dst),
                    "reason": m.reason,
                }
                for m in plan.moves
            ]
        }

    def _load_manifest(self, path: Path) -> Dict:
        import json
        return json.loads(path.read_text(encoding="utf-8"))

    def build_plan_from_manifest(self, manifest: Dict) -> ExecutionPlan:
        moves: List[MoveAction] = []
        for item in manifest.get("ntp_core_files", []):
            src = self.project_root / item["path"]
            dst = (
                self.project_root / "projects" / "ntp" / "core" / Path(item["path"]).name
            )
            moves.append(
                MoveAction(src=src, dst=dst, reason=item.get("reason", "NTP_CORE"))
            )
        for item in manifest.get("ntp_support_files", []):
            src = self.project_root / item["path"]
            dst = (
                self.project_root
                / "projects"
                / "ntp"
                / "support"
                / Path(item["path"]).name
            )
            moves.append(
                MoveAction(src=src, dst=dst, reason=item.get("reason", "NTP_SUPPORT"))
            )
        return ExecutionPlan(base_dir=self.project_root, moves=moves)

    def execute_plan(self, plan: ExecutionPlan, dry_run: bool = True) -> None:
        for action in plan.moves:
            action.dst.parent.mkdir(parents=True, exist_ok=True)
            if dry_run:
                print(f"[DRY-RUN] mover {action.src} -> {action.dst} ({action.reason})")
            else:
                print(f"Movendo {action.src} -> {action.dst} ({action.reason})")
                shutil.move(str(action.src), str(action.dst))
