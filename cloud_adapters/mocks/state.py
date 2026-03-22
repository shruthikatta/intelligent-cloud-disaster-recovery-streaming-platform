from __future__ import annotations

"""In-memory shared state for local demo mode (thread-safe enough for async demo)."""


import threading
import time
import uuid
from collections import deque
from typing import Any, Literal

RegionRole = Literal["primary", "dr"]

_lock = threading.Lock()

_active_region: RegionRole = "primary"
_failover_state: str = "stable"
_metric_points: dict[str, list[dict[str, Any]]] = {}
_events_log: deque[dict[str, Any]] = deque(maxlen=500)
_recovery_timeline: deque[dict[str, Any]] = deque(maxlen=200)
_queue_messages: deque[dict[str, Any]] = deque(maxlen=200)
_notifications: deque[dict[str, Any]] = deque(maxlen=100)
_anomaly_alerts: deque[dict[str, Any]] = deque(maxlen=50)


def get_active_region() -> RegionRole:
    with _lock:
        return _active_region


def set_active_region(r: RegionRole, reason: str) -> dict[str, Any]:
    global _active_region, _failover_state
    with _lock:
        _active_region = r
        _failover_state = "failover_complete" if r == "dr" else "stable"
        evt = {
            "id": str(uuid.uuid4()),
            "ts_ms": int(time.time() * 1000),
            "type": "region_shift",
            "detail": {"target": r, "reason": reason},
        }
        _recovery_timeline.append(evt)
        _events_log.append({"source": "mock.route53", "detail": evt})
        return evt


def get_failover_state() -> str:
    with _lock:
        return _failover_state


def append_metric(namespace: str, name: str, value: float, ts_ms: int) -> None:
    key = f"{namespace}:{name}"
    with _lock:
        if key not in _metric_points:
            _metric_points[key] = []
        _metric_points[key].append({"timestamp_ms": ts_ms, "value": value})
        # cap series length
        if len(_metric_points[key]) > 2000:
            _metric_points[key] = _metric_points[key][-2000:]


def get_series(namespace: str, name: str) -> list[dict[str, Any]]:
    key = f"{namespace}:{name}"
    with _lock:
        return list(_metric_points.get(key, []))


def log_event(source: str, detail_type: str, detail: dict[str, Any]) -> str:
    eid = str(uuid.uuid4())
    with _lock:
        _events_log.append(
            {
                "id": eid,
                "ts_ms": int(time.time() * 1000),
                "source": source,
                "detail_type": detail_type,
                "detail": detail,
            }
        )
    return eid


def get_events() -> list[dict[str, Any]]:
    with _lock:
        return list(_events_log)


def append_timeline(entry: dict[str, Any]) -> None:
    with _lock:
        _recovery_timeline.append(entry)


def get_timeline() -> list[dict[str, Any]]:
    with _lock:
        return list(_recovery_timeline)


def enqueue(body: str) -> str:
    mid = str(uuid.uuid4())
    with _lock:
        _queue_messages.append({"id": mid, "body": body, "ts_ms": int(time.time() * 1000)})
    return mid


def drain_queue(max_n: int = 10) -> list[dict[str, Any]]:
    with _lock:
        out = []
        while _queue_messages and len(out) < max_n:
            out.append(_queue_messages.popleft())
        return out


def notify(subject: str, message: str) -> str:
    nid = str(uuid.uuid4())
    with _lock:
        _notifications.append(
            {"id": nid, "subject": subject, "message": message, "ts_ms": int(time.time() * 1000)}
        )
    return nid


def get_notifications() -> list[dict[str, Any]]:
    with _lock:
        return list(_notifications)


def add_anomaly(alert: dict[str, Any]) -> None:
    with _lock:
        _anomaly_alerts.append(alert)


def get_anomalies() -> list[dict[str, Any]]:
    with _lock:
        return list(_anomaly_alerts)
