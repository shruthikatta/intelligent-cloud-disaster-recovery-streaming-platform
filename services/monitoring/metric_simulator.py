from __future__ import annotations

"""
Simulates CloudWatch-style metrics for local demo.
Pushes to MetricsAdapter (mock or CloudWatch) on an interval.
"""


import asyncio
import random
import time
from typing import Any

from shared.config.settings import get_settings
from shared.metrics_nominal_demo import nominal_metrics_phase
from shared.utils.timeutil import now_ms

from cloud_adapters.dependency_factory import get_metrics_adapter

NS = "StreamVault/App"


_simulator: MetricSimulator | None = None


def get_simulator() -> MetricSimulator:
    global _simulator
    if _simulator is None:
        _simulator = MetricSimulator()
    return _simulator


class MetricSimulator:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._scenario: str = "steady"
        self._t0 = time.time()

    def set_scenario(self, name: str) -> None:
        self._scenario = name

    def get_scenario(self) -> str:
        return self._scenario

    async def _tick(self) -> dict[str, float]:
        t = time.time() - self._t0
        rng = random.Random(int(t // 5))

        # Steady orbit: human-readable normals (CPU %, latency ms, modest error fraction).
        base = nominal_metrics_phase(t / 12.0)
        base_cpu = base["cpu_utilization"]
        req = base["request_rate"]
        lat = base["latency_ms"]
        net = base["network_mbps"]
        err = base["error_rate"]

        if self._scenario == "cpu_spike":
            base_cpu = min(100.0, base_cpu + 48.0 + 2.0 * rng.random())
        elif self._scenario == "request_surge":
            req = req * 2.8 + 50
            lat = lat * 1.4
        elif self._scenario == "network_degradation":
            net = net * 0.35
            lat = lat * 2.2
        elif self._scenario == "instance_unhealthy":
            err = min(1.0, 0.12 + 0.05 * rng.random())
            lat = lat * 3
        elif self._scenario == "periodic_failure":
            if int(t) % 90 < 12:
                lat = lat * 2.5
                err = min(1.0, max(err, 0.08))

        base_cpu = min(100.0, max(0.0, base_cpu))
        err = min(1.0, max(0.0, err))

        return {
            "cpu_utilization": base_cpu,
            "request_rate": req,
            "latency_ms": lat,
            "network_mbps": net,
            "error_rate": err,
        }

    async def push_once(self) -> dict[str, float]:
        metrics = await self._tick()
        adapter = get_metrics_adapter()
        ts = now_ms()
        settings = get_settings()
        dims = {"Region": settings.primary_region, "Stack": "demo"}
        for k, v in metrics.items():
            await adapter.put_metric(NS, k, float(v), unit="None", dimensions=dims, timestamp_ms=ts)
        return metrics

    async def run_loop(self, interval_sec: float = 3.0) -> None:
        while True:
            await self.push_once()
            await asyncio.sleep(interval_sec)

    def start_background(self, interval_sec: float = 3.0) -> None:
        loop = asyncio.get_event_loop()
        if self._task and not self._task.done():
            self._task.cancel()

        async def _run() -> None:
            while True:
                try:
                    await self.push_once()
                    await asyncio.sleep(interval_sec)
                except asyncio.CancelledError:
                    break

        self._task = loop.create_task(_run())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


def series_for_chart(
    points: list[dict[str, Any]],
    key: str = "value",
) -> list[dict[str, Any]]:
    return [{"t": p["timestamp_ms"], "v": p.get(key, p.get("value")) or 0.0} for p in points]
