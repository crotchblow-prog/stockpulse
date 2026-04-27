"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { COMPANY } from "@/lib/company";

/**
 * Footer with bilingual disclaimer + Asia/Taipei timestamp + user-local time.
 * The server-rendered timestamp is the report's `date` field; the user-local
 * time is computed client-side via Intl.DateTimeFormat after hydration.
 */
export function V2Footer({ date, lang }: { date: string; lang: "en" | "zh" }) {
  const [localTime, setLocalTime] = useState<string | null>(null);

  useEffect(() => {
    // Anchor the local-time display to start-of-day in Asia/Taipei (where the
    // report is generated). For minute-level precision we'd need a server
    // timestamp; for now the date alone is sufficient context.
    try {
      const fmt = new Intl.DateTimeFormat(undefined, {
        dateStyle: "long",
        timeZone: undefined,
      });
      setLocalTime(fmt.format(new Date(`${date}T00:00:00+08:00`)));
    } catch {
      setLocalTime(null);
    }
  }, [date]);

  const year = new Date().getFullYear();
  const company = lang === "zh" ? COMPANY.nameZh : COMPANY.nameEn;
  const isZh = lang === "zh";

  return (
    <footer
      className="mt-12 border-t pt-6 pb-12 text-xs text-[color:var(--color-muted)]"
      style={{ borderColor: "var(--color-border)" }}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="font-mono">
          <span>{isZh ? "報告日期" : "Generated"}: {date} · Asia/Taipei</span>
          {localTime && (
            <span className="ml-1">
              · {isZh ? "你的時區" : "your local"}: {localTime}
            </span>
          )}
        </div>
        <div className="space-x-3">
          <span>{isZh ? "非投資建議" : "not investment advice"}</span>
          <a
            className="underline underline-offset-2 hover:text-[color:var(--color-fg)]"
            href="https://github.com/crotchblow-prog/stockpulse"
          >
            GitHub
          </a>
        </div>
      </div>
      <div
        className="mt-4 flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between"
        style={{ borderColor: "var(--color-border)" }}
      >
        <div>© {year} {company} · VIX Pulse</div>
        <nav className="flex flex-wrap gap-x-3 gap-y-1">
          <Link href={`/${lang}/about`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {isZh ? "關於我們" : "About"}
          </Link>
          <Link href={`/${lang}/privacy`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {isZh ? "隱私權政策" : "Privacy"}
          </Link>
          <Link href={`/${lang}/terms`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {isZh ? "服務條款" : "Terms"}
          </Link>
          <a
            href={`mailto:${COMPANY.contactEmail}`}
            className="underline underline-offset-2 hover:text-[color:var(--color-fg)]"
          >
            {isZh ? "聯絡我們" : "Contact"}
          </a>
        </nav>
      </div>
    </footer>
  );
}
