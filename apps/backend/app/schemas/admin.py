from __future__ import annotations

from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="cpu_spike | request_surge | network_degradation | instance_unhealthy | periodic_failure | steady",
    )


class FailoverRequest(BaseModel):
    target: str = Field(default="dr", pattern="^(primary|dr)$")
    reason: str = "manual demo failover"
