from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class QueueAdapter(Protocol):
    """SQS-compatible queue."""

    async def send_message(self, body: str, delay_seconds: int = 0) -> str:
        """Return message id."""
        ...

    async def receive_messages(self, max_messages: int = 10) -> list[dict[str, Any]]:
        ...
