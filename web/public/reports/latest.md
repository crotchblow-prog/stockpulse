# 📊 StockPulse — Awaiting first run

The daily pipeline hasn't produced a real report yet. This placeholder will be replaced as soon as `python scripts/generate_report.py` runs (locally or via the GitHub Actions cron at 10:00 Asia/Taipei).

## What you'll see here

| Section | Contents |
|---|---|
| Header | Date, VIX value, **Tier** action and cash target |
| Snapshot | VIX / VIX3M, S&P 500, Nasdaq, Dow, USD/JPY, BTC, Gold, WTI |
| Holdings | Each ticker's price, % vs avg cost, RSI(14), distance from 50DMA |
| Tier Action | Today's `buy_list` and `buy_size_pct` from `tier_strategy` |

## Next step

Wait for MIRA's Python pipeline (or run it locally — see [README](../../../README.md)).
