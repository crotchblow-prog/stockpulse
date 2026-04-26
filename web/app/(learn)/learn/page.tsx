import { ReportViewer } from "@/components/ReportViewer";

export const dynamic = "force-static";

const CONTENT = `# 📊 VIXPulse — A Beginner's Guide

VIXPulse is a daily decision-support tool for stock market investors. This page explains what VIX is, what each section of the daily report shows, and how to use the framework to invest with discipline rather than emotion.

---

## What is VIX?

VIX is **Wall Street's fear gauge**. It measures how nervous the market is *right now*, looking ahead 30 days.

Mechanically, it's calculated from S&P 500 options prices (options are contracts that pay out if the market crosses a price by a certain date). When traders pay up for crash protection, VIX rises. When they don't bother, VIX falls.

**Important**: VIX measures *expected* volatility, not direction. A high VIX means "big moves likely" — could be up or down — but historically big VIX moves correlate with falling markets.

### A rough mental model

| VIX level | What it means | Common pattern |
|---|---|---|
| Below 15 | Market complacent, trader confidence high | Often precedes corrections |
| 15–20 | Normal conditions | Most weeks of most years |
| 20–25 | Some concern; news creating volatility | Average bear-market level |
| 25–35 | Real fear; selloff in progress | Often near short-term bottoms |
| Above 35 | Panic; major crisis | Historic buying opportunities (2008, 2020) |

The VIX has spent ~85% of its history below 25. Periods above 35 are rare and short-lived. **By the time most retail investors notice the news driving a high VIX, the worst is often already in.**

---

## The VIXPulse framework — six tiers

VIXPulse codifies how to act based on the current VIX. Six tiers, each with a target cash percentage to keep on the sidelines, a target buy size per new position, and a buy list appropriate for that level of fear.

| Tier | VIX | Action | Cash Target | Buy Size |
|---|---|---|---|---|
| 0 | <15 | 休兵 (rest) | 70% | 0% |
| 1 | 15–18 | 警戒佈局 (cautious positioning) | 60% | 2-5% |
| 2 | 18–24.6 | 觀察 (watch) | 50% | 3-5% |
| 3 | 24.6–29.5 | 分批進場 (scale in) ⭐ | 35% | 5-10% |
| 4 | 29.5–35 | 恐慌承接 (catch the panic) ⭐⭐ | 20% | 10-20% |
| 5 | >35 | 極端機會 (extreme opportunity) ⭐⭐⭐ | 20% | heavy, but never all-in |

**The core insight**: most investors do the opposite of what the VIX recommends. They buy heavily when markets feel safe (low VIX, near tops) and sell when markets feel scary (high VIX, often near bottoms). The framework forces the reverse — light buying in calm, heavy buying in panic.

---

## How to read the daily report

Each daily report has six sections, each answering a different question.

### 📊 Tier banner — *"Where are we today?"*

The header shows the current VIX, today's tier, the suggested cash target, and the buy-size band. Glance at this first — it's the macro context for everything else.

### 📝 Today's Take — *"What should I do?"*

A two-paragraph synthesis from Claude (an AI):
- **Market read** — a 1-3 sentence summary of today's tape through the tier-framework lens.
- **Devil's advocate** — a 1-2 sentence contrarian view: what could invalidate the main read.

Plus per-position **Position calls**: for each holding, an action (\`hold\`, \`add\`, \`trim\`, \`exit\`, or \`watch\` — meaning "wait for a setup, don't act yet") with confidence and rationale.

### 🚩 Watch List — *"What should I worry about in my current positions?"*

Holdings that triggered any of a fixed set of standardized labels — short tags like \`oversold_rsi\`, \`earnings_within_7d\`, \`deep_drawdown\`, \`near_52w_high\`. Use this as a per-position alarm system.

### 📡 Universe Scanner — *"What could I add to / avoid right now?"*

A list of candidates from a 59-ticker universe of US large-caps, filtered by today's VIX tier and how each name has historically behaved across VIX regimes. Separated into:
- 🟢 **Add candidates** — tier-appropriate names with strong historical behavior in the current regime.
- 🟡 **Watch (transition)** — names that benefit when VIX falls; entry candidates as fear subsides.
- 🔴 **Avoid candidates** — names that historically break under VIX spikes.

### 💼 Holdings — *"Current position statistics"*

For each holding: price, return vs cost, RSI, distance from 50-day and 200-day moving averages, distance from the 52-week high.

### 🌐 Market Snapshot — *"Broad context"*

VIX itself, VIX3M (forward expectation), S&P 500, Nasdaq, Dow, USD/JPY, BTC, gold, WTI oil. The cross-asset context for today.

---

## Five rules for using VIXPulse to invest better

### 1. Use cash targets as anchors, not commands

If today says 50% cash and you're at 40%, that's a signal to be cautious about adding (not a panic-sell signal). If you're at 70%, that's room to deploy. The cash target is gravity — your portfolio drifts toward it over time, not in one day.

### 2. Add slowly during stress, sell slowly during euphoria

When VIX moves into Tier 3-5, it's tempting to wait for "the absolute bottom." Don't. Add 5-10% per Tier 3 day, 10-20% per Tier 4 day, in chunks. Some buys will be early; that's fine. The goal is **disciplined accumulation**, not perfect timing.

### 3. Trust the framework over the headline

When the news is screaming "WORST CRISIS EVER" and VIXPulse is in Tier 4, the framework is telling you to buy. The discomfort of buying *during* fear is precisely the edge — most investors freeze and miss it.

### 4. Position sizing matters more than timing

A 3% position in NVDA at the wrong moment is recoverable. A 30% position in NVDA at the right moment is also recoverable, but a 30% position in NVDA at the wrong moment is not. **Always size within the tier's buy-size band.** Concentration is the source of pain even when you were directionally correct.

### 5. Earnings and special-case rules override the framework

If a holding has \`earnings_within_7d\`, default to trim or hedge — even if the tier says add. Binary catalysts (earnings, FDA decisions, merger votes) introduce a single-event risk that the framework's regime logic doesn't price. The Watch List flags these so you don't have to track them by hand.

---

## What VIXPulse is NOT

- ❌ **Not financial advice.** Every report ends with "not investment advice." The framework is one input — your judgment is the final call.
- ❌ **Not auto-trading.** No orders are sent. Every action is manual.
- ❌ **Not day-trading.** Timeframes are daily and multi-day. If you're in and out within hours, this isn't for you.
- ❌ **Not get-rich-quick.** The framework is about *not losing money in the wrong regime*. Compounding wins come from discipline over years.

---

## Getting started

1. **Read today's report.** Note the current tier and cash target.
2. **Compare to your portfolio.** Are you above or below the cash target?
3. **Set a small drift goal.** "I'll move 5% closer to the target this week" — not "I'll restructure everything today."
4. **Watch the Watch List for your holdings** for binary catalysts (earnings, special-case flags).
5. **Use the Universe Scanner** when you have cash to deploy and want to see what fits today's regime.

---

## Open source

VIXPulse is open-source: [github.com/crotchblow-prog/stockpulse](https://github.com/crotchblow-prog/stockpulse). The framework lives in \`config/holdings.json:tier_strategy\`. The 59-ticker universe lives in \`scripts/analyzers/regime_sensitivity.py:UNIVERSE\`. Daily reports are committed to \`web/public/reports/\`.

---

*Generated daily · Asia/Taipei · not investment advice.*
`;

export default function LearnPage() {
  return <ReportViewer markdown={CONTENT} />;
}
