from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageAdapter(Protocol):
    """Object storage (S3-compatible): catalog assets, video URLs, logs."""

    async def get_public_url(self, key: str) -> str:
        """Return URL for streaming or download (presigned or public)."""
        ...

    async def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes; return stored key or URI."""
        ...

    async def exists(self, key: str) -> bool:
        ...
