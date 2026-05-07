# SageMaker TensorFlow inference handler for ED-LSTM (.keras in model.tar.gz).
# Place under code/inference.py next to 1/ed_lstm_demo.keras when building model.tar.gz.
# See scripts/sagemaker/README.md

from __future__ import annotations

import json
import logging
import os

import numpy as np

logger = logging.getLogger(__name__)


def model_fn(model_dir: str):
    import tensorflow as tf

    for rel in ("1/ed_lstm_demo.keras", "ed_lstm_demo.keras"):
        p = os.path.join(model_dir, rel)
        if os.path.isfile(p):
            return tf.keras.models.load_model(p, compile=False)
    raise FileNotFoundError(
        f"ed_lstm_demo.keras not found under {model_dir} (expected 1/ed_lstm_demo.keras)"
    )


def input_fn(request_body: bytes, content_type: str) -> np.ndarray:
    if content_type not in ("application/json", "application/json; charset=UTF-8"):
        raise ValueError(f"Unsupported content type: {content_type}")
    body = json.loads(request_body.decode("utf-8"))
    instances = body.get("instances")
    if not instances:
        raise ValueError("JSON body must contain 'instances' list")
    window = np.asarray(instances[0], dtype=np.float32)
    if window.ndim != 2:
        raise ValueError("instances[0] must be 2D: (lookback, n_features)")
    return window


def predict_fn(input_data: np.ndarray, model):
    x = np.expand_dims(input_data, axis=0)
    return model.predict(x, verbose=0)


def output_fn(prediction: np.ndarray, accept: str) -> tuple[bytes, str]:
    del accept
    # (batch, horizon, n_features) -> list of rows for API adapter
    rows = prediction[0].tolist()
    body = json.dumps({"predictions": rows}).encode("utf-8")
    return body, "application/json"
