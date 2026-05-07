from __future__ import annotations

"""Load frozen ML windows from `data/demo_windows/predefined_windows.json` for repeatable demos."""

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_JSON = _REPO_ROOT / "data" / "demo_windows" / "predefined_windows.json"


@lru_cache
def _load_doc() -> dict:
    raw = _DEFAULT_JSON.read_text(encoding="utf-8")
    return json.loads(raw)


def predefined_windows_path() -> Path:
    return _DEFAULT_JSON


def list_demo_window_presets() -> list[str]:
    doc = _load_doc()
    windows = doc.get("windows") or {}
    return sorted(windows.keys())


def demo_window_documentation() -> dict:
    doc = _load_doc()
    return {
        "path": str(_DEFAULT_JSON.relative_to(_REPO_ROOT)),
        "description": doc.get("description"),
        "feature_order": doc.get("feature_order"),
        "presets": list_demo_window_presets(),
    }


def get_demo_window(preset: str, lookback: int) -> list[list[float]] | None:
    """Return a copy of `windows[preset]` trimmed or padded to `lookback`; None if preset missing."""
    doc = _load_doc()
    raw_map = doc.get("windows") or {}
    candidate = raw_map.get(preset)
    if candidate is None or not isinstance(candidate, list) or len(candidate) == 0:
        return None

    rows: list[list[float]] = [[float(x) for x in row] for row in candidate]
    lb = max(1, lookback)
    if len(rows) >= lb:
        window = rows[-lb:]
        return deepcopy(window)
    pad = lb - len(rows)
    last = rows[-1]
    window = deepcopy(rows)
    window.extend(deepcopy([last]) * pad)
    return window
