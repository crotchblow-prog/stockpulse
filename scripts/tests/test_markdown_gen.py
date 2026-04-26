"""Watch List sensitivity_tag rendering — Phase 2.5 Commit 5."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from reporters.markdown_gen import _render_buy_list, _render_watch_list, _tier_relevant_sensitivity_tags  # noqa: E402


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


# ── Universe Scanner (Phase 2.5 Commit 6) ────────────────────────────────────

from reporters.markdown_gen import _render_universe_scanner, render  # noqa: E402

def _u(beta_normal=1.0, beta_stress=1.0, spike_decay=0.0, spike_decay_p25=None,
       crush_recovery=0.0, sensitivity_tags=None, confidence="high",
       spike_count=20, crush_count=20, stress_weeks=50, normal_weeks=200):
    # spike_decay_p25 defaults to median when caller doesn't differentiate — the test
    # only exercises one regime at a time. Commit 8 added p25 as a separate field.
    return {
        "beta_normal": beta_normal,
        "beta_stress": beta_stress,
        "vix_spike_decay_pct": spike_decay,
        "vix_spike_decay_p25_pct": spike_decay if spike_decay_p25 is None else spike_decay_p25,
        "vix_crush_recovery_pct": crush_recovery,
        "spike_event_count": spike_count,
        "crush_event_count": crush_count,
        "stress_weeks": stress_weeks,
        "normal_weeks": normal_weeks,
        "confidence": confidence,
        "sensitivity_tags": sensitivity_tags or [],
    }


def test_universe_scanner_tier_0_2_filters_for_high_normal():
    universe = {
        "TSLA": _u(beta_normal=2.0, sensitivity_tags=["high_normal"]),
        "KO": _u(beta_normal=0.2, sensitivity_tags=["defensive"]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    assert "## 📡 Universe Scanner — Tier 2" in out
    assert "🟢 Add candidates" in out
    assert "high_normal" in out
    # Tier 2 → Add filter is high_normal → TSLA appears in Add, KO does not.
    add_section = out.split("🟡 Watch")[0]
    assert "TSLA" in add_section
    assert "KO" not in add_section


def test_universe_scanner_tier_3_filters_for_defensive():
    universe = {
        "TSLA": _u(beta_normal=2.0, sensitivity_tags=["high_normal"]),
        "KO": _u(beta_normal=0.2, sensitivity_tags=["defensive"]),
    }
    out = "\n".join(_render_universe_scanner(3, "分批進場", universe))
    add_section = out.split("🟡 Watch")[0]
    # Tier 3 → Add filter is defensive → KO appears, TSLA does not.
    assert "KO" in add_section
    assert "TSLA" not in add_section


def test_universe_scanner_tier_5_uses_defensive_filter_like_tier_3_4():
    universe = {"KO": _u(beta_normal=0.2, sensitivity_tags=["defensive"])}
    out = "\n".join(_render_universe_scanner(5, "極端機會", universe))
    assert "## 📡 Universe Scanner — Tier 5" in out
    assert "KO" in out


def test_universe_scanner_top_5_truncation_with_alpha_tiebreak():
    # Six high_normal candidates; same |beta_normal| for the tiebreak case.
    universe = {
        "AAA": _u(beta_normal=2.5, sensitivity_tags=["high_normal"]),
        "BBB": _u(beta_normal=2.0, sensitivity_tags=["high_normal"]),
        "CCC": _u(beta_normal=2.0, sensitivity_tags=["high_normal"]),  # tie with BBB
        "DDD": _u(beta_normal=1.8, sensitivity_tags=["high_normal"]),
        "EEE": _u(beta_normal=1.6, sensitivity_tags=["high_normal"]),
        "FFF": _u(beta_normal=1.5, sensitivity_tags=["high_normal"]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    add_section = out.split("🟡 Watch")[0]
    # Top 5 by abs(beta_normal) descending → AAA, BBB, CCC, DDD, EEE — FFF excluded.
    assert "FFF" not in add_section
    for s in ("AAA", "BBB", "CCC", "DDD", "EEE"):
        assert s in add_section
    # Alpha tiebreak: BBB before CCC (both at 2.0).
    assert add_section.index("BBB") < add_section.index("CCC")


def test_universe_scanner_empty_sub_region_renders_placeholder():
    # No candidates fire any filter.
    universe = {"AAPL": _u(sensitivity_tags=[])}
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    assert "_no candidates at current thresholds_" in out
    # All three sub-region headers must still be present.
    assert "🟢 Add candidates" in out
    assert "🟡 Watch (transition)" in out
    assert "🔴 Avoid candidates" in out


def test_universe_scanner_overlap_decorates_both_rows():
    # Same ticker tagged both high_normal and crisis_alpha → must appear in both
    # Add and Avoid with cross-warnings.
    universe = {
        "TSLA": _u(beta_normal=2.0, spike_decay=-12.3,
                   sensitivity_tags=["high_normal", "crisis_alpha"]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    add_section = out.split("🟡 Watch")[0]
    avoid_section = out.split("🔴 Avoid")[1]
    # Add row gets the warning, Avoid row gets the plain note.
    assert "⚠️ also in Avoid" in add_section
    assert "also in Add" in avoid_section
    # The warning emoji must NOT appear in the Avoid section row.
    avoid_lines = [ln for ln in avoid_section.split("\n") if "TSLA" in ln]
    assert len(avoid_lines) == 1
    assert "⚠️" not in avoid_lines[0]


def test_universe_scanner_excludes_low_confidence_tickers():
    universe = {
        "WEAK": _u(beta_normal=2.5, sensitivity_tags=["high_normal"], confidence="low"),
        "OK": _u(beta_normal=1.5, sensitivity_tags=["high_normal"], confidence="high"),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    add_section = out.split("🟡 Watch")[0]
    assert "OK" in add_section
    assert "WEAK" not in add_section


def test_universe_scanner_position_between_watch_list_and_holdings():
    """Section ordering invariant — Universe Scanner must land between Watch List and Holdings."""
    from analyzers.vix_tier import TierResult
    tier = TierResult(name="tier_2", index=2, action="觀察", cash_target_pct=50,
                      buy_list=[], vix_range=(18.0, 24.6))
    report = {
        "date": "2026-04-26",
        "vix_value": 18.71,
        "tier": tier,
        "snapshot": {},
        "holdings": {
            "TSM": {
                "account": "Exness", "tier_index": 2,
                "flags": ["near_52w_high", "buy_list_member"],
                "sensitivity_tags": ["high_normal"], "missing_from_universe": False,
                "last": 400.0, "vs_avg_cost": 0.1, "rsi_14": 60.0,
                "pct_from_ma_50": 0.05, "pct_from_ma_200": 0.10, "pct_from_52w_high": -0.02,
            },
        },
        "regime_universe": {"TSM": _u(beta_normal=1.4, sensitivity_tags=["high_normal"])},
    }
    out = render(report)
    # Substring positions establish the canonical order.
    pos_watch = out.index("🚩 Watch List")
    pos_scanner = out.index("📡 Universe Scanner")
    pos_holdings = out.index("💼 Holdings")
    assert pos_watch < pos_scanner < pos_holdings


def test_universe_scanner_missing_data_renders_graceful_placeholder():
    out = "\n".join(_render_universe_scanner(2, "觀察", None))
    assert "## 📡 Universe Scanner — Tier 2" in out
    assert "_universe data not loaded — run scripts/analyzers/regime_sensitivity.py_" in out
    # All three sub-region headers still present.
    assert "🟢 Add candidates" in out
    assert "🟡 Watch (transition)" in out
    assert "🔴 Avoid candidates" in out


def test_universe_scanner_empty_universe_renders_graceful_placeholder():
    out = "\n".join(_render_universe_scanner(2, "觀察", {}))
    assert "_universe data not loaded — run scripts/analyzers/regime_sensitivity.py_" in out


def test_universe_scanner_watch_transition_sorted_by_crush_recovery_desc():
    universe = {
        "BBB": _u(crush_recovery=8.0, spike_decay=-6.0, sensitivity_tags=["mean_reverter"]),
        "AAA": _u(crush_recovery=10.0, spike_decay=-7.0, sensitivity_tags=["mean_reverter"]),
        "CCC": _u(crush_recovery=6.0, spike_decay=-5.5, sensitivity_tags=["mean_reverter"]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    watch_section = out.split("🟡 Watch")[1].split("🔴 Avoid")[0]
    # Sort: AAA (10) > BBB (8) > CCC (6).
    assert watch_section.index("AAA") < watch_section.index("BBB") < watch_section.index("CCC")


def test_universe_scanner_avoid_sorted_by_abs_spike_decay_desc():
    universe = {
        "MILD": _u(spike_decay=-10.5, sensitivity_tags=["crisis_alpha"]),
        "WORST": _u(spike_decay=-25.3, sensitivity_tags=["crisis_alpha"]),
        "MID": _u(spike_decay=-15.0, sensitivity_tags=["crisis_alpha"]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    avoid_section = out.split("🔴 Avoid")[1]
    # Sort: WORST (-25.3) > MID (-15.0) > MILD (-10.5).
    assert avoid_section.index("WORST") < avoid_section.index("MID") < avoid_section.index("MILD")


# ── Commit 6.5: enriched empty-placeholder text with threshold gap ───────────

def test_watch_transition_empty_renders_single_axis_crush_gap():
    # Commit 10: mean_reverter is single-axis (crush > +0.6%); placeholder drops the AND-clause.
    # Three tickers, all under +0.6% recovery → none qualify, gap text shows best recovery.
    universe = {
        "AAA": _u(crush_recovery=0.5, sensitivity_tags=[]),  # best
        "BBB": _u(crush_recovery=0.3, sensitivity_tags=[]),
        "CCC": _u(crush_recovery=-0.5, sensitivity_tags=[]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    watch_section = out.split("🟡 Watch")[1].split("🔴 Avoid")[0]
    assert "best today: +0.50%" in watch_section
    assert "no candidates fire crush > +0.6%" in watch_section
    # No AND-clause anymore.
    assert "AND" not in watch_section.split("no candidates fire")[1].split("_")[0]


def test_avoid_empty_renders_gap_at_minus_4_threshold():
    # Commit 10: threshold tuned to -4% (was -10% pre-Commit 10, then proposed -5%
    # but data didn't reach -5%). Still uses p25 field (Commit 8 methodology).
    universe = {
        "AAA": _u(spike_decay=-2.0, spike_decay_p25=-3.0, sensitivity_tags=[]),
        "BBB": _u(spike_decay=-1.0, spike_decay_p25=-3.5, sensitivity_tags=[]),  # worst p25 just under -4
        "CCC": _u(spike_decay=1.5, spike_decay_p25=-1.0, sensitivity_tags=[]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    avoid_section = out.split("🔴 Avoid")[1]
    assert "worst today: -3.50%" in avoid_section
    assert "no candidates fire p25 decay < -4%" in avoid_section


def test_empty_regime_universe_still_shows_universe_data_not_loaded():
    # Regression check — the gap-enriched text MUST NOT clobber the
    # "universe data not loaded" message when there's no data to gap-against.
    out = "\n".join(_render_universe_scanner(2, "觀察", {}))
    assert "_universe data not loaded — run scripts/analyzers/regime_sensitivity.py_" in out
    # And we never render "best today" or "worst today" without data.
    assert "best today" not in out
    assert "worst today" not in out


def test_watch_transition_gap_falls_back_when_all_tickers_low_confidence():
    # All confidence == "low" → exclude from gap math. Render simple
    # threshold-only string with no parenthetical.
    universe = {
        "WEAK1": _u(crush_recovery=20.0, spike_decay=-50.0, spike_decay_p25=-60.0,
                    confidence="low", sensitivity_tags=[]),
        "WEAK2": _u(crush_recovery=15.0, spike_decay=-30.0, spike_decay_p25=-40.0,
                    confidence="low", sensitivity_tags=[]),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    watch_section = out.split("🟡 Watch")[1].split("🔴 Avoid")[0]
    assert "no candidates fire crush > +0.6%" in watch_section
    assert "best today" not in watch_section  # no parenthetical when no valid data
    avoid_section = out.split("🔴 Avoid")[1]
    assert "no candidates fire p25 decay < -4%" in avoid_section
    assert "worst today" not in avoid_section


# ── Commit 10.5: Sample column field swap + framework legend + bilingual heading ─

def test_add_sample_column_reads_normal_weeks_not_spike_event_count():
    # 🟢 Add row's metric is β normal (computed from normal-regime weeks). Sample
    # column should match that calculation basis. spike_event_count is unrelated.
    universe = {
        "TSLA": _u(beta_normal=2.5, sensitivity_tags=["high_normal"],
                   normal_weeks=180, spike_count=20),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    add_section = out.split("🟡 Watch")[0]
    # Find TSLA's row and assert it shows 180 (normal_weeks) not 20 (spike_event_count).
    tsla_line = next(line for line in add_section.split("\n") if "TSLA" in line)
    assert " 180 " in tsla_line
    assert " 20 " not in tsla_line.split("|")[3]  # Sample column (4th cell after leading |)


def test_avoid_sample_column_unchanged_uses_spike_event_count():
    # Regression: Avoid section's metric is spike decay; Sample stays on
    # spike_event_count via the existing min() conservatism (smallest of all four).
    universe = {
        "TSLA": _u(beta_normal=2.5, spike_decay=-15.0, spike_decay_p25=-12.0,
                   sensitivity_tags=["crisis_alpha"], spike_count=20,
                   crush_count=25, stress_weeks=50, normal_weeks=180),
    }
    out = "\n".join(_render_universe_scanner(2, "觀察", universe))
    avoid_section = out.split("🔴 Avoid")[1]
    tsla_line = next(line for line in avoid_section.split("\n") if "TSLA" in line)
    assert " 20 " in tsla_line  # min of {20, 25, 50, 180} = 20 (spike_count)


def test_universe_scanner_renders_framework_legend_and_bilingual_heading():
    universe = {"KO": _u(beta_normal=0.2, sensitivity_tags=["defensive"])}
    out = "\n".join(_render_universe_scanner(3, "分批進場", universe))
    # Bilingual heading
    assert "## 📡 Universe Scanner — Tier 3 (分批進場)" in out
    # Framework legend present, contains all three metric terms.
    assert "β normal" in out
    assert "Crush recovery" in out
    assert "Spike decay" in out
    # Legend is italic and lands BEFORE the first sub-region header.
    legend_idx = out.index("β normal")
    add_idx = out.index("🟢 Add candidates")
    assert legend_idx < add_idx


# ── Buy-list annotation (Phase 2.5 Commit 9) ─────────────────────────────────

def test_buy_list_no_synthesis_renders_plain_backticks():
    """Without synthesis (e.g. ANTHROPIC_API_KEY missing), buy list stays as plain ticker codes."""
    out = _render_buy_list(["GOOGL", "TSM", "AVGO"], synthesis=None)
    assert out == "`GOOGL`, `TSM`, `AVGO`"


def test_buy_list_annotates_held_tickers_with_synthesis_action():
    """The fix for the Tier-Action / Today's Take perceived contradiction."""
    synthesis = {
        "positions": [
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "..."},
        ],
    }
    out = _render_buy_list(["GOOGL", "TSM", "AVGO"], synthesis=synthesis)
    # Held + synthesized → annotated
    assert "`TSM` (hold)" in out
    # Pure framework candidates → plain
    assert "`GOOGL`," in out
    assert out.endswith("`AVGO`")


def test_buy_list_annotates_with_each_action_value():
    """Verify all five action enum values render correctly."""
    synthesis = {
        "positions": [
            {"symbol": "A", "action": "add", "confidence": "high", "rationale": ""},
            {"symbol": "B", "action": "hold", "confidence": "medium", "rationale": ""},
            {"symbol": "C", "action": "trim", "confidence": "high", "rationale": ""},
            {"symbol": "D", "action": "exit", "confidence": "low", "rationale": ""},
            {"symbol": "E", "action": "watch", "confidence": "low", "rationale": ""},
        ],
    }
    out = _render_buy_list(["A", "B", "C", "D", "E"], synthesis=synthesis)
    for sym, action in [("A", "add"), ("B", "hold"), ("C", "trim"), ("D", "exit"), ("E", "watch")]:
        assert f"`{sym}` ({action})" in out


def test_buy_list_skips_annotation_when_position_malformed():
    """Defense in depth — drop unannotated if position dict is missing fields."""
    synthesis = {
        "positions": [
            {"symbol": "TSM", "action": "hold", "confidence": "medium", "rationale": "ok"},
            {"symbol": "X"},  # no action
            {"action": "hold"},  # no symbol
            "not a dict",
        ],
    }
    out = _render_buy_list(["TSM", "X", "GOOGL"], synthesis=synthesis)
    assert "`TSM` (hold)" in out
    assert "`X`," in out  # no annotation, but ticker still rendered as plain
    assert out.endswith("`GOOGL`")


def test_buy_list_empty_synthesis_positions():
    """Synthesis present but positions empty (e.g. clean run with no holdings issued) — plain render."""
    out = _render_buy_list(["GOOGL"], synthesis={"positions": []})
    assert out == "`GOOGL`"
