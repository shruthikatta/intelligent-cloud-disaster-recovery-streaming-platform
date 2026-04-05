from __future__ import annotations

"""Build multivariate windows for ED-LSTM from recent metric snapshots."""


from shared.utils.timeutil import now_ms

from cloud_adapters.dependency_factory import get_metrics_adapter

NS = "StreamVault/App"
METRIC_NAMES = ["cpu_utilization", "request_rate", "latency_ms", "network_mbps", "error_rate"]


async def build_feature_window(lookback: int = 24) -> tuple[list[list[float]], list[int]]:
    adapter = get_metrics_adapter()
    end = now_ms()
    start = end - lookback * 60_000  # assume ~1 point/min if simulator every 3s we still have many points
    series_by_name: dict[str, list[tuple[int, float]]] = {}
    for name in METRIC_NAMES:
        pts = await adapter.get_metric_series(NS, name, start, end, period_seconds=60)
        series_by_name[name] = [(p["timestamp_ms"], p["value"]) for p in pts]

    # Align by merging on closest timestamps — for demo, zip last lookback rows from each if same length
    lengths = [len(series_by_name[n]) for n in METRIC_NAMES]
    if not lengths or min(lengths) == 0:
        # synthetic fallback
        return _synthetic_window(lookback), []

    min_len = min(lengths)
    window: list[list[float]] = []
    ts_tail: list[int] = []
    for i in range(max(0, min_len - lookback), min_len):
        row = []
        for name in METRIC_NAMES:
            row.append(float(series_by_name[name][i][1]))
        window.append(row)
        ts_tail.append(series_by_name[METRIC_NAMES[0]][i][0])
    if len(window) < lookback:
        return _synthetic_window(lookback), []
    return window[-lookback:], ts_tail[-lookback:]


def _synthetic_window(lookback: int) -> list[list[float]]:
    import math

    out: list[list[float]] = []
    for i in range(lookback):
        t = i / 5.0
        out.append(
            [
                0.4 + 0.05 * math.sin(t),
                200 + 20 * math.sin(t),
                45 + 3 * math.sin(t),
                50 + 5 * math.sin(t),
                0.01,
            ]
        )
    return out
