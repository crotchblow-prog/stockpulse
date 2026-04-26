import { promises as fs } from "node:fs";
import path from "node:path";
import type { Lang } from "./reports";

const REPORTS_DIR = path.join(process.cwd(), "public", "reports");
const BACKFILL_PATH = path.join(process.cwd(), "public", "vix-history.json");

export type VixPoint = { date: string; vix: number };

type BackfillFile = { points?: VixPoint[] };

/**
 * Sparkline data source. Two layers, newer wins per date:
 *
 * 1. `public/vix-history.json` (committed, populated by `scripts/backfill_vix_history.py`)
 *    — bootstraps history before the daily cron has accumulated 30 dated reports.
 *
 * 2. Dated JSON sidecars (`public/reports/<lang>/<YYYY-MM-DD>.json`'s `vix_value`)
 *    — accumulated by the daily cron. Each new day's sidecar overlays the backfill
 *    for that date.
 *
 * Returns the last N points sorted oldest → newest. en is the canonical history
 * source for VIX (the zh sidecars duplicate the same numeric `vix_value`).
 */
export async function loadVixHistory(n = 30, lang: Lang = "en"): Promise<VixPoint[]> {
  const byDate = new Map<string, number>();

  // Layer 1: backfill file
  try {
    const raw = await fs.readFile(BACKFILL_PATH, "utf8");
    const parsed = JSON.parse(raw) as BackfillFile;
    for (const p of parsed.points ?? []) {
      if (typeof p.vix === "number" && Number.isFinite(p.vix) && /^\d{4}-\d{2}-\d{2}$/.test(p.date)) {
        byDate.set(p.date, p.vix);
      }
    }
  } catch {
    // backfill file missing — proceed with whatever dated reports exist
  }

  // Layer 2: dated report sidecars (newer wins)
  const langDir = path.join(REPORTS_DIR, lang);
  try {
    const entries = await fs.readdir(langDir);
    const dateFiles = entries
      .filter((name) => /^\d{4}-\d{2}-\d{2}\.json$/.test(name))
      .map((name) => name.replace(/\.json$/, ""));
    for (const date of dateFiles) {
      try {
        const raw = await fs.readFile(path.join(langDir, `${date}.json`), "utf8");
        const parsed = JSON.parse(raw) as { vix_value?: number };
        if (typeof parsed.vix_value === "number" && Number.isFinite(parsed.vix_value)) {
          byDate.set(date, parsed.vix_value); // overwrites backfill for matching dates
        }
      } catch {
        // bad / missing — skip silently
      }
    }
  } catch {
    // reports dir missing — fall through with whatever the backfill gave us
  }

  const sorted = [...byDate.entries()]
    .sort((a, b) => (a[0] < b[0] ? -1 : 1))
    .slice(-n)
    .map(([date, vix]) => ({ date, vix }));

  return sorted;
}
