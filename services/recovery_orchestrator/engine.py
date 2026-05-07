from __future__ import annotations

"""
Recovery orchestration: maps ML anomaly + health to actions (monitor / warn / failover).
Mirrors CloudWatch -> EventBridge -> automation -> Route 53 flow in mock/AWS adapters.
"""


import time
import uuid
from typing import Any, Literal

from shared.config.settings import get_settings

from cloud_adapters.dependency_factory import (
    get_dns_adapter,
    get_event_bus_adapter,
    get_notification_adapter,
    get_queue_adapter,
    get_recovery_adapter,
)
from cloud_adapters.mocks import state

Action = Literal["monitor", "warn", "failover"]

# Metric simulator failure modes (see `POST /admin/scenario`). Steady state must not use
# severity-only failover: MAE/threshold ratio is often high even when `anomaly` is false
# (e.g. raw window vs scaled model), which would false-trigger DR on "steady".
_METRIC_SIMULATOR_STRESS_SCENARIOS = frozenset(
    {
        "cpu_spike",
        "request_surge",
        "network_degradation",
        "instance_unhealthy",
        "periodic_failure",
    }
)


class RecoveryEngine:
    async def evaluate(
        self,
        anomaly: bool,
        severity: float,
        mean_abs_error: float,
        metric_scenario: str | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        action: Action = "monitor"
        model_failover = anomaly and severity > 0.5
        stress_failover = (
            metric_scenario in _METRIC_SIMULATOR_STRESS_SCENARIOS and severity >= 0.75
        )
        should_failover = model_failover or stress_failover
        should_warn = (anomaly or severity > 0.25) and not should_failover

        if should_failover:
            action = "failover"
        elif should_warn:
            action = "warn"

        failover_trigger: str | None = None
        if should_failover:
            if model_failover:
                failover_trigger = "model_anomaly"
            elif stress_failover:
                failover_trigger = "severity_escalation"

        detail = {
            "anomaly": anomaly,
            "severity": severity,
            "mae": mean_abs_error,
            "metric_scenario": metric_scenario,
            "action": action,
            "failover_trigger": failover_trigger,
            "primary_region": settings.primary_region,
            "dr_region": settings.dr_region,
        }

        bus = get_event_bus_adapter()
        await bus.put_events("streamvault.recovery", "AnomalyEvaluated", detail)

        if action == "warn":
            n = get_notification_adapter()
            await n.publish_alert(
                "StreamVault warning",
                f"Anomaly detected (mae={mean_abs_error:.4f}). Continuing to monitor.",
            )
            q = get_queue_adapter()
            await q.send_message(f"warn:{detail}")

        if action == "failover":
            rec = get_recovery_adapter()
            reason = (
                "model_anomaly"
                if detail.get("failover_trigger") == "model_anomaly"
                else "severity_escalation"
            )
            await rec.invoke_recovery_workflow(
                "proactive_failover",
                {"reason": reason, **detail},
            )
            dns = get_dns_adapter()
            await dns.shift_traffic_to("dr", "proactive ML-driven failover")
            n = get_notification_adapter()
            await n.publish_alert("Failover initiated", "Traffic shifting to DR region (us-east-1).")

        entry = {
            "id": str(uuid.uuid4()),
            "ts_ms": int(time.time() * 1000),
            "action": action,
            "detail": detail,
        }
        state.append_timeline(entry)
        if anomaly or action == "failover":
            msg = (
                f"ED-LSTM flagged anomaly (action={action}, mae={mean_abs_error:.4f})"
                if anomaly
                else f"Failover from severity escalation (action={action}, mae={mean_abs_error:.4f})"
            )
            state.add_anomaly(
                {
                    "ts_ms": entry["ts_ms"],
                    "severity": severity,
                    "message": msg,
                }
            )

        return {"decision": action, "timeline_id": entry["id"]}
