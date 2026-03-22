from __future__ import annotations

"""Local filesystem-backed storage with public file:// or http URLs for demo."""


import os
from pathlib import Path

from shared.config.settings import get_settings


class MockStorageAdapter:
    def __init__(self, base_dir: str | None = None) -> None:
        root = base_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "storage")
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.lstrip("/").replace("..", "")
        return self._root / safe

    async def get_public_url(self, key: str) -> str:
        # Demo: return placeholder HTTPS for known sample streams
        if key.startswith("http"):
            return key
        p = self._path(key)
        if p.exists():
            return f"file://{p}"
        settings = get_settings()
        return f"https://{settings.s3_bucket}.s3.amazonaws.com/{settings.s3_prefix}{key}"

    async def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    async def exists(self, key: str) -> bool:
        return self._path(key).exists()
