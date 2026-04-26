"use client";

import { useEffect, useState } from "react";

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

  return (
    <footer
      className="mt-12 border-t pt-6 pb-12 text-xs text-[color:var(--color-muted)]"
      style={{ borderColor: "var(--color-border)" }}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="font-mono">
          <span>{lang === "zh" ? "報告日期" : "Generated"}: {date} · Asia/Taipei</span>
          {localTime && (
            <span className="ml-1">
              · {lang === "zh" ? "你的時區" : "your local"}: {localTime}
            </span>
          )}
        </div>
        <div className="space-x-3">
          <span>{lang === "zh" ? "非投資建議" : "not investment advice"}</span>
          <a
            className="underline underline-offset-2 hover:text-[color:var(--color-fg)]"
            href="https://github.com/crotchblow-prog/stockpulse"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
