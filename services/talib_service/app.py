from typing import List, Optional

import numpy as np
import talib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Falcom TA-LIB Service", version="0.1.0")


class SeriesPayload(BaseModel):
    values: List[float] = Field(..., description="Lista de valores numéricos (por exemplo, closes)")
    period: Optional[int] = Field(14, description="Período do indicador")


class IndicatorResponse(BaseModel):
    result: List[float]
    length: int


def _ensure_min_length(values: List[float], min_len: int) -> np.ndarray:
    if len(values) < min_len:
        raise HTTPException(
            status_code=400,
            detail=f"São necessários pelo menos {min_len} pontos. Recebidos: {len(values)}.",
        )
    return np.array(values, dtype=float)


@app.get("/health", tags=["meta"])
async def healthcheck() -> dict:
    return {"status": "ok", "service": "talib", "version": "0.1.0"}


@app.post("/indicator/rsi", response_model=IndicatorResponse, tags=["talib"])
async def indicator_rsi(payload: SeriesPayload) -> IndicatorResponse:
    values = _ensure_min_length(payload.values, min_len=payload.period + 1)
    try:
        rsi = talib.RSI(values, timeperiod=payload.period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular RSI: {e}")
    return IndicatorResponse(result=rsi.tolist(), length=len(rsi))


@app.post("/indicator/ema", response_model=IndicatorResponse, tags=["talib"])
async def indicator_ema(payload: SeriesPayload) -> IndicatorResponse:
    values = _ensure_min_length(payload.values, min_len=payload.period + 1)
    try:
        ema = talib.EMA(values, timeperiod=payload.period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular EMA: {e}")
    return IndicatorResponse(result=ema.tolist(), length=len(ema))
