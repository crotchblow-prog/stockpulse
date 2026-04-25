"""yfinance wrappers — one call per asset, errors logged + returned, not raised."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


@dataclass
class Quote:
    """Last close + change for a single symbol; `error` is set on fetch failure."""

    symbol: str
    label: str
    last: float | None = None
    prev_close: float | None = None
    change: float | None = None
    change_pct: float | None = None
    error: str | None = None


@dataclass
class HoldingHistory:
    """One year of daily closes for a holding/watchlist ticker, plus error if fetch failed."""

    symbol: str
    closes: pd.Series | None = None
    last: float | None = None
    prev_close: float | None = None
    change: float | None = None
    change_pct: float | None = None
    error: str | None = None


# ── canonical asset list for the daily snapshot ──────────────────────────────
SNAPSHOT_ASSETS: list[tuple[str, str]] = [
    ("^VIX", "VIX"),
    ("^VIX3M", "VIX3M"),
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq"),
    ("^DJI", "Dow"),
    ("JPY=X", "USD/JPY"),
    ("BTC-USD", "BTC"),
    ("GC=F", "Gold"),
    ("CL=F", "WTI"),
]


def _quote_from_history(symbol: str, label: str, hist: pd.DataFrame) -> Quote:
    """Build a Quote from a 5-day history DataFrame, computing day-over-day change."""
    if hist is None or hist.empty:
        return Quote(symbol=symbol, label=label, error="empty history")
    closes = hist["Close"].dropna()
    if len(closes) < 1:
        return Quote(symbol=symbol, label=label, error="no closes")
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    if prev is not None and prev != 0:
        change = last - prev
        change_pct = change / prev
    else:
        change = None
        change_pct = None
    return Quote(
        symbol=symbol,
        label=label,
        last=last,
        prev_close=prev,
        change=change,
        change_pct=change_pct,
    )


def fetch_quote(symbol: str, label: str | None = None) -> Quote:
    """Fetch a single quote (last close + dod change). Never raises; returns Quote with `error` set."""
    label = label or symbol
    try:
        hist = yf.Ticker(symbol).history(period="5d", auto_adjust=False)
        return _quote_from_history(symbol, label, hist)
    except Exception as e:  # noqa: BLE001 — yfinance throws a varied set
        log.warning("fetch_quote(%s) failed: %s", symbol, e)
        return Quote(symbol=symbol, label=label, error=str(e))


def fetch_snapshot() -> dict[str, Quote]:
    """Fetch the full snapshot table (VIX, indices, FX, BTC, gold, oil). Keyed by label."""
    out: dict[str, Quote] = {}
    for symbol, label in SNAPSHOT_ASSETS:
        out[label] = fetch_quote(symbol, label)
    return out


def fetch_holding_history(symbol: str) -> HoldingHistory:
    """Fetch one year of daily closes for a holding ticker. Never raises."""
    try:
        hist = yf.Ticker(symbol).history(period="1y", auto_adjust=False)
    except Exception as e:  # noqa: BLE001
        log.warning("fetch_holding_history(%s) failed: %s", symbol, e)
        return HoldingHistory(symbol=symbol, error=str(e))

    if hist is None or hist.empty:
        return HoldingHistory(symbol=symbol, error="empty history")
    closes = hist["Close"].dropna()
    if closes.empty:
        return HoldingHistory(symbol=symbol, error="no closes")
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    change = last - prev if prev is not None else None
    change_pct = change / prev if prev not in (None, 0) else None
    return HoldingHistory(
        symbol=symbol,
        closes=closes,
        last=last,
        prev_close=prev,
        change=change,
        change_pct=change_pct,
    )


def fetch_many_histories(symbols: Iterable[str]) -> dict[str, HoldingHistory]:
    """Fetch histories for multiple tickers; failures are isolated per-symbol."""
    return {sym: fetch_holding_history(sym) for sym in symbols}
