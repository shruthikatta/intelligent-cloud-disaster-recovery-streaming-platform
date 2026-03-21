from __future__ import annotations

"""Invoke Lambda for recovery automation."""


import json
from typing import Any

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class LambdaRecoveryAdapter:
    def __init__(self) -> None:
        self._client = get_client("lambda")
        self._arn = get_aws_settings().lambda_recovery_arn

    async def invoke_recovery_workflow(self, workflow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"workflow": workflow_name, **payload}
        resp = self._client.invoke(
            FunctionName=self._arn,
            InvocationType="RequestResponse",
            Payload=json.dumps(body).encode("utf-8"),
        )
        raw = resp["Payload"].read().decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
