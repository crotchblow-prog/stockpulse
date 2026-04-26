import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "VIXPulse",
  description: "Daily VIX-tier US-market analysis",
};

/**
 * Layout for the new (Phase 3.0) report pages — was at /v2/* during M1-M3.
 * Wraps the [lang]/* subtree in `[data-v2-root]` so the v2 surface tokens
 * (--bg-base, --tier-current via [data-tier]) apply scoped to the new
 * design without bleeding into the legacy or default subtrees.
 *
 * `data-v2-root` attr name retained so existing CSS selectors and the
 * Playwright smoke test continue to work post-cutover.
 */
export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-v2-root
      style={{ background: "var(--color-bg-base)", minHeight: "100dvh" }}
      className="font-sans overflow-x-hidden"
    >
      {children}
    </div>
  );
}
