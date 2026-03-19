from __future__ import annotations

"""SQS send/receive adapter."""


from typing import Any

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class SQSQueueAdapter:
    def __init__(self) -> None:
        self._sqs = get_client("sqs")
        self._queue_url = get_aws_settings().sqs_queue_url

    async def send_message(self, body: str, delay_seconds: int = 0) -> str:
        resp = self._sqs.send_message(
            QueueUrl=self._queue_url,
            MessageBody=body,
            DelaySeconds=min(delay_seconds, 900),
        )
        return resp.get("MessageId", "")

    async def receive_messages(self, max_messages: int = 10) -> list[dict[str, Any]]:
        resp = self._sqs.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=1,
        )
        out = []
        for m in resp.get("Messages", []):
            out.append(
                {
                    "id": m.get("MessageId"),
                    "body": m.get("Body"),
                    "receipt_handle": m.get("ReceiptHandle"),
                }
            )
        return out
