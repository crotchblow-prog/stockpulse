"""Single Anthropic call → structured 'Today's Take' for the daily report. Phase 2 Commit 3.

The output dict matches the contract `markdown_gen._render_todays_take` reads:
    {
        "market":    {"read": str, "devils_advocate": str},
        "positions": [{"symbol", "action", "confidence", "rationale"}, ...],
        "model":     str,
        "usage":     {"input_tokens", "output_tokens", "cache_read_input_tokens"},
    }

Strict JSON shape is enforced by emitting via a tool_use block (`tool_choice` forces it),
so the model cannot return free-form prose. The caller in `generate_report.maybe_synthesize`
catches Exception and degrades to no-synthesis if anything here raises.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

log = logging.getLogger(__name__)

# `claude-sonnet-4-6` is the floating alias for the latest Sonnet 4.6 release.
# Pin to a dated alias once one is published if we ever see synthesis drift between days.
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024  # one short read paragraph + N position calls; ample for 4–8 holdings.

ACTION_ENUM = ["hold", "add", "trim", "exit", "watch"]
CONFIDENCE_ENUM = ["low", "medium", "high"]

# ── Output contract — emitted via tool_use to guarantee strict JSON ──────────

SYNTHESIS_TOOL: dict[str, Any] = {
    "name": "emit_todays_take",
    "description": "Emit the structured 'Today's Take' for the daily market report.",
    "input_schema": {
        "type": "object",
        "properties": {
            "market": {
                "type": "object",
                "properties": {
                    "read": {
                        "type": "string",
                        "description": (
                            "1–3 sentence read on today's market through the VIX tier lens. "
                            "Decision-grade prose. No disclaimers."
                        ),
                    },
                    "devils_advocate": {
                        "type": "string",
                        "description": (
                            "1–2 sentence genuine contrarian read — what would invalidate the "
                            "main thesis. Not a hedging boilerplate."
                        ),
                    },
                },
                "required": ["read", "devils_advocate"],
            },
            "positions": {
                "type": "array",
                "description": "One entry per holding currently in the book.",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "action": {"type": "string", "enum": ACTION_ENUM},
                        "confidence": {"type": "string", "enum": CONFIDENCE_ENUM},
                        "rationale": {
                            "type": "string",
                            "description": (
                                "≤2 short sentences referencing concrete flags / numbers from "
                                "the input (e.g. 'RSI 55, 23% below 200DMA, 30% underwater')."
                            ),
                        },
                    },
                    "required": ["symbol", "action", "confidence", "rationale"],
                },
            },
        },
        "required": ["market", "positions"],
    },
}

# ── System prompt — encodes Carina's framework + §2.4 special-case rules ─────

SYSTEM_PROMPT = """\
You are the synthesis layer for StockPulse, a daily decision-support report for Carina, a USD/JPY forex trader who also runs a small US equity book across three accounts (Exness CFD, Taiwan brokerage cash equities, LEAPS).

Your job: read the day's market snapshot, VIX tier classification, and per-holding facts (price action, technicals, closed-vocab flags, earnings countdown), and emit a structured 'Today's Take' that tells Carina what to *do* — not just what is.

# Framework she trades by

- VIX tier system, 6 tiers. The VIX is a probability gauge, not a forecast. Each tier has a cash target and a buy list:
  - Tier 0 (VIX <15): 70% cash, no buys — market complacent, asymmetric downside.
  - Tier 1 (15-18): 60% cash, 2-5% buys — defensives only (KO, JNJ, WMT, VZ, PG, MRK).
  - Tier 2 (18-24.6): 50% cash, 3-5% buys — quality growth small entries.
  - Tier 3 (24.6-29.5): 35% cash, 5-10% buys — real opportunity emerges.
  - Tier 4 (29.5-35): 20% cash, 10-20% buys — high-conviction.
  - Tier 5 (>35): 20% cash, large but never all-in — best risk/reward in years.
- Never below 20% cash, even Tier 5. Preserve optionality.
- Beta-aware sizing: Beta > 1.5 gets tighter stops.
- No averaging down on losers, especially names with negative catalysts.
- Trim or hedge before known earnings (within 7 days).
- Single-name concentration cap: ~30% of total assets.

# Special-case positions (do not improvise around these)

- SOFI is flagged `high_risk` due to active Muddy Waters short-seller report (April 2026). Treat as a binary event play around earnings. Never recommend `add` for SOFI within 7 days of earnings — `hold`, `trim`, or `exit` are the only valid actions when `earnings_within_7d` is in flags. Outside the 7d window, SOFI may be `hold` or `trim`; `add` requires an extraordinarily clear setup and at most `low` confidence.
- TSM has standing geopolitical tail risk (Taiwan Strait). Polymarket "China invades Taiwan 2026" is monitored but only actioned if it crosses 25% (currently around 9%, not a factor for today). Treat TSM like any other Tier 2/3 buy-list semi name today.

# Regime sensitivity tags (Phase 2.5 — read each position's `sensitivity_tags` if present)

Each position may include `sensitivity_tags` reflecting how the ticker historically responds to VIX regime changes. When present, factor them into the action call:

- `crisis_alpha` — falls hard on VIX spikes. Avoid `add` for these names during a tier transition UP into stress regimes (Tier 2→3, 3→4).
- `defensive` — low VIX-sensitivity (KO/JNJ/PG-style). Remains a candidate for `add` even at Tier 3-4. Do not trim on Tier 2 framework bias against high-beta if the name is defensively tagged.
- `mean_reverter` — drops then snaps back. Promote to `watch` priority on tier transitions DOWN (Tier 3→2, 4→3) — these are entry candidates as the regime relaxes.
- `high_normal` — high vol under calm regime. Appropriate `add` target at Tier 0-2 only. Do not add at Tier 3+.
- `high_stress` — amplifies in stress. Warning at Tier 3+; prefer `trim` over `hold` if also flagged `high_stress`.

Holdings without `sensitivity_tags` (or with `missing_from_universe`) are tickers outside the regime universe (e.g., SOFI, IONQ, PLTR are not on Exness so not backtested). Reason from flags + tier alone for those.

# Style

- Decision-grade. No hedging boilerplate, no "consult a financial advisor" disclaimers — Carina knows.
- Reference concrete flags / numbers from the input (e.g. "RSI 55, 23% below 200DMA, 30% underwater") rather than vague language.
- The devil's advocate must be a real contrarian thesis — what would invalidate the main read — not a polite rephrasing.
- Match `action` to the tier's posture: do not recommend `add` at Tier 0 even on a `buy_list_member`.
- Output exactly one tool call to `emit_todays_take`. No prose outside the tool call.
"""


def synthesize(report: dict[str, Any]) -> dict[str, Any]:
    """Call Anthropic once and return the structured Today's Take dict.

    The caller (`generate_report.maybe_synthesize`) catches Exception and degrades to no
    synthesis on any failure, so this raises freely on API errors / malformed responses.
    """
    client = anthropic.Anthropic()
    user_payload = _build_user_payload(report)

    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[SYNTHESIS_TOOL],
        tool_choice={"type": "tool", "name": SYNTHESIS_TOOL["name"]},
        messages=[{"role": "user", "content": user_payload}],
    )

    payload = _extract_tool_payload(resp)
    payload["model"] = MODEL
    payload["usage"] = {
        "input_tokens": getattr(resp.usage, "input_tokens", None),
        "output_tokens": getattr(resp.usage, "output_tokens", None),
        "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", None),
    }
    log.info(
        "synthesis ok — in=%s out=%s cache_read=%s",
        payload["usage"]["input_tokens"],
        payload["usage"]["output_tokens"],
        payload["usage"]["cache_read_input_tokens"],
    )
    return payload


def _extract_tool_payload(resp: Any) -> dict[str, Any]:
    """Pull the single emit_todays_take tool_use input from a Messages response."""
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == SYNTHESIS_TOOL["name"]:
            return dict(block.input)
    raise RuntimeError(
        f"no {SYNTHESIS_TOOL['name']!r} tool_use in response; "
        f"stop_reason={getattr(resp, 'stop_reason', '?')}"
    )


def _build_user_payload(report: dict[str, Any]) -> str:
    """Compact JSON of the day's facts for the model. Stable shape — keeps day-over-day diffs minimal."""
    tier = report["tier"]

    snapshot_brief: dict[str, Any] = {}
    for label, q in (report.get("snapshot") or {}).items():
        if getattr(q, "error", None):
            continue
        snapshot_brief[label] = {
            "last": getattr(q, "last", None),
            "change_pct": getattr(q, "change_pct", None),
        }

    holdings_brief: dict[str, Any] = {}
    for sym, h in (report.get("holdings") or {}).items():
        if h.get("error"):
            holdings_brief[sym] = {"error": h["error"]}
            continue
        holdings_brief[sym] = {
            "last": h.get("last"),
            "vs_avg_cost": h.get("vs_avg_cost"),
            "rsi_14": h.get("rsi_14"),
            "pct_from_ma_50": h.get("pct_from_ma_50"),
            "pct_from_ma_200": h.get("pct_from_ma_200"),
            "pct_from_52w_high": h.get("pct_from_52w_high"),
            "tags": h.get("tags") or [],
            "flags": h.get("flags") or [],
            "sensitivity_tags": h.get("sensitivity_tags") or [],
            "missing_from_universe": bool(h.get("missing_from_universe")),
            "days_to_earnings": h.get("days_to_earnings"),
            "earnings_date": h.get("earnings_date"),
            "account": h.get("account"),
        }

    payload = {
        "date": report["date"],
        "vix": report.get("vix_value"),
        "tier": {
            "index": tier.index,
            "name": tier.name,
            "action": tier.action,
            "cash_target_pct": tier.cash_target_pct,
            "buy_size_pct": tier.buy_size_pct,
            "buy_list": list(tier.buy_list or []),
            "sell_list": list(tier.sell_list or []),
            "note": tier.note,
        },
        "snapshot": snapshot_brief,
        "holdings": holdings_brief,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
