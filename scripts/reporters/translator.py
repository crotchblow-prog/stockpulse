"""English → Traditional Chinese translation for the daily report. Brief A Commit 4.

Two entry points:
- `translate_markdown(en_markdown)` — translates the full rendered markdown body.
- `translate_synthesis(en_synthesis)` — translates only the text fields inside the
  synthesis dict, preserving structure (so the JSON sidecar is valid in both langs).

Both raise on hard failure; the caller in generate_report.py catches Exception and
ships the EN report alone with a warning. Translation quality is best-effort —
Carina has explicitly accepted that nuance may be lost; do NOT over-engineer.
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

log = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS_MARKDOWN = 4096  # full markdown body, generous budget
MAX_TOKENS_SYNTHESIS = 1536  # mirrors claude_synthesis output budget + slack

# ── Markdown translation ─────────────────────────────────────────────────────

MARKDOWN_SYSTEM_PROMPT = """\
You translate English daily-market reports for a Taiwanese trader (Carina) into Traditional Chinese (zh-TW). The source is rendered Markdown for the StockPulse / VIXPulse decision-support tool.

# Translation rules — non-negotiable

- Output ONLY the translated Markdown. No preamble, no explanation, no code fences around the whole document.
- Preserve ALL Markdown structure exactly: headings, tables, list bullets, bold/italic, blockquotes, horizontal rules, code spans, line breaks. Do not reformat.
- **Ticker symbols** (TSM, SOFI, IONQ, PLTR, NVDA, GOOGL, etc.) stay verbatim. Never translate or transliterate them.
- **Flag names** in code spans or backticks (`oversold_rsi`, `earnings_within_7d`, `buy_list_member`, `high_risk_tag`, `event_play`, etc.) stay verbatim. Never translate.
- **Action verbs** in position calls (add, hold, trim, exit, watch) stay English. They map to Carina's manual execution language.
- **Confidence levels** (low, medium, high) stay English.
- **All numeric values** (prices, percentages, RSI numbers, dates in YYYY-MM-DD form) stay verbatim. Never round, reformat, or restate.
- **Section headers** translate normally:
  - "Today's Take" → "今日觀點"
  - "Watch List" → "關注名單"
  - "Holdings" → "持倉"
  - "Market Snapshot" → "市場快照"
  - "Tier Action" → "Tier 行動" (keep "Tier" verbatim — it's framework signature)
  - "Daily Market" → "每日市場"
  - "Buy list" → "買進清單", "Sell list" → "賣出清單"
  - "Market read" → "市場解讀", "Devil's advocate" → "反方觀點", "Position calls" → "持倉判斷"
- **Framework terms** keep English with transliteration where natural:
  - "Tier 0/1/2/…" stays as "Tier 0/1/2/…" (do not translate to "第 X 階")
  - "VIX" stays as "VIX"
  - "DMA" stays as "DMA" (e.g., "vs 50DMA" → "相對 50DMA")
  - "RSI" stays as "RSI"
  - "Cash target" → "現金目標"
  - "buy size" → "進場規模"
- **Pre-existing Chinese text** (e.g., "觀察", "警戒佈局", "避開財報前 7 天的標的") stays exactly as-is. Do not re-translate or re-paraphrase.
- **Footer disclaimer** ("not investment advice") → "非投資建議".
- **Generation timestamp** ("Generated 2026-04-26 · Asia/Taipei") → "生成於 2026-04-26 · Asia/Taipei".

# Tone

Professional, concise, framework-native. Match the source's terse "decision-grade" register — do not soften, hedge, or add disclaimers the source didn't have.
"""


def translate_markdown(en_markdown: str) -> str:
    """One Anthropic call, full markdown in → translated markdown out. Raises on failure."""
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_MARKDOWN,
        system=[
            {
                "type": "text",
                "text": MARKDOWN_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": en_markdown}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    if not parts:
        raise RuntimeError(
            f"translator returned no text blocks; stop_reason={getattr(resp, 'stop_reason', '?')}"
        )
    log.info(
        "translate_markdown ok — in=%s out=%s cache_read=%s",
        getattr(resp.usage, "input_tokens", None),
        getattr(resp.usage, "output_tokens", None),
        getattr(resp.usage, "cache_read_input_tokens", None),
    )
    return "".join(parts).strip() + "\n"


# ── Synthesis-dict translation ───────────────────────────────────────────────

SYNTHESIS_TRANSLATE_TOOL: dict[str, Any] = {
    "name": "emit_translated_synthesis",
    "description": "Emit the synthesis payload with text fields translated to zh-TW; structure unchanged.",
    "input_schema": {
        "type": "object",
        "properties": {
            "market": {
                "type": "object",
                "properties": {
                    "read": {"type": "string", "description": "Translate to zh-TW. Tickers/flags/numbers stay English."},
                    "devils_advocate": {"type": "string", "description": "Translate to zh-TW."},
                },
                "required": ["read", "devils_advocate"],
            },
            "positions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker — keep verbatim, do not translate."},
                        "action": {"type": "string", "description": "Action enum — keep English (add|hold|trim|exit|watch)."},
                        "confidence": {"type": "string", "description": "Confidence enum — keep English (low|medium|high)."},
                        "rationale": {"type": "string", "description": "Translate to zh-TW. Numbers/flags/tickers stay verbatim."},
                    },
                    "required": ["symbol", "action", "confidence", "rationale"],
                },
            },
        },
        "required": ["market", "positions"],
    },
}

SYNTHESIS_SYSTEM_PROMPT = """\
You translate the text fields in a StockPulse / VIXPulse synthesis payload from English to Traditional Chinese (zh-TW), preserving the JSON structure exactly.

Translate ONLY these fields:
- market.read
- market.devils_advocate
- positions[].rationale

Keep verbatim (do NOT translate):
- All ticker symbols (TSM, SOFI, IONQ, PLTR, etc.)
- All flag names (oversold_rsi, earnings_within_7d, etc.)
- All numeric values (RSI numbers, percentages, dates, prices)
- positions[].symbol, positions[].action, positions[].confidence
- Framework terms: Tier 0/1/2/…, VIX, DMA, RSI

Translation register: terse, decision-grade, framework-native. Match source tone — do not soften or add hedging.

Emit exactly one tool call to `emit_translated_synthesis`. No prose outside the tool call.
"""


def translate_synthesis(en_synthesis: dict[str, Any]) -> dict[str, Any]:
    """Translate only the text fields inside a synthesis dict; preserve structure + metadata.

    Input shape matches `claude_synthesis.synthesize` output. Output preserves the same
    `market`/`positions` shape with text fields in zh-TW; non-text fields (`model`,
    `usage`) are passed through from the original.
    """
    payload = {
        "market": en_synthesis.get("market") or {},
        "positions": en_synthesis.get("positions") or [],
    }
    client = anthropic.Anthropic()
    import json
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_SYNTHESIS,
        system=[
            {
                "type": "text",
                "text": SYNTHESIS_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[SYNTHESIS_TRANSLATE_TOOL],
        tool_choice={"type": "tool", "name": SYNTHESIS_TRANSLATE_TOOL["name"]},
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == SYNTHESIS_TRANSLATE_TOOL["name"]:
            translated = dict(block.input)
            # Re-attach metadata so the zh JSON sidecar carries the same provenance as en.
            for k in ("model", "usage"):
                if k in en_synthesis:
                    translated[k] = en_synthesis[k]
            log.info(
                "translate_synthesis ok — in=%s out=%s",
                getattr(resp.usage, "input_tokens", None),
                getattr(resp.usage, "output_tokens", None),
            )
            return translated
    raise RuntimeError(
        f"no {SYNTHESIS_TRANSLATE_TOOL['name']!r} tool_use in response; "
        f"stop_reason={getattr(resp, 'stop_reason', '?')}"
    )
