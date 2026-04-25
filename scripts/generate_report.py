"""Daily market-analysis pipeline. Run via cron at 10:00 Asia/Taipei or `python generate_report.py`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytz

# Make sibling packages importable when run as `python scripts/generate_report.py`.
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers import technical, vix_tier  # noqa: E402
from fetchers import market_data  # noqa: E402
from reporters import markdown_gen  # noqa: E402

REPO_ROOT = SCRIPTS_DIR.parent
HOLDINGS_PATH = REPO_ROOT / "config" / "holdings.json"
REPORTS_DIR = REPO_ROOT / "web" / "public" / "reports"
TAIPEI = pytz.timezone("Asia/Taipei")

log = logging.getLogger("stockpulse")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate today's StockPulse market report.")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout, don't write files.")
    p.add_argument("--date", help="Override report date (YYYY-MM-DD, Asia/Taipei).")
    p.add_argument("-v", "--verbose", action="store_true", help="DEBUG logging.")
    return p.parse_args()


def today_taipei() -> str:
    """Return today's date in Asia/Taipei as YYYY-MM-DD."""
    return datetime.now(TAIPEI).strftime("%Y-%m-%d")


def load_holdings() -> dict:
    """Load and return config/holdings.json as a dict."""
    with HOLDINGS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def parse_avg_cost(holding_meta: dict) -> float | None:
    """Pluck avg_cost from a holding entry; tolerate missing or non-numeric."""
    v = holding_meta.get("avg_cost")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def build_holdings_data(holdings_cfg: dict, history_map: dict) -> dict[str, dict]:
    """Combine per-holding history + technicals + cost basis into the dict markdown_gen expects."""
    out: dict[str, dict] = {}
    for symbol, meta in holdings_cfg["current_holdings"].items():
        h = history_map.get(symbol)
        if h is None or h.error:
            out[symbol] = {"error": h.error if h else "no history"}
            continue
        tech = technical.compute(h.closes)
        avg_cost = parse_avg_cost(meta)
        vs_avg = ((h.last - avg_cost) / avg_cost) if (avg_cost and h.last) else None
        out[symbol] = {
            "last": h.last,
            "change": h.change,
            "change_pct": h.change_pct,
            "avg_cost": avg_cost,
            "vs_avg_cost": vs_avg,
            "rsi_14": tech.rsi_14,
            "ma_50": tech.ma_50,
            "ma_200": tech.ma_200,
            "pct_from_ma_50": tech.pct_from_ma_50,
            "pct_from_ma_200": tech.pct_from_ma_200,
            "pct_from_52w_high": tech.pct_from_52w_high,
            "pct_from_52w_low": tech.pct_from_52w_low,
        }
    return out


def write_report(date: str, markdown: str) -> tuple[Path, Path]:
    """Write the dated report and overwrite latest.md. Returns the two paths written."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dated = REPORTS_DIR / f"{date}.md"
    latest = REPORTS_DIR / "latest.md"
    dated.write_text(markdown, encoding="utf-8")
    latest.write_text(markdown, encoding="utf-8")
    return dated, latest


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    report_date = args.date or os.environ.get("REPORT_DATE") or today_taipei()
    log.info("generating report for %s", report_date)

    holdings_cfg = load_holdings()

    log.info("fetching market snapshot…")
    snapshot = market_data.fetch_snapshot()

    vix_quote = snapshot.get("VIX")
    if not vix_quote or vix_quote.error or vix_quote.last is None:
        log.error("VIX fetch failed (%s) — aborting", getattr(vix_quote, "error", "missing"))
        return 1
    vix_value = float(vix_quote.last)

    tier = vix_tier.classify(vix_value, holdings_cfg)
    log.info("VIX %.2f → %s (%s)", vix_value, tier.name, tier.action)

    holding_symbols = list(holdings_cfg["current_holdings"].keys())
    log.info("fetching %d holding histories…", len(holding_symbols))
    history_map = market_data.fetch_many_histories(holding_symbols)
    holdings_data = build_holdings_data(holdings_cfg, history_map)

    report = {
        "date": report_date,
        "vix_value": vix_value,
        "tier": tier,
        "snapshot": snapshot,
        "holdings": holdings_data,
    }
    md = markdown_gen.render(report)

    if args.dry_run:
        sys.stdout.write(md)
        log.info("dry-run: %d chars not written to disk", len(md))
        return 0

    dated, latest = write_report(report_date, md)
    log.info("wrote %s and %s", dated.name, latest.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
