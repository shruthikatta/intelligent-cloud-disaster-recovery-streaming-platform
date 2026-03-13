from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MetricsAdapter(Protocol):
    """CloudWatch-compatible metrics read/write abstraction."""

    async def put_metric(
        self,
        namespace: str,
        name: str,
        value: float,
        unit: str = "None",
        dimensions: dict[str, str] | None = None,
        timestamp_ms: int | None = None,
    ) -> None:
        ...

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
        """Return list of {timestamp_ms, value}."""
        ...
