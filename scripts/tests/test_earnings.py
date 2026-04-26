"""Earnings fetcher — per-symbol calls, cache TTL + symbol coverage, graceful degrade."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from fetchers import earnings  # noqa: E402


# ── Fakes ────────────────────────────────────────────────────────────────────


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise earnings.requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


def _row(symbol: str, date: str, hour: str | None = None) -> dict[str, Any]:
    return {"symbol": symbol, "date": date, "hour": hour}


def _make_fake_get(per_symbol: dict[str, list[dict]], captured: list[dict]):
    """Return a fake requests.get that records each call and returns per-symbol rows."""
    def fake_get(url: str, params: dict[str, Any] | None = None, timeout: float | None = None):
        captured.append({"url": url, "params": params or {}})
        sym = (params or {}).get("symbol", "")
        return FakeResponse({"earningsCalendar": per_symbol.get(sym, [])})
    return fake_get


# ── Tests ────────────────────────────────────────────────────────────────────


def test_no_api_key_returns_all_nones(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    out = earnings.fetch_calendar(
        ["SOFI", "TSM"],
        as_of_date="2026-04-26",
        api_key=None,
        cache_path=tmp_path / "cache.json",
        now_ts=1000.0,
    )
    assert out == {"SOFI": None, "TSM": None}
    assert not (tmp_path / "cache.json").exists()  # no key → no cache write


def test_per_symbol_calls_with_symbol_param(tmp_path: Path, monkeypatch):
    """The fix: every fetch must pass `symbol=` to Finnhub, not a broad window."""
    captured: list[dict] = []
    per_symbol = {
        "SOFI": [_row("SOFI", "2026-04-29", "bmo")],
        "TSM": [_row("TSM", "2026-07-15", "amc")],
    }
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    out = earnings.fetch_calendar(
        ["SOFI", "TSM"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=tmp_path / "cache.json",
        now_ts=1000.0,
    )

    assert len(captured) == 2  # one call per symbol
    assert {c["params"]["symbol"] for c in captured} == {"SOFI", "TSM"}
    for c in captured:
        assert c["params"]["from"] == "2026-04-26"
        assert c["params"]["to"] == "2026-07-25"
        assert c["params"]["token"] == "fake"

    sofi = out["SOFI"]
    assert sofi is not None
    assert sofi.date == "2026-04-29"
    assert sofi.days_to_earnings == 3
    assert sofi.hour == "bmo"


def test_sofi_apr_29_inside_7d_window(tmp_path: Path, monkeypatch):
    """Regression for the production bug: SOFI Apr-29 must surface from a 90d lookahead."""
    captured: list[dict] = []
    per_symbol = {"SOFI": [_row("SOFI", "2026-04-29")]}
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    out = earnings.fetch_calendar(
        ["SOFI"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=tmp_path / "cache.json",
        now_ts=1000.0,
    )
    info = out["SOFI"]
    assert info is not None
    assert 0 <= info.days_to_earnings <= 7  # the flag boundary that gates SOFI's special-case rule


def test_cache_hit_within_ttl_skips_network(tmp_path: Path, monkeypatch):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({
        "fetched_at": 1000.0,
        "symbols": ["SOFI"],
        "rows": [_row("SOFI", "2026-04-29")],
    }))

    captured: list[dict] = []
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get({}, captured))

    out = earnings.fetch_calendar(
        ["SOFI"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=cache_path,
        now_ts=1000.0 + earnings.CACHE_TTL_SECONDS - 1,  # within TTL
    )
    assert out["SOFI"] is not None
    assert out["SOFI"].date == "2026-04-29"
    assert captured == []  # network not called


def test_cache_miss_when_new_symbol_added(tmp_path: Path, monkeypatch):
    """If a new ticker is added to holdings, cache must refetch — not silently None it."""
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({
        "fetched_at": 1000.0,
        "symbols": ["SOFI"],
        "rows": [_row("SOFI", "2026-04-29")],
    }))

    captured: list[dict] = []
    per_symbol = {
        "SOFI": [_row("SOFI", "2026-04-29")],
        "NVDA": [_row("NVDA", "2026-05-22")],
    }
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    out = earnings.fetch_calendar(
        ["SOFI", "NVDA"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=cache_path,
        now_ts=1000.0 + 1,  # within TTL but new symbol → must refetch
    )
    assert out["NVDA"].date == "2026-05-22"
    assert {c["params"]["symbol"] for c in captured} == {"SOFI", "NVDA"}


def test_cache_expires_past_ttl(tmp_path: Path, monkeypatch):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({
        "fetched_at": 1000.0, "symbols": ["SOFI"], "rows": [_row("SOFI", "2026-01-01")],
    }))

    captured: list[dict] = []
    per_symbol = {"SOFI": [_row("SOFI", "2026-04-29")]}
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    out = earnings.fetch_calendar(
        ["SOFI"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=cache_path,
        now_ts=1000.0 + earnings.CACHE_TTL_SECONDS + 1,  # TTL expired
    )
    assert out["SOFI"].date == "2026-04-29"
    assert len(captured) == 1  # refetched


def test_partial_api_failure_still_returns_other_symbols(tmp_path: Path, monkeypatch):
    """If one ticker's API call fails but others succeed, we return what we got."""
    def flaky_get(url: str, params: dict[str, Any] | None = None, timeout: float | None = None):
        sym = (params or {}).get("symbol", "")
        if sym == "SOFI":
            raise earnings.requests.RequestException("network")
        return FakeResponse({"earningsCalendar": [_row(sym, "2026-05-15")]})
    monkeypatch.setattr(earnings.requests, "get", flaky_get)

    out = earnings.fetch_calendar(
        ["SOFI", "TSM"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=tmp_path / "cache.json",
        now_ts=1000.0,
    )
    assert out["SOFI"] is None  # failed
    assert out["TSM"] is not None and out["TSM"].date == "2026-05-15"


def test_total_api_failure_returns_all_nones_no_cache_write(tmp_path: Path, monkeypatch):
    def all_fail(url: str, params: dict[str, Any] | None = None, timeout: float | None = None):
        raise earnings.requests.RequestException("network")
    monkeypatch.setattr(earnings.requests, "get", all_fail)

    cache_path = tmp_path / "cache.json"
    out = earnings.fetch_calendar(
        ["SOFI", "TSM"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=cache_path,
        now_ts=1000.0,
    )
    assert out == {"SOFI": None, "TSM": None}
    assert not cache_path.exists()  # don't poison the cache with empty rows


def test_cache_write_includes_symbols_field(tmp_path: Path, monkeypatch):
    """Symbol coverage must be persisted so future cache hits can detect new tickers."""
    captured: list[dict] = []
    per_symbol = {"SOFI": [_row("SOFI", "2026-04-29")], "TSM": []}
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    cache_path = tmp_path / "cache.json"
    earnings.fetch_calendar(
        ["SOFI", "TSM"],
        as_of_date="2026-04-26",
        api_key="fake",
        cache_path=cache_path,
        now_ts=1000.0,
    )
    payload = json.loads(cache_path.read_text())
    assert payload["symbols"] == ["SOFI", "TSM"]
    assert payload["fetched_at"] == 1000.0


def test_picks_soonest_event_when_multiple(tmp_path: Path, monkeypatch):
    captured: list[dict] = []
    per_symbol = {
        "SOFI": [
            _row("SOFI", "2026-07-30"),  # later
            _row("SOFI", "2026-04-29"),  # soonest — must win
        ],
    }
    monkeypatch.setattr(earnings.requests, "get", _make_fake_get(per_symbol, captured))

    out = earnings.fetch_calendar(
        ["SOFI"], as_of_date="2026-04-26", api_key="fake",
        cache_path=tmp_path / "cache.json", now_ts=1000.0,
    )
    assert out["SOFI"].date == "2026-04-29"
