"""Render the report dict produced by generate_report into a Markdown document."""

from __future__ import annotations

from typing import Any

from analyzers.flags import is_watchworthy
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


def _render_todays_take(synthesis: dict[str, Any] | None) -> list[str]:
    """Render the 📝 Today's Take section, or [] if synthesis is missing/empty."""
    if not synthesis:
        return []
    market = synthesis.get("market") or {}
    positions = synthesis.get("positions") or []
    read = market.get("read")
    devils = market.get("devils_advocate")
    if not (read or devils or positions):
        return []
    lines = ["## 📝 Today's Take", ""]
    if read:
        lines.append(f"**Market read.** {read}")
        lines.append("")
    if devils:
        lines.append(f"**Devil's advocate.** {devils}")
        lines.append("")
    if positions:
        lines.append("**Position calls:**")
        for p in positions:
            sym = p.get("symbol", "—")
            action = p.get("action", "—")
            conf = p.get("confidence", "—")
            rationale = p.get("rationale", "").strip()
            tail = f" {rationale}" if rationale else ""
            lines.append(f"- **{sym}** — {action} ({conf}).{tail}")
        lines.append("")
    return lines


def _render_watch_list(holdings: dict[str, dict[str, Any]]) -> list[str]:
    """Render 🚩 Watch List for holdings whose flags are watchworthy. Skips section if no rows."""
    rows: list[str] = []
    for symbol, h in holdings.items():
        flags = h.get("flags") or []
        if not is_watchworthy(flags):
            continue
        account = h.get("account") or "?"
        tier_idx = h.get("tier_index")
        tier_str = f"Tier {tier_idx}" if tier_idx is not None else "—"
        flag_str = ", ".join(flags) if flags else "_no flags_"
        rows.append(f"- **{symbol}** ({tier_str} / {account}): {flag_str}")
    if not rows:
        return []
    return ["## 🚩 Watch List", "", *rows, ""]


def render(report: dict[str, Any]) -> str:
    """Render a report dict to a Markdown string. Top-level keys: date, vix_value, tier, snapshot, holdings, synthesis?."""
    date: str = report["date"]
    tier: TierResult = report["tier"]
    vix_value: float = report["vix_value"]
    snapshot: dict[str, Any] = report["snapshot"]
    holdings: dict[str, dict[str, Any]] = report["holdings"]
    synthesis = report.get("synthesis")

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

    # ── Today's Take (synthesis) ──────────────────────────────────────────
    lines.extend(_render_todays_take(synthesis))

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

    # ── Watch List (flag-driven) ──────────────────────────────────────────
    lines.extend(_render_watch_list(holdings))

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
