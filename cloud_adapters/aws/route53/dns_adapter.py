from __future__ import annotations

"""
Route 53 failover-style adapter.

This placeholder updates health-checked weighted records or failover records
when your hosted zone and record names are configured in environment variables.
For a minimal demo, it calls ChangeResourceRecordSets with UPSERT on health flags
only if ROUTE53_* vars are set; otherwise returns a descriptive stub.
"""


from typing import Any, Literal

from botocore.exceptions import ClientError

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings
from cloud_adapters.mocks import state

RegionRole = Literal["primary", "dr"]


class Route53FailoverAdapter:
    def __init__(self) -> None:
        self._client = get_client("route53")
        self._settings = get_aws_settings()

    async def get_active_region(self) -> RegionRole:
        # Without full DNS state, default to primary; DR drills should use app-level state
        return "primary"

    async def shift_traffic_to(self, target: RegionRole, reason: str) -> dict[str, Any]:
        zid = self._settings.route53_hosted_zone_id
        if not zid:
            state.set_active_region(target, reason)
            return {
                "ok": True,
                "message": "ROUTE53_HOSTED_ZONE_ID not configured; updated app-level failover state only.",
                "target": target,
                "reason": reason,
            }
        # Placeholder: real impl would flip failover records or weights
        try:
            _ = self._client.get_hosted_zone(Id=zid)
        except ClientError as e:
            return {"ok": False, "error": str(e)}
        state.set_active_region(target, reason)
        return {
            "ok": True,
            "simulated": True,
            "target": target,
            "reason": reason,
            "note": "Wire ChangeResourceRecordSets here for production failover.",
        }

    async def get_health_summary(self) -> dict[str, Any]:
        return {
            "primary": {"region": "us-west-2"},
            "dr": {"region": "us-east-1"},
            "adapter": "route53",
        }
