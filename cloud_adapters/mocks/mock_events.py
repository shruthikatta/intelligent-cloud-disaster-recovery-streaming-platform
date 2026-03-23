from __future__ import annotations

"""Mock EventBridge bus."""

from typing import Any

from cloud_adapters.mocks import state


class MockEventBusAdapter:
    async def put_events(self, source: str, detail_type: str, detail: dict[str, Any]) -> str:
        return state.log_event(source, detail_type, detail)
