from __future__ import annotations

"""SNS publish adapter."""

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class SNSNotificationAdapter:
    def __init__(self) -> None:
        self._sns = get_client("sns")
        self._topic = get_aws_settings().sns_topic_arn

    async def publish_alert(self, subject: str, message: str, attributes: dict[str, str] | None = None) -> str:
        kwargs: dict = {"TopicArn": self._topic, "Subject": subject, "Message": message}
        if attributes:
            kwargs["MessageAttributes"] = {
                k: {"DataType": "String", "StringValue": v} for k, v in attributes.items()
            }
        resp = self._sns.publish(**kwargs)
        return resp.get("MessageId", "")
