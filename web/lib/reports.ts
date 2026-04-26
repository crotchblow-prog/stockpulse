import { promises as fs } from "node:fs";
import path from "node:path";

const REPORTS_DIR = path.join(process.cwd(), "public", "reports");

export type Lang = "en" | "zh";

export type ReportEntry = {
  date: string;        // YYYY-MM-DD
  filename: string;    // e.g. 2026-04-25.md
};

const NO_REPORT_FALLBACK: Record<Lang, string> = {
  en: "# No report yet\n\nThe daily pipeline hasn't produced a report. Check back after the next cron run (~10:00 ET / 22:00 Asia/Taipei).",
  zh: "# 尚無報告\n\n每日管線尚未產出報告，請於下次 cron 執行後（約 10:00 ET / 22:00 Asia/Taipei）回來查看。",
};

function langDir(lang: Lang): string {
  return path.join(REPORTS_DIR, lang);
}

export async function readLatestReport(lang: Lang = "en"): Promise<string> {
  const file = path.join(langDir(lang), "latest.md");
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return NO_REPORT_FALLBACK[lang];
  }
}

export async function readReportByDate(date: string, lang: Lang = "en"): Promise<string | null> {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  const file = path.join(langDir(lang), `${date}.md`);
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return null;
  }
}

export async function listArchivedReports(lang: Lang = "en"): Promise<ReportEntry[]> {
  let entries: string[];
  try {
    entries = await fs.readdir(langDir(lang));
  } catch {
    return [];
  }
  return entries
    .filter((name) => /^\d{4}-\d{2}-\d{2}\.md$/.test(name))
    .map((filename) => ({ date: filename.replace(/\.md$/, ""), filename }))
    .sort((a, b) => (a.date < b.date ? 1 : -1));
}

// ── JSON sidecar (v2 frontend reads this, not the .md) ───────────────────────

export type Quote = {
  symbol: string;
  label: string;
  last: number | null;
  prev_close: number | null;
  change: number | null;
  change_pct: number | null;
  error: string | null;
};

export type Holding = {
  account: string;
  avg_cost: number | null;
  change: number | null;
  change_pct: number | null;
  days_to_earnings: number | null;
  earnings_date: string | null;
  flags: string[];
  last: number | null;
  ma_200: number | null;
  ma_50: number | null;
  missing_from_universe?: boolean;
  pct_from_52w_high: number | null;
  pct_from_52w_low: number | null;
  pct_from_ma_200: number | null;
  pct_from_ma_50: number | null;
  regime_metrics: Record<string, unknown> | null;
  rsi_14: number | null;
  sensitivity_tags: string[];
  tags?: string[];
  tier_index: number | null;
  vs_avg_cost: number | null;
};

export type SynthesisPosition = {
  symbol: string;
  action: string;
  confidence: string;
  rationale: string;
};

export type Synthesis = {
  market: { read: string; devils_advocate: string } | string | null;
  positions: SynthesisPosition[];
  model?: string;
  usage?: Record<string, number>;
};

export type Tier = {
  index: number;
  name: string;
  action: string;
  buy_list: string[];
  buy_size_pct: string;
  cash_target_pct: number;
  vix_range: [number, number];
  note?: string;
  sell_list?: string[] | null;
};

export type RegimeUniverseEntry = {
  beta_normal: number | null;
  beta_stress: number | null;
  vix_spike_decay_pct: number | null;
  vix_spike_decay_p25_pct: number | null;
  vix_crush_recovery_pct: number | null;
  spike_event_count: number;
  crush_event_count: number;
  stress_weeks: number;
  normal_weeks: number;
  confidence: "high" | "low";
  sensitivity_tags: string[];
};

export type ReportPayload = {
  schema_version: number;
  date: string;
  vix_value: number;
  tier: Tier;
  snapshot: Record<string, Quote>;
  holdings: Record<string, Holding>;
  synthesis?: Synthesis | null;
  accounts?: Record<string, { holdings: string[]; tier_index: number; total_value: number | null }>;
  regime_universe?: Record<string, RegimeUniverseEntry>;
};

export async function readReportJsonByDate(
  date: string | "latest",
  lang: Lang = "en",
): Promise<ReportPayload | null> {
  const filename = date === "latest" ? "latest.json" : `${date}.json`;
  if (date !== "latest" && !/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  const file = path.join(langDir(lang), filename);
  try {
    const raw = await fs.readFile(file, "utf8");
    return JSON.parse(raw) as ReportPayload;
  } catch {
    return null;
  }
}
