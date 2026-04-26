"""Closed-vocab flag derivation — boundary cases plus the mandatory SOFI scenario."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers.flags import FLAG_VOCAB, FlagInputs, derive_flags, is_watchworthy  # noqa: E402


def _empty(symbol: str = "TEST", **overrides) -> FlagInputs:
    """Build a FlagInputs with all-None numerics so each test can twiddle just the field it cares about."""
    base = dict(
        symbol=symbol,
        rsi_14=None,
        pct_from_ma_50=None,
        pct_from_ma_200=None,
        pct_from_52w_high=None,
        pct_from_52w_low=None,
        vs_cost=None,
        days_to_earnings=None,
        tags=(),
        tier_index=None,
        tier_buy_list=(),
        tier_sell_list=(),
    )
    base.update(overrides)
    return FlagInputs(**base)


# ── SOFI realistic scenario (mandatory per Phase 2 Commit 1 brief) ─────────────


def test_sofi_realistic_scenario():
    flags = derive_flags(
        FlagInputs(
            symbol="SOFI",
            rsi_14=55,
            pct_from_ma_50=0.0335,
            pct_from_ma_200=-0.2274,
            pct_from_52w_high=-0.4275,
            pct_from_52w_low=0.30,
            vs_cost=-0.297,
            days_to_earnings=3,
            tags=("fintech", "high_risk", "muddy_waters_target"),
            tier_index=2,
            tier_buy_list=("GOOGL", "MSFT"),
            tier_sell_list=(),
        )
    )
    must_fire = {
        "below_200dma",
        "deep_drawdown",
        "underwater",
        "earnings_within_3d",
        "earnings_within_7d",
        "high_risk_tag",
        "event_play",
    }
    assert must_fire.issubset(set(flags))
    assert "oversold_rsi" not in flags  # RSI 55 → neither extreme


def test_emission_order_matches_vocab():
    flags = derive_flags(
        FlagInputs(
            symbol="X",
            rsi_14=80,
            pct_from_ma_200=-0.10,
            vs_cost=-0.20,
            days_to_earnings=1,
            tags=("high_risk",),
        )
    )
    indices = [FLAG_VOCAB.index(f) for f in flags]
    assert indices == sorted(indices)


# ── Momentum: oversold_rsi / overbought_rsi ────────────────────────────────────


@pytest.mark.parametrize(
    "rsi,expected_set",
    [
        (29.99, {"oversold_rsi"}),
        (30.0, set()),
        (70.0, set()),
        (70.01, {"overbought_rsi"}),
        (50.0, set()),
    ],
)
def test_rsi_thresholds(rsi, expected_set):
    flags = derive_flags(_empty(rsi_14=rsi))
    assert (set(flags) & {"oversold_rsi", "overbought_rsi"}) == expected_set


# ── Trend: near_50dma / below_50dma / below_200dma ─────────────────────────────


@pytest.mark.parametrize(
    "pct50,fires_near,fires_below",
    [
        (0.0199, True, False),
        (0.02, False, False),
        (-0.0199, True, False),
        (-0.05, False, False),    # |pct|=5% is not <2%, and -5% is not <-5% — neither fires
        (-0.0501, False, True),
        (-0.10, False, True),
    ],
)
def test_ma50_thresholds(pct50, fires_near, fires_below):
    flags = set(derive_flags(_empty(pct_from_ma_50=pct50)))
    assert ("near_50dma" in flags) is fires_near
    assert ("below_50dma" in flags) is fires_below


@pytest.mark.parametrize(
    "pct200,fires",
    [
        (0.0, False),
        (-0.0001, True),
        (-0.30, True),
        (0.10, False),
    ],
)
def test_ma200_threshold(pct200, fires):
    assert ("below_200dma" in derive_flags(_empty(pct_from_ma_200=pct200))) is fires


# ── Extremes: near_52w_low / near_52w_high / deep_drawdown ─────────────────────


@pytest.mark.parametrize(
    "from_low,fires",
    [
        (0.0, True),
        (0.0499, True),
        (0.05, False),
        (0.20, False),
    ],
)
def test_near_52w_low(from_low, fires):
    assert ("near_52w_low" in derive_flags(_empty(pct_from_52w_low=from_low))) is fires


@pytest.mark.parametrize(
    "from_high,near,deep",
    [
        (0.0, True, False),
        (-0.0199, True, False),
        (-0.02, False, False),
        (-0.30, False, False),
        (-0.3001, False, True),
        (-0.50, False, True),
    ],
)
def test_high_and_drawdown(from_high, near, deep):
    flags = set(derive_flags(_empty(pct_from_52w_high=from_high)))
    assert ("near_52w_high" in flags) is near
    assert ("deep_drawdown" in flags) is deep


# ── P&L: underwater / big_gain ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "vs_cost,under,gain",
    [
        (-0.10, False, False),     # exactly -10% does NOT trigger (strict <-10%)
        (-0.1001, True, False),
        (-0.30, True, False),
        (0.20, False, False),       # exactly +20% does NOT trigger (strict >20%)
        (0.2001, False, True),
        (0.50, False, True),
    ],
)
def test_pnl_thresholds(vs_cost, under, gain):
    flags = set(derive_flags(_empty(vs_cost=vs_cost)))
    assert ("underwater" in flags) is under
    assert ("big_gain" in flags) is gain


# ── Calendar: earnings_within_7d / 3d ──────────────────────────────────────────


@pytest.mark.parametrize(
    "days,within7,within3",
    [
        (0, True, True),
        (3, True, True),
        (4, True, False),
        (7, True, False),
        (8, False, False),
        (-1, False, False),
        (None, False, False),
    ],
)
def test_earnings_window(days, within7, within3):
    flags = set(derive_flags(_empty(days_to_earnings=days)))
    assert ("earnings_within_7d" in flags) is within7
    assert ("earnings_within_3d" in flags) is within3


# ── Tags: high_risk_tag / event_play ───────────────────────────────────────────


def test_high_risk_tag_fires():
    assert "high_risk_tag" in derive_flags(_empty(tags=("high_risk",)))


def test_event_play_via_muddy_waters():
    assert "event_play" in derive_flags(_empty(tags=("muddy_waters_target",)))


def test_no_tag_no_flag():
    flags = set(derive_flags(_empty(tags=("fintech",))))
    assert "high_risk_tag" not in flags
    assert "event_play" not in flags


# ── Tier membership ────────────────────────────────────────────────────────────


def test_buy_list_member():
    f = derive_flags(_empty(symbol="TSM", tier_buy_list=("TSM", "MSFT")))
    assert "buy_list_member" in f


def test_sell_list_exact_match():
    f = derive_flags(_empty(symbol="TSLA", tier_sell_list=("TSLA",)))
    assert "sell_list_member" in f


def test_sell_list_wildcard_tag():
    f = derive_flags(
        _empty(symbol="NVDA", tags=("high_beta",), tier_sell_list=("high_beta_*",))
    )
    assert "sell_list_member" in f


def test_beta_size_warn_low_tier():
    f = derive_flags(_empty(tags=("high_beta",), tier_index=0))
    assert "beta_size_warn" in f
    f1 = derive_flags(_empty(tags=("high_beta",), tier_index=1))
    assert "beta_size_warn" in f1


def test_beta_size_warn_skipped_in_higher_tiers():
    f = derive_flags(_empty(tags=("high_beta",), tier_index=2))
    assert "beta_size_warn" not in f


# ── is_watchworthy helper ──────────────────────────────────────────────────────


def test_watchworthy_excludes_pure_buy_list():
    assert is_watchworthy(["buy_list_member"]) is False
    assert is_watchworthy(["buy_list_member", "underwater"]) is True
    assert is_watchworthy([]) is False
    assert is_watchworthy(["oversold_rsi"]) is True


# ── Robustness: None inputs never raise ────────────────────────────────────────


def test_all_none_returns_empty_or_minimal():
    flags = derive_flags(_empty())
    assert all(f in FLAG_VOCAB for f in flags)
