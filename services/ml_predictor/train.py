from __future__ import annotations

"""
Train ED-LSTM on synthetic cloud-like series and save model.

Usage (from repo root, venv active):
  PYTHONPATH=. python services/ml_predictor/train.py
"""


import os

import numpy as np

from services.ml_predictor.ed_lstm.model import build_ed_lstm
from services.ml_predictor.preprocess.windows import make_windows, normalize


def synthetic_series(n: int = 800, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 50, n)
    cpu = 0.4 + 0.1 * np.sin(t) + 0.05 * rng.standard_normal(n)
    req = 200 + 40 * np.sin(t * 1.1) + 10 * rng.standard_normal(n)
    lat = 40 + 8 * np.sin(t * 0.9) + 3 * rng.standard_normal(n)
    net = 50 + 12 * np.sin(t * 1.05) + 4 * rng.standard_normal(n)
    err = np.abs(0.01 + 0.005 * rng.standard_normal(n))
    data = np.stack([cpu, req, lat, net, err], axis=1).astype(np.float32)
    return data


def main() -> None:
    lookback, horizon = 24, 6
    raw = synthetic_series()
    scaled, _, _ = normalize(raw)
    x, y = make_windows(scaled, lookback, horizon)
    split = int(len(x) * 0.85)
    x_train, y_train = x[:split], y[:split]
    x_val, y_val = x[split:], y[split:]

    model = build_ed_lstm(lookback, horizon, raw.shape[1])
    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=25,
        batch_size=32,
        verbose=1,
    )

    out_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "ed_lstm_demo.keras")
    model.save(path)
    print(f"Saved model to {path}")


if __name__ == "__main__":
    main()
