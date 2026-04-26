"""Sidecar JSON writer — the synthesis contract. Bump SCHEMA_VERSION on field rename/removal."""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def build_payload(report: dict[str, Any]) -> dict[str, Any]:
    """Shape the in-memory report dict into the canonical JSON payload (schema_version=1)."""
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "date": report["date"],
        "vix_value": report.get("vix_value"),
        "tier": _serialize(report.get("tier")),
        "snapshot": {label: _serialize(q) for label, q in (report.get("snapshot") or {}).items()},
        "holdings": _serialize_holdings(report.get("holdings") or {}),
        "accounts": report.get("accounts") or {},
    }
    if "synthesis" in report:
        payload["synthesis"] = _serialize(report["synthesis"])
    return _coerce_nan(payload)


def write(date: str, reports_dir: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    """Write {date}.json and latest.json into reports_dir; returns the two paths written."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(report)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    dated = reports_dir / f"{date}.json"
    latest = reports_dir / "latest.json"
    dated.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    log.info("wrote %s and %s", dated.name, latest.name)
    return dated, latest


def _serialize_holdings(holdings: dict[str, Any]) -> dict[str, Any]:
    """Shape per-symbol holding dicts; preserve any 'flags' / 'earnings' fields that callers attach."""
    out: dict[str, Any] = {}
    for sym, data in holdings.items():
        out[sym] = _serialize(data)
    return out


def _serialize(value: Any) -> Any:
    """Recursively convert dataclasses, tuples, and lists into JSON-friendly primitives."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value
    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    # Fallback for pandas/numpy scalars and anything else with a sane repr.
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)


def _coerce_nan(value: Any) -> Any:
    """Replace NaN / +Inf / -Inf with None so the JSON is strictly valid."""
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(value, dict):
        return {k: _coerce_nan(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_nan(v) for v in value]
    return value
