from __future__ import annotations

"""In-memory SQS."""

from typing import Any

from cloud_adapters.mocks import state


class MockQueueAdapter:
    async def send_message(self, body: str, delay_seconds: int = 0) -> str:
        return state.enqueue(body)

    async def receive_messages(self, max_messages: int = 10) -> list[dict[str, Any]]:
        return state.drain_queue(max_messages)
