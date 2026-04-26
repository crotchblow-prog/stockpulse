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
