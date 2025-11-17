import json
import os
from typing import List

import httpx
import yaml
from mcp.server.fastmcp import FastMCPServer


def load_config() -> dict:
    """
    Carrega config de serviços.

    Caminho default:
      ~/falcom-mcp-suite/config/services.yaml
    ou sobrescrito por FALCOM_CONFIG.
    """
    cfg_path = os.environ.get(
        "FALCOM_CONFIG",
        os.path.expanduser("~/falcom-mcp-suite/config/services.yaml"),
    )
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
TALIB_URL = CONFIG["services"]["talib"]["url"].rstrip("/")

server = FastMCPServer("falcom-mcp-gateway")


async def _post_json(url: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


@server.tool(
    name="talib.rsi",
    description="Calcula RSI via serviço HTTP TA-LIB (lista de valores + período).",
)
async def talib_rsi(values: List[float], period: int = 14) -> str:
    payload = {"values": values, "period": period}
    data = await _post_json(f"{TALIB_URL}/indicator/rsi", payload)
    return json.dumps(
        {
            "indicator": "RSI",
            "period": period,
            "length": data.get("length"),
            "result": data.get("result"),
        }
    )


@server.tool(
    name="talib.ema",
    description="Calcula EMA via serviço HTTP TA-LIB (lista de valores + período).",
)
async def talib_ema(values: List[float], period: int = 14) -> str:
    payload = {"values": values, "period": period}
    data = await _post_json(f"{TALIB_URL}/indicator/ema", payload)
    return json.dumps(
        {
            "indicator": "EMA",
            "period": period,
            "length": data.get("length"),
            "result": data.get("result"),
        }
    )


@server.tool(
    name="utils.healthcheck",
    description="Verifica saúde do gateway e do serviço TA-LIB.",
)
async def healthcheck() -> str:
    result = {
        "gateway": "ok",
        "talib_service": None,
        "talib_url": TALIB_URL,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{TALIB_URL}/health")
            resp.raise_for_status()
            result["talib_service"] = resp.json()
    except Exception as e:
        result["talib_service"] = {"status": "error", "detail": str(e)}
    return json.dumps(result)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
