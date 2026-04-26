"""Regime sensitivity analyzer — Phase 2.5 Commit 5.

Computes per-ticker VIX-regime sensitivity metrics (beta in normal vs stress, 5-day
cumulative return after VIX spikes and VIX crushes) over a 5y weekly/daily history,
then assigns sensitivity_tags consumed by claude_synthesis and the Watch List.

Output: ``config/regime_sensitivity.json``. Run weekly (cron) — beta values shift slowly.

CLI: ``python scripts/analyzers/regime_sensitivity.py``
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

log = logging.getLogger("regime_sensitivity")

# ARIA's brief listed 59 explicit names but called it 51-ticker; using all 59 as
# the explicit list is authoritative. Discrepancy flagged back via bus.
UNIVERSE: tuple[str, ...] = (
    "AAPL", "ABBV", "ABT", "ADBE", "ADP", "AMD", "AMGN", "AMT", "AMZN", "AVGO",
    "BA", "BAC", "BIIB", "BMY", "C", "CHTR", "CMCSA", "CME", "COST", "CSCO",
    "CSX", "CVS", "EA", "EBAY", "EQIX", "F", "FTNT", "GILD", "GOOGL", "HD",
    "IBM", "INTC", "INTU", "ISRG", "JNJ", "JPM", "KO", "LIN", "MRK", "MS",
    "MSFT", "NFLX", "NKE", "NVDA", "SBUX", "T", "TMO", "TMUS", "TSLA", "TSM",
    "UNH", "UPS", "V", "VRTX", "VZ", "WFC", "WMT", "XOM", "META",
)

LOOKBACK_YEARS = 5
MIN_SAMPLE_SIZE = 8

VIX_NORMAL_LO = 12.0       # weeks classified `normal` if Friday-close VIX ∈ [12, 20]
VIX_NORMAL_HI = 20.0
VIX_STRESS_THRESHOLD = 20.0  # weeks classified `stress` if Friday-close VIX > 20

SPIKE_PCT_THRESHOLD = 0.20   # day-over-day VIX rise ≥ 20% qualifies as a spike event
CRUSH_PCT_THRESHOLD = 0.30   # VIX falls ≥ 30% from rolling 60-day high → crush event
CRUSH_LOOKBACK = 60          # trading days for the rolling-high reference window
EVENT_WINDOW_DAYS = 5        # post-event 5-trading-day cumulative return horizon

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "config" / "regime_sensitivity.json"

SPX_SYMBOL = "^GSPC"
VIX_SYMBOL = "^VIX"


@dataclass
class TickerMetrics:
    beta_normal: float | None
    beta_stress: float | None
    vix_spike_decay_pct: float | None
    vix_crush_recovery_pct: float | None
    spike_event_count: int
    crush_event_count: int
    stress_weeks: int
    normal_weeks: int

    def min_sample(self) -> int:
        return min(self.spike_event_count, self.crush_event_count,
                   self.stress_weeks, self.normal_weeks)


# ── Data layer ───────────────────────────────────────────────────────────────

def _fetch_all(symbols: list[str], years: int) -> dict[str, pd.DataFrame]:
    """Single batch yfinance pull for all symbols. Returns {symbol: daily-close DataFrame}.

    Failures are per-symbol — empty DataFrame for any ticker yfinance refuses.
    """
    end = datetime.now(timezone.utc).date()
    start = end.replace(year=end.year - years)
    log.info("fetching %d symbols from %s to %s (yfinance batch)", len(symbols), start, end)
    df = yf.download(
        symbols, start=start, end=end, auto_adjust=True, progress=False,
        group_by="ticker", threads=True,
    )

    out: dict[str, pd.DataFrame] = {}
    if isinstance(df.columns, pd.MultiIndex):
        for sym in symbols:
            if sym in df.columns.get_level_values(0):
                sub = df[sym].dropna(how="all")
                out[sym] = sub
            else:
                out[sym] = pd.DataFrame()
    else:
        # Single-symbol pull collapses the MultiIndex.
        sym = symbols[0]
        out[sym] = df.dropna(how="all")
    return out


def _weekly_close(daily: pd.DataFrame) -> pd.Series:
    """Friday close per week (last available trading day of each ISO week)."""
    if daily.empty or "Close" not in daily.columns:
        return pd.Series(dtype=float)
    return daily["Close"].resample("W-FRI").last().dropna()


# ── Metric computation ──────────────────────────────────────────────────────

def _ols_beta(y: np.ndarray, x: np.ndarray) -> float | None:
    """Slope of OLS y = a + b*x. None if fewer than 2 valid pairs or zero variance."""
    if len(x) < 2 or len(y) < 2:
        return None
    if np.var(x) == 0:
        return None
    cov = np.cov(y, x, ddof=1)
    if cov.shape != (2, 2):
        return None
    return float(cov[0, 1] / cov[1, 1])


def _detect_events_with_cooldown(
    is_event: pd.Series, cooldown: int = EVENT_WINDOW_DAYS,
) -> list[pd.Timestamp]:
    """Return event anchor dates with cooldown applied (next anchor ≥ prev + cooldown).

    Rule: collapse overlapping post-windows into the earliest; subsequent event must
    be at least `cooldown` trading days after the most recent kept anchor.
    """
    anchors: list[pd.Timestamp] = []
    last_kept_idx = -10**9
    indices = np.where(is_event.values)[0]
    for i in indices:
        if i - last_kept_idx >= cooldown:
            anchors.append(is_event.index[i])
            last_kept_idx = i
    return anchors


def _five_day_cum_returns(
    daily_close: pd.Series, anchors: list[pd.Timestamp], horizon: int = EVENT_WINDOW_DAYS,
) -> list[float]:
    """For each anchor, compound the next `horizon` daily returns. Skip anchors near the tail."""
    out: list[float] = []
    closes = daily_close.values
    idx_map = {ts: i for i, ts in enumerate(daily_close.index)}
    for ts in anchors:
        i = idx_map.get(ts)
        if i is None or i + horizon >= len(closes):
            continue  # not enough forward data
        anchor_price = closes[i]
        end_price = closes[i + horizon]
        if anchor_price <= 0 or np.isnan(anchor_price) or np.isnan(end_price):
            continue
        out.append(float(end_price / anchor_price - 1.0))
    return out


def compute_metrics(
    ticker_daily: pd.DataFrame,
    spx_daily: pd.DataFrame,
    vix_daily: pd.DataFrame,
) -> TickerMetrics:
    """Compute the four metrics + their sample counts for one ticker."""
    if ticker_daily.empty or spx_daily.empty or vix_daily.empty:
        return TickerMetrics(None, None, None, None, 0, 0, 0, 0)

    # Weekly closes for beta (Friday-close convention).
    tw = _weekly_close(ticker_daily)
    sw = _weekly_close(spx_daily)
    vw = _weekly_close(vix_daily)

    # Align on common weeks.
    common = tw.index.intersection(sw.index).intersection(vw.index)
    tw = tw.loc[common]
    sw = sw.loc[common]
    vw = vw.loc[common]

    # Simple weekly returns (drops first row).
    t_ret = tw.pct_change().dropna()
    s_ret = sw.pct_change().dropna()
    v_class = vw.reindex(t_ret.index)  # Friday-close VIX classification per return-week

    normal_mask = (v_class >= VIX_NORMAL_LO) & (v_class <= VIX_NORMAL_HI)
    stress_mask = v_class > VIX_STRESS_THRESHOLD

    beta_normal = _ols_beta(t_ret[normal_mask].values, s_ret[normal_mask].values)
    beta_stress = _ols_beta(t_ret[stress_mask].values, s_ret[stress_mask].values)
    normal_weeks = int(normal_mask.sum())
    stress_weeks = int(stress_mask.sum())

    # Daily VIX spike/crush event detection + 5-trading-day forward returns.
    vix_close = vix_daily["Close"].dropna() if "Close" in vix_daily.columns else pd.Series(dtype=float)
    if vix_close.empty:
        return TickerMetrics(
            beta_normal, beta_stress, None, None,
            0, 0, stress_weeks, normal_weeks,
        )

    vix_pct_change = vix_close.pct_change()
    spike_mask = vix_pct_change >= SPIKE_PCT_THRESHOLD
    spike_anchors = _detect_events_with_cooldown(spike_mask.fillna(False))

    rolling_high = vix_close.rolling(window=CRUSH_LOOKBACK, min_periods=1).max()
    drawdown = vix_close / rolling_high - 1.0
    crush_mask = drawdown <= -CRUSH_PCT_THRESHOLD
    crush_anchors = _detect_events_with_cooldown(crush_mask.fillna(False))

    ticker_close = ticker_daily["Close"].dropna() if "Close" in ticker_daily.columns else pd.Series(dtype=float)
    spike_returns = _five_day_cum_returns(ticker_close, spike_anchors)
    crush_returns = _five_day_cum_returns(ticker_close, crush_anchors)

    spike_decay_pct = (float(np.median(spike_returns)) * 100.0) if spike_returns else None
    crush_recovery_pct = (float(np.median(crush_returns)) * 100.0) if crush_returns else None

    return TickerMetrics(
        beta_normal=beta_normal,
        beta_stress=beta_stress,
        vix_spike_decay_pct=spike_decay_pct,
        vix_crush_recovery_pct=crush_recovery_pct,
        spike_event_count=len(spike_returns),
        crush_event_count=len(crush_returns),
        stress_weeks=stress_weeks,
        normal_weeks=normal_weeks,
    )


# ── Tag assignment ───────────────────────────────────────────────────────────

def assign_tags(m: TickerMetrics) -> list[str]:
    """Apply the five sensitivity_tag rules. Empty list if any required metric is None."""
    tags: list[str] = []
    bn, bs = m.beta_normal, m.beta_stress
    sd, cr = m.vix_spike_decay_pct, m.vix_crush_recovery_pct

    if bn is not None and bs is not None and bn > 1.3 and bs < bn:
        tags.append("high_normal")
    if bn is not None and bs is not None and bs > 1.5 and bs > bn:
        tags.append("high_stress")
    if sd is not None and sd < -10:
        tags.append("crisis_alpha")
    if cr is not None and sd is not None and cr > 5 and sd < -5:
        tags.append("mean_reverter")
    if bn is not None and bs is not None and abs(bn) < 0.8 and abs(bs) < 1.0:
        tags.append("defensive")
    return tags


# ── Top-level orchestration ─────────────────────────────────────────────────

def compute_all(universe: tuple[str, ...] = UNIVERSE) -> dict[str, dict[str, Any]]:
    """Fetch + compute metrics + assign tags for every ticker. Returns {symbol: per-ticker dict}."""
    symbols = list(universe) + [SPX_SYMBOL, VIX_SYMBOL]
    histories = _fetch_all(symbols, LOOKBACK_YEARS)
    spx = histories.get(SPX_SYMBOL, pd.DataFrame())
    vix = histories.get(VIX_SYMBOL, pd.DataFrame())
    if spx.empty or vix.empty:
        log.error("SPX or VIX history empty — aborting (cannot compute betas without market reference)")
        return {}

    out: dict[str, dict[str, Any]] = {}
    for sym in universe:
        ticker = histories.get(sym, pd.DataFrame())
        if ticker.empty:
            log.warning("%s: no history — emitting low-confidence empty metrics", sym)
            out[sym] = _serialize_metrics(sym, TickerMetrics(None, None, None, None, 0, 0, 0, 0))
            continue
        m = compute_metrics(ticker, spx, vix)
        out[sym] = _serialize_metrics(sym, m)
    return out


def _serialize_metrics(symbol: str, m: TickerMetrics) -> dict[str, Any]:
    """Per-ticker JSON shape — matches the brief's example exactly."""
    confidence = "high" if m.min_sample() >= MIN_SAMPLE_SIZE else "low"
    tags = assign_tags(m) if confidence == "high" else []
    return {
        "beta_normal": _round(m.beta_normal, 3),
        "beta_stress": _round(m.beta_stress, 3),
        "vix_spike_decay_pct": _round(m.vix_spike_decay_pct, 2),
        "vix_crush_recovery_pct": _round(m.vix_crush_recovery_pct, 2),
        "spike_event_count": m.spike_event_count,
        "crush_event_count": m.crush_event_count,
        "stress_weeks": m.stress_weeks,
        "normal_weeks": m.normal_weeks,
        "confidence": confidence,
        "sensitivity_tags": tags,
    }


def _round(v: float | None, digits: int) -> float | None:
    return None if v is None else round(v, digits)


def write_json(tickers: dict[str, dict[str, Any]], output_path: Path = OUTPUT_PATH) -> Path:
    """Write the JSON output. Idempotent — only `computed_at` shifts when data is unchanged."""
    payload = {
        "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lookback_years": LOOKBACK_YEARS,
        "min_sample_size": MIN_SAMPLE_SIZE,
        "universe_size": len(UNIVERSE),
        "tickers": tickers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log.info("wrote %s (%d tickers)", output_path, len(tickers))
    return output_path


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    tickers = compute_all()
    if not tickers:
        return 1
    write_json(tickers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
