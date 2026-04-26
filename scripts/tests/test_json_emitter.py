"""JSON sidecar shape, NaN coercion, dataclass flattening — the synthesis contract."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers.vix_tier import TierResult  # noqa: E402
from fetchers.market_data import Quote  # noqa: E402
from reporters import json_emitter  # noqa: E402


def _sample_report(date: str = "2026-04-26") -> dict:
    """Minimal but realistic in-memory report dict matching what generate_report.py builds."""
    tier = TierResult(
        name="tier_2",
        index=2,
        action="觀察",
        cash_target_pct=50,
        buy_list=["GOOGL", "MSFT"],
        vix_range=(18.0, 24.6),
        sell_list=None,
        buy_size_pct="3-5",
        note="避開財報前 7 天的標的",
    )
    return {
        "date": date,
        "vix_value": 18.71,
        "tier": tier,
        "snapshot": {
            "VIX": Quote(symbol="^VIX", label="VIX", last=18.71, prev_close=19.31,
                         change=-0.60, change_pct=-0.0311),
            "S&P 500": Quote(symbol="^GSPC", label="S&P 500", last=7165.08,
                             prev_close=7108.40, change=56.68, change_pct=0.008),
        },
        "holdings": {
            "TSM": {
                "last": 402.46, "vs_avg_cost": 0.0943, "rsi_14": 68.0,
                "flags": ["overbought_rsi", "buy_list_member"],
                "earnings": {"date": "2026-04-30", "days_to_earnings": 4},
            },
            "SOFI": {
                "last": 18.44, "vs_avg_cost": -0.2973,
                "flags": ["below_200dma", "deep_drawdown", "underwater"],
            },
        },
        "accounts": {"Exness": {"cash_target": 0.50}},
    }


def test_payload_has_schema_version_and_top_level_fields():
    payload = json_emitter.build_payload(_sample_report())
    assert payload["schema_version"] == 1
    for key in ("date", "vix_value", "tier", "snapshot", "holdings", "accounts"):
        assert key in payload
    assert "synthesis" not in payload  # absent when not provided


def test_tier_dataclass_flattened_to_dict():
    payload = json_emitter.build_payload(_sample_report())
    tier = payload["tier"]
    assert isinstance(tier, dict)
    assert tier["name"] == "tier_2"
    assert tier["index"] == 2
    assert tier["vix_range"] == [18.0, 24.6]


def test_snapshot_quotes_flattened():
    payload = json_emitter.build_payload(_sample_report())
    vix = payload["snapshot"]["VIX"]
    assert isinstance(vix, dict)
    assert vix["last"] == 18.71
    assert vix["error"] is None


def test_holdings_preserve_attached_subfields():
    payload = json_emitter.build_payload(_sample_report())
    tsm = payload["holdings"]["TSM"]
    assert tsm["flags"] == ["overbought_rsi", "buy_list_member"]
    assert tsm["earnings"]["days_to_earnings"] == 4


def test_nan_inf_coerced_to_null():
    report = _sample_report()
    report["holdings"]["NaNHolder"] = {"rsi_14": math.nan, "vs_avg_cost": math.inf,
                                       "ma_50": -math.inf, "last": 1.23}
    payload = json_emitter.build_payload(report)
    h = payload["holdings"]["NaNHolder"]
    assert h["rsi_14"] is None
    assert h["vs_avg_cost"] is None
    assert h["ma_50"] is None
    assert h["last"] == 1.23


def test_synthesis_block_round_trips_when_present():
    report = _sample_report()
    report["synthesis"] = {"model": "claude-sonnet-4-6", "todays_take": "..."}
    payload = json_emitter.build_payload(report)
    assert payload["synthesis"]["model"] == "claude-sonnet-4-6"


def test_write_creates_dated_and_latest(tmp_path: Path):
    report = _sample_report("2026-04-26")
    dated, latest = json_emitter.write("2026-04-26", tmp_path, report)
    assert dated.name == "2026-04-26.json"
    assert latest.name == "latest.json"
    parsed = json.loads(latest.read_text(encoding="utf-8"))
    assert parsed == json.loads(dated.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == 1
    assert parsed["tier"]["name"] == "tier_2"


def test_write_round_trip_is_strict_json(tmp_path: Path):
    report = _sample_report()
    report["holdings"]["BadFloats"] = {"x": math.nan, "y": math.inf}
    json_emitter.write("2026-04-26", tmp_path, report)
    text = (tmp_path / "latest.json").read_text(encoding="utf-8")
    parsed = json.loads(text)  # would fail if NaN/Inf weren't coerced
    assert parsed["holdings"]["BadFloats"]["x"] is None
    assert parsed["holdings"]["BadFloats"]["y"] is None
