"""claude_synthesis — mock the Anthropic client; verify request shape and response handling."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers.vix_tier import TierResult  # noqa: E402
from fetchers.market_data import Quote  # noqa: E402
from reporters import claude_synthesis  # noqa: E402


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _sample_report() -> dict[str, Any]:
    """Tier-2 day with TSM near 52w high and SOFI inside the 7d earnings window."""
    tier = TierResult(
        name="tier_2",
        index=2,
        action="觀察",
        cash_target_pct=50,
        buy_list=["GOOGL", "TSM"],
        vix_range=(18.0, 24.6),
        sell_list=None,
        buy_size_pct="3-5",
        note=None,
    )
    return {
        "date": "2026-04-26",
        "vix_value": 18.71,
        "tier": tier,
        "snapshot": {
            "VIX": Quote(symbol="^VIX", label="VIX", last=18.71, change_pct=-0.031),
            "BAD": Quote(symbol="X", label="BAD", error="boom"),
        },
        "holdings": {
            "TSM": {
                "last": 402.46, "vs_avg_cost": 0.094, "rsi_14": 68.0,
                "pct_from_ma_50": 0.127, "pct_from_ma_200": 0.336,
                "pct_from_52w_high": 0.0,
                "flags": ["near_52w_high", "buy_list_member"],
                "tags": ["semi", "high_beta"], "account": "Exness",
                "days_to_earnings": None, "earnings_date": None,
            },
            "SOFI": {
                "last": 18.44, "vs_avg_cost": -0.297, "rsi_14": 55.0,
                "pct_from_ma_50": 0.034, "pct_from_ma_200": -0.227,
                "pct_from_52w_high": -0.428,
                "flags": [
                    "below_200dma", "deep_drawdown", "underwater",
                    "earnings_within_7d", "earnings_within_3d",
                    "high_risk_tag", "event_play",
                ],
                "tags": ["fintech", "high_risk", "muddy_waters_target"],
                "days_to_earnings": 3, "earnings_date": "2026-04-29",
                "account": "Taiwan_Brokerage",
            },
        },
        "accounts": {},
    }


# Minimal fakes that mimic the parts of the anthropic SDK response we touch.

@dataclass
class FakeUsage:
    input_tokens: int = 1234
    output_tokens: int = 256
    cache_read_input_tokens: int | None = 1100


@dataclass
class FakeToolUse:
    type: str
    name: str
    input: dict[str, Any]


@dataclass
class FakeResponse:
    content: list[Any]
    usage: FakeUsage = field(default_factory=FakeUsage)
    stop_reason: str = "tool_use"


class FakeMessages:
    def __init__(self, response: FakeResponse, captured: dict[str, Any]):
        self._response = response
        self._captured = captured

    def create(self, **kwargs):
        self._captured.update(kwargs)
        return self._response


class FakeClient:
    def __init__(self, response: FakeResponse, captured: dict[str, Any]):
        self.messages = FakeMessages(response, captured)


def _good_response() -> FakeResponse:
    payload = {
        "market": {
            "read": "Tier 2 — quality growth small entries.",
            "devils_advocate": "VIX 18.7 is mid-range; a hawkish Fed surprise breaks this.",
        },
        "positions": [
            {
                "symbol": "TSM", "action": "hold", "confidence": "medium",
                "rationale": "Buy-list member but pinned at 52w high — wait for pullback.",
            },
            {
                "symbol": "SOFI", "action": "hold", "confidence": "high",
                "rationale": "Earnings in 3d, Muddy Waters report active — no add allowed.",
            },
        ],
    }
    return FakeResponse(
        content=[FakeToolUse(
            type="tool_use",
            name=claude_synthesis.SYNTHESIS_TOOL["name"],
            input=payload,
        )],
    )


@pytest.fixture
def captured(monkeypatch):
    """Patch anthropic.Anthropic, capture the request kwargs, and return the dict."""
    captured: dict[str, Any] = {}
    fake_response = _good_response()
    monkeypatch.setattr(
        claude_synthesis.anthropic, "Anthropic",
        lambda *a, **kw: FakeClient(fake_response, captured),
    )
    return captured


# ── Tests ────────────────────────────────────────────────────────────────────


def test_returns_structured_payload_with_metadata(captured):
    out = claude_synthesis.synthesize(_sample_report())
    assert out["market"]["read"].startswith("Tier 2")
    assert any(p["symbol"] == "SOFI" for p in out["positions"])
    assert out["model"] == claude_synthesis.MODEL
    assert out["usage"]["input_tokens"] == 1234
    assert out["usage"]["output_tokens"] == 256
    assert out["usage"]["cache_read_input_tokens"] == 1100


def test_request_uses_correct_model_and_tool_choice(captured):
    claude_synthesis.synthesize(_sample_report())
    assert captured["model"] == claude_synthesis.MODEL
    assert captured["max_tokens"] == claude_synthesis.MAX_TOKENS
    assert captured["tool_choice"] == {
        "type": "tool", "name": claude_synthesis.SYNTHESIS_TOOL["name"],
    }
    assert captured["tools"] == [claude_synthesis.SYNTHESIS_TOOL]


def test_system_prompt_uses_cache_control_block(captured):
    claude_synthesis.synthesize(_sample_report())
    system = captured["system"]
    assert isinstance(system, list) and len(system) == 1
    assert system[0]["type"] == "text"
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert "VIX tier system" in system[0]["text"]


def test_system_prompt_includes_sofi_and_tsm_special_rules(captured):
    """SOFI Muddy-Waters rule and TSM Taiwan-Strait rule must be in §2.4 verbatim intent."""
    claude_synthesis.synthesize(_sample_report())
    sys_text = captured["system"][0]["text"]
    assert "SOFI" in sys_text
    assert "Muddy Waters" in sys_text
    assert "earnings_within_7d" in sys_text  # the explicit guard
    assert "TSM" in sys_text
    assert "Taiwan" in sys_text


def test_system_prompt_includes_phase_2_5_sensitivity_tag_rules(captured):
    """Phase 2.5: prompt must teach the model how to factor sensitivity_tags into action calls."""
    claude_synthesis.synthesize(_sample_report())
    sys_text = captured["system"][0]["text"]
    # Each tag's directional rule should be present
    for tag in ("crisis_alpha", "defensive", "mean_reverter", "high_normal", "high_stress"):
        assert tag in sys_text, f"missing tag rule: {tag}"
    # Explicit handling for tickers outside the regime universe (SOFI/IONQ/PLTR)
    assert "missing_from_universe" in sys_text


def test_user_payload_includes_sensitivity_tags_field(captured):
    """sensitivity_tags + missing_from_universe must reach the model even when absent in input."""
    claude_synthesis.synthesize(_sample_report())
    user_msg = captured["messages"][0]["content"]
    assert "sensitivity_tags" in user_msg
    assert "missing_from_universe" in user_msg


def test_user_payload_contains_holdings_facts_and_skips_errored_quotes(captured):
    claude_synthesis.synthesize(_sample_report())
    user_msg = captured["messages"][0]["content"]
    assert '"SOFI"' in user_msg
    assert "earnings_within_3d" in user_msg
    assert "muddy_waters_target" in user_msg
    # errored snapshot quote must be dropped so the model isn't fed bad data
    assert "BAD" not in user_msg


def test_user_payload_includes_tier_action_and_buy_list(captured):
    claude_synthesis.synthesize(_sample_report())
    user_msg = captured["messages"][0]["content"]
    assert "tier_2" in user_msg
    assert "GOOGL" in user_msg and "TSM" in user_msg


def test_raises_when_no_tool_use_block(monkeypatch):
    bad = FakeResponse(content=[SimpleNamespace(type="text", text="hello")])
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        claude_synthesis.anthropic, "Anthropic",
        lambda *a, **kw: FakeClient(bad, captured),
    )
    with pytest.raises(RuntimeError, match="no 'emit_todays_take' tool_use"):
        claude_synthesis.synthesize(_sample_report())


def test_tool_schema_pins_action_and_confidence_enums():
    """Schema is the contract for downstream renderers — guard the enums against drift."""
    schema = claude_synthesis.SYNTHESIS_TOOL["input_schema"]
    pos_item = schema["properties"]["positions"]["items"]
    assert pos_item["properties"]["action"]["enum"] == claude_synthesis.ACTION_ENUM
    assert pos_item["properties"]["confidence"]["enum"] == claude_synthesis.CONFIDENCE_ENUM
    assert set(schema["properties"]["market"]["properties"]) == {"read", "devils_advocate"}
    assert pos_item["required"] == ["symbol", "action", "confidence", "rationale"]


def test_holding_with_fetch_error_passes_through_as_error(captured):
    report = _sample_report()
    report["holdings"]["DEAD"] = {"error": "no history"}
    claude_synthesis.synthesize(report)
    user_msg = captured["messages"][0]["content"]
    assert '"DEAD"' in user_msg
    assert '"no history"' in user_msg


# ── Phase 2.5 Commit 7: payload normalization (tool_use schema-violation defense) ──
#
# Anthropic's tool_use input_schema is a guide, not a server-side validator.
# These tests pin the normalization behavior for known model-shape variances.


def _norm_response(payload: dict[str, Any]) -> "FakeResponse":
    return FakeResponse(content=[FakeToolUse(
        type="tool_use",
        name=claude_synthesis.SYNTHESIS_TOOL["name"],
        input=payload,
    )])


def _patched_with(monkeypatch, payload: dict[str, Any]) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        claude_synthesis.anthropic, "Anthropic",
        lambda *a, **kw: FakeClient(_norm_response(payload), captured),
    )
    return captured


def test_normalize_market_collapsed_to_string(monkeypatch, caplog):
    """The exact production bug MIRA caught — model returns market as a flat string."""
    _patched_with(monkeypatch, {
        "market": "VIX 18 — Tier 2 quality entries; bull-case the term-structure flips against us.",
        "positions": [],
    })
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    assert isinstance(out["market"], dict)
    assert out["market"]["read"].startswith("VIX 18")
    assert out["market"]["devils_advocate"] == ""
    assert any("collapsed to string" in r.message for r in caplog.records)


def test_normalize_market_missing_devils_advocate(monkeypatch, caplog):
    """Half-populated market dict — preserve read, default devils to empty string."""
    _patched_with(monkeypatch, {
        "market": {"read": "Tier 2 read."},  # devils_advocate absent
        "positions": [],
    })
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    assert out["market"]["read"] == "Tier 2 read."
    assert out["market"]["devils_advocate"] == ""


def test_normalize_market_entirely_missing(monkeypatch, caplog):
    _patched_with(monkeypatch, {"positions": []})  # no market at all
    out = claude_synthesis.synthesize(_sample_report())
    assert out["market"] == {"read": "", "devils_advocate": ""}


def test_normalize_drops_position_with_invalid_action(monkeypatch, caplog):
    _patched_with(monkeypatch, {
        "market": {"read": "x", "devils_advocate": "y"},
        "positions": [
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "ok"},
            {"symbol": "SOFI", "action": "buy", "confidence": "high", "rationale": "bad action"},  # 'buy' not in enum
        ],
    })
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    syms = [p["symbol"] for p in out["positions"]]
    assert syms == ["TSM"]
    assert any("not in enum" in r.message and "SOFI" in r.message for r in caplog.records)


def test_normalize_drops_position_missing_symbol(monkeypatch):
    _patched_with(monkeypatch, {
        "market": {"read": "x", "devils_advocate": "y"},
        "positions": [
            {"action": "hold", "confidence": "low", "rationale": "no symbol"},
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "ok"},
        ],
    })
    out = claude_synthesis.synthesize(_sample_report())
    assert [p["symbol"] for p in out["positions"]] == ["TSM"]


def test_normalize_position_invalid_confidence_defaults_low(monkeypatch, caplog):
    _patched_with(monkeypatch, {
        "market": {"read": "x", "devils_advocate": "y"},
        "positions": [
            {"symbol": "TSM", "action": "hold", "confidence": "very-high", "rationale": "out of enum"},
        ],
    })
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    assert out["positions"][0]["confidence"] == "low"
    assert any("very-high" in r.message for r in caplog.records)


def test_normalize_drops_non_dict_position(monkeypatch):
    _patched_with(monkeypatch, {
        "market": {"read": "x", "devils_advocate": "y"},
        "positions": [
            "TSM hold medium ok",  # string instead of dict
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "ok"},
        ],
    })
    out = claude_synthesis.synthesize(_sample_report())
    assert [p["symbol"] for p in out["positions"]] == ["TSM"]


def test_normalize_positions_not_a_list_coerced_to_empty(monkeypatch, caplog):
    _patched_with(monkeypatch, {
        "market": {"read": "x", "devils_advocate": "y"},
        "positions": "not a list at all",
    })
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    assert out["positions"] == []


def test_normalize_clean_payload_unchanged(monkeypatch, caplog):
    """Happy path — well-formed payload passes through without warnings."""
    clean = {
        "market": {"read": "Tier 2 read.", "devils_advocate": "Bear case."},
        "positions": [
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "fine"},
        ],
    }
    _patched_with(monkeypatch, clean)
    with caplog.at_level("WARNING"):
        out = claude_synthesis.synthesize(_sample_report())
    assert out["market"] == clean["market"]
    assert out["positions"][0]["symbol"] == "TSM"
    norm_warnings = [r for r in caplog.records if "synthesis normalize" in r.message]
    assert norm_warnings == []  # zero warnings on clean input


def test_system_prompt_explicitly_forbids_market_string_collapse(captured):
    """Belt-and-braces: prompt must instruct the model not to collapse market into a string."""
    claude_synthesis.synthesize(_sample_report())
    sys_text = captured["system"][0]["text"]
    # The exact failure mode we hit in production
    assert "Never" in sys_text and "collapse" in sys_text
    assert "read" in sys_text and "devils_advocate" in sys_text
