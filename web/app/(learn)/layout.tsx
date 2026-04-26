import Link from "next/link";

/**
 * Layout for /learn and /zh/learn — applies the same Phase 3.0 design tokens
 * as the [lang] report routes so the explainer pages don't visually diverge
 * from the main app post-cutover.
 *
 * Route group `(learn)` is URL-invisible: /learn → web/app/(learn)/learn/page.tsx,
 * /zh/learn → web/app/(learn)/zh/learn/page.tsx. Both routes resolve at their
 * existing public URLs, preserving any external bookmarks / shared links.
 *
 * The `[data-v2-root]` attr matches the [lang] subtree's wrapper so global
 * styles cascade identically. Body uses --bg-base, prose inherits Inter via
 * the root layout's font variable.
 */
export default function LearnLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-v2-root
      data-area="learn"
      style={{ background: "var(--color-bg-base)", minHeight: "100dvh" }}
      className="font-sans"
    >
      <header className="border-b" style={{ borderColor: "var(--color-border)" }}>
        <div className="mx-auto max-w-3xl px-6 py-5 flex items-center justify-between gap-3">
          <Link href="/" className="text-base font-semibold tracking-tight font-mono">
            📊 VIXPulse
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-8 report-prose">{children}</main>
      <footer
        className="mx-auto max-w-3xl px-6 py-10 text-xs text-[color:var(--color-muted)] border-t mt-12"
        style={{ borderColor: "var(--color-border)" }}
      >
        Asia/Taipei · not investment advice · {" "}
        <a className="underline" href="https://github.com/crotchblow-prog/stockpulse">
          GitHub
        </a>
      </footer>
    </div>
  );
}
