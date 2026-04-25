# StockPulse — Daily US Market Analysis

Automated, VIX-tier-driven daily report for a personal US-equity portfolio. Runs every weekday at 10:00 Asia/Taipei via GitHub Actions, commits a Markdown report, and Vercel auto-redeploys the static site.

> Phase 1 (this repo) = data + tier classification + Markdown report + Next.js viewer.
> Phase 2 = RSI/MA technicals, earnings, Polymarket, Claude synthesis.
> Phase 3 = Telegram push, history page, Supabase archive.

## Architecture

```
GitHub Actions (cron 02:00 UTC = 10:00 Taipei)
        │
        └─▶ python scripts/generate_report.py
                    │
                    ├─ fetchers/    ← yfinance + (later) news/Polymarket
                    ├─ analyzers/   ← VIX tier + technicals
                    └─ reporters/   ← writes web/public/reports/{YYYY-MM-DD,latest}.md
                                          │
                                          └─▶ git commit + push → Vercel redeploy
```

## Repo layout

```
StockPulse/
├── config/holdings.json              # holdings + tier strategy (single source of truth)
├── scripts/                          # Python pipeline (owned by MIRA)
│   ├── generate_report.py
│   ├── fetchers/   analyzers/   reporters/
│   └── requirements.txt
├── web/                              # Next.js 14 App Router viewer
│   ├── app/page.tsx                  # latest report
│   ├── app/archive/                  # history list + per-date page
│   └── public/reports/               # *.md committed by the cron job
├── .github/workflows/daily-report.yml
├── .env.example
└── README.md
```

## Local development

### Backend

```bash
cd scripts
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python generate_report.py            # writes web/public/reports/latest.md
python generate_report.py --dry-run  # logs what it *would* write
```

### Frontend

```bash
cd web
pnpm install     # or npm/yarn
pnpm dev         # http://localhost:3000
```

The viewer reads `web/public/reports/latest.md` at request time. A placeholder is committed so the site renders before the first cron run.

## Deploying

1. **Create a GitHub repo** and push this directory.
2. **Vercel:** Import the repo. When asked for the project root, choose `web/`. Framework auto-detects as Next.js. No env vars needed for Phase 1.
3. **GitHub Actions:** No setup beyond pushing — the workflow runs on cron and uses `GITHUB_TOKEN` to commit reports back. To trigger manually: Actions tab → "Daily Market Report" → "Run workflow".

### Secrets (when needed)

| Secret | Phase | Where |
|---|---|---|
| `ANTHROPIC_API_KEY` | 2 | GitHub repo Secrets |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | 3 | GitHub repo Secrets |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | 3 | GitHub repo Secrets |

Phase 1 runs with **no secrets** — yfinance is public.

## Expected output

Each run produces a `web/public/reports/YYYY-MM-DD.md` like:

```markdown
# 📊 Daily Market — 2026-04-25

**VIX:** 17.2 → **Tier 1** 警戒佈局 · cash target 60% · buy size 2–5%

## Snapshot
| Asset | Last | Change |
|---|---|---|
| ^VIX | 17.2 | +0.4 |
| S&P 500 | 5,712 | -0.3% |
| ...

## Holdings
| Ticker | Last | vs avg cost | RSI(14) | 50DMA |
| TSM | 372.1 | +1.2% | 58 | +3.4% |
| ...
```

The Next.js viewer renders this with `react-markdown`.

## VIX Tier system

Defined in `config/holdings.json` under `tier_strategy`. Six tiers, each with `vix_range`, `action`, `cash_target_pct`, and a context-specific `buy_list`. Edit that JSON to retune — no code changes needed.

| Tier | VIX | Action |
|---|---|---|
| 0 | <15 | 休兵 |
| 1 | 15–18 | 警戒佈局 |
| 2 | 18–24.6 | 觀察 |
| 3 | 24.6–29.5 | 分批進場 ⭐ |
| 4 | 29.5–35 | 恐慌承接 ⭐⭐ |
| 5 | >35 | 極端機會 ⭐⭐⭐ |

## Status

- [x] Repo skeleton, config, workflow, web viewer (ARIA — 2026-04-25)
- [ ] Python pipeline: fetchers + analyzers + markdown_gen (MIRA — in progress)
- [ ] First green cron run
- [ ] Phase 2 features
