from __future__ import annotations

"""SageMaker runtime invoke for hosted models."""


import json
from typing import Any

import numpy as np

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class SageMakerInferenceAdapter:
    def __init__(self) -> None:
        self._runtime = get_client("sagemaker-runtime")
        self._endpoint = get_aws_settings().sagemaker_endpoint_name

    async def predict(self, window: list[list[float]]) -> dict[str, Any]:
        payload = json.dumps({"instances": [window]})
        resp = self._runtime.invoke_endpoint(
            EndpointName=self._endpoint,
            ContentType="application/json",
            Body=payload.encode("utf-8"),
        )
        raw = resp["Body"].read().decode("utf-8")
        data = json.loads(raw)
        # Expect predictions list aligned with paper demo
        pred_vec = np.array(data.get("predictions", [[0.0]])[0], dtype=float)
        return {
            "predicted_next": pred_vec.tolist(),
            "mean_abs_error": float(np.mean(np.abs(pred_vec))),
            "anomaly": False,
            "backend": "sagemaker",
            "raw": data,
        }
