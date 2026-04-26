# StockPulse — Daily VIX-Tier US Market Analysis (Live as VIXPulse)

A daily decision-support report for a single-user US-equity portfolio, driven by VIX-tier classification + Anthropic synthesis + regime-sensitivity backtesting. Runs automatically on a Mac Mini's launchd cron at 22:00 Asia/Taipei (10 AM EDT, 30 min post-NYSE-open), commits the Markdown + JSON sidecar to git, and pushes via Vercel deploy hook.

**Live**: <https://vixpulse.asia> · EN at `/`, 中文 at `/zh`

> The canonical strategic context lives in [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md) — read that first if you're trying to understand WHY this project exists. This README covers WHAT was built and HOW to run it.

## What's implemented (as of 2026-04-26)

### Phase 1 — Data + Tier classification ✅ (shipped 2026-04-25)
- yfinance market snapshot (VIX, VIX3M, indices, FX, BTC, gold, oil)
- VIX 6-tier auto-classification driven by `config/holdings.json`
- Holdings table with RSI, MA distances, 52-week range
- Markdown report committed to git, served by a Next.js viewer on Vercel

### Phase 2 — Decision support layer ✅ (shipped 2026-04-26)
Four sequential commits delivered the synthesis layer:
1. **Deterministic enrichment** — 17-flag closed vocabulary (`flags.py`), Finnhub earnings calendar (24h cached, per-symbol fetch), JSON sidecar contract (`schema_version: 1`).
2. **Rendering + wiring** — Today's Take + Watch List markdown sections, `--no-synthesis` CLI flag for offline iteration.
3. **Synthesis layer** — Single Anthropic call per report (`claude-sonnet-4-6`, `tool_use` for strict JSON), §2.4 SOFI/TSM special-case rules in the system prompt. Display rebrand StockPulse → VIXPulse on `vixpulse.asia` + OpenGraph meta.
4. **i18n dual output** — English canonical + zh-TW translation via separate Anthropic call. Reports land at `web/public/reports/{en,zh}/<date>.{md,json}`. Site has `/` (EN) + `/zh` routes with EN | 中 toggle.

### Phase 2.5 — Regime sensitivity + Universe Scanner ✅ (shipped 2026-04-26)
1. **Commit 5** — `regime_sensitivity.py` 5-year weekly backtest over a 59-ticker Exness-tradable universe. Computes `beta_normal`, `beta_stress`, `vix_spike_decay_pct`, `vix_crush_recovery_pct`. Assigns `high_normal` / `high_stress` / `crisis_alpha` / `mean_reverter` / `defensive` tags. Schema bumped to `schema_version: 2`. Weekly GH Actions cron (Sundays 03:00 UTC).
2. **Commit 6** — Universe Scanner UI region with three sub-regions (🟢 Add / 🟡 Watch / 🔴 Avoid), top-5 by relevant metric, overlap indicator (`⚠️ also in Avoid`).
3. **Commit 6.5** — Empty-placeholder enriched with threshold-gap text (`_no candidates fire decay < -10% (worst today: -2.04%)_`) so the threshold-tuning conversation is grounded in data.
4. **Commit 7** — Synthesis payload normalization: defense against `tool_use` shape drift (Anthropic's input_schema is a guide, not a server-side validator). System prompt hardened with explicit shape contract.

161 tests pass. Daily run cost: ~$0.08 bilingual (~$2.40/month, well under the $5–10 cap in [`PROJECT_BRIEF`](./PROJECT_BRIEF.md) §5.1).

## What's left

| Area | Status | When |
|---|---|---|
| Threshold tuning for `crisis_alpha` / `mean_reverter` | Open Carina-decision (both tags fired zero across 5y data, thresholds too strict) | After 1-2 weeks of production data — May 2026 |
| Brief B — Frontend redesign (Next.js 15 + Tailwind + shadcn/ui + recharts + Playwright) | Brief locked, **DEFERRED to June** | June 2026, ~4 weeks |
| Telegram bot push (Phase 3) | Not started | July 2026 |
| Searchable archive UI + Supabase archive (Phase 3) | Skeleton at `/archive`; Supabase not wired | August 2026 |
| MetaApi Track A — auto-sync Exness holdings (Phase 3) | Not started; plan in [`PROJECT_BRIEF`](./PROJECT_BRIEF.md) §6.7 | September 2026 |
| MetaApi Track B — interactive Exness via Claude Desktop MCP (Phase 3) | Not started; plan in §6.7 | Q4 2026 |

These are estimates, not commitments. Owner-confirm before any of these become firm.

## Architecture

```
MIRA's launchd cron (22:00 Asia/Taipei = 10 AM EDT, 30 min post-NYSE-open)
        │
        └─▶ scripts/run_daily.sh
              │
              ├─ git pull --rebase --autostash
              ├─ source .env.local  (ANTHROPIC_API_KEY, FINNHUB_API_KEY, VERCEL_DEPLOY_HOOK)
              └─ python scripts/generate_report.py
                    │
                    ├─ fetchers/
                    │     ├─ market_data.py        (yfinance — VIX, indices, FX, holdings)
                    │     └─ earnings.py           (Finnhub per-symbol, 24h cached, graceful degrade)
                    ├─ analyzers/
                    │     ├─ vix_tier.py           (6-tier classification)
                    │     ├─ technical.py          (RSI, MA, 52w high/low)
                    │     ├─ flags.py              (17-flag closed vocab — Phase 2)
                    │     └─ regime_sensitivity.py (5y backtest, 59-ticker universe — Phase 2.5)
                    ├─ reporters/
                    │     ├─ claude_synthesis.py   (Anthropic tool_use → normalized payload)
                    │     ├─ translator.py         (Anthropic → zh-TW, separate call)
                    │     ├─ markdown_gen.py       (Today's Take + Watch List + Universe Scanner)
                    │     └─ json_emitter.py       (sidecar contract, schema_version=2)
                    │
                    └─▶ web/public/reports/{en,zh}/{YYYY-MM-DD,latest}.{md,json}
                          │
                          ├─ git add + commit + push origin main
                          └─ curl POST $VERCEL_DEPLOY_HOOK → vixpulse.asia rebuilds (~30s)
```

**Side-job**: `regime_sensitivity.py` reruns weekly via separate GitHub Actions cron (Sundays 03:00 UTC) and commits an updated `config/regime_sensitivity.json`.

**Fallback**: `gh workflow run daily-report.yml` triggers the same pipeline from GitHub Actions if MIRA's launchd is down.

## Repo layout

```
StockPulse/
├── PROJECT_BRIEF.md                      # canonical strategic context — read first
├── config/
│   ├── holdings.json                     # holdings + tier strategy (single source of truth)
│   └── regime_sensitivity.json           # 5y backtest output (regenerated weekly, committed)
├── scripts/                              # Python pipeline
│   ├── generate_report.py                # orchestrator
│   ├── run_daily.sh                      # MIRA's launchd wrapper
│   ├── com.stockpulse.daily.plist.template  # launchd plist template
│   ├── fetchers/    analyzers/    reporters/
│   ├── tests/                            # 161 tests as of 2026-04-26
│   └── requirements.txt
├── web/                                  # Next.js 15 viewer (App Router)
│   ├── app/
│   │   ├── page.tsx                      # /  → en/latest.md
│   │   ├── archive/                      # /archive + /archive/[date]
│   │   └── zh/                           # /zh, /zh/archive, /zh/archive/[date]
│   ├── lib/reports.ts                    # Lang-aware report reader
│   └── public/reports/{en,zh}/           # markdown + JSON committed by the cron
├── .github/workflows/
│   ├── daily-report.yml                  # workflow_dispatch fallback (schedule disabled)
│   └── regime_sensitivity.yml            # weekly Sundays 03:00 UTC
├── .env.example
└── README.md
```

## Local development

### Backend (Python)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt

# Generate today's report (requires .env.local with ANTHROPIC_API_KEY)
python scripts/generate_report.py

# Useful flags
python scripts/generate_report.py --dry-run         # logs what it'd write, no disk
python scripts/generate_report.py --no-synthesis    # skip Anthropic call (also implies --en-only)
python scripts/generate_report.py --en-only         # ship EN, skip zh translation
python scripts/generate_report.py --date 2026-04-26 # backfill specific date

# Rerun the regime sensitivity backtest (heavy: 5y × 59 tickers via yfinance)
python scripts/analyzers/regime_sensitivity.py

# Tests
pytest scripts/tests/ -q
```

### Frontend (Next.js 15)

```bash
cd web
npm install
npm run dev    # http://localhost:3000
npm run build  # static + dynamic routes
```

The viewer reads `web/public/reports/<lang>/latest.md` at request time. EN is the default; `/zh` switches.

## Secrets

All live in `.env.local` (gitignored). The MIRA-local cron sources this file via `scripts/run_daily.sh`.

| Secret | Phase | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | 2 | Claude synthesis + zh translation |
| `FINNHUB_API_KEY` | 2 | Earnings calendar (free tier — degrades to no countdown if missing) |
| `VERCEL_DEPLOY_HOOK` | 2 | Triggers Vercel production rebuild after each cron commit |
| `TELEGRAM_BOT_TOKEN` + `_CHAT_ID` | 3 | Push notifications (not yet wired) |
| `SUPABASE_URL` + `_SERVICE_KEY` | 3 | Backtest archive (not yet wired) |
| `METAAPI_TOKEN` | 3 | Live Exness sync (not yet wired) — see [`PROJECT_BRIEF`](./PROJECT_BRIEF.md) §6.7 |

## Deploying

The site lives on Vercel at `vixpulse.asia`. Deployments happen two ways:

1. **Daily cron-triggered** — `scripts/run_daily.sh` POSTs to `$VERCEL_DEPLOY_HOOK` after each successful `git push`. Vercel rebuilds in ~30s.
2. **Manual** — `cd web && vercel --prod --yes` from any FDA-granted Terminal session.

The Vercel project is configured with **Root Directory = `web`** (set via REST API on 2026-04-26). Don't change this — without it, builds fail looking for `pages/` or `app/` at the repo root.

## VIX Tier system

Six tiers, each with `vix_range`, `action`, `cash_target_pct`, `buy_list`. Defined in `config/holdings.json` under `tier_strategy`. Edit JSON to retune — no code changes.

| Tier | VIX | Action | Cash | Buy size |
|---|---|---|---|---|
| 0 | <15 | 休兵 | 70% | 0% |
| 1 | 15–18 | 警戒佈局 | 60% | 2-5% |
| 2 | 18–24.6 | 觀察 | 50% | 3-5% |
| 3 | 24.6–29.5 | 分批進場 ⭐ | 35% | 5-10% |
| 4 | 29.5–35 | 恐慌承接 ⭐⭐ | 20% | 10-20% |
| 5 | >35 | 極端機會 ⭐⭐⭐ | 20% | 重押但不 all in |

Full philosophy in [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md) §2.

## Regime sensitivity universe (59 tickers)

The 59-ticker universe used by Phase 2.5's `regime_sensitivity.py` backtest. **Authoritative source**: `scripts/analyzers/regime_sensitivity.py:UNIVERSE`. Chinese ADRs are explicitly excluded (VIX-correlation too weak); TSM is included despite being a Taiwan ADR because its trading behavior mirrors US large-cap semis.

This is the candidate pool for the 📡 Universe Scanner section in each daily report — *not* the holdings list. Current holdings live in `config/holdings.json:current_holdings`.

| Sector | # | Tickers |
|---|---:|---|
| **Information Technology** | 13 | AAPL · ADBE · ADP · AMD · AVGO · CSCO · FTNT · IBM · INTC · INTU · MSFT · NVDA · TSM |
| **Health Care** | 13 | ABBV · ABT · AMGN · BIIB · BMY · CVS · GILD · ISRG · JNJ · MRK · TMO · UNH · VRTX |
| **Communication Services** | 9 | CHTR · CMCSA · EA · GOOGL · META · NFLX · T · TMUS · VZ |
| **Consumer Discretionary** | 7 | AMZN · EBAY · F · HD · NKE · SBUX · TSLA |
| **Financials** | 7 | BAC · C · CME · JPM · MS · V · WFC |
| **Consumer Staples** | 3 | COST · KO · WMT |
| **Industrials** | 3 | BA · CSX · UPS |
| **Real Estate** | 2 | AMT · EQIX |
| **Energy** | 1 | XOM |
| **Materials** | 1 | LIN |

**Excluded** (Chinese ADRs, sensitivity calc skipped per [`PROJECT_BRIEF`](./PROJECT_BRIEF.md) §3.2 Phase 2.5 decision): BABA, BIDU, JD, NIO, XPEV, LI, BEKE, FUTU, EDU, TAL, VIPS, YUMC, ZTO, BILI, NTES, TME.

To add or remove a ticker, edit `scripts/analyzers/regime_sensitivity.py:UNIVERSE`, rerun `python scripts/analyzers/regime_sensitivity.py` to refresh `config/regime_sensitivity.json`, and commit both files. The weekly cron also keeps the JSON fresh on its own (Sundays 03:00 UTC).

## Multi-agent ownership

Built collaboratively by two Claude Code instances coordinated via the [agent-bus](https://github.com/crotchblow-prog/agent-bus) (a git-backed message queue):

- **ARIA** (Mac Air, interactive) — architect; owns frontend/UX, prompt design, brief decomposition.
- **MIRA** (Mac Mini, always-on) — worker; owns headless Python, scheduled cron, backtest computation.

Each commit message tagged `[bus:<msg-id>]` traces back to the originating bus task. Phase 2 + 2.5 (8 commits) shipped in one day with this split.

See [`PROJECT_BRIEF`](./PROJECT_BRIEF.md) §4.5 for the full multi-agent invariants.

## License

Personal use. Not for redistribution. Output is a decision-support tool, **not investment advice** — see footer of every report.
