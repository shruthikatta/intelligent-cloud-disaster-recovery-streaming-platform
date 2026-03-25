from __future__ import annotations

"""
Simulates CloudWatch-style metrics for local demo.
Pushes to MetricsAdapter (mock or CloudWatch) on an interval.
"""


import asyncio
import math
import random
import time
from typing import Any

from shared.config.settings import get_settings
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

    async def _tick(self) -> dict[str, float]:
        t = time.time() - self._t0
        rng = random.Random(int(t // 5))

        base_cpu = 0.35 + 0.04 * math.sin(t / 30)
        req = 180 + 20 * math.sin(t / 25)
        lat = 45 + 5 * math.sin(t / 40)
        net = 55 + 10 * math.sin(t / 35)
        err = 0.01

        if self._scenario == "cpu_spike":
            base_cpu = min(0.95, base_cpu + 0.45 + 0.01 * rng.random())
        elif self._scenario == "request_surge":
            req = req * 2.8 + 50
            lat = lat * 1.4
        elif self._scenario == "network_degradation":
            net = net * 0.35
            lat = lat * 2.2
        elif self._scenario == "instance_unhealthy":
            err = 0.12 + 0.05 * rng.random()
            lat = lat * 3
        elif self._scenario == "periodic_failure":
            if int(t) % 90 < 12:
                lat = lat * 2.5
                err = 0.08

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
    return [{"t": p["timestamp_ms"], "v": p.get(key, p.get("value"))} for p in points]
