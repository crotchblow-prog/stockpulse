"""Translator — mock the Anthropic client; verify prompts, structure, and metadata passthrough."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from reporters import translator  # noqa: E402


# ── Fakes ────────────────────────────────────────────────────────────────────


@dataclass
class FakeUsage:
    input_tokens: int = 1500
    output_tokens: int = 1500
    cache_read_input_tokens: int | None = 0


@dataclass
class FakeText:
    type: str
    text: str


@dataclass
class FakeToolUse:
    type: str
    name: str
    input: dict[str, Any]


@dataclass
class FakeResponse:
    content: list[Any]
    usage: FakeUsage = field(default_factory=FakeUsage)
    stop_reason: str = "end_turn"


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


# ── translate_markdown ───────────────────────────────────────────────────────


def test_translate_markdown_returns_translated_body(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeText(type="text", text="# 每日市場 — 2026-04-26\n\n本文。")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    out = translator.translate_markdown("# Daily Market — 2026-04-26\n\nBody.")
    assert "每日市場" in out
    assert out.endswith("\n")  # always trailing newline


def test_translate_markdown_uses_cache_control_and_correct_model(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeText(type="text", text="x")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    translator.translate_markdown("hi")
    assert captured["model"] == translator.MODEL
    sys_blocks = captured["system"]
    assert isinstance(sys_blocks, list)
    assert sys_blocks[0]["cache_control"] == {"type": "ephemeral"}
    # Core rules must be in the prompt — guards against silent prompt drift.
    sys_text = sys_blocks[0]["text"]
    assert "Ticker symbols" in sys_text
    assert "Flag names" in sys_text
    assert "Action verbs" in sys_text
    assert "今日觀點" in sys_text  # section header mapping example


def test_translate_markdown_prompt_handles_universe_scanner_section(monkeypatch):
    """Phase 2.5: prompt must teach translation rules for the new Universe Scanner section."""
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeText(type="text", text="x")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    translator.translate_markdown("hi")
    sys_text = captured["system"][0]["text"]
    assert "Universe Scanner" in sys_text
    assert "標的掃描" in sys_text
    assert "加碼候選" in sys_text
    assert "避開候選" in sys_text
    # Sensitivity tags treated like flag names (verbatim in code spans).
    for tag in ("high_normal", "crisis_alpha", "mean_reverter", "defensive"):
        assert tag in sys_text


def test_translate_markdown_sends_full_input_as_user_message(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeText(type="text", text="x")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    big = "# Heading\n\n" + ("body line\n" * 100)
    translator.translate_markdown(big)
    assert captured["messages"][0]["content"] == big


def test_translate_markdown_raises_when_no_text_block(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[SimpleNamespace(type="tool_use")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    with pytest.raises(RuntimeError, match="no text blocks"):
        translator.translate_markdown("hi")


# ── translate_synthesis ──────────────────────────────────────────────────────


def _en_synthesis() -> dict[str, Any]:
    return {
        "market": {"read": "Tier 2 — quality growth small entries.",
                   "devils_advocate": "VIX3M contango may flip via spot spike."},
        "positions": [
            {"symbol": "SOFI", "action": "trim", "confidence": "high",
             "rationale": "Earnings in 3 days, Muddy Waters report active."},
        ],
        "model": "claude-sonnet-4-6",
        "usage": {"input_tokens": 3000, "output_tokens": 600, "cache_read_input_tokens": 0},
    }


def _zh_translated_payload() -> dict[str, Any]:
    return {
        "market": {"read": "Tier 2 — 高品質成長股小額進場。",
                   "devils_advocate": "VIX3M contango 可能因現貨飆升而反轉。"},
        "positions": [
            {"symbol": "SOFI", "action": "trim", "confidence": "high",
             "rationale": "3 天後財報，Muddy Waters 做空報告仍在發酵中。"},
        ],
    }


def test_translate_synthesis_preserves_structure_and_metadata(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeToolUse(
        type="tool_use",
        name=translator.SYNTHESIS_TRANSLATE_TOOL["name"],
        input=_zh_translated_payload(),
    )])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    en = _en_synthesis()
    out = translator.translate_synthesis(en)

    # Translated fields are zh
    assert "高品質成長股" in out["market"]["read"]
    assert "Muddy Waters" in out["positions"][0]["rationale"]  # keyword stays English

    # Symbol/action/confidence stay verbatim
    assert out["positions"][0]["symbol"] == "SOFI"
    assert out["positions"][0]["action"] == "trim"
    assert out["positions"][0]["confidence"] == "high"

    # Metadata passed through from original — provenance preserved across the language pair
    assert out["model"] == "claude-sonnet-4-6"
    assert out["usage"]["input_tokens"] == 3000


def test_translate_synthesis_uses_tool_choice_for_strict_json(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeToolUse(
        type="tool_use",
        name=translator.SYNTHESIS_TRANSLATE_TOOL["name"],
        input=_zh_translated_payload(),
    )])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    translator.translate_synthesis(_en_synthesis())
    assert captured["tool_choice"] == {
        "type": "tool", "name": translator.SYNTHESIS_TRANSLATE_TOOL["name"],
    }
    assert captured["tools"] == [translator.SYNTHESIS_TRANSLATE_TOOL]


def test_translate_synthesis_only_sends_market_and_positions(monkeypatch):
    """Metadata (model, usage) must NOT be sent to the model — saves tokens, avoids confusion."""
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeToolUse(
        type="tool_use",
        name=translator.SYNTHESIS_TRANSLATE_TOOL["name"],
        input=_zh_translated_payload(),
    )])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    translator.translate_synthesis(_en_synthesis())
    user_payload = json.loads(captured["messages"][0]["content"])
    assert set(user_payload.keys()) == {"market", "positions"}
    assert "model" not in user_payload
    assert "usage" not in user_payload


def test_translate_synthesis_raises_when_no_tool_use(monkeypatch):
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeText(type="text", text="hello")])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    with pytest.raises(RuntimeError, match="no 'emit_translated_synthesis' tool_use"):
        translator.translate_synthesis(_en_synthesis())


def test_translate_synthesis_handles_missing_metadata_gracefully(monkeypatch):
    """Even if the EN dict has no model/usage, output should still be valid (no KeyError)."""
    captured: dict[str, Any] = {}
    fake = FakeResponse(content=[FakeToolUse(
        type="tool_use",
        name=translator.SYNTHESIS_TRANSLATE_TOOL["name"],
        input=_zh_translated_payload(),
    )])
    monkeypatch.setattr(translator.anthropic, "Anthropic", lambda *a, **kw: FakeClient(fake, captured))

    out = translator.translate_synthesis({"market": {"read": "x", "devils_advocate": "y"}, "positions": []})
    assert "model" not in out
    assert "usage" not in out
    assert "market" in out and "positions" in out
