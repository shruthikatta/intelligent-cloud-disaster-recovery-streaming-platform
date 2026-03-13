from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventBusAdapter(Protocol):
    """EventBridge-compatible publish/subscribe."""

    async def put_events(self, source: str, detail_type: str, detail: dict[str, Any]) -> str:
        """Return event id or batch id."""
        ...
