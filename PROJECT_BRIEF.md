# StockPulse — Project Brief

> **Purpose**: This document is the single source of truth for *why* StockPulse exists and *how* decisions should be made. ARIA and MIRA should consult this before making architectural changes. The owner (Carina) updates this when strategic direction changes.
>
> **Last updated**: 2026-04-27
> **Owner**: Carina
> **Maintainer**: ARIA (Claude Code on MacBook Air)
> **Worker**: MIRA (Claude Code on Mac Mini, via [agent-bus](https://github.com/crotchblow-prog/agent-bus))
>
> **Strategic advisor**: Conversations with Claude on claude.ai (the owner relays decisions back here)

---

## 1. Owner Profile & Context

**Carina** is primarily a USD/JPY forex trader (via Exness MT5) who also holds a US equity portfolio across three accounts. She has prior experience building production trading infrastructure (SMC Pulse — Python + Supabase + GitHub Actions stack) and has built her own multi-agent coordination layer ([agent-bus](https://github.com/crotchblow-prog/agent-bus)) on top of git.

### Trading accounts

| Account | Type | Purpose | Current state (as of 2026-04-25) |
|---|---|---|---|
| **Exness** (MT5) | CFD | USD/JPY primary + occasional US equity CFDs | Holds TSM, recently closed GOOGL & TSLA |
| **Taiwan brokerage** (複委託) | Cash equities | Long-term US stock positions | IONQ, PLTR, SOFI; ex-RKLB (closed) |
| **LEAPS account** (US broker) | Long-dated options | Thematic 2027/2028 calls | Currently 100% cash after recent cleanup |

### Decision-making style

Carina prefers:
- **Framework-driven decisions** over gut feel
- **Quantitative thresholds** (e.g., VIX tier boundaries) over vibes
- **Risk management first** (avoid losses) over upside chasing
- **Discipline over FOMO** — willing to sit in cash and wait
- **Multiple confluences** before acting (VIX + technical + Polymarket + earnings calendar)

### What StockPulse is NOT for

- ❌ Auto-trading (Carina executes manually, always)
- ❌ Day trading signals (timeframe is daily / multi-day)
- ❌ Get-rich-quick recommendations
- ❌ Replacing human judgment

StockPulse is a **decision-support system**, not an auto-pilot.

---

## 2. Investment Philosophy (Embedded in `holdings.json`)

### 2.1 The VIX Tier System (core framework)

The VIX is treated as a *probability gauge* for risk-adjusted entry timing. Six tiers, each with a specific cash target and buy-list profile. The boundaries are derived from historical VIX percentile analysis:

| Tier | VIX range | Action | Cash target | Buy size | Rationale |
|---|---|---|---|---|---|
| 0 | < 15 | 休兵 (rest) | 70% | 0% | Bottom decile of VIX history → market complacent → asymmetric downside |
| 1 | 15–18 | 警戒佈局 | 60% | 2-5% | Below average → small defensive positioning only |
| 2 | 18–24.6 | 觀察 | 50% | 3-5% | Median range → quality growth small entries |
| 3 | 24.6–29.5 | 分批進場 ⭐ | 35% | 5-10% | Top quartile → real opportunity emerges |
| 4 | 29.5–35 | 恐慌承接 ⭐⭐ | 20% | 10-20% | Top decile → genuine fear → high-conviction buys |
| 5 | > 35 | 極端機會 ⭐⭐⭐ | 20% | 重押但不 all-in | Crisis territory → best risk/reward in years |

**Critical principles**:
- Never go below 20% cash, even in Tier 5 (preserve optionality for "worse than worst case")
- Buy lists per tier are codified in `config/holdings.json` under `tier_strategy`
- Defensive stocks (KO, JNJ, WMT, VZ, PG, MRK) are accumulated *earlier* (Tier 1+); high-beta growth (NVDA, TSLA, AMD) only at Tier 3+

### 2.2 Why this framework exists

It solves a specific psychological failure mode: **buying high (low VIX = market euphoria) and selling low (high VIX = panic)**. By codifying entry sizing as a function of VIX percentile, Carina removes emotion from the entry decision.

### 2.3 Risk management rules (apply to all positions)

1. **Beta-aware sizing**: positions with Beta > 1.5 get tighter stops
2. **Event-day reduction**: trim or hedge before known earnings / FOMC
3. **No averaging down on losers** — especially on names with negative catalysts
4. **Pair high-beta with defensive**: every $10K NVDA-equivalent gets $3K KO/JNJ
5. **Single-name concentration cap**: no single ticker > ~30% of total assets

### 2.4 Special-case positions

- **SOFI** is flagged as `high_risk` due to active short-seller report (Muddy Waters, Apr 2026). Standard rules suspended; treated as binary event play around earnings.
- **TSM** has standing geopolitical tail risk (Taiwan Strait). Polymarket "China invades Taiwan 2026" stays around 9% — monitored but not actioned unless > 25%.

---

## 3. Project Goals & Phases

### 3.1 The core problem StockPulse solves

> "I have the framework, but I don't have the *daily discipline* to execute it. I need a tool that tells me where we are in the framework today, what my positions look like through that lens, and what specific actions are warranted."

### 3.2 Phased delivery

#### **Phase 1 — Data + Tier classification** ✅ (shipped 2026-04-25)
- yfinance market snapshot (VIX, VIX3M, indices, FX, BTC, gold, oil)
- VIX tier auto-classification with `holdings.json`-driven buy lists
- Holdings table with RSI, MA distances, 52-week-high distance
- Markdown report committed by the daily cron (initially GitHub Actions; moved to MIRA's launchd at `a1041ad`), rendered on Vercel

**Live at**: https://vixpulse.asia (rebranded 2026-04-26 from `stockpulse-indol.vercel.app`)

#### **Phase 2 — Decision support layer** ✅ (shipped 2026-04-26, four commits)

| # | What | Commit |
|---|---|---|
| 1 | Deterministic enrichment — `analyzers/flags.py` (17-flag closed vocab), `fetchers/earnings.py` (Finnhub, 24h cached), `reporters/json_emitter.py` (schema_version=1) | `caeeced` |
| 2 | Rendering + wiring — `markdown_gen.py` "📝 Today's Take" + "🚩 Watch List" sections, `generate_report.py` rewiring + `--no-synthesis` flag | `552c21d` |
| 3 | Synthesis layer — `claude_synthesis.py` single Anthropic call via `tool_use` (strict JSON contract), §2.4 SOFI/TSM rules in system prompt; display rebrand StockPulse → VIX Pulse + OG meta tags | `aacd6b4` + `e8436e1` |
| 4 | i18n dual output — `translator.py`, `web/public/reports/{en,zh}/<date>.{md,json}` paths, /zh routes, EN \| 中 toggle | `87c7a90` |

Polymarket integration was **deferred to Phase 2.5+** pending production data. Cross-account view (Exness + LEAPS positions) is partially in via `build_accounts_summary` but full sync waits on §6.7 MetaApi Track A.

#### **Phase 2.5 — Regime sensitivity + Universe Scanner** ✅ (shipped 2026-04-26, seven commits)

Adds a regime-conditional layer on top of single-axis VIX tier classification: each ticker in a 59-symbol Exness-tradable universe gets backtested over 5 years to compute `beta_normal`, `beta_stress`, `vix_spike_decay_pct`, `vix_spike_decay_p25_pct`, `vix_crush_recovery_pct`, then assigned to one of `high_normal` / `high_stress` / `crisis_alpha` / `mean_reverter` / `defensive` (or none). Holdings inherit their ticker's tags; the report surfaces a Universe Scanner section listing tier-appropriate Add / Watch / Avoid candidates from the full universe (not just current holdings).

| # | What | Commit |
|---|---|---|
| 5 | Regime sensitivity calc + holdings integration — `analyzers/regime_sensitivity.py`, weekly GH Actions cron (Sundays 03:00 UTC), `config/regime_sensitivity.json`, schema_version 1→2, Watch List `⋮ <tags>` divider | `30412f4` |
| 6 | Universe Scanner UI region — three sub-regions (🟢 Add / 🟡 Watch / 🔴 Avoid), top-5 each, overlap indicator | `454d716` |
| 6.5 | Empty-placeholder enriched with threshold gap (`_no candidates fire decay < -10% (worst today: -2.04%)_`) | `8110990` |
| 7 | Synthesis payload normalization — defense against tool_use shape drift; system prompt hardened with explicit shape contract; structured warning logs for drift tracking | `b0bf66f` |
| 8 | `vix_spike_decay_p25_pct` (25th-percentile post-spike 5d return) added; `crisis_alpha` switches to p25 methodology to capture asymmetric tail behavior | (Phase 2.5) |
| 10 | Threshold redefinition tuned to natural breaks in the 2021-2026 universe: `crisis_alpha p25 < -4%` (5/59 fire); `mean_reverter` becomes single-axis `crush_recovery > +0.6%` (9/59 fire) — "drops then snaps back" doesn't manifest in the data; top-recovery names rally OFF spikes | `1733907` |
| 10.5 | Universe Scanner readability pass — Sample column reads `normal_weeks` for 🟢 Add, framework legend under section heading, bilingual tier action in heading (`📡 Universe Scanner — Tier 2 (觀察)`) | `25d1103` |

#### **Phase 3.0 — Frontend redesign (Brief B)** ✅ (shipped 2026-04-26)

The "DEFERRED to June" instruction in the 2026-04-26 morning consolidated brief was overruled the same day. All four milestones plus hardening landed under bus task `2026-04-26T09-21-32`. See §11 for routing/layout/design-system detail.

| # | What | Commit |
|---|---|---|
| M1 | Next.js 15 + Tailwind v4 + shadcn primitives + design tokens + `/v2/*` (basic-auth gated) + Playwright smoke | `6e56ba8` |
| M2 | Hero / WatchList (severity-classified) / Holdings (table desktop + cards mobile) / SnapshotGrid / V2Footer | `ee91fa5` |
| M3 | VIX sparkline (recharts, lazy) + custom i18n (EN \| 中) + dynamic OG card | `85d37dd` |
| M4 cutover | `/v2/*` → `/`, Phase 1 → `/legacy/*`, basic-auth dropped | `1f2660b` |
| M4 hardening | Visual regression CI workflow + `/archive` redirects + doc updates | `d4aa387` |

#### **Phase 3.1 — TodaysTake / TierAction / UniverseScanner + `/learn` v2 chrome** ✅ (shipped 2026-04-27)

Three new Server Components landed between hero+sparkline and watch list, and `/learn` moved under the `(learn)` route group with the same Phase 3.0 chrome. First-Load JS unchanged (2.17 KB / 108 KB total — zero client JS added). 30 Playwright tests on `main` (was 19; +11 for Phase 3.1).

| # | What | Commit |
|---|---|---|
| 3.1 | `TodaysTake` (market read + devil's advocate + position calls) · `TierAction` (buy_list with held-ticker `(hold)` annotation) · `UniverseScanner` (Add / Watch / Avoid + cross-region overlap warnings) · `(learn)` route group with `[data-v2-root][data-area='learn']` chrome · `regime_universe` surfaced into JSON sidecar via additive `json_emitter` change | `d4a1e9a` |
| 3.2 | Tier-action label localization · double-edged tag clarification · hero synthesis read truncation fix · "VIX Pulse" wordmark spacing · tier-ladder logo · `/learn` UX redesign (visual tier ramp, numbered rule cards) · 30+ days of VIX history backfilled so the sparkline renders on first deploys | `2fb37f9` · `8d42dc8` · `c585a61` · `acdab4a` · `1ab49e4` · `64118c9` · `2099892` · `d22e7d7` |

#### **Privacy stripping (`--public` mode)** ✅ (shipped 2026-04-26, hardened 2026-04-27)

§5.2 was inverted on 2026-04-26 — see §6.8 below. `scripts/generate_report.py --public` empties `report.holdings`, `report.accounts`, and `report.synthesis.positions` before render. Markdown drops the Holdings + position-call sections; JSON sidecars expose `holdings: {}` and `synthesis.positions: []`. `scripts/run_daily.sh` passes `--public` to the daily cron; local invocations without the flag retain the full personal view.

| # | What | Commit |
|---|---|---|
| Privacy mode | `--public` flag in `generate_report.py` + `run_daily.sh`, markdown skips empty Holdings, v2 components return `null` rather than placeholder cards | `c2ad7a1` |
| zh sidecar fix | One-line — captured `synthesis` local was passed to `maybe_translate` before the strip propagated; reading off `report` after strip closes the leak | `f12fb89` |
| Legal pages | `/about` · `/privacy` · `/terms` + site-wide © + nav footer | `295721d` |

#### **Phase 3 follow-ups** 📅 (planned, no firm dates)

| Component | Status | Why it matters | Estimated effort |
|---|---|---|---|
| **Threshold tuning for `crisis_alpha` / `mean_reverter`** | Resolved in Commit 10 (5/59 + 9/59 fire counts; thresholds tuned to natural universe breaks) — revisit only if the 2021-2026 universe regime changes meaningfully | — | resolved |
| **Brief B — Frontend redesign** | ✅ Shipped 2026-04-26 across M1→M4 + hardening + Phase 3.1 | — | shipped |
| **Vercel↔GitHub auto-deploy integration** | Broken since 2026-04-26; webhook returns `incorrect_git_source_info`. Manual `vercel --prod` is the working path. ARIA + MIRA root-causing on the bus. | Cron pushes don't trigger builds; site goes stale unless someone manually deploys | <1 day once root-caused |
| **MIRA's launchd cron honoring `--public`** | Today's cron commit `c646f33` produced an unstripped sidecar despite `run_daily.sh` calling `--public`; root-cause delegated to MIRA. Script-side zh leak fixed in `f12fb89`. | Privacy regression on every cron run until fixed | <1 day |
| **Phase 4 — multi-user accounts** | Brief-writer scheduled for 2026-04-27. Sign-up + screenshot/API holdings + per-user watch list + per-user synthesis. | Scales the framework beyond Carina; reduces privacy-strip pressure | 6–8 weeks once brief lands |
| **Telegram bot push** | Not started | Morning summary + intraday alerts on tier transitions or watchworthy flag changes | 1-2 weeks |
| **Searchable archive UI** | Skeleton exists at `/legacy/archive` | Date-range filter + flag-filter + full-text search | 1 week |
| **Supabase archive** | Not started | Structured DB of all daily reports for backtesting + analytics. Markdown remains canonical artifact (per §6.4) | 1-2 weeks |
| **MetaApi Track A** (auto-sync Exness holdings) | Not started, plan in §6.7 | Replace manual `holdings.json` Exness edits with daily auto-sync via `metaapi-cloud-sdk`. ~$5/mo with auto-undeploy | 1 week |
| **MetaApi Track B** (interactive Exness queries) | Not started, plan in §6.7 | Claude Desktop MCP for "what's my Exness account looking like?" — read-only, order tools disabled | 3-5 days |

**Suggested ordering** (Carina to confirm):

1. **Now (2026-04-27)** — Restore Vercel↔GitHub auto-deploy and root-cause the cron not honoring `--public`. Both are P0 operational issues that must clear before any new feature work.
2. **Late April / Early May 2026** — Phase 4 brief lands today (2026-04-27); Carina reviews while traveling. No implementation while she's in the US (4/28–5/7).
3. **May 2026** — Carina back from US 5/8. First two weeks of real Phase 2 + 2.5 production data inform whether threshold tuning needs another pass. Phase 4 implementation kickoff once she's settled.
4. **June 2026** — Phase 4 milestones (auth + holdings ingestion + per-user state). ARIA-owned frontend, MIRA-owned backend.
5. **July 2026** — Telegram bot push (Phase 3.1 in original numbering — now bumped after multi-user). MIRA-suggested.
6. **August 2026** — Supabase archive + searchable archive UI. Both can land together since they share the data path.
7. **September 2026** — MetaApi Track A (live Exness sync, critical path).
8. **Q4 2026** — MetaApi Track B (interactive, nice-to-have).

These are estimates, not commitments. Phase 2 + 2.5 + 3.0 + 3.1 took two days of intensive ARIA + MIRA collaboration; the operational issues uncovered today (broken auto-deploy, cron not stripping) are reminders that integration surfaces will continue to surface their own surprises.

---

## 4. Architecture

### 4.1 Current shape (Phase 2 + 2.5, as of 2026-04-26)

```
MIRA's launchd cron (StartCalendarInterval: 22:00 Asia/Taipei = 10 AM EDT, 30 min post-NYSE-open)
        │
        └─▶ scripts/run_daily.sh
              │
              ├─ git pull --rebase --autostash
              ├─ source .env.local  (ANTHROPIC_API_KEY, FINNHUB_API_KEY, VERCEL_DEPLOY_HOOK)
              └─ python scripts/generate_report.py
                    │
                    ├─ fetchers/
                    │     ├─ market_data.py       (yfinance — VIX, indices, FX, holdings)
                    │     └─ earnings.py          (Finnhub per-symbol, 24h cached)
                    ├─ analyzers/
                    │     ├─ vix_tier.py          (6-tier classification)
                    │     ├─ technical.py         (RSI, MA, 52w high/low)
                    │     ├─ flags.py             (17-flag closed vocab, Phase 2)
                    │     └─ regime_sensitivity.py (5y backtest, 59-ticker universe, weekly cron — Phase 2.5)
                    ├─ reporters/
                    │     ├─ claude_synthesis.py  (Anthropic tool_use, strict JSON, normalized payload)
                    │     ├─ markdown_gen.py      (Today's Take + Watch List + Universe Scanner sections)
                    │     ├─ translator.py        (Anthropic → zh-TW, Phase 2 Commit 4)
                    │     └─ json_emitter.py      (sidecar contract, schema_version=2)
                    │
                    └─▶ web/public/reports/{en,zh}/{YYYY-MM-DD,latest}.{md,json}
                          │
                          ├─ git commit + push origin main
                          └─ curl POST $VERCEL_DEPLOY_HOOK → vixpulse.asia rebuilds in ~30s
```

**Weekly side-job** (separate GH Actions cron, Sundays 03:00 UTC): `python scripts/analyzers/regime_sensitivity.py` rebuilds `config/regime_sensitivity.json` (59 tickers × 5y weekly backtest); commits if changed.

**Manual fallback** for the daily cron: `gh workflow run daily-report.yml` from the GitHub UI — `daily-report.yml` keeps the workflow_dispatch trigger as a backup if MIRA's launchd is down.

### 4.3 Technology choices and *why*

| Choice | Why | Alternatives rejected and why |
|---|---|---|
| **Python for pipeline** | Carina's existing stack (SMC Pulse), best ecosystem for finance data | Node — weaker for pandas/yfinance |
| **Next.js + Vercel for viewer** | Free hosting, instant redeploy on git push, server-side rendering of Markdown | Pure static site — less flexible for future interactive features |
| **GitHub Actions for cron** | Free, reliable, version-controlled, no separate infra | Vercel Cron (paid), self-hosted (complexity) |
| **Markdown reports as artifacts** | Version-controlled, diffable, plain-text searchable, render anywhere | DB-only — harder to inspect, debug, share |
| **`config/holdings.json` as single source of truth** | Strategy edits don't require code changes; ARIA/MIRA can reason about it | Hardcoded constants — brittle |
| **`yfinance`** for Phase 1 | Free, no auth, sufficient quality for daily timeframe | Polygon/IEX — overkill for daily, requires keys |
| **`claude-sonnet-4-6` for synthesis** | Best price/intelligence ratio for narrative generation | GPT-4o — higher cost, weaker on long-context structured input |

### 4.4 Synthesis sidecar contract (`schema_version`)

The JSON sidecar at `web/public/reports/{en,zh}/<date>.json` is a versioned contract between the pipeline and any downstream consumer (the web viewer, future Telegram bot, third-party dashboards). The top-level `schema_version` integer governs compatibility.

- **`schema_version: 1`** — initial Phase 2 shape. Per-holding fields: `last`, `flags`, technicals, earnings.
- **`schema_version: 2`** — Phase 2.5 additive bump. Per-holding fields gain `regime_metrics` (`beta_normal`, `beta_stress`, `vix_spike_decay_pct`, `vix_crush_recovery_pct`, `confidence`), `sensitivity_tags` (list, possibly empty), and `missing_from_universe` (bool). Commit 8 (2026-04-26) adds `vix_spike_decay_p25_pct` inside `regime_metrics` — 25th-percentile of post-spike 5-day cumulative returns, basis for `crisis_alpha`. Commit 10 (2026-04-26) reshapes the tag rules against observed 2021-2026 data: `crisis_alpha` uses p25 < -4% (tuned to natural break in 5y universe distribution; worst p25 in the 59-ticker universe is INTC at -4.98%, so a -5% bar would have fired zero); `mean_reverter` drops the spike-decay conjunction and becomes single-axis (`vix_crush_recovery_pct > +0.6%`) — the "drops then snaps back" pattern doesn't manifest in our universe; top-recovery names rally OFF spikes (V-shape). Both thresholds are tuned to natural breaks rather than absolute targets; expect to revisit if the universe regime changes meaningfully (true crisis return, etc.). Existing v1 fields are unchanged; the v2 additive guarantee holds.

**Compatibility rule:** consumers MUST tolerate unknown fields gracefully. Adding a field is always permitted within a major version; renaming or removing one bumps the version. The `schema_version` is never decremented. When an old viewer reads a newer payload, it should ignore unknown keys; when a new viewer reads an older payload, it should treat the missing v2 fields as `None` / `[]` / `False` respectively.

### 4.5 Multi-agent execution (ARIA + MIRA via agent-bus)

- **ARIA** (Claude Code on MacBook Air) is the *architect*: receives requirements from Carina (often relayed from her conversations with Claude on claude.ai), decides architecture, decomposes work, delegates concrete tasks to MIRA via agent-bus. Persona: exploratory, proposes options first.
- **MIRA** (Claude Code on Mac Mini, always-on) is the *worker*: receives well-scoped tasks, implements, tests, reports back. Persona: precise, terse, asks before acting.
- **agent-bus** is the inter-agent communication layer at https://github.com/crotchblow-prog/agent-bus — a git-backed message queue with `msgs/` (inbox) and `processed/` (archive) directories. See that repo's README for the full operator's manual.

#### Key invariants ARIA and MIRA must respect

These come from agent-bus protocol rules:

1. **The bus is durable, agents are ephemeral.** Tasks live as files in git; agents can die and restart freely.
2. **Never edit a message you didn't author.** Reply by creating a new file.
3. **Always `git pull --rebase`** before reading the inbox; **always commit + push** after writing.
4. **Mark handled messages** with `git mv msgs/<file> processed/` to prevent re-processing.
5. **Address messages explicitly** (`to: aria` or `to: mira`, never assume).
6. **End threads cleanly** with `ack` or `stop` — no infinite ping-pong.
7. **Escalate disagreements after two rounds** to the user with `to: user, type: question`.
8. **A loop must already be running** for the agent to act. Delegating only puts a task in the inbox; if the recipient's loop is dead, the task piles up forever.

#### Fallback when peer is unreachable

If the agent-bus is offline (as happened on 2026-04-25 when the network was unreachable from one Mac), or if the peer's loop is dead:
- ARIA executes the full task herself rather than blocking
- Document fallback in commit messages with `ARIA solo` or `MIRA solo` tag
- This lets us track when fallback was used and review whether the peer should have been involved

#### Cross-repo commit conventions

When ARIA or MIRA acts on a task that originated in agent-bus, the commit on the *target* repo (e.g., StockPulse) should include the originating message ID:

```
feat: add Polymarket fetcher

[bus:2026-04-25T14-22-01]
```

This lets us trace any StockPulse commit back to the user task that triggered it.

#### Implication for delegation

When ARIA receives a request, she should consider:
1. Is this scoped concretely enough to delegate? If not, refine the spec first.
2. Is MIRA reachable? Check `STATUS.md` for recent timestamp; if stale, fall back to solo execution.
3. Does the task touch architectural decisions? If yes, ARIA owns it; only delegate the implementation.

---

## 5. Constraints

### 5.1 Budget

| Item | Limit |
|---|---|
| Anthropic API (Phase 2 synthesis) | $5–10 / month |
| MetaApi (Phase 3, auto-undeploy mode) | $5 / month |
| Other paid services | Avoid unless clearly justified |
| **Total monthly cost ceiling** | **$20** |

### 5.2 Operational

- **Scale**: single-user (Phase 4 in 2026-Q3 will introduce multi-user). No auth, multi-tenancy, or scale work beyond personal use until then.
- **Privacy**: deployed `vixpulse.asia/` is public but **does not expose Carina's holdings or position calls**. The cron runs `generate_report.py --public`, which empties holdings, accounts, and synthesis position calls before render — see §6.8 and the `--public` shipping notes in §3.2. Local pipeline runs without `--public` retain the full personal view for Carina.
- **Reliability target**: best-effort. A skipped daily report is annoying but not catastrophic.
- **Latency target**: report should be ready by 10:30 Asia/Taipei (i.e., within 30 min of cron trigger).

### 5.3 Code quality

- All Python functions should have docstrings explaining *purpose*, not just signature
- All API calls must have error handling — a single failed fetcher should *not* break the whole report
- All time handling uses `Asia/Taipei` timezone explicitly; no naive datetimes
- No secrets in code; use environment variables and document them in `.env.example`
- Use `logging`, not `print()`, for anything beyond top-level CLI output

---

## 6. Decisions Already Made (do not re-litigate without owner approval)

These are settled. Future contributors should not propose changes to these without explicit discussion with Carina.

### 6.1 No MetaApi MCP integration in StockPulse's daily report pipeline

The `metatrader-mcp-server` fork was evaluated and rejected for StockPulse's automated pipeline:
- StockPulse's cron job runs in GitHub Actions, not Claude Desktop — MCP protocol is unnecessary
- For Phase 3 live Exness sync, use the **MetaApi Python SDK directly** (`metaapi-cloud-sdk`)
- The MCP server *is* acceptable for **interactive** use cases (Claude Desktop chatting with the broker), tracked separately in §6.7

### 6.2 No auto-trading

StockPulse never sends orders. All MetaApi integrations (Phase 3 Track A and Track B in §6.7) are read-only. Carina executes all orders manually in the Exness app. This is a hard line and protects against:
- Bugs in the integration causing accidental trades
- Prompt injection attacks via market data (e.g., a malicious news headline that tries to trigger a sell)
- LLM hallucinations leading to unintended orders

Features that automate execution are out of scope and should be rejected.

### 6.3 No live LLM inference at request time

The Vercel site renders pre-generated Markdown. There is no "ask Claude a question" interactive feature on the site. All Claude synthesis happens in the cron job, output is static. This keeps cost predictable and the site fast.

### 6.4 Markdown is the canonical artifact

Even when Supabase is added in Phase 3, the Markdown file remains the source of truth. The DB is a *secondary* index for search/analytics, not a replacement.

### 6.5 Holdings live in `config/holdings.json`, edited manually (until Phase 3 §6.7 lands)

Phase 1 and 2 keep holdings hardcoded. When Carina opens/closes positions, she edits the JSON. Phase 3 introduces auto-sync for Exness only (§6.7 Track A); Taiwan brokerage and LEAPS remain manually edited indefinitely.

### 6.6 agent-bus stays git-backed

The agent-bus has been deliberately kept simple — git repo + slash commands + 60s polling. Tempting alternatives (Tailscale push, WebSocket, SDK-based daemon) are tracked as deferred work in the agent-bus repo, not adopted.

The boring-tech choice (git + GitHub) gives us audit trail, conflict resolution, persistence, multi-device sync, mobile access, and free hosting for free. Any proposal to replace this needs to demonstrably solve a pain that the current setup actually has — not a hypothetical scaling concern.

### 6.7 MetaApi integration plan (Phase 3+)

Carina wants to integrate Exness MT5 via MetaApi Cloud for two distinct use cases. Both are read-only.

#### Track A — Automated holdings sync for StockPulse (production critical path)

**Goal**: Replace manual maintenance of Exness positions in `holdings.json` with daily automated sync.

**Technical approach**:
- Use **MetaApi Python SDK** (`metaapi-cloud-sdk`), **not** MCP
- New file: `scripts/fetchers/exness_positions.py`
- Returns positions + account info from `connection.terminal_state`
- Merged into the holdings structure consumed by report generation
- Taiwan brokerage and LEAPS positions remain in `holdings.json` (manually edited)

**Auth**: read-only token (MetaApi "Investor" level), stored as `METAAPI_TOKEN` GitHub secret.

**Cost**: ~$5/month using `METAAPI_AUTO_UNDEPLOY=true` (account is undeployed between cron runs, so billing is per-run not per-month).

**Sequencing**: implement only after Phase 2 features are stable. Don't block Phase 2 on this.

#### Track B — Interactive Exness queries via Claude Desktop

**Goal**: Carina can ask Claude Desktop "what's my Exness account looking like?" and get live data.

**Technical approach**:
- Use **`metatrader-mcp-server`** (cross-platform fork at `crotchblow-prog/metatrader-mcp-server`, MetaApi-backed)
- Configured in Claude Desktop's `claude_desktop_config.json`
- Same MetaApi token as Track A (one MetaApi account, both use cases)
- **Order-execution tools (`place_market_order`, `close_position`, etc.) MUST be disabled** in the MCP config — only `get_*` tools enabled

**Sequencing**: after Track A is stable. Track B is quality-of-life, not production critical.

#### Why two separate tracks instead of one

- Track A runs in GitHub Actions, headless. MCP requires a host (Claude Desktop) — wrong tool for cron jobs.
- Track B is interactive. Python SDK doesn't help when Carina is on her phone asking Claude a question.
- They share the MetaApi account and credentials, but the integration code is independent.

#### Privacy reminder

Track A pulls live account balance and equity. Per §6.8, deployed `vixpulse.asia/` is stripped of all holdings via `--public` mode — Track A's output goes through the same strip path. The local (non-`--public`) view is what Carina actually consumes for personal decision support.

### 6.8 Privacy stripping reversed the original "public-readable" stance (2026-04-26)

§5.2 originally said the deployed site was public-readable with holdings amounts visible. Carina reversed that on 2026-04-26 — the deployed `vixpulse.asia/` should be framework + market data + Universe Scanner + `/learn` only, **not** holdings, watch list, position calls, or buy-list annotations.

This is now the steady state, not a phase. Implementation:
- `scripts/generate_report.py --public` strips `report.holdings`, `report.accounts`, and `report.synthesis.positions` before render. `markdown_gen` skips the Holdings section header when holdings is empty. v2 components (`Holdings.tsx`, `WatchList.tsx`) return `null` rather than placeholder cards so the public site simply doesn't have those sections.
- `scripts/run_daily.sh` passes `--public` so cron output is always stripped. Local invocations without the flag retain the full personal view.
- The legacy markdown render at `/legacy/` is also stripped (`markdown_gen` reads the same report dict).
- The `f12fb89` follow-up fixes a one-line bug in `generate_report.py:363` where the captured `synthesis` local was passed to `maybe_translate` before the strip propagated, leaking the zh sidecar even when EN was clean.

Personal-portfolio rendering is parked for Phase 4 (multi-user accounts) where each user can authenticate and see their own positions only.

---

## 7. Open Questions (not yet decided)

These need owner input before significant work happens:

1. **Phase 4 brief scope** — multi-user accounts dropping 2026-04-27. Who can sign up (waitlist? open?), holdings ingestion path (screenshot OCR vs broker API), and how per-user synthesis interacts with the shared market data.
2. **Polymarket scope** — which exact contracts to track? Still deferred from Phase 2; need a curated list, not all of them.
3. **Telegram bot UX** — push full report or summary + link? Time-zone-respecting quiet hours? Still queued.
4. **Backtesting** — at some point Carina will want to ask "did the tier system actually work?" — needs structured archival, hooks into the Supabase Phase 3 work.
5. **Heartbeat monitoring for agent-bus** — currently no automated detection of dead loops. MIRA prototyped a deploy-hook health check on 2026-04-27; same pattern (LaunchAgent + bus alert) could surface stale STATUS.md timestamps.
6. **STATUS.md write contention** — both agents write to the same file. So far no conflicts, but as cadence grows, may need to split into `STATUS-aria.md` + `STATUS-mira.md` and merge at render time.
7. **MetaApi Track A timing** — does it land before or after Phase 4 (multi-user)? Phase 4 may obsolete the auto-sync if users bring their own holdings via screenshot/API.

---

## 8. How to use this document

### For ARIA
- Read this fully when starting a new conversation/session
- Reference §2 (philosophy) when deciding what data matters
- Reference §4 (architecture) before proposing structural changes
- Reference §6 (settled decisions) before proposing things that may have been already considered
- Update this document when Carina makes a new strategic decision (and commit with `[brief]` prefix in the commit message)

### For MIRA
- You generally won't read this end-to-end. ARIA will hand you scoped tasks.
- If a task feels like it conflicts with §2 philosophy or §6 settled decisions, ask ARIA before proceeding.

### For Carina
- Edit this document directly when strategic direction changes
- Use §7 (open questions) as a running list of "things to think about"
- This is the document to send to a new collaborator (or a fresh Claude conversation) to bootstrap context

---

## 9. Related documents

- `README.md` — technical setup, deployment, repo layout
- `config/holdings.json` — current positions and tier strategy (the *operational* truth)
- `docs/` — (TBD) per-feature design docs as Phase 2 work begins
- [`crotchblow-prog/agent-bus`](https://github.com/crotchblow-prog/agent-bus) — multi-agent communication infrastructure (separate repo, full operator's manual in its README)
- [`crotchblow-prog/metatrader-mcp-server`](https://github.com/crotchblow-prog/metatrader-mcp-server) — MetaApi-backed MCP server for Track B (§6.7); cross-platform fork of `ariadng/metatrader-mcp-server`

---

## 11. Frontend architecture

Phase 3.0 (the frontend redesign) ships at `vixpulse.asia/` after the M4 cutover. Phase 1's markdown viewer is preserved at `/legacy/*` as an escape hatch.

### Routing table

| URL | Layout | Render |
|---|---|---|
| `/` | minimal root | redirect → `/en` |
| `/en`, `/zh` | `[lang]/layout.tsx` (Phase 3.0 chrome) | hero + sparkline + watch list + holdings + snapshot grid |
| `/en/<date>`, `/zh/<date>` | same | dated report |
| `/en/<date>/opengraph-image` | (Next.js OG convention) | dynamic 1200×630 typography card |
| `/learn`, `/zh/learn` | `(learn)/layout.tsx` (Phase 3.0 chrome with `data-area='learn'`) | bilingual VIX-101 explainer with `report-prose` markdown styling |
| `/legacy/`, `/legacy/zh/` | `legacy/layout.tsx` (Phase 1 chrome) | Phase 1 markdown viewer |
| `/legacy/archive`, `/legacy/zh/archive` | same | archive index |
| `/archive`, `/zh/archive`, `/archive/<date>`, `/zh/archive/<date>` | (308) | redirect to `/legacy/...` (next.config.ts) |

### Layout isolation

The root layout (`web/app/layout.tsx`) is intentionally minimal — html + body + font CSS variables only. Each area provides its own chrome:

- `[lang]/layout.tsx` wraps in `[data-v2-root]` with `--bg-base` (`#0a0a0b`), font-sans default, overflow-x-hidden.
- `legacy/layout.tsx` reproduces Phase 1's header (SiteNav with brand + "(legacy)" suffix) + Phase 1 footer.
- `(learn)/layout.tsx` (URL-invisible route group, Phase 3.1) gives `/learn` and `/zh/learn` the Phase 3.0 chrome with `data-area='learn'` and a `report-prose` cascade so existing markdown styles compose with Inter / JetBrains Mono.

This isolation keeps Phase 3.0's design tokens scoped to `[data-v2-root]` so any future routes (e.g. an admin page) start from a clean slate.

### Design system

Tokens live in `web/app/globals.css` under Tailwind v4's `@theme` block. The tier color ramp (cobalt / cyan / gray / amber / orange-red / alert red) is referenced by `--color-tier-N` and surfaces by `--color-bg-base / -surface / -elevated`. `--tier-current` is set per-element via the `[data-tier="N"]` attribute on parent containers, picked up by descendant CSS via `var(--tier-current)`.

Typography: Inter for prose, JetBrains Mono for numerics (both via `next/font`, self-hosted). All numeric columns use `tabular-nums` for digit-glyph alignment.

shadcn primitives (Button / Card / Badge / Separator) live in `web/components/ui/` — added manually rather than via shadcn-CLI because Tailwind v4's CSS-first config conflicts with the CLI's `tailwind.config.ts`-writing init flow.

### Phase 3.0 milestones

Brief B was delivered across four atomic milestones, each landing as one commit per ARIA's discipline:

| # | What | Commit |
|---|---|---|
| M1 | Foundation — Next.js 15 + Tailwind v4 + shadcn primitives + design tokens + `/v2/*` routes (gated behind basic-auth) + Playwright smoke | `6e56ba8` |
| M2 | Core redesign — Hero / WatchList (severity-classified) / Holdings (desktop table + mobile cards) / SnapshotGrid / V2Footer | `ee91fa5` |
| M3 | VIX sparkline (recharts, lazy-loaded) + custom i18n (en/zh dictionary + EN \| 中 toggle) + dynamic OG card | `85d37dd` |
| M4 cutover | `/v2/*` → `/`, Phase 1 → `/legacy/*`, basic-auth middleware dropped | `1f2660b` |
| M4 hardening | Visual regression CI workflow + `/archive` redirects + this brief section | `d4aa387` |
| Phase 3.1 | TodaysTake + TierAction + UniverseScanner + `(learn)` route group with v2 chrome | `d4a1e9a` |

---

## 10. Commit message conventions

Different prefixes signal different intent for grep / log review:

| Prefix | Meaning | Example |
|---|---|---|
| `[brief]` | Strategic / direction change in this document | `[brief] add Polymarket to Phase 2 priority list` |
| `[bus:<msg-id>]` | Implementation triggered by an agent-bus message | `feat: add earnings fetcher [bus:2026-04-26T09-15-00]` |
| `ARIA solo` / `MIRA solo` | Fallback execution because peer was unreachable | `feat: ship vix_tier.py (ARIA solo, bus offline)` |
| (none) | Routine work | `fix: handle yfinance timeout gracefully` |

---

*This brief is intentionally opinionated. Disagreement is welcome — raise it with the owner rather than working around it.*
