"""Watch List sensitivity_tag rendering — Phase 2.5 Commit 5."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from reporters.markdown_gen import _render_watch_list, _tier_relevant_sensitivity_tags  # noqa: E402


# ── _tier_relevant_sensitivity_tags filtering rules ──────────────────────────

def test_tier_0_2_surfaces_high_normal_only():
    # Tier 1, has all sensitivity tags → only high_normal + defensive expected.
    out = _tier_relevant_sensitivity_tags(1, ["high_normal", "high_stress", "crisis_alpha", "defensive"])
    assert "high_normal" in out
    assert "high_stress" not in out
    assert "crisis_alpha" not in out
    assert "defensive" in out


def test_tier_3_plus_surfaces_high_stress_and_crisis_alpha():
    out = _tier_relevant_sensitivity_tags(3, ["high_normal", "high_stress", "crisis_alpha", "defensive"])
    assert "high_normal" not in out
    assert "high_stress" in out
    assert "crisis_alpha" in out
    assert "defensive" in out


def test_defensive_always_surfaces_regardless_of_tier():
    for tier in (0, 1, 2, 3, 4, 5):
        out = _tier_relevant_sensitivity_tags(tier, ["defensive"])
        assert out == ["defensive"]


def test_no_sensitivity_tags_returns_empty():
    assert _tier_relevant_sensitivity_tags(2, []) == []


def test_mean_reverter_intentionally_not_surfaced():
    # Synthesis prompt handles transition triggers, not the static Watch List.
    out = _tier_relevant_sensitivity_tags(2, ["mean_reverter"])
    assert "mean_reverter" not in out


# ── End-to-end Watch List render ─────────────────────────────────────────────

def _watchworthy_holding(symbol: str, tier_idx: int, tags: list[str]) -> dict:
    return {
        "account": "Exness",
        "tier_index": tier_idx,
        "flags": ["buy_list_member", "oversold_rsi"],  # is_watchworthy returns True
        "sensitivity_tags": tags,
    }


def test_watch_list_renders_divider_and_tier_relevant_tags():
    holdings = {"TSLA": _watchworthy_holding("TSLA", 2, ["high_normal", "high_stress"])}
    out = "\n".join(_render_watch_list(holdings))
    assert "## 🚩 Watch List" in out
    assert "TSLA" in out
    assert "⋮" in out
    assert "high_normal" in out
    # Tier 2 → high_stress filtered out:
    assert "high_stress" not in out


def test_watch_list_omits_divider_when_no_tier_relevant_tags():
    # Tier 4 holding with only mean_reverter → not surfaced → no divider.
    holdings = {"NVDA": _watchworthy_holding("NVDA", 4, ["mean_reverter"])}
    out = "\n".join(_render_watch_list(holdings))
    assert "NVDA" in out
    assert "⋮" not in out


def test_watch_list_omits_divider_when_holding_lacks_sensitivity_tags():
    holdings = {"SOFI": _watchworthy_holding("SOFI", 2, [])}
    out = "\n".join(_render_watch_list(holdings))
    assert "SOFI" in out
    assert "⋮" not in out


def test_watch_list_section_skipped_when_no_watchworthy_rows():
    # is_watchworthy returns False for empty flags, so no section emitted.
    holdings = {"AAPL": {"account": "Exness", "tier_index": 2, "flags": [], "sensitivity_tags": ["defensive"]}}
    assert _render_watch_list(holdings) == []
