from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
import httpx

from shared.config.settings import get_settings
from shared.utils.timeutil import now_ms

from apps.backend.app.schemas.admin import FailoverRequest, ScenarioRequest
from apps.backend.app.services.metrics_window import METRIC_NAMES, NS, build_feature_window
from cloud_adapters.dependency_factory import get_dns_adapter, get_metrics_adapter, get_model_inference_adapter
from cloud_adapters.mocks import state
from services.monitoring.metric_simulator import get_simulator
from services.recovery_orchestrator.engine import RecoveryEngine
from shared.predefined_demo_windows import demo_window_documentation

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def overview() -> dict[str, Any]:
    settings = get_settings()
    return {
        "app_mode": settings.app_mode,
        "primary_region": settings.primary_region,
        "dr_region": settings.dr_region,
        "active_region": state.get_active_region(),
        "failover_state": state.get_failover_state(),
        "rto_target_min": 15,
        "rpo_target_min": 5,
        "recovery_readiness": 0.92 if state.get_active_region() == "primary" else 0.88,
    }


@router.get("/metrics/series")
async def metrics_series(
    minutes: int = 60,
) -> dict[str, Any]:
    adapter = get_metrics_adapter()
    end = now_ms()
    start = end - minutes * 60_000
    out: dict[str, list] = {}
    for name in METRIC_NAMES:
        series = await adapter.get_metric_series(NS, name, start, end, period_seconds=60)
        out[name] = [{"t": p["timestamp_ms"], "v": p["value"]} for p in series]
    return {"namespace": NS, "series": out}


@router.get("/region-status")
async def region_status() -> dict[str, Any]:
    dns = get_dns_adapter()
    health = await dns.get_health_summary()
    return {
        "active_region": state.get_active_region(),
        "dns": health,
        "primary": {"id": "us-west-2", "role": "primary"},
        "dr": {"id": "us-east-1", "role": "standby"},
    }


@router.post("/scenario")
async def set_scenario(body: ScenarioRequest) -> dict[str, Any]:
    get_simulator().set_scenario(body.scenario)
    return {
        "scenario": body.scenario,
        "hint": "Simulator will push updated metrics on its interval; click Run ED-LSTM + policy to see ml_input.window in the response.",
    }


@router.post("/failover/manual")
async def manual_failover(body: FailoverRequest) -> dict[str, Any]:
    dns = get_dns_adapter()
    r = await dns.shift_traffic_to(body.target, body.reason)  # type: ignore[arg-type]
    state.set_active_region(body.target, body.reason)  # type: ignore[arg-type]
    return {"ok": True, "result": r}


@router.get("/events")
async def events() -> dict[str, Any]:
    return {"events": state.get_events()[-100:]}


@router.get("/timeline")
async def timeline() -> dict[str, Any]:
    return {"timeline": state.get_timeline()[-100:]}


@router.get("/anomalies")
async def anomalies() -> dict[str, Any]:
    return {"alerts": state.get_anomalies()[-50:]}


@router.get("/notifications")
async def notifications() -> dict[str, Any]:
    return {"notifications": state.get_notifications()[-50:]}


@router.get("/prediction/demo-presets")
async def prediction_demo_presets() -> dict[str, Any]:
    doc = demo_window_documentation()
    doc["server_default_preset"] = get_settings().ml_demo_window_preset
    return doc


@router.post("/prediction/run")
async def run_prediction(
    preset: str | None = Query(
        None,
        description="Overrides ML_DEMO_WINDOW_PRESET for this call (e.g. normal, high_cpu).",
    ),
) -> dict[str, Any]:
    settings = get_settings()
    window, timestamps_tail_ms, source = await build_feature_window(lookback=24, preset=preset)
    if settings.ml_use_standalone_service:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{settings.ml_service_url}/predict", json={"window": window})
            r.raise_for_status()
            pred = r.json()
    else:
        adapter = get_model_inference_adapter()
        pred = await adapter.predict(window)

    mae = float(pred.get("mean_abs_error", pred.get("threshold_dynamic", 0.5)))
    anomaly = bool(pred.get("anomaly", False))
    severity = min(1.0, mae / max(pred.get("threshold_dynamic", 1.0), 0.1))
    engine = RecoveryEngine()
    decision = await engine.evaluate(
        anomaly=anomaly,
        severity=severity,
        mean_abs_error=mae,
        metric_scenario=get_simulator().get_scenario(),
    )
    return {
        "prediction": pred,
        "decision": decision,
        "ml_window_source": source,
        "metric_simulator_scenario": get_simulator().get_scenario(),
        "ml_input": {
            "namespace": NS,
            "feature_order": list(METRIC_NAMES),
            "lookback_steps": len(window),
            "window": window,
            "timestamps_tail_ms": timestamps_tail_ms,
            "description": (
                "Rows are oldest→newest time steps fed to the model; each row matches feature_order "
                "(raw units from the metrics adapter, e.g. CPU %, req/s, ms)."
            ),
        },
    }


@router.get("/charts/forecast")
async def forecast_chart(
    preset: str | None = Query(
        None,
        description="Optional frozen window preset for chart (matches /prediction/run).",
    ),
) -> dict[str, Any]:
    """ED-LSTM future trend for visualization (uses last window)."""
    window, _, source = await build_feature_window(24, preset=preset)
    adapter = get_model_inference_adapter()
    pred = await adapter.predict(window)
    future = pred.get("predicted_future")
    if isinstance(future, list) and future and isinstance(future[0], list):
        series = future[0]
    else:
        series = pred.get("predicted_next", [])
    return {"forecast": series, "raw": pred, "ml_window_source": source}
