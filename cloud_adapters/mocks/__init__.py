from __future__ import annotations

from cloud_adapters.mocks.mock_dns import MockDNSFailoverAdapter
from cloud_adapters.mocks.mock_events import MockEventBusAdapter
from cloud_adapters.mocks.mock_metrics import MockMetricsAdapter
from cloud_adapters.mocks.mock_model_inference import MockModelInferenceAdapter
from cloud_adapters.mocks.mock_notification import MockNotificationAdapter
from cloud_adapters.mocks.mock_queue import MockQueueAdapter
from cloud_adapters.mocks.mock_recovery import MockRecoveryAdapter
from cloud_adapters.mocks.mock_storage import MockStorageAdapter

__all__ = [
    "MockDNSFailoverAdapter",
    "MockEventBusAdapter",
    "MockMetricsAdapter",
    "MockModelInferenceAdapter",
    "MockNotificationAdapter",
    "MockQueueAdapter",
    "MockRecoveryAdapter",
    "MockStorageAdapter",
]
