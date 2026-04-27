"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { COMPANY } from "@/lib/company";

/**
 * Footer used inside the (learn) route group, where the route segment does
 * NOT carry the lang param (en lives at /learn, zh at /zh/learn). We detect
 * the locale from the pathname instead.
 */
export function LearnFooter() {
  const pathname = usePathname();
  const isZh = pathname?.startsWith("/zh") ?? false;
  const lang = isZh ? "zh" : "en";
  const year = new Date().getFullYear();
  const company = isZh ? COMPANY.nameZh : COMPANY.nameEn;

  return (
    <footer
      className="mx-auto max-w-3xl px-6 py-10 text-xs text-[color:var(--color-muted)] border-t mt-12"
      style={{ borderColor: "var(--color-border)" }}
    >
      <div>
        Asia/Taipei · {isZh ? "非投資建議" : "not investment advice"} ·{" "}
        <a className="underline" href="https://github.com/crotchblow-prog/stockpulse">
          GitHub
        </a>
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
