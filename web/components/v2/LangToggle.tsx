"use client";

import Link from "next/link";
import { useEffect } from "react";
import type { Locale } from "@/lib/i18n";

/**
 * Two-link toggle (`EN | 中`) — URL is the source of truth. Persists the
 * current choice to localStorage on mount so a future bare /v2/ visit can
 * land on the user's last locale (handled in /v2/page.tsx via cookie or
 * a client-side redirect; M3 keeps the simple URL-driven mode).
 */
export function LangToggle({
  current,
  pathSuffix,
}: {
  current: Locale;
  pathSuffix: string; // e.g. "" for /v2/{lang}, or "/2026-04-26" for dated
}) {
  useEffect(() => {
    try {
      localStorage.setItem("vixpulse:locale", current);
    } catch {
      // storage disabled / quota — ignore
    }
  }, [current]);

  const enHref = `/v2/en${pathSuffix}`;
  const zhHref = `/v2/zh${pathSuffix}`;

  return (
    <nav
      aria-label="Language"
      className="flex items-center gap-1 text-sm font-mono"
    >
      <Link
        href={enHref}
        className={
          current === "en"
            ? "text-[color:var(--color-fg)] font-semibold"
            : "text-[color:var(--color-muted)] hover:text-[color:var(--color-fg)]"
        }
        aria-current={current === "en" ? "page" : undefined}
      >
        EN
      </Link>
      <span className="text-[color:var(--color-muted)]">|</span>
      <Link
        href={zhHref}
        className={
          current === "zh"
            ? "text-[color:var(--color-fg)] font-semibold"
            : "text-[color:var(--color-muted)] hover:text-[color:var(--color-fg)]"
        }
        aria-current={current === "zh" ? "page" : undefined}
      >
        中
      </Link>
    </nav>
  );
}
