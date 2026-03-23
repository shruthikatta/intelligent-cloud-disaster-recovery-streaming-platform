from __future__ import annotations

"""
Mock ED-LSTM inference: lightweight numpy extrapolation when TF model absent.
Replaced by TensorFlow adapter in production path when model file exists.
"""


import math
from typing import Any


class MockModelInferenceAdapter:
    async def predict(self, window: list[list[float]]) -> dict[str, Any]:
        if not window:
            return {"error": "empty window", "anomaly": False}
        last = window[-1]
        # naive next step: damped continuation
        pred = [x * 1.02 + 0.01 * math.sin(len(window)) for x in last]
        err = sum(abs(a - b) for a, b in zip(last, pred)) / max(len(last), 1)
        threshold = 0.25
        return {
            "predicted_next": pred,
            "mean_abs_error": err,
            "anomaly": err > threshold,
            "threshold": threshold,
            "backend": "mock_numpy",
        }
