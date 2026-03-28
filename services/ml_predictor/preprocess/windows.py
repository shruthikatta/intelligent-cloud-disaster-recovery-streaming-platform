from __future__ import annotations

"""Sliding windows and min-max scaling for metric tensors."""


import numpy as np


def normalize(data: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Min-max per feature; returns scaled, min, max."""
    mins = data.min(axis=0)
    maxs = data.max(axis=0)
    denom = np.where((maxs - mins) < 1e-8, 1.0, maxs - mins)
    scaled = (data - mins) / denom
    return scaled.astype(np.float32), mins.astype(np.float32), maxs.astype(np.float32)


def make_windows(series: np.ndarray, lookback: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Build (X, y) where X: (N, lookback, F), y: (N, horizon, F)."""
    x_list, y_list = [], []
    for i in range(0, len(series) - lookback - horizon + 1):
        x_list.append(series[i : i + lookback])
        y_list.append(series[i + lookback : i + lookback + horizon])
    if not x_list:
        return np.empty((0, lookback, series.shape[1])), np.empty((0, horizon, series.shape[1]))
    return np.stack(x_list, axis=0), np.stack(y_list, axis=0)
