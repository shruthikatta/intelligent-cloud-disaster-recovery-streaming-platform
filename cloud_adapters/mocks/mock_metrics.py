from __future__ import annotations

"""In-memory metrics that mirror CloudWatch-style series."""


from typing import Any

from shared.utils.timeutil import now_ms

from cloud_adapters.mocks import state


class MockMetricsAdapter:
    NS = "StreamVault/App"

    async def put_metric(
        self,
        namespace: str,
        name: str,
        value: float,
        unit: str = "None",
        dimensions: dict[str, str] | None = None,
        timestamp_ms: int | None = None,
    ) -> None:
        ts = timestamp_ms or now_ms()
        state.append_metric(namespace, name, value, ts)

    async def get_metric_series(
        self,
        namespace: str,
        metric_name: str,
        start_ms: int,
        end_ms: int,
        period_seconds: int = 60,
        stat: str = "Average",
        dimensions: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        series = state.get_series(namespace, metric_name)
        return [p for p in series if start_ms <= p["timestamp_ms"] <= end_ms]
