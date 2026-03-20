from __future__ import annotations

"""EventBridge PutEvents adapter."""


import json
from typing import Any

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class EventBridgeAdapter:
    def __init__(self) -> None:
        self._client = get_client("events")
        self._bus = get_aws_settings().eventbridge_bus_name

    async def put_events(self, source: str, detail_type: str, detail: dict[str, Any]) -> str:
        resp = self._client.put_events(
            Entries=[
                {
                    "Source": source,
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail),
                    "EventBusName": self._bus,
                }
            ]
        )
        entries = resp.get("Entries") or []
        return entries[0].get("EventId", "unknown") if entries else "unknown"
