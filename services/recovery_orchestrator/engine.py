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


class RecoveryEngine:
    async def evaluate(
        self,
        anomaly: bool,
        severity: float,
        mean_abs_error: float,
    ) -> dict[str, Any]:
        settings = get_settings()
        action: Action = "monitor"
        # Failover used to require anomaly=True; ED-LSTM often leaves anomaly=False while
        # mean_abs_error / threshold_dynamic still implies severe drift → endless "warn".
        model_failover = anomaly and severity > 0.5
        stress_failover = severity >= 0.75
        should_failover = model_failover or stress_failover
        should_warn = (anomaly or severity > 0.25) and not should_failover

        if should_failover:
            action = "failover"
        elif should_warn:
            action = "warn"

        detail = {
            "anomaly": anomaly,
            "severity": severity,
            "mae": mean_abs_error,
            "action": action,
            "failover_trigger": (
                "model_anomaly"
                if should_failover and model_failover
                else ("severity_escalation" if should_failover and stress_failover else None)
            ),
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
                f"ED-LSTM flagged anomaly (action={action})"
                if anomaly
                else f"Failover from severity escalation (mae={mean_abs_error:.4f}, action={action})"
            )
            state.add_anomaly(
                {
                    "ts_ms": entry["ts_ms"],
                    "severity": severity,
                    "message": msg,
                }
            )

        return {"decision": action, "timeline_id": entry["id"]}
