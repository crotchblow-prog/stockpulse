"""Render the report dict produced by generate_report into a Markdown document."""

from __future__ import annotations

from typing import Any

from analyzers.vix_tier import TierResult, TIER_BADGE, TIER_STARS


def _fmt_price(v: float | None, digits: int = 2) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{v:,.{digits}f}"
    return f"{v:.{digits}f}"


def _fmt_pct(v: float | None, digits: int = 2) -> str:
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v * 100:.{digits}f}%"


def _fmt_change(change: float | None, change_pct: float | None) -> str:
    if change is None and change_pct is None:
        return "—"
    parts = []
    if change is not None:
        sign = "+" if change >= 0 else ""
        parts.append(f"{sign}{change:.2f}")
    if change_pct is not None:
        parts.append(f"({_fmt_pct(change_pct)})")
    return " ".join(parts)


def _quote_row(label: str, q: Any) -> str:
    if getattr(q, "error", None):
        return f"| {label} | _unavailable_ | _{q.error}_ |"
    return f"| {label} | {_fmt_price(q.last)} | {_fmt_change(q.change, q.change_pct)} |"


def _holding_row(symbol: str, h: dict[str, Any]) -> str:
    if h.get("error"):
        return f"| **{symbol}** | _unavailable_ | _{h['error']}_ | — | — | — | — |"

    last = _fmt_price(h.get("last"))
    vs_cost = _fmt_pct(h.get("vs_avg_cost"))
    rsi = "—" if h.get("rsi_14") is None else f"{h['rsi_14']:.0f}"
    ma_50 = _fmt_pct(h.get("pct_from_ma_50"))
    ma_200 = _fmt_pct(h.get("pct_from_ma_200"))
    hi_52 = _fmt_pct(h.get("pct_from_52w_high"))
    return f"| **{symbol}** | {last} | {vs_cost} | {rsi} | {ma_50} | {ma_200} | {hi_52} |"


def render(report: dict[str, Any]) -> str:
    """Render a report dict to a Markdown string. Top-level keys: date, vix_value, tier, snapshot, holdings."""
    date: str = report["date"]
    tier: TierResult = report["tier"]
    vix_value: float = report["vix_value"]
    snapshot: dict[str, Any] = report["snapshot"]
    holdings: dict[str, dict[str, Any]] = report["holdings"]

    badge = TIER_BADGE.get(tier.index, "•")
    stars = TIER_STARS.get(tier.index, "")

    lines: list[str] = []
    lines.append(f"# 📊 Daily Market — {date}")
    lines.append("")

    # ── Tier banner ───────────────────────────────────────────────────────
    range_lo, range_hi = tier.vix_range
    range_str = f"VIX {range_lo:g}–{range_hi:g}" if range_hi < 100 else f"VIX ≥{range_lo:g}"
    banner = (
        f"**VIX {vix_value:.2f}** → {badge} **Tier {tier.index} · {tier.action}** {stars}\n\n"
        f"Cash target **{tier.cash_target_pct}%**"
    )
    if tier.buy_size_pct:
        banner += f" · buy size **{tier.buy_size_pct}%**"
    banner += f" · range _{range_str}_"
    lines.append(banner)
    if tier.note:
        lines.append("")
        lines.append(f"> _{tier.note}_")
    lines.append("")

    # ── Tier action (today's playbook) ────────────────────────────────────
    lines.append("## 🎯 Tier Action")
    lines.append("")
    if tier.buy_list:
        lines.append("**Buy list:** " + ", ".join(f"`{t}`" for t in tier.buy_list))
    else:
        lines.append("**Buy list:** _(no buys at this tier)_")
    if tier.sell_list:
        lines.append("")
        lines.append("**Sell list:** " + ", ".join(f"`{t}`" for t in tier.sell_list))
    lines.append("")

    # ── Holdings ──────────────────────────────────────────────────────────
    lines.append("## 💼 Holdings")
    lines.append("")
    lines.append("| Ticker | Last | vs avg cost | RSI(14) | vs 50DMA | vs 200DMA | vs 52w high |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for symbol, h in holdings.items():
        lines.append(_holding_row(symbol, h))
    lines.append("")

    # ── Snapshot ──────────────────────────────────────────────────────────
    lines.append("## 🌐 Market Snapshot")
    lines.append("")
    lines.append("| Asset | Last | Δ |")
    lines.append("|---|---:|---:|")
    for label, q in snapshot.items():
        lines.append(_quote_row(label, q))
    lines.append("")

    # ── Footer ────────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated {date} · Asia/Taipei · not investment advice._")
    lines.append("")
    return "\n".join(lines)
