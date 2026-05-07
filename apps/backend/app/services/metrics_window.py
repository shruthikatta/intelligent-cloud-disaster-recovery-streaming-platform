from __future__ import annotations

"""Multivariate ED-LSTM windows from live/mock metrics or frozen presets in ``data/demo_windows/``."""

from shared.config.settings import get_settings
from shared.metrics_nominal_demo import METRIC_SERIES_KEYS, nominal_window_rows
from shared.predefined_demo_windows import get_demo_window
from shared.utils.timeutil import now_ms

from cloud_adapters.dependency_factory import get_metrics_adapter

NS = "StreamVault/App"
METRIC_NAMES = list(METRIC_SERIES_KEYS)


async def build_feature_window(
    lookback: int = 24, preset: str | None = None
) -> tuple[list[list[float]], list[int], str]:
    """Returns ``(window, timestamps_tail, source)``. ``source`` is ``predefined:<name>``, ``metrics``, or ``synthetic_fallback``."""
    lookback = max(1, lookback)
    settings = get_settings()
    resolved = (preset or settings.ml_demo_window_preset or "").strip()
    if resolved:
        fixed = get_demo_window(resolved, lookback)
        if fixed is not None:
            return fixed, [], f"predefined:{resolved}"

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
        return _synthetic_window(lookback), [], "synthetic_fallback"

    min_len = min(lengths)
    window: list[list[float]] = []
    ts_tail: list[int] = []
    start_idx = max(0, min_len - lookback)
    for i in range(start_idx, min_len):
        row = []
        for name in METRIC_NAMES:
            row.append(float(series_by_name[name][i][1]))
        window.append(row)
        ts_tail.append(series_by_name[METRIC_NAMES[0]][i][0])

    if len(window) == 0:
        return _synthetic_window(lookback), [], "synthetic_fallback"

    # Cold demo: simulator runs every ~3s but we ask for 24 minute buckets — early on there may
    # be < lookback raw points in range. Pad at the front with the oldest row so shape stays (lookback, F).
    if len(window) < lookback:
        pad_n = lookback - len(window)
        pad_row = list(window[0])
        base_ts = ts_tail[0]
        prepend_ts = [base_ts - (pad_n - k) * 60_000 for k in range(pad_n)]
        window = [pad_row.copy() for _ in range(pad_n)] + window
        ts_tail = prepend_ts + ts_tail
        return window, ts_tail, "metrics_padded"

    return window[-lookback:], ts_tail[-lookback:], "metrics"


def _synthetic_window(lookback: int) -> list[list[float]]:
    return nominal_window_rows(lookback, phase_step=0.2)
