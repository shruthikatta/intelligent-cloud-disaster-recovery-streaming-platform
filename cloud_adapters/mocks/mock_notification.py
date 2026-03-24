from __future__ import annotations

"""In-app SNS mock."""

from cloud_adapters.mocks import state


class MockNotificationAdapter:
    async def publish_alert(self, subject: str, message: str, attributes: dict[str, str] | None = None) -> str:
        return state.notify(subject, message)
