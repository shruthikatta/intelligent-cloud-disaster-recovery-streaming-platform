from __future__ import annotations

"""Load Keras ED-LSTM and run inference + dynamic threshold on error."""


import numpy as np
import tensorflow as tf
from tensorflow import keras

from shared.utils.timeutil import now_ms


class LocalTensorFlowInferenceAdapter:
    FEATURE_ORDER = ["cpu", "request_rate", "latency_ms", "network_mbps", "errors"]

    def __init__(self, model_path: str, k_sigma: float = 3.0) -> None:
        self._model: keras.Model = keras.models.load_model(model_path, compile=False)
        self._k = k_sigma
        self._error_history: list[float] = []

    async def predict(self, window: list[list[float]]) -> dict:
        arr = np.array(window, dtype=np.float32)
        if arr.ndim != 2:
            return {"error": "expected 2D window", "anomaly": False}
        x = np.expand_dims(arr, axis=0)
        y_hat = self._model.predict(x, verbose=0)
        # Next-step error: compare last predicted step to last actual (simple anomaly proxy)
        pred_next = y_hat[0, 0].tolist()
        last = arr[-1]
        err_vec = np.abs(last - y_hat[0, 0])
        mae = float(np.mean(err_vec))
        self._error_history.append(mae)
        errs = self._error_history[-30:]
        mu = float(np.mean(errs))
        sd = float(np.std(errs) + 1e-8)
        threshold = mu + self._k * sd
        anomaly = mae > threshold and len(errs) >= 5
        return {
            "predicted_future": y_hat.tolist(),
            "predicted_next": pred_next,
            "mean_abs_error": mae,
            "threshold_dynamic": threshold,
            "anomaly": bool(anomaly),
            "backend": "keras_ed_lstm",
            "ts_ms": now_ms(),
        }
