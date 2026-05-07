from __future__ import annotations

"""SageMaker runtime invoke for hosted models."""

import json
from typing import Any

import numpy as np

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings
from shared.utils.timeutil import now_ms


class SageMakerInferenceAdapter:
    """Endpoint must accept JSON `{"instances": [window]}` and return JSON with a `predictions` field.

    Supported shapes for `predictions`:
    - List of rows: each row is one forecast timestep (length = n_features), e.g. ``(horizon, n_features)``.
    - Flat list: single timestep, length n_features.

    Optionally include top-level ``predicted_future`` mirroring local Keras output (list of lists).
    """

    def __init__(self, k_sigma: float = 3.0) -> None:
        self._runtime = get_client("sagemaker-runtime")
        self._endpoint = get_aws_settings().sagemaker_endpoint_name
        self._k = k_sigma
        self._error_history: list[float] = []

    async def predict(self, window: list[list[float]]) -> dict[str, Any]:
        if not self._endpoint:
            return {"error": "SAGEMAKER_ENDPOINT_NAME not set", "anomaly": False, "backend": "sagemaker"}

        payload = json.dumps({"instances": [window]})
        resp = self._runtime.invoke_endpoint(
            EndpointName=self._endpoint,
            ContentType="application/json",
            Accept="application/json",
            Body=payload.encode("utf-8"),
        )
        raw = resp["Body"].read().decode("utf-8")
        data = json.loads(raw)

        predicted_future = data.get("predicted_future")
        pred_vec, future_matrix = _parse_predictions(data.get("predictions"), predicted_future)

        if pred_vec.size == 0:
            return {
                "error": "could not parse predictions from endpoint response",
                "anomaly": False,
                "backend": "sagemaker",
                "raw": data,
            }

        last = np.array(window[-1], dtype=np.float32)
        mae = float(np.mean(np.abs(last - pred_vec)))
        self._error_history.append(mae)
        errs = self._error_history[-30:]
        mu = float(np.mean(errs))
        sd = float(np.std(errs) + 1e-8)
        threshold = mu + self._k * sd
        anomaly = mae > threshold and len(errs) >= 5

        out: dict[str, Any] = {
            "predicted_next": pred_vec.tolist(),
            "mean_abs_error": mae,
            "threshold_dynamic": threshold,
            "anomaly": bool(anomaly),
            "backend": "sagemaker",
            "ts_ms": now_ms(),
            "raw": data,
        }
        if future_matrix is not None:
            out["predicted_future"] = future_matrix
        elif predicted_future is not None:
            out["predicted_future"] = predicted_future
        return out


def _parse_predictions(
    predictions: Any,
    predicted_future: Any,
) -> tuple[np.ndarray, list | None]:
    """Return (first_timestep_vector, optional full horizon as list of rows for charts)."""
    if predicted_future is not None and isinstance(predicted_future, list) and predicted_future:
        first = np.array(predicted_future[0], dtype=float)
        return first, predicted_future

    if predictions is None:
        return np.array([]), None

    pred_list = predictions
    if isinstance(pred_list, np.ndarray):
        pred_list = pred_list.tolist()

    if not pred_list:
        return np.array([]), None

    # Single flat timestep: [f1, f2, ...]
    if isinstance(pred_list[0], (int, float)):
        vec = np.array(pred_list, dtype=float)
        return vec, [pred_list]

    # List of rows: [[f1..], [f1..], ...]
    if isinstance(pred_list[0], list):
        future_matrix = pred_list
        first = np.array(pred_list[0], dtype=float)
        return first, future_matrix

    return np.array([]), None
