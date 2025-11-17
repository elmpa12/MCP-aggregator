from fastapi import FastAPI, WebSocket
from pathlib import Path
from typing import Dict, Any

from agents.ntp.separator_agent import NTPSepAgent
from agents.doc_agent.agent import DocAgent
from agents.executor_agent.agent import ExecutorAgent

app = FastAPI(title="Falcom Orchestrator", version="0.1.0")

# Ajuste o caminho para o workspace conforme necessário; aqui usamos diretório atual
WORKSPACE = Path(".")

AGENTS = {
    "ntp": {
        "separator": NTPSepAgent,
        "doc": DocAgent,
        "executor": ExecutorAgent
    },
    # adicione outros projetos e agentes aqui
}


def run_agent(project: str, agent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    root = WORKSPACE / "projects" / project
    agent_cls = AGENTS[project][agent]
    instance = agent_cls(project_root=root, config=params)
    result = instance.run()
    return result


@app.post("/run")
async def run_agent_rest(payload: Dict[str, Any]):
    project = payload["project"]
    agent = payload["agent"]
    params = payload.get("params", {})
    output = run_agent(project, agent, params)
    return {
        "status": "ok",
        "agent": agent,
        "project": project,
        "output": output
    }


@app.websocket("/stream")
async def ws_run(websocket: WebSocket):
    await websocket.accept()
    payload = await websocket.receive_json()
    project = payload["project"]
    agent = payload["agent"]
    params = payload.get("params", {})

    await websocket.send_json({"event": "agent.start", "agent": agent})

    result = run_agent(project, agent, params)

    await websocket.send_json({"event": "agent.result", "output": result})
    await websocket.send_json({"event": "agent.end", "agent": agent})
    await websocket.close()
