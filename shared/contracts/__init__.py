from __future__ import annotations

from shared.contracts.dns import DNSFailoverAdapter
from shared.contracts.events import EventBusAdapter
from shared.contracts.metrics import MetricsAdapter
from shared.contracts.model_inference import ModelInferenceAdapter
from shared.contracts.notification import NotificationAdapter
from shared.contracts.queue import QueueAdapter
from shared.contracts.recovery import RecoveryAdapter
from shared.contracts.storage import StorageAdapter

__all__ = [
    "DNSFailoverAdapter",
    "EventBusAdapter",
    "MetricsAdapter",
    "ModelInferenceAdapter",
    "NotificationAdapter",
    "QueueAdapter",
    "RecoveryAdapter",
    "StorageAdapter",
]
