import type { Holding } from "@/lib/reports";
import { fmtPct, fmtPrice, fmtRsi } from "@/lib/formatters";

export function Holdings({
  holdings,
  lang,
}: {
  holdings: Record<string, Holding>;
  lang: "en" | "zh";
}) {
  const entries = Object.entries(holdings).sort(([a], [b]) => a.localeCompare(b));

  // Default-strip removes holdings; render nothing (no header, no placeholder)
  // so the public site doesn't leak a "No holdings" placeholder card.
  if (entries.length === 0) return null;

  return (
    <section className="space-y-3" data-component="holdings">
      <h2 className="text-lg font-medium">{lang === "zh" ? "💼 持倉" : "💼 Holdings"}</h2>

      {/* Desktop table — ≥768px (md:) */}
      <div
        className="hidden md:block rounded-lg border overflow-hidden"
        style={{ borderColor: "var(--color-border)", background: "var(--color-bg-surface)" }}
      >
        <table className="w-full text-sm tabular-nums">
          <thead>
            <tr
              className="border-b text-left text-xs uppercase tracking-wider text-[color:var(--color-muted)]"
              style={{ borderColor: "var(--color-border)" }}
            >
              <th className="px-4 py-3 font-medium">{lang === "zh" ? "標的" : "Ticker"}</th>
              <th className="px-4 py-3 font-medium text-right">{lang === "zh" ? "現價" : "Last"}</th>
              <th className="px-4 py-3 font-medium text-right">{lang === "zh" ? "vs 成本" : "vs cost"}</th>
              <th className="px-4 py-3 font-medium text-right">RSI</th>
              <th className="px-4 py-3 font-medium text-right">vs 50DMA</th>
              <th className="px-4 py-3 font-medium text-right">vs 200DMA</th>
              <th className="px-4 py-3 font-medium text-right">{lang === "zh" ? "vs 52週高" : "vs 52w high"}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([sym, h]) => (
              <tr
                key={sym}
                className="border-b last:border-b-0 hover:bg-[color:var(--color-bg-elevated)]"
                style={{ borderColor: "var(--color-border)" }}
              >
                <td className="px-4 py-3 font-mono font-semibold">{sym}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtPrice(h.last)}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtPct(h.vs_avg_cost)}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtRsi(h.rsi_14)}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtPct(h.pct_from_ma_50)}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtPct(h.pct_from_ma_200)}</td>
                <td className="px-4 py-3 text-right font-mono">{fmtPct(h.pct_from_52w_high)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards — <768px. No horizontal scroll at 375px. */}
      <ul className="md:hidden space-y-2" data-mobile-holdings>
        {entries.map(([sym, h]) => (
          <li
            key={sym}
            className="rounded-lg border p-4"
            style={{
              borderColor: "var(--color-border)",
              background: "var(--color-bg-surface)",
            }}
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-mono text-xl font-bold">{sym}</span>
              <span className="font-mono text-base tabular-nums">{fmtPrice(h.last)}</span>
            </div>
            <div className="mt-1 flex items-baseline justify-between gap-2 text-sm">
              <span className="text-[color:var(--color-muted)]">
                {lang === "zh" ? "vs 成本" : "vs cost"}
              </span>
              <span className="font-mono tabular-nums">{fmtPct(h.vs_avg_cost)}</span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs font-mono tabular-nums">
              <div className="flex justify-between">
                <span className="text-[color:var(--color-muted)]">RSI</span>
                <span>{fmtRsi(h.rsi_14)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[color:var(--color-muted)]">52w</span>
                <span>{fmtPct(h.pct_from_52w_high)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[color:var(--color-muted)]">50DMA</span>
                <span>{fmtPct(h.pct_from_ma_50)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[color:var(--color-muted)]">200DMA</span>
                <span>{fmtPct(h.pct_from_ma_200)}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
