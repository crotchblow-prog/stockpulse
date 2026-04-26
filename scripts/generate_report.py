"""Daily market-analysis pipeline. Run via cron at 10:00 Asia/Taipei or `python generate_report.py`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz

# Make sibling packages importable when run as `python scripts/generate_report.py`.
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers import technical, vix_tier  # noqa: E402
from analyzers.flags import FlagInputs, derive_flags  # noqa: E402
from analyzers.vix_tier import TierResult  # noqa: E402
from fetchers import market_data  # noqa: E402
from fetchers import earnings as earnings_fetcher  # noqa: E402
from reporters import json_emitter, markdown_gen  # noqa: E402

REPO_ROOT = SCRIPTS_DIR.parent
HOLDINGS_PATH = REPO_ROOT / "config" / "holdings.json"
REGIME_SENSITIVITY_PATH = REPO_ROOT / "config" / "regime_sensitivity.json"
REPORTS_DIR = REPO_ROOT / "web" / "public" / "reports"
TAIPEI = pytz.timezone("Asia/Taipei")

log = logging.getLogger("stockpulse")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate today's StockPulse market report.")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout, don't write files.")
    p.add_argument("--date", help="Override report date (YYYY-MM-DD, Asia/Taipei).")
    p.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip Claude synthesis call. Implies --en-only (no synthesis → nothing to translate).",
    )
    p.add_argument(
        "--en-only",
        action="store_true",
        help="Skip the zh translation step. EN report still ships normally.",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="DEBUG logging.")
    return p.parse_args()


def today_taipei() -> str:
    """Return today's date in Asia/Taipei as YYYY-MM-DD."""
    return datetime.now(TAIPEI).strftime("%Y-%m-%d")


def load_holdings() -> dict:
    """Load and return config/holdings.json as a dict."""
    with HOLDINGS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_regime_sensitivity() -> dict[str, dict[str, Any]]:
    """Load config/regime_sensitivity.json's `tickers` map. Empty dict if missing or unreadable."""
    if not REGIME_SENSITIVITY_PATH.exists():
        log.info("regime_sensitivity.json not present yet — sensitivity_tags skipped")
        return {}
    try:
        with REGIME_SENSITIVITY_PATH.open(encoding="utf-8") as f:
            return json.load(f).get("tickers", {})
    except (OSError, ValueError) as e:
        log.warning("regime_sensitivity.json unreadable (%s) — sensitivity_tags skipped", e)
        return {}


def attach_regime_fields(holding: dict[str, Any], symbol: str, regime: dict[str, dict[str, Any]]) -> None:
    """Mutate `holding` in place to attach regime_metrics, sensitivity_tags, missing_from_universe."""
    entry = regime.get(symbol)
    if entry is None:
        holding["regime_metrics"] = None
        holding["sensitivity_tags"] = []
        holding["missing_from_universe"] = True
        return

    metrics = {
        "beta_normal": entry.get("beta_normal"),
        "beta_stress": entry.get("beta_stress"),
        "vix_spike_decay_pct": entry.get("vix_spike_decay_pct"),
        "vix_crush_recovery_pct": entry.get("vix_crush_recovery_pct"),
        "confidence": entry.get("confidence"),
    }
    holding["regime_metrics"] = metrics
    holding["missing_from_universe"] = False
    if entry.get("confidence") == "low":
        holding["sensitivity_tags"] = []
    else:
        holding["sensitivity_tags"] = list(entry.get("sensitivity_tags") or [])


def parse_avg_cost(holding_meta: dict) -> float | None:
    """Pluck avg_cost from a holding entry; tolerate missing or non-numeric."""
    v = holding_meta.get("avg_cost")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def build_holdings_data(
    holdings_cfg: dict,
    history_map: dict,
    snapshot: dict[str, Any],
    earnings_map: dict[str, Any],
    tier: TierResult,
    regime: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict]:
    """Combine history + technicals + cost + flags + earnings into the dict markdown_gen expects."""
    out: dict[str, dict] = {}
    tier_buy = tuple(tier.buy_list or ())
    tier_sell = tuple(tier.sell_list or ())
    regime = regime or {}
    for symbol, meta in holdings_cfg["current_holdings"].items():
        account = meta.get("account")
        tags = list(meta.get("tags") or [])
        avg_cost = parse_avg_cost(meta)

        h = history_map.get(symbol)
        if h is None or h.error:
            err_holding = {
                "error": h.error if h else "no history",
                "account": account,
                "tags": tags,
                "tier_index": tier.index,
                "flags": [],
                "earnings_date": None,
                "days_to_earnings": None,
            }
            attach_regime_fields(err_holding, symbol, regime)
            out[symbol] = err_holding
            continue
        tech = technical.compute(h.closes)
        vs_avg = ((h.last - avg_cost) / avg_cost) if (avg_cost and h.last) else None

        ev = earnings_map.get(symbol) if earnings_map else None
        days_to_earnings = getattr(ev, "days_to_earnings", None)
        earnings_date = getattr(ev, "date", None)

        flags = derive_flags(
            FlagInputs(
                symbol=symbol,
                rsi_14=tech.rsi_14,
                pct_from_ma_50=tech.pct_from_ma_50,
                pct_from_ma_200=tech.pct_from_ma_200,
                pct_from_52w_high=tech.pct_from_52w_high,
                pct_from_52w_low=tech.pct_from_52w_low,
                vs_cost=vs_avg,
                days_to_earnings=days_to_earnings,
                tags=tuple(tags),
                tier_index=tier.index,
                tier_buy_list=tier_buy,
                tier_sell_list=tier_sell,
            )
        )

        holding = {
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
            "account": account,
            "tags": tags,
            "tier_index": tier.index,
            "earnings_date": earnings_date,
            "days_to_earnings": days_to_earnings,
            "flags": flags,
        }
        attach_regime_fields(holding, symbol, regime)
        out[symbol] = holding
    return out


def build_accounts_summary(holdings: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group holdings by account → {tier_index, total_value, holdings: [symbol]}.

    Phase 3 MetaApi Track A regrouping prep — no new data source, just a view.
    `total_value` is None until share counts and cash balances are sourced.
    """
    out: dict[str, dict[str, Any]] = {}
    for symbol, h in holdings.items():
        account = h.get("account") or "Unknown"
        bucket = out.setdefault(
            account, {"tier_index": h.get("tier_index"), "total_value": None, "holdings": []}
        )
        bucket["holdings"].append(symbol)
    return out


def maybe_synthesize(report: dict[str, Any], skip: bool) -> dict[str, Any] | None:
    """Try Commit 3's claude_synthesis; return None on flag, missing key, ImportError, or any failure."""
    if skip:
        log.info("synthesis skipped via --no-synthesis")
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.info("ANTHROPIC_API_KEY missing — synthesis skipped")
        return None
    try:
        from reporters import claude_synthesis  # type: ignore[import-not-found]  # noqa: E402
    except ImportError:
        log.info("claude_synthesis not present yet — synthesis skipped")
        return None
    try:
        return claude_synthesis.synthesize(report)
    except Exception as e:  # noqa: BLE001 — synthesis must never crash the report
        log.warning("synthesis raised %s — degrading to no synthesis", e)
        return None


def maybe_translate(
    en_markdown: str, en_synthesis: dict[str, Any] | None, skip: bool
) -> tuple[str, dict[str, Any] | None] | None:
    """Translate EN markdown + synthesis dict → ZH equivalents. Returns None on any failure or skip.

    Translation is best-effort: any error returns None and the EN report ships alone.
    Synthesis-dict translation is skipped when there's nothing to translate (no synthesis).
    """
    if skip:
        log.info("translation skipped via --en-only")
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.info("ANTHROPIC_API_KEY missing — translation skipped")
        return None
    try:
        from reporters import translator  # type: ignore[import-not-found]  # noqa: E402
    except ImportError:
        log.info("translator not present — translation skipped")
        return None
    try:
        zh_markdown = translator.translate_markdown(en_markdown)
    except Exception as e:  # noqa: BLE001 — translation must never crash the EN report
        log.warning("translate_markdown raised %s — zh skipped", e)
        return None

    zh_synthesis: dict[str, Any] | None = None
    if en_synthesis is not None:
        try:
            zh_synthesis = translator.translate_synthesis(en_synthesis)
        except Exception as e:  # noqa: BLE001
            log.warning("translate_synthesis raised %s — zh JSON synthesis dropped", e)
            zh_synthesis = None
    return zh_markdown, zh_synthesis


def write_markdown(reports_dir: Path, date: str, markdown: str) -> tuple[Path, Path]:
    """Write {date}.md and latest.md into reports_dir. Returns the two paths written."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    dated = reports_dir / f"{date}.md"
    latest = reports_dir / "latest.md"
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

    log.info("fetching earnings calendar (degrades if no FINNHUB_API_KEY)…")
    earnings_map = earnings_fetcher.fetch_calendar(holding_symbols, as_of_date=report_date)

    regime = load_regime_sensitivity()
    holdings_data = build_holdings_data(
        holdings_cfg, history_map, snapshot, earnings_map, tier, regime
    )
    accounts = build_accounts_summary(holdings_data)

    report: dict[str, Any] = {
        "date": report_date,
        "vix_value": vix_value,
        "tier": tier,
        "snapshot": snapshot,
        "holdings": holdings_data,
        "accounts": accounts,
        "regime_universe": regime,
    }

    synthesis = maybe_synthesize(report, skip=args.no_synthesis)
    if synthesis is not None:
        report["synthesis"] = synthesis

    en_md = markdown_gen.render(report)

    if args.dry_run:
        sys.stdout.write(en_md)
        log.info("dry-run: %d chars not written to disk", len(en_md))
        return 0

    en_dir = REPORTS_DIR / "en"
    en_dated_md, en_latest_md = write_markdown(en_dir, report_date, en_md)
    log.info("wrote en/%s and en/%s", en_dated_md.name, en_latest_md.name)
    en_dated_json, en_latest_json = json_emitter.write(report_date, en_dir, report)
    log.info("wrote en/%s and en/%s", en_dated_json.name, en_latest_json.name)

    # zh translation is best-effort — failure here never blocks the EN report.
    zh = maybe_translate(en_md, synthesis, skip=(args.en_only or args.no_synthesis))
    if zh is not None:
        zh_md, zh_synthesis = zh
        zh_dir = REPORTS_DIR / "zh"
        zh_dated_md, zh_latest_md = write_markdown(zh_dir, report_date, zh_md)
        log.info("wrote zh/%s and zh/%s", zh_dated_md.name, zh_latest_md.name)
        zh_dated_json, zh_latest_json = json_emitter.write(
            report_date, zh_dir, report, synthesis_override=zh_synthesis
        )
        log.info("wrote zh/%s and zh/%s", zh_dated_json.name, zh_latest_json.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
