import { promises as fs } from "node:fs";
import path from "node:path";

const REPORTS_DIR = path.join(process.cwd(), "public", "reports");

export type ReportEntry = {
  date: string;        // YYYY-MM-DD
  filename: string;    // e.g. 2026-04-25.md
};

export async function readLatestReport(): Promise<string> {
  const file = path.join(REPORTS_DIR, "latest.md");
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return "# No report yet\n\nThe daily pipeline hasn't produced a report. Check back at 10:00 Asia/Taipei.";
  }
}

export async function readReportByDate(date: string): Promise<string | null> {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  const file = path.join(REPORTS_DIR, `${date}.md`);
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return null;
  }
}

export async function listArchivedReports(): Promise<ReportEntry[]> {
  let entries: string[];
  try {
    entries = await fs.readdir(REPORTS_DIR);
  } catch {
    return [];
  }
  return entries
    .filter((name) => /^\d{4}-\d{2}-\d{2}\.md$/.test(name))
    .map((filename) => ({ date: filename.replace(/\.md$/, ""), filename }))
    .sort((a, b) => (a.date < b.date ? 1 : -1));
}
