#!/usr/bin/env bash
# Daily health check for the Vercel deploy hook used by run_daily.sh.
#
# 200  → silent exit
# any other → drop a message into ~/agent-bus/msgs/ so MIRA + ARIA + the user
#             see it on next pull, and exit non-zero so launchd records failure
#
# The hook itself does NOT redeploy when called by this script — Vercel
# deploys the latest commit on `main`. If main is unchanged from the last
# successful deploy, Vercel returns 200 and no-ops. Safe to ping daily.

set -uo pipefail

REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"}"
BUS="${BUS:-$HOME/agent-bus}"

if [[ -f "$REPO/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO/.env.local"
  set +a
fi

if [[ -z "${VERCEL_DEPLOY_HOOK:-}" ]]; then
  echo "ERROR: VERCEL_DEPLOY_HOOK not set in $REPO/.env.local" >&2
  exit 2
fi

TS_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TS_FILE="$(date -u +%Y-%m-%dT%H-%M-%S)"
TMP_BODY="$(mktemp -t deploy-hook-body)"
trap 'rm -f "$TMP_BODY"' EXIT

HTTP_CODE="$(curl -s -o "$TMP_BODY" -w "%{http_code}" -X POST "$VERCEL_DEPLOY_HOOK" || echo "000")"

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
  echo "[$TS_UTC] deploy hook OK ($HTTP_CODE)"
  exit 0
fi

# Non-OK — alert via the agent bus so it shows up on both Macs.
BODY="$(tr -d '\r' < "$TMP_BODY" | head -c 2000)"
MSG="$BUS/msgs/${TS_FILE}-mira-to-user.md"

mkdir -p "$BUS/msgs"
cat > "$MSG" <<EOF
---
id: ${TS_FILE}
from: mira
to: user
type: question
subject: Vercel deploy hook returning HTTP ${HTTP_CODE} — integration still broken
---

# Daily deploy-hook health check failed

Pinged \`VERCEL_DEPLOY_HOOK\` at ${TS_UTC} → HTTP **${HTTP_CODE}**.

Response body:

\`\`\`
${BODY}
\`\`\`

If the body still says \`incorrect_git_source_info\`, the Vercel↔GitHub
integration that broke on 2026-04-27 has not been fixed yet. Background +
diagnosis: \`~/agent-bus/msgs/2026-04-27T14-46-10-mira-to-aria.md\`.

Until this is fixed, tomorrow's report cron will push to GitHub but the
site won't update — you'll need a manual \`npx vercel deploy --prod\` from
the repo root.

— MIRA (deploy-hook health check)
EOF

if [[ -d "$BUS/.git" ]]; then
  (
    cd "$BUS" && \
    git pull --rebase --quiet && \
    git add "msgs/${TS_FILE}-mira-to-user.md" && \
    git -c user.name="MIRA" -c user.email="blowcrotch@Blows-Mac-mini.local" \
        commit -q -m "msg: mira→user — deploy hook ${HTTP_CODE}" && \
    git push --quiet
  ) || echo "WARN: bus push failed; message left at $MSG" >&2
fi

# Also surface a desktop notification on the Mac Mini if it's awake.
osascript -e "display notification \"deploy hook returned ${HTTP_CODE}\" with title \"vixpulse.asia health check\"" 2>/dev/null || true

echo "[$TS_UTC] deploy hook FAIL ($HTTP_CODE) — bus message written" >&2
exit 1
