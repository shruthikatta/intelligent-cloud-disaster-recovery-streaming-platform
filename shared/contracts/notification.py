from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationAdapter(Protocol):
    """SNS-compatible topic publish."""

    async def publish_alert(self, subject: str, message: str, attributes: dict[str, str] | None = None) -> str:
        """Return message id."""
        ...
