from __future__ import annotations

"""Mock Lambda recovery workflow."""

from typing import Any

from cloud_adapters.mocks import state


class MockRecoveryAdapter:
    async def invoke_recovery_workflow(self, workflow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "workflow": workflow_name,
            "payload": payload,
            "status": "completed",
        }
        state.append_timeline(entry)
        return {"ok": True, "workflow": workflow_name, "result": entry}
