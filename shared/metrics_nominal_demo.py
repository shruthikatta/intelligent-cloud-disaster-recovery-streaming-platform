from __future__ import annotations

"""
Nominal bands for simulated multivariate app metrics (local demo / CloudWatch mock).

Mirrors steady production-like traffic without failures. Used by MetricSimulator and
the synthetic inference window fallback.

cpu_utilization: percent 0–100 (normal orbit ~31–49)
error_rate: fraction 0–1 (e.g. 0.01 ≈ 1%)
"""

import math


# Order must match ingestion and ML-facing windows (`apps/backend/app/services/metrics_window.py`).
METRIC_SERIES_KEYS: tuple[str, ...] = (
    "cpu_utilization",
    "request_rate",
    "latency_ms",
    "network_mbps",
    "error_rate",
)


def nominal_metrics_phase(phase: float) -> dict[str, float]:
    """Gentle sinusoidal drift around steady-state norms; `phase` is a unitless time index."""
    t = float(phase)
    return {
        # ~31–49% CPU — reads clearly on dashboards
        "cpu_utilization": 40.0 + 9.0 * math.sin(t),
        "request_rate": 200.0 + 38.0 * math.sin(t * 1.1),
        "latency_ms": 42.0 + 9.0 * math.sin(t * 0.9),
        "network_mbps": 56.0 + 14.0 * math.sin(t * 1.05),
        "error_rate": float(max(0.0, min(0.06, 0.012 + 0.004 * math.sin(t * 0.7)))),
    }


def nominal_window_rows(lookback: int, *, phase_step: float = 0.2) -> list[list[float]]:
    """`(lookback, 5)` matrix for ED-LSTM / SageMaker payloads when no adapter data exists."""
    rows: list[list[float]] = []
    for i in range(lookback):
        m = nominal_metrics_phase(i * phase_step)
        rows.append([float(m[k]) for k in METRIC_SERIES_KEYS])
    return rows
