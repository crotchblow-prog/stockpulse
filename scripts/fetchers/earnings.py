"""Finnhub earnings calendar — 90-day lookahead, 24h disk cache, graceful degrade without API key."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pytz
import requests

log = logging.getLogger(__name__)

TAIPEI = pytz.timezone("Asia/Taipei")
CACHE_PATH = (
    Path(__file__).resolve().parents[2] / "web" / "public" / "reports" / "earnings_cache.json"
)
CACHE_TTL_SECONDS = 24 * 60 * 60
LOOKAHEAD_DAYS = 90
FINNHUB_URL = "https://finnhub.io/api/v1/calendar/earnings"


@dataclass
class EarningsInfo:
    """Next earnings event for a symbol within the lookahead window."""

    symbol: str
    date: str               # YYYY-MM-DD (calendar)
    days_to_earnings: int   # from `as_of_date` to `date`, inclusive of today=0
    hour: str | None = None # "bmo" / "amc" / "dmh" when Finnhub provides it


def fetch_calendar(
    symbols: list[str],
    as_of_date: str | None = None,
    api_key: str | None = None,
    cache_path: Path | None = None,
    now_ts: float | None = None,
) -> dict[str, EarningsInfo | None]:
    """Return next-earnings info per symbol for the next 90 calendar days.

    Returns {symbol: None} for every symbol when FINNHUB_API_KEY is missing or the API errors.
    Cache lives in `web/public/reports/earnings_cache.json` and is committed; TTL is 24h.

    Strategy: one Finnhub call per symbol with `&symbol=...`. Avoids the broad-window
    1500-row truncation that drops near-term earnings (the broad call sorts desc and
    cuts off the earliest dates when the window is dense).
    """
    api_key = api_key if api_key is not None else os.environ.get("FINNHUB_API_KEY")
    cache_path = cache_path or CACHE_PATH
    now = now_ts if now_ts is not None else time.time()
    as_of = as_of_date or datetime.now(TAIPEI).strftime("%Y-%m-%d")

    cached = _load_cache_with_symbols(cache_path, now, symbols)
    if cached is not None:
        rows = cached
    else:
        if not api_key:
            log.info("FINNHUB_API_KEY missing — skipping earnings fetch, returning Nones")
            return {sym: None for sym in symbols}
        rows = _fetch_per_symbol_rows(api_key, as_of, symbols)
        if rows is None:
            return {sym: None for sym in symbols}
        _save_cache(cache_path, rows, now, symbols)

    return {sym: _next_event_for(sym, rows, as_of) for sym in symbols}


def _load_cache_with_symbols(
    cache_path: Path, now: float, symbols: list[str]
) -> list[dict] | None:
    """Return cached rows iff present, within TTL, AND covering every requested symbol.

    The cache records which symbols it was built for; if a new ticker is added to the
    portfolio, the cache is refetched rather than silently returning None for the new one.
    """
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("earnings cache unreadable (%s) — refetching", e)
        return None
    if now - float(payload.get("fetched_at", 0)) > CACHE_TTL_SECONDS:
        return None
    covered = set(payload.get("symbols", []) or [])
    if not covered.issuperset(symbols):
        log.info("earnings cache missing symbols %s — refetching", set(symbols) - covered)
        return None
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else None


def _save_cache(cache_path: Path, rows: list[dict], now: float, symbols: list[str]) -> None:
    """Persist Finnhub rows + the symbol set the cache was built for."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": now, "symbols": sorted(set(symbols)), "rows": rows}
    try:
        cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except OSError as e:
        log.warning("failed to write earnings cache to %s: %s", cache_path, e)


def _fetch_per_symbol_rows(api_key: str, as_of: str, symbols: list[str]) -> list[dict] | None:
    """One Finnhub call per symbol over as_of → as_of+90d. Returns the union of rows.

    Returns None only if every per-symbol call fails (degrade-with-no-data semantics).
    Per-symbol calls each return ≤ a handful of rows — never hits the 1500-row server cap
    that the broad-window query suffers from when earnings season is dense.
    """
    end = (datetime.strptime(as_of, "%Y-%m-%d") + timedelta(days=LOOKAHEAD_DAYS)).strftime("%Y-%m-%d")
    aggregated: list[dict] = []
    fail_count = 0
    for sym in symbols:
        rows = _fetch_one_symbol(api_key, as_of, end, sym)
        if rows is None:
            fail_count += 1
            continue
        aggregated.extend(rows)
    if fail_count == len(symbols):
        log.warning("Finnhub earnings fetch failed for all %d symbols", len(symbols))
        return None
    return aggregated


def _fetch_one_symbol(api_key: str, as_of: str, end: str, symbol: str) -> list[dict] | None:
    """Fetch the earnings calendar for a single symbol. Returns [] if the API has no events."""
    try:
        resp = requests.get(
            FINNHUB_URL,
            params={"from": as_of, "to": end, "symbol": symbol, "token": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        log.warning("Finnhub earnings fetch failed for %s: %s", symbol, e)
        return None
    rows = data.get("earningsCalendar")
    if not isinstance(rows, list):
        log.warning("Finnhub returned unexpected payload shape for %s: %s", symbol, type(rows).__name__)
        return None
    return rows


def _next_event_for(symbol: str, rows: list[dict], as_of: str) -> EarningsInfo | None:
    """Pick the soonest event ≥ as_of for `symbol` from a Finnhub earningsCalendar list."""
    as_of_dt = datetime.strptime(as_of, "%Y-%m-%d")
    candidates: list[tuple[int, dict]] = []
    for row in rows:
        if row.get("symbol") != symbol:
            continue
        date_str = row.get("date")
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        delta = (dt - as_of_dt).days
        if delta < 0:
            continue
        candidates.append((delta, row))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    days, row = candidates[0]
    return EarningsInfo(
        symbol=symbol,
        date=row["date"],
        days_to_earnings=days,
        hour=row.get("hour") or None,
    )
