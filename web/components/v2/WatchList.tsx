import type { Holding } from "@/lib/reports";
import { classifyAndSort, type Severity } from "@/lib/severity";

const SEVERITY_STYLE: Record<
  Severity,
  { border: string; padding: string; textSize: string; label: string; labelColor: string }
> = {
  CRITICAL: {
    border: "var(--color-tier-5)",        // alert red
    padding: "p-6",
    textSize: "text-lg",
    label: "CRITICAL",
    labelColor: "var(--color-tier-5)",
  },
  HIGH: {
    border: "var(--color-tier-4)",        // orange-red
    padding: "p-5",
    textSize: "text-base",
    label: "HIGH",
    labelColor: "var(--color-tier-4)",
  },
  MEDIUM: {
    border: "var(--color-tier-3)",        // amber
    padding: "p-4",
    textSize: "text-base",
    label: "MEDIUM",
    labelColor: "var(--color-tier-3)",
  },
  LOW: {
    border: "var(--color-border)",
    padding: "p-3",
    textSize: "text-sm",
    label: "LOW",
    labelColor: "var(--color-muted)",
  },
};

export function WatchList({
  holdings,
  lang,
}: {
  holdings: Record<string, Holding>;
  lang: "en" | "zh";
}) {
  const classified = classifyAndSort(holdings);

  // Default-strip removes holdings; the Watch List has nothing to render so
  // skip the section entirely (no header, no placeholder).
  if (classified.length === 0) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-medium">
        {lang === "zh" ? "🚩 關注名單" : "🚩 Watch List"}
      </h2>
      <ul className="space-y-2">
        {classified.map(({ symbol, severity, holding }) => {
          const style = SEVERITY_STYLE[severity];
          const flagsStr = holding.flags.join(", ");
          return (
            <li
              key={symbol}
              data-severity={severity}
              data-symbol={symbol}
              className={`rounded-lg border ${style.padding} ${style.textSize}`}
              style={{ borderColor: style.border, background: "var(--color-bg-surface)" }}
            >
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <span
                    className="text-xs uppercase font-mono tracking-wider font-medium"
                    style={{ color: style.labelColor }}
                  >
                    {style.label}
                  </span>
                  <span className="font-mono font-semibold">{symbol}</span>
                  <span className="text-xs text-[color:var(--color-muted)]">
                    Tier {holding.tier_index ?? "—"} · {holding.account}
                  </span>
                </div>
              </div>
              <div className="mt-2 text-xs sm:text-sm text-[color:var(--color-muted)] font-mono">
                {flagsStr}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
