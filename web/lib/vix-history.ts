import { promises as fs } from "node:fs";
import path from "node:path";
import type { Lang } from "./reports";

const REPORTS_DIR = path.join(process.cwd(), "public", "reports");

export type VixPoint = { date: string; vix: number };

/**
 * Read the last N daily JSON sidecars (en) and extract `vix_value`. Returns
 * an array sorted oldest → newest, capped to N points. Used by the M3
 * sparkline. en is the canonical history source — the zh files duplicate
 * the same numeric `vix_value`, so we don't bother reading both.
 */
export async function loadVixHistory(n = 30, lang: Lang = "en"): Promise<VixPoint[]> {
  const langDir = path.join(REPORTS_DIR, lang);
  let entries: string[];
  try {
    entries = await fs.readdir(langDir);
  } catch {
    return [];
  }

  const dateFiles = entries
    .filter((name) => /^\d{4}-\d{2}-\d{2}\.json$/.test(name))
    .map((name) => name.replace(/\.json$/, ""))
    .sort(); // ascending YYYY-MM-DD

  const recent = dateFiles.slice(-n);
  const points: VixPoint[] = [];
  for (const date of recent) {
    try {
      const raw = await fs.readFile(path.join(langDir, `${date}.json`), "utf8");
      const parsed = JSON.parse(raw) as { vix_value?: number };
      if (typeof parsed.vix_value === "number" && Number.isFinite(parsed.vix_value)) {
        points.push({ date, vix: parsed.vix_value });
      }
    } catch {
      // bad / missing JSON — skip silently
    }
  }
  return points;
}
