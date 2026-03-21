from __future__ import annotations

"""
Resolve platform adapters from APP_MODE / USE_REAL_AWS flags.
Application code should import adapters only via this module or FastAPI deps.
"""


from typing import TYPE_CHECKING

from shared.config.settings import AppSettings, get_settings

if TYPE_CHECKING:
    from shared.contracts import (
        DNSFailoverAdapter,
        EventBusAdapter,
        MetricsAdapter,
        ModelInferenceAdapter,
        NotificationAdapter,
        QueueAdapter,
        RecoveryAdapter,
        StorageAdapter,
    )


def _use_aws(settings: AppSettings) -> bool:
    return settings.app_mode == "aws" or settings.use_real_aws


def get_storage_adapter() -> "StorageAdapter":
    settings = get_settings()
    if _use_aws(settings):
        from cloud_adapters.aws.s3.storage_adapter import S3StorageAdapter

        return S3StorageAdapter()
    from cloud_adapters.mocks.mock_storage import MockStorageAdapter

    return MockStorageAdapter()


def get_metrics_adapter() -> "MetricsAdapter":
    settings = get_settings()
    if _use_aws(settings):
        from cloud_adapters.aws.cloudwatch.metrics_adapter import CloudWatchMetricsAdapter

        return CloudWatchMetricsAdapter()
    from cloud_adapters.mocks.mock_metrics import MockMetricsAdapter

    return MockMetricsAdapter()


def get_event_bus_adapter() -> "EventBusAdapter":
    settings = get_settings()
    if _use_aws(settings):
        from cloud_adapters.aws.eventbridge.eventbus_adapter import EventBridgeAdapter

        return EventBridgeAdapter()
    from cloud_adapters.mocks.mock_events import MockEventBusAdapter

    return MockEventBusAdapter()


def get_recovery_adapter() -> "RecoveryAdapter":
    settings = get_settings()
    if _use_aws(settings):
        from cloud_adapters.aws.lambda_fn.recovery_adapter import LambdaRecoveryAdapter

        return LambdaRecoveryAdapter()
    from cloud_adapters.mocks.mock_recovery import MockRecoveryAdapter

    return MockRecoveryAdapter()


def get_dns_adapter() -> "DNSFailoverAdapter":
    settings = get_settings()
    if _use_aws(settings):
        from cloud_adapters.aws.route53.dns_adapter import Route53FailoverAdapter

        return Route53FailoverAdapter()
    from cloud_adapters.mocks.mock_dns import MockDNSFailoverAdapter

    return MockDNSFailoverAdapter()


def get_notification_adapter() -> "NotificationAdapter":
    settings = get_settings()
    if _use_aws(settings) and settings.enable_sns:
        from cloud_adapters.aws.sns.notification_adapter import SNSNotificationAdapter

        return SNSNotificationAdapter()
    from cloud_adapters.mocks.mock_notification import MockNotificationAdapter

    return MockNotificationAdapter()


def get_queue_adapter() -> "QueueAdapter":
    settings = get_settings()
    if _use_aws(settings) and settings.enable_sqs:
        from cloud_adapters.aws.sqs.queue_adapter import SQSQueueAdapter

        return SQSQueueAdapter()
    from cloud_adapters.mocks.mock_queue import MockQueueAdapter

    return MockQueueAdapter()


def get_model_inference_adapter() -> "ModelInferenceAdapter":
    """Prefer local ED-LSTM file if present; else SageMaker in AWS; else mock."""
    from pathlib import Path

    from cloud_adapters.mocks.mock_model_inference import MockModelInferenceAdapter

    settings = get_settings()
    path = Path(settings.ml_model_path)
    if path.exists():
        from services.ml_predictor.inference.local_tensorflow import LocalTensorFlowInferenceAdapter

        return LocalTensorFlowInferenceAdapter(str(path))

    if _use_aws(settings):
        from cloud_adapters.aws.config.aws_settings import get_aws_settings

        if get_aws_settings().sagemaker_endpoint_name:
            from cloud_adapters.aws.sagemaker.model_inference_adapter import SageMakerInferenceAdapter

            return SageMakerInferenceAdapter()

    return MockModelInferenceAdapter()
