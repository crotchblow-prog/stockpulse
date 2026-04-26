"""Backfill 30+ days of VIX history into web/public/vix-history.json.

Bootstraps the M3 sparkline so it has historical data before the daily cron has
accumulated 30 dated JSON sidecars. After this runs once, the sparkline shows
real history immediately; the daily cron's per-date JSONs progressively
overlay newer points on top.

Run-once:  python scripts/backfill_vix_history.py
Idempotent: rerun overwrites the file with fresh yfinance data.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytz
import yfinance as yf

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "web" / "public" / "vix-history.json"
TAIPEI = pytz.timezone("Asia/Taipei")
LOOKBACK_DAYS = 60  # fetch 60 to allow for weekends/holidays; sparkline picks last 30


def main() -> int:
    today = datetime.now(TAIPEI).date()
    start = today - timedelta(days=LOOKBACK_DAYS + 5)
    log.info("fetching VIX from %s to %s", start.isoformat(), today.isoformat())

    ticker = yf.Ticker("^VIX")
    hist = ticker.history(start=start.isoformat(), end=(today + timedelta(days=1)).isoformat(), interval="1d")
    if hist is None or hist.empty:
        log.error("yfinance returned empty VIX history")
        return 1

    points: list[dict[str, object]] = []
    for ts, row in hist.iterrows():
        vix = row.get("Close")
        if vix is None or not (vix == vix):  # NaN check
            continue
        date_str = ts.strftime("%Y-%m-%d")
        points.append({"date": date_str, "vix": float(vix)})

    points.sort(key=lambda p: p["date"])  # ascending — sparkline expects oldest → newest
    log.info("collected %d points (range %s → %s)", len(points), points[0]["date"], points[-1]["date"])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "yfinance ^VIX daily close, backfilled",
        "computed_at": datetime.now(TAIPEI).isoformat(),
        "points": points,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log.info("wrote %s (%d points)", OUT_PATH, len(points))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
