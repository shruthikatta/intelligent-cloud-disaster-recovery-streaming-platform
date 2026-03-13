from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

RegionRole = Literal["primary", "dr"]


@runtime_checkable
class DNSFailoverAdapter(Protocol):
    """Route 53 health check and failover simulation."""

    async def get_active_region(self) -> RegionRole:
        ...

    async def shift_traffic_to(self, target: RegionRole, reason: str) -> dict:
        ...

    async def get_health_summary(self) -> dict:
        ...
