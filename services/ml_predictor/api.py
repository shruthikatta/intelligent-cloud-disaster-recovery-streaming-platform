from __future__ import annotations

"""Optional standalone FastAPI service for ML inference (port 8001)."""


from fastapi import FastAPI
from pydantic import BaseModel, Field

from cloud_adapters.dependency_factory import get_model_inference_adapter

app = FastAPI(title="StreamVault ML Predictor", version="1.0.0")


class PredictRequest(BaseModel):
    window: list[list[float]] = Field(..., description="Shape: (lookback, features)")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ml-predictor"}


@app.post("/predict")
async def predict(req: PredictRequest) -> dict:
    adapter = get_model_inference_adapter()
    return await adapter.predict(req.window)
