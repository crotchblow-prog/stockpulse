import Link from "next/link";

/**
 * Layout for /learn and /zh/learn. Minimal chrome — just brand link +
 * spacing. The explainer pages aren't part of the v2 report flow but
 * still benefit from a small header so they don't render bare on the
 * post-cutover minimal root.
 */
export default function DefaultLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-default-root
      style={{ background: "var(--color-bg-base)" }}
      className="font-sans min-h-dvh"
    >
      <header className="border-b" style={{ borderColor: "var(--color-border)" }}>
        <div className="mx-auto max-w-3xl px-6 py-5">
          <Link href="/" className="font-semibold tracking-tight font-mono">
            📊 VIXPulse
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-8">{children}</main>
    </div>
  );
}
