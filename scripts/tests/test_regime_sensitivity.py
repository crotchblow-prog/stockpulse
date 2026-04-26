"""Regime sensitivity analyzer — math, tag rules, sample-size guard, JSON shape."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers import regime_sensitivity as rs  # noqa: E402
from analyzers.regime_sensitivity import TickerMetrics, assign_tags  # noqa: E402


# ── Tag assignment thresholds — boundary tests ───────────────────────────────

def _m(**kw) -> TickerMetrics:
    """Build a TickerMetrics with all sample counts safely above MIN_SAMPLE_SIZE."""
    defaults = dict(
        beta_normal=1.0, beta_stress=1.0,
        vix_spike_decay_pct=0.0, vix_spike_decay_p25_pct=0.0,
        vix_crush_recovery_pct=0.0,
        spike_event_count=20, crush_event_count=20,
        stress_weeks=50, normal_weeks=200,
    )
    defaults.update(kw)
    return TickerMetrics(**defaults)  # type: ignore[arg-type]


def test_high_normal_assigned_when_beta_normal_gt_1_3_and_stress_lower():
    assert "high_normal" in assign_tags(_m(beta_normal=1.31, beta_stress=1.0))


def test_high_normal_not_assigned_at_boundary_1_3():
    assert "high_normal" not in assign_tags(_m(beta_normal=1.3, beta_stress=1.0))


def test_high_normal_not_assigned_when_stress_higher_than_normal():
    assert "high_normal" not in assign_tags(_m(beta_normal=1.5, beta_stress=1.6))


def test_high_stress_assigned_when_beta_stress_gt_1_5_and_higher_than_normal():
    assert "high_stress" in assign_tags(_m(beta_normal=1.2, beta_stress=1.51))


def test_high_stress_not_assigned_at_boundary_1_5():
    assert "high_stress" not in assign_tags(_m(beta_normal=1.0, beta_stress=1.5))


def test_crisis_alpha_assigned_when_p25_decay_lt_minus_10():
    # Commit 8: p25 is the basis, not median.
    assert "crisis_alpha" in assign_tags(_m(vix_spike_decay_p25_pct=-10.01))


def test_crisis_alpha_not_at_boundary_minus_10_p25():
    assert "crisis_alpha" not in assign_tags(_m(vix_spike_decay_p25_pct=-10.0))


def test_crisis_alpha_fires_when_median_mild_but_p25_extreme():
    # Asymmetric tail: median = -2% (would NOT have fired under old methodology)
    # but p25 = -12% (the bottom-quartile reaction is severe). Must fire under Commit 8.
    tags = assign_tags(_m(vix_spike_decay_pct=-2.0, vix_spike_decay_p25_pct=-12.0))
    assert "crisis_alpha" in tags


def test_crisis_alpha_does_not_fire_when_median_severe_but_p25_mild():
    # Right-skew of one mild event near the threshold but with most events benign.
    # Median = -8% but p25 = -3% → does NOT fire. Old rule would have, new rule doesn't.
    tags = assign_tags(_m(vix_spike_decay_pct=-8.0, vix_spike_decay_p25_pct=-3.0))
    assert "crisis_alpha" not in tags


def test_mean_reverter_requires_both_clauses_at_relaxed_thresholds():
    # Commit 8: thresholds relaxed from ±5% to ±2%.
    assert "mean_reverter" in assign_tags(
        _m(vix_crush_recovery_pct=2.01, vix_spike_decay_pct=-2.01)
    )
    assert "mean_reverter" not in assign_tags(
        _m(vix_crush_recovery_pct=2.01, vix_spike_decay_pct=-1.99)
    )
    assert "mean_reverter" not in assign_tags(
        _m(vix_crush_recovery_pct=1.99, vix_spike_decay_pct=-3.0)
    )


def test_mean_reverter_boundary_fires_at_2_5_does_not_fire_at_1_5():
    # Both axes inside threshold → fires.
    assert "mean_reverter" in assign_tags(
        _m(vix_crush_recovery_pct=2.5, vix_spike_decay_pct=-2.5)
    )
    # Both axes outside threshold → does not fire.
    assert "mean_reverter" not in assign_tags(
        _m(vix_crush_recovery_pct=1.5, vix_spike_decay_pct=-1.5)
    )


def test_defensive_assigned_for_low_beta_pair():
    assert "defensive" in assign_tags(_m(beta_normal=0.5, beta_stress=0.7))
    assert "defensive" in assign_tags(_m(beta_normal=-0.6, beta_stress=-0.95))  # abs values matter


def test_defensive_excluded_at_boundaries():
    assert "defensive" not in assign_tags(_m(beta_normal=0.8, beta_stress=0.5))
    assert "defensive" not in assign_tags(_m(beta_normal=0.5, beta_stress=1.0))


def test_defensive_and_high_normal_can_coexist_only_in_pathological_cases():
    # Constructed: beta_normal = -0.79 (|.| < 0.8, fails high_normal > 1.3),
    # beta_stress = 0.9 (|.| < 1.0). defensive only.
    tags = assign_tags(_m(beta_normal=-0.79, beta_stress=0.9))
    assert "defensive" in tags
    assert "high_normal" not in tags


# ── Sample-size guard at the 7 / 8 boundary ──────────────────────────────────

def test_low_confidence_excludes_tags_when_min_sample_below_8():
    m = _m(
        beta_normal=1.5, beta_stress=2.0,  # would yield high_normal + high_stress
        spike_event_count=7,
    )
    serialized = rs._serialize_metrics("TEST", m)
    assert serialized["confidence"] == "low"
    assert serialized["sensitivity_tags"] == []


def test_high_confidence_at_exactly_8():
    m = _m(beta_normal=1.5, beta_stress=2.0, spike_event_count=8, crush_event_count=8)
    serialized = rs._serialize_metrics("TEST", m)
    assert serialized["confidence"] == "high"
    assert "high_stress" in serialized["sensitivity_tags"]


def test_low_confidence_when_normal_weeks_thin():
    m = _m(beta_normal=0.5, beta_stress=0.5, normal_weeks=5)
    serialized = rs._serialize_metrics("TEST", m)
    assert serialized["confidence"] == "low"
    assert serialized["sensitivity_tags"] == []


# ── Event de-duplication with cooldown ──────────────────────────────────────

def test_event_dedup_collapses_overlapping_anchors():
    # Five consecutive True days → only the first should survive a 5-day cooldown.
    idx = pd.date_range("2025-01-01", periods=10, freq="B")
    is_event = pd.Series([True, True, True, True, True, False, False, False, False, False], index=idx)
    anchors = rs._detect_events_with_cooldown(is_event, cooldown=5)
    assert len(anchors) == 1
    assert anchors[0] == idx[0]


def test_event_dedup_keeps_separate_clusters():
    # Two clusters separated by > cooldown → both survive.
    idx = pd.date_range("2025-01-01", periods=20, freq="B")
    is_event = pd.Series([False] * 20, index=idx)
    is_event.iloc[1] = True  # first cluster
    is_event.iloc[10] = True  # 9 days later, > 5-day cooldown
    anchors = rs._detect_events_with_cooldown(is_event, cooldown=5)
    assert len(anchors) == 2


# ── 5-day cumulative return ──────────────────────────────────────────────────

def test_five_day_cum_returns_compounds_correctly():
    # Daily closes 100, 102, 104, 105, 110, 115 → window from t=0 (100→115) = 15%.
    idx = pd.date_range("2025-01-01", periods=6, freq="B")
    closes = pd.Series([100.0, 102.0, 104.0, 105.0, 110.0, 115.0], index=idx)
    rets = rs._five_day_cum_returns(closes, [idx[0]], horizon=5)
    assert len(rets) == 1
    assert abs(rets[0] - 0.15) < 1e-9


def test_five_day_cum_returns_skips_anchor_too_close_to_tail():
    idx = pd.date_range("2025-01-01", periods=4, freq="B")
    closes = pd.Series([100.0, 102.0, 104.0, 105.0], index=idx)
    rets = rs._five_day_cum_returns(closes, [idx[0]], horizon=5)
    assert rets == []  # not enough forward data


# ── OLS beta math ────────────────────────────────────────────────────────────

def test_ols_beta_recovers_known_slope():
    np.random.seed(42)
    x = np.random.randn(100)
    y = 1.5 * x + 0.1 * np.random.randn(100)
    beta = rs._ols_beta(y, x)
    assert beta is not None
    assert abs(beta - 1.5) < 0.05


def test_ols_beta_none_for_insufficient_data():
    assert rs._ols_beta(np.array([1.0]), np.array([1.0])) is None
    assert rs._ols_beta(np.array([]), np.array([])) is None


def test_ols_beta_none_for_zero_variance_x():
    assert rs._ols_beta(np.array([1.0, 2.0, 3.0]), np.array([5.0, 5.0, 5.0])) is None


# ── JSON output shape ────────────────────────────────────────────────────────

def test_serialize_metrics_has_brief_required_keys():
    m = _m()
    out = rs._serialize_metrics("TSLA", m)
    required = {
        "beta_normal", "beta_stress",
        "vix_spike_decay_pct", "vix_spike_decay_p25_pct",  # Commit 8 adds p25
        "vix_crush_recovery_pct",
        "spike_event_count", "crush_event_count", "stress_weeks", "normal_weeks",
        "confidence", "sensitivity_tags",
    }
    assert required.issubset(out.keys())


def test_serialize_metrics_includes_p25_alongside_median():
    m = _m(vix_spike_decay_pct=-3.0, vix_spike_decay_p25_pct=-11.0)
    out = rs._serialize_metrics("TSLA", m)
    assert out["vix_spike_decay_pct"] == -3.0
    assert out["vix_spike_decay_p25_pct"] == -11.0


def test_serialize_metrics_rounds_floats():
    m = _m(beta_normal=1.234567, vix_spike_decay_pct=-8.345678)
    out = rs._serialize_metrics("TSLA", m)
    assert out["beta_normal"] == 1.235
    assert out["vix_spike_decay_pct"] == -8.35


def test_serialize_metrics_handles_none_floats():
    m = _m(beta_normal=None, beta_stress=None,
           vix_spike_decay_pct=None, vix_spike_decay_p25_pct=None,
           vix_crush_recovery_pct=None,
           spike_event_count=0, crush_event_count=0,
           stress_weeks=0, normal_weeks=0)
    out = rs._serialize_metrics("EMPTY", m)
    assert out["beta_normal"] is None
    assert out["vix_spike_decay_p25_pct"] is None
    assert out["confidence"] == "low"
    assert out["sensitivity_tags"] == []


# ── p25 computation (Commit 8) ───────────────────────────────────────────────

def test_compute_metrics_emits_p25_below_median_for_left_skewed_returns():
    """Synthetic ticker with a left-skewed tail across spike events: 7 mild events
    plus 1 severe (-15%) event. p25 must capture the bottom quartile (the -15%);
    median stays near 0. Validates that p25 ≠ median when the distribution is asymmetric."""
    # Build 200 trading days with VIX_close generating exactly 8 spike events at known
    # positions, with ticker reactions to each spike of: 0,+1%,-1%,+2%,-2%,+3%,-3%,-15%.
    # p25 of those 8 = nearer the worst quartile; median ≈ 0.
    rng = pd.date_range("2024-01-01", periods=300, freq="B")
    # VIX flat at 15 most days, jumps +25% at 8 chosen indices (≥ 5 days apart for cooldown).
    vix = pd.Series([15.0] * 300, index=rng)
    spike_indices = [10, 30, 50, 70, 90, 110, 130, 150]
    for i in spike_indices:
        vix.iloc[i] = 15.0 * 1.30  # +30% jump triggers spike
        vix.iloc[i + 1] = 15.0  # back to baseline next day
    vix_df = pd.DataFrame({"Close": vix})

    # Ticker: flat 100 except for engineered 5d cumulative returns at each spike anchor.
    ticker_close = pd.Series([100.0] * 300, index=rng)
    reactions = [0.00, 0.01, -0.01, 0.02, -0.02, 0.03, -0.03, -0.15]
    for i, r in zip(spike_indices, reactions):
        ticker_close.iloc[i + 5] = 100.0 * (1.0 + r)
    ticker_df = pd.DataFrame({"Close": ticker_close})

    # SPX: flat — beta math is degenerate but we only care about spike metrics here.
    spx_df = pd.DataFrame({"Close": pd.Series([4000.0] * 300, index=rng)})

    m = rs.compute_metrics(ticker_df, spx_df, vix_df)
    assert m.vix_spike_decay_pct is not None
    assert m.vix_spike_decay_p25_pct is not None
    # p25 should be more negative than median (left-skewed distribution).
    assert m.vix_spike_decay_p25_pct < m.vix_spike_decay_pct
    # Median of the 8 reactions = mean of {-0.01, 0} → -0.5%.
    assert abs(m.vix_spike_decay_pct - (-0.5)) < 0.5
    # p25 of those 8 reactions: numpy default linear interp lands between -3% and -2%.
    assert m.vix_spike_decay_p25_pct < -2.0
