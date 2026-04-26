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


def _render_buy_list(buy_list: list[str], synthesis: dict[str, Any] | None) -> str:
    """Render the Tier Action buy list, annotating each ticker with its synthesis action when held.

    Resolves the visual contradiction between the static framework view (the buy list says "TSM
    is a Tier-2 candidate") and the tactical synthesis view (Today's Take says "TSM hold today
    because it's at 52w high"). For each buy-list ticker that's also in `synthesis.positions[]`
    (i.e. a current holding the model issued an action for), append the action inline:

        TSM (hold)

    Tickers not in the synthesis positions are framework candidates only — left as plain
    backticks so a reader can see at a glance which are pure candidates and which are held.
    """
    actions: dict[str, str] = {}
    if synthesis:
        for p in synthesis.get("positions") or []:
            if not isinstance(p, dict):
                continue
            sym = p.get("symbol")
            action = p.get("action")
            if isinstance(sym, str) and isinstance(action, str):
                actions[sym] = action
    parts: list[str] = []
    for t in buy_list:
        action = actions.get(t)
        if action:
            parts.append(f"`{t}` ({action})")
        else:
            parts.append(f"`{t}`")
    return ", ".join(parts)


def _render_todays_take(synthesis: dict[str, Any] | None) -> list[str]:
    """Render the 📝 Today's Take section, or [] if synthesis is missing/empty."""
    if not synthesis:
        return []
    market_raw = synthesis.get("market")
    if isinstance(market_raw, str):
        # Synthesis sometimes collapses `market` into a single string when the model
        # decides one paragraph captures both read and devils — tolerate it.
        market = {"read": market_raw}
    elif isinstance(market_raw, dict):
        market = market_raw
    else:
        market = {}
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


def _tier_relevant_sensitivity_tags(tier_idx: int | None, sensitivity_tags: list[str]) -> list[str]:
    """Filter sensitivity_tags to those relevant for the row's tier_index.

    Rules (from Phase 2.5 brief):
    - Tier 0-2: surface `high_normal`.
    - Tier 3+: surface `high_stress`, `crisis_alpha`.
    - Always surface `defensive` regardless of tier (tier-agnostic safe).

    `mean_reverter` is intentionally not surfaced here — it's a transition-trigger tag,
    surfaced via the synthesis prompt rather than the static Watch List.
    """
    if not sensitivity_tags:
        return []
    out: list[str] = []
    if tier_idx is not None and tier_idx <= 2 and "high_normal" in sensitivity_tags:
        out.append("high_normal")
    if tier_idx is not None and tier_idx >= 3:
        for tag in ("high_stress", "crisis_alpha"):
            if tag in sensitivity_tags:
                out.append(tag)
    if "defensive" in sensitivity_tags:
        out.append("defensive")
    return out


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
        sens_tags = _tier_relevant_sensitivity_tags(tier_idx, h.get("sensitivity_tags") or [])
        sens_str = f" ⋮ {' '.join(sens_tags)}" if sens_tags else ""
        rows.append(f"- **{symbol}** ({tier_str} / {account}): {flag_str}{sens_str}")
    if not rows:
        return []
    return ["## 🚩 Watch List", "", *rows, ""]


# ── Universe Scanner (Phase 2.5 Commit 6) ────────────────────────────────────

def _add_candidate_filter(tier_idx: int) -> tuple[str, str]:
    """Return (sensitivity_tag, human-readable filter description) for the Add column at this tier."""
    if tier_idx <= 2:
        return "high_normal", "high_normal"
    return "defensive", "defensive"


def _eligible(entry: dict[str, Any], tag: str) -> bool:
    """Universe entry passes the sample-size guard AND has the named sensitivity tag."""
    if entry.get("confidence") == "low":
        return False
    return tag in (entry.get("sensitivity_tags") or [])


def _fmt_signed_pct(v: Any) -> str:
    """JSON-serialized percentages live here as numbers (e.g. -8.3 = -8.3%); render with sign + 1 decimal."""
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%"


def _fmt_beta(v: Any) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}"


def _empty_row(col_count: int) -> str:
    """Render the `_no candidates_` placeholder row with the right number of cells."""
    cells = ["_no candidates at current thresholds_"] + [""] * (col_count - 1)
    return "| " + " | ".join(cells) + " |"


def _missing_universe_row(col_count: int) -> str:
    cells = ["_universe data not loaded — run scripts/analyzers/regime_sensitivity.py_"] + [""] * (col_count - 1)
    return "| " + " | ".join(cells) + " |"


def _render_add_candidates(
    tier_idx: int, regime_universe: dict[str, dict[str, Any]], avoid_tickers: set[str], data_present: bool,
) -> list[str]:
    tag, label = _add_candidate_filter(tier_idx)
    lines = [f"**🟢 Add candidates** _({label}, sample ≥ 8)_", "",
             "| Ticker | β normal | Sample | Note |",
             "|---|---:|---:|---|"]
    if not data_present:
        lines.append(_missing_universe_row(4))
        lines.append("")
        return lines

    candidates = [(s, e) for s, e in regime_universe.items() if _eligible(e, tag)]
    candidates.sort(key=lambda kv: (-abs(kv[1].get("beta_normal") or 0.0), kv[0]))
    top5 = candidates[:5]
    if not top5:
        lines.append(_empty_row(4))
    else:
        for sym, entry in top5:
            # Add row's metric (β normal) is computed from normal-regime weeks; show
            # normal_weeks here so Sample matches the metric's calculation basis.
            # Watch and Avoid sections show their own regime-matched counts.
            sample = entry.get("normal_weeks") or 0
            note = "⚠️ also in Avoid" if sym in avoid_tickers else ""
            lines.append(f"| {sym} | {_fmt_beta(entry.get('beta_normal'))} | {sample} | {note} |")
    lines.append("")
    return lines


def _watch_transition_empty_message(regime_universe: dict[str, dict[str, Any]]) -> str:
    """Italic placeholder text for 🟡 Watch — single-axis crush > +0.6% (Commit 10)."""
    valid = [e for e in regime_universe.values() if e.get("confidence") != "low"]
    recoveries = [e.get("vix_crush_recovery_pct") for e in valid if e.get("vix_crush_recovery_pct") is not None]
    if not recoveries:
        return "_no candidates fire crush > +0.6%_"
    best_recovery = max(recoveries)
    return f"_no candidates fire crush > +0.6% (best today: {best_recovery:+.2f}%)_"


def _render_watch_transition(
    regime_universe: dict[str, dict[str, Any]], data_present: bool,
) -> list[str]:
    lines = ["**🟡 Watch (transition)** _(mean_reverter, sample ≥ 8)_", "",
             "| Ticker | Crush recovery | Spike decay | Note |",
             "|---|---:|---:|---|"]
    if not data_present:
        lines.append(_missing_universe_row(4))
        lines.append("")
        return lines

    candidates = [(s, e) for s, e in regime_universe.items() if _eligible(e, "mean_reverter")]
    candidates.sort(key=lambda kv: (-(kv[1].get("vix_crush_recovery_pct") or 0.0), kv[0]))
    top5 = candidates[:5]
    if not top5:
        msg = _watch_transition_empty_message(regime_universe)
        lines.append(f"| {msg} |  |  |  |")
    else:
        for sym, entry in top5:
            lines.append(
                f"| {sym} | {_fmt_signed_pct(entry.get('vix_crush_recovery_pct'))} | "
                f"{_fmt_signed_pct(entry.get('vix_spike_decay_pct'))} |  |"
            )
    lines.append("")
    return lines


def _avoid_empty_message(regime_universe: dict[str, dict[str, Any]]) -> str:
    """Italic placeholder text for 🔴 Avoid — surfaces today's worst p25 spike-decay vs the -4% threshold.

    Commit 10 (2026-04-26): threshold tuned from -10% → -4% (initially proposed
    -5% but data showed worst p25 was INTC at -4.98%, just above the bar). Tuned
    to natural break in 5y 2021-2026 universe. Commit 8 introduced p25 methodology.
    """
    valid = [e for e in regime_universe.values() if e.get("confidence") != "low"]
    p25_decays = [e.get("vix_spike_decay_p25_pct") for e in valid if e.get("vix_spike_decay_p25_pct") is not None]
    if not p25_decays:
        return "_no candidates fire p25 decay < -4%_"
    worst_decay = min(p25_decays)
    return f"_no candidates fire p25 decay < -4% (worst today: {worst_decay:+.2f}%)_"


def _render_avoid_candidates(
    regime_universe: dict[str, dict[str, Any]], add_tickers: set[str], data_present: bool,
) -> list[str]:
    lines = ["**🔴 Avoid candidates** _(crisis_alpha, sample ≥ 8)_", "",
             "| Ticker | Spike decay | Sample | Note |",
             "|---|---:|---:|---|"]
    if not data_present:
        lines.append(_missing_universe_row(4))
        lines.append("")
        return lines

    candidates = [(s, e) for s, e in regime_universe.items() if _eligible(e, "crisis_alpha")]
    candidates.sort(key=lambda kv: (-abs(kv[1].get("vix_spike_decay_pct") or 0.0), kv[0]))
    top5 = candidates[:5]
    if not top5:
        msg = _avoid_empty_message(regime_universe)
        lines.append(f"| {msg} |  |  |  |")
    else:
        for sym, entry in top5:
            sample = min(
                entry.get("spike_event_count") or 0,
                entry.get("crush_event_count") or 0,
                entry.get("stress_weeks") or 0,
                entry.get("normal_weeks") or 0,
            )
            note = "also in Add" if sym in add_tickers else ""
            lines.append(
                f"| {sym} | {_fmt_signed_pct(entry.get('vix_spike_decay_pct'))} | {sample} | {note} |"
            )
    lines.append("")
    return lines


def _render_universe_scanner(
    tier_idx: int, tier_action: str, regime_universe: dict[str, dict[str, Any]] | None,
) -> list[str]:
    """Render the 📡 Universe Scanner block with three always-rendered sub-regions.

    All three sub-regions render even when their candidate list is empty — the placeholder row
    surfaces "thresholds need tuning" as an observable state rather than hiding the question.

    Heading is bilingual (`Tier 2 (觀察)`) so a Chinese-reading skim shows tier intent without
    reading the table. `tier_action` is `tier.action` from analyzers.vix_tier (e.g. "觀察").
    """
    universe = regime_universe or {}
    data_present = bool(universe)

    add_tag, _ = _add_candidate_filter(tier_idx)
    add_set = (
        {s for s, e in universe.items() if _eligible(e, add_tag)} if data_present else set()
    )
    avoid_set = (
        {s for s, e in universe.items() if _eligible(e, "crisis_alpha")} if data_present else set()
    )

    lines: list[str] = [
        f"## 📡 Universe Scanner — Tier {tier_idx} ({tier_action})",
        "",
        "_β normal: regime-conditional beta vs SPX in calm weeks. "
        "Crush recovery: 5-day return after VIX falls ≥30%. "
        "Spike decay: 5-day return after VIX rises ≥20%._",
        "",
    ]
    lines.extend(_render_add_candidates(tier_idx, universe, avoid_set, data_present))
    lines.extend(_render_watch_transition(universe, data_present))
    lines.extend(_render_avoid_candidates(universe, add_set, data_present))
    return lines


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
        lines.append("**Buy list:** " + _render_buy_list(tier.buy_list, synthesis))
    else:
        lines.append("**Buy list:** _(no buys at this tier)_")
    if tier.sell_list:
        lines.append("")
        lines.append("**Sell list:** " + ", ".join(f"`{t}`" for t in tier.sell_list))
    lines.append("")

    # ── Watch List (flag-driven) ──────────────────────────────────────────
    lines.extend(_render_watch_list(holdings))

    # ── Universe Scanner (regime sensitivity) ─────────────────────────────
    lines.extend(_render_universe_scanner(tier.index, tier.action, report.get("regime_universe")))

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
