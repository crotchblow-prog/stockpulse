#!/bin/bash
# Daily StockPulse pipeline runner — owned by MIRA's launchd cron.
#
# Sources .env.local (ANTHROPIC_API_KEY, FINNHUB_API_KEY, optional
# VERCEL_DEPLOY_HOOK), pulls, regenerates the report, commits + pushes if
# anything changed, and optionally pings a Vercel deploy hook.
#
# All output is appended to ~/.local/state/stockpulse/daily-<UTC-date>.log.
# Designed to be idempotent: rerunning the same day overwrites the dated
# report files but the commit step is a no-op if the diff is empty.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${HOME}/.local/state/stockpulse"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily-$(date -u +%Y-%m-%d).log"

cd "$REPO_DIR"

{
  echo "=== run started $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

  if [[ -f .env.local ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env.local
    set +a
  fi

  git pull --rebase --autostash

  if [[ ! -x ./.venv/bin/python ]]; then
    echo "ERROR: ./.venv/bin/python not found or not executable" >&2
    exit 1
  fi

  ./.venv/bin/python scripts/generate_report.py

  if [[ -n "$(git status --porcelain web/public/reports/)" ]]; then
    git add web/public/reports/
    git commit -m "report: $(date -u +%Y-%m-%d) — auto [mira-cron]"
    git push origin main
    echo "pushed $(git rev-parse --short HEAD)"
  else
    echo "no changes — nothing to commit"
  fi

  if [[ -n "${VERCEL_DEPLOY_HOOK:-}" ]]; then
    if curl -fsS -X POST "$VERCEL_DEPLOY_HOOK" > /dev/null; then
      echo "vercel deploy hook triggered"
    else
      echo "WARN: vercel deploy hook failed" >&2
    fi
  fi

  echo "=== run done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} >> "$LOG_FILE" 2>&1
