from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelInferenceAdapter(Protocol):
    """SageMaker or local ED-LSTM inference."""

    async def predict(self, window: list[list[float]]) -> dict[str, Any]:
        """
        window: sequence of feature vectors (time steps x features).
        Returns predictions, errors, anomaly flags as dict.
        """
        ...
