from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RecoveryAdapter(Protocol):
    """Lambda-style automation hooks for failover workflows."""

    async def invoke_recovery_workflow(
        self,
        workflow_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        ...
