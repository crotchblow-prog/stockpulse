# M4 Cutover — `/v2` → `/`

Phase 3.0 frontend redesign cutover. Swaps the basic-auth-gated `/v2/*`
routes to live at `/` and demotes the Phase 1 markdown render to
`/legacy/*` as an escape hatch.

**Snapshot reference**: this commit is `[FILLED IN POST-PUSH]`. Roll back via
`vercel promote <previous-deployment-url>` if anything regresses on
production for >30 minutes.

## End state

| URL | Pre-cutover | Post-cutover |
|---|---|---|
| `/` | Phase 1 markdown English | redirect to `/en` |
| `/en` | (404) | Phase 3.0 English report |
| `/en/<date>` | (404) | Phase 3.0 dated English report |
| `/zh` | Phase 1 markdown Chinese | Phase 3.0 Chinese report (via `[lang]`) |
| `/zh/<date>` | (404) | Phase 3.0 dated Chinese report |
| `/v2/*` | Phase 3.0 (basic-auth gated) | (gone — middleware removed) |
| `/learn` | Phase 1 explainer English | unchanged |
| `/zh/learn` | Phase 1 explainer Chinese | unchanged |
| `/archive` | Phase 1 archive index | (302 → `/legacy/archive`) |
| `/legacy/` | (404) | Phase 1 markdown English (escape hatch) |
| `/legacy/zh/` | (404) | Phase 1 markdown Chinese |
| `/legacy/archive` | (404) | Phase 1 archive index |
| `/legacy/zh/archive` | (404) | Phase 1 Chinese archive |

## Sequence

1. [x] Plan written here. This commit's body documents which boxes were
       ticked.
2. [x] Snapshot: previous production deploy is the previous commit's
       Vercel deploy. `git log --oneline -1` before push captures it. If
       rollback needed, `vercel promote <previous-deployment-url>`.
3. [x] Move Phase 1 → `/legacy/*`:
       - `web/app/page.tsx` (OLD root) → `web/app/legacy/page.tsx`
       - `web/app/archive/` → `web/app/legacy/archive/`
       - `web/app/zh/page.tsx` → `web/app/legacy/zh/page.tsx`
       - `web/app/zh/archive/` → `web/app/legacy/zh/archive/`
       - Add `web/app/legacy/layout.tsx` (extracted from old root chrome).
4. [x] Move v2 → `/`:
       - `web/app/v2/page.tsx` → `web/app/page.tsx` (top-level redirect)
       - `web/app/v2/[lang]/` → `web/app/[lang]/`
       - `web/app/v2/layout.tsx` → `web/app/[lang]/layout.tsx`
       - `web/app/v2/_tokens/` → dropped (dev-only, served its purpose).
5. [x] Add `(default)` route group for `/learn` + `/zh/learn` so they
       keep a minimal header — without this, root layout strips chrome
       and the explainer pages render bare.
       - `web/app/learn/page.tsx` → `web/app/(default)/learn/page.tsx`
       - `web/app/zh/learn/page.tsx` → `web/app/(default)/zh/learn/page.tsx`
       - `web/app/(default)/layout.tsx` (minimal Phase 1 chrome).
6. [x] Strip root layout (`web/app/layout.tsx`) chrome. Root becomes
       html + body + font variables only. Each area (`(default)`,
       `[lang]`, `legacy`) provides its own chrome.
7. [x] Drop basic-auth middleware. `/v2/*` no longer exists; `/legacy/*`
       is intentionally public (the brief explicitly calls it out as an
       escape hatch).
8. [x] Update `web/lib/reports.ts` — paths unchanged (it reads from
       `web/public/reports/<lang>/`, route-agnostic).
9. [x] `npm run build` clean. New route table verified.
10. [x] `npx playwright test` passes — paths updated from `/v2/en` →
        `/en`, `/v2/zh` → `/zh`. Same 12 assertions, plus a new check
        that `/legacy/` returns the Phase 1 markdown view.
11. [x] Local smoke against `npm run dev`: `/`, `/en`, `/zh`, `/legacy/`,
        `/legacy/zh/`, `/learn`, `/zh/learn`, `/archive` (302),
        `/legacy/archive` all verified.
12. [x] Push. Vercel deploy auto-fires. M4-hardening (visual regression
        suite + CI + lighthouse + polish + docs) lands in a follow-up
        M4.5 commit per the staged-cutover discipline — see ack.

## Rollback

If `vixpulse.asia/` regresses for >30 min on production:

```bash
vercel ls                           # find the previous deployment URL
vercel promote <previous-deploy>    # promote that as production
```

Until the underlying issue is fixed. The commit can stay on `main` — the
rollback is at the deploy layer, not the git layer. Re-deploy via push
once the fix is verified locally.
