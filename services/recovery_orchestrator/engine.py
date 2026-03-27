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
    get_model_inference_adapter,
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
        if anomaly and severity > 0.5:
            action = "failover"
        elif anomaly or severity > 0.25:
            action = "warn"

        detail = {
            "anomaly": anomaly,
            "severity": severity,
            "mae": mean_abs_error,
            "action": action,
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
            await rec.invoke_recovery_workflow(
                "proactive_failover",
                {"reason": "model_anomaly", **detail},
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
        if anomaly:
            state.add_anomaly(
                {
                    "ts_ms": entry["ts_ms"],
                    "severity": severity,
                    "message": f"ED-LSTM flagged anomaly (action={action})",
                }
            )

        return {"decision": action, "timeline_id": entry["id"]}
