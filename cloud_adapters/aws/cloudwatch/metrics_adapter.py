from __future__ import annotations

"""CloudWatch GetMetricStatistics / PutMetricData adapter."""


import datetime as dt
from typing import Any

from cloud_adapters.aws.config.aws_session import get_client


class CloudWatchMetricsAdapter:
    def __init__(self) -> None:
        self._cw = get_client("cloudwatch")

    async def put_metric(
        self,
        namespace: str,
        name: str,
        value: float,
        unit: str = "None",
        dimensions: dict[str, str] | None = None,
        timestamp_ms: int | None = None,
    ) -> None:
        dims = [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
        ts = None
        if timestamp_ms:
            ts = dt.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=dt.timezone.utc)
        metric_data: dict = {
            "MetricName": name,
            "Value": value,
            "Unit": "None" if unit in ("None", "") else unit,
        }
        if dims:
            metric_data["Dimensions"] = dims
        if ts:
            metric_data["Timestamp"] = ts
        self._cw.put_metric_data(Namespace=namespace, MetricData=[metric_data])

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
        dims = [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
        resp = self._cw.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dims,
            StartTime=dt.datetime.fromtimestamp(start_ms / 1000.0, tz=dt.timezone.utc),
            EndTime=dt.datetime.fromtimestamp(end_ms / 1000.0, tz=dt.timezone.utc),
            Period=period_seconds,
            Statistics=[stat],
        )
        out: list[dict[str, Any]] = []
        for p in resp.get("Datapoints", []):
            ts = int(p["Timestamp"].timestamp() * 1000)
            val = p.get(stat)
            if val is not None:
                out.append({"timestamp_ms": ts, "value": float(val)})
        out.sort(key=lambda x: x["timestamp_ms"])
        return out
