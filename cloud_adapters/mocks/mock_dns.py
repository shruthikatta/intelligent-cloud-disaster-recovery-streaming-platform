from __future__ import annotations

"""Simulated Route 53 failover."""

from typing import Any, Literal

from cloud_adapters.mocks import state

RegionRole = Literal["primary", "dr"]


class MockDNSFailoverAdapter:
    async def get_active_region(self) -> RegionRole:
        return state.get_active_region()

    async def shift_traffic_to(self, target: RegionRole, reason: str) -> dict[str, Any]:
        evt = state.set_active_region(target, reason)
        return {"shifted_to": target, "event": evt}

    async def get_health_summary(self) -> dict[str, Any]:
        return {
            "primary": {"healthy": state.get_active_region() == "primary", "region": "us-west-2"},
            "dr": {"healthy": True, "region": "us-east-1", "standby": state.get_active_region() == "primary"},
            "active": state.get_active_region(),
        }
