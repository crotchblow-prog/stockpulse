"use client";

import dynamic from "next/dynamic";
import type { ComponentProps } from "react";
import type { VixSparkline } from "./VixSparkline";

/**
 * Lazy-load wrapper. recharts ships ~85 KB gzipped — keep it out of the
 * initial /v2/[lang] bundle and let the sparkline hydrate after first
 * paint. ssr: false because recharts uses ResizeObserver / window APIs.
 *
 * The 220px placeholder card maintains the page layout (CLS-safe) until
 * the chart hydrates.
 */
const Sparkline = dynamic(
  () => import("./VixSparkline").then((m) => m.VixSparkline),
  {
    ssr: false,
    loading: () => (
      <div
        className="rounded-lg border"
        style={{
          borderColor: "var(--color-border)",
          background: "var(--color-bg-surface)",
          aspectRatio: "16 / 5",
          minHeight: "220px",
        }}
      />
    ),
  }
);

export function VixSparklineLazy(props: ComponentProps<typeof VixSparkline>) {
  return <Sparkline {...props} />;
}
