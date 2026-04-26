import type { Quote } from "@/lib/reports";
import { fmtPrice, fmtPct, fmtSignedNum } from "@/lib/formatters";

const ORDER_EN = [
  "VIX", "VIX3M", "S&P 500", "Nasdaq", "Dow", "USD/JPY", "BTC", "Gold", "WTI",
];

const LABEL_ZH: Record<string, string> = {
  "VIX": "VIX 恐慌指數",
  "VIX3M": "VIX 三月期",
  "S&P 500": "S&P 500",
  "Nasdaq": "Nasdaq",
  "Dow": "Dow",
  "USD/JPY": "美元 / 日圓",
  "BTC": "比特幣",
  "Gold": "黃金",
  "WTI": "原油 (WTI)",
};

export function SnapshotGrid({
  snapshot,
  tierIndex,
  lang,
}: {
  snapshot: Record<string, Quote>;
  tierIndex: number;
  lang: "en" | "zh";
}) {
  const ordered = ORDER_EN.filter((k) => snapshot[k]);

  return (
    <section className="space-y-3" data-tier={tierIndex} data-component="snapshot">
      <h2 className="text-lg font-medium">
        {lang === "zh" ? "🌐 市場快照" : "🌐 Market Snapshot"}
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {ordered.map((key) => {
          const q = snapshot[key];
          const isVix = key === "VIX";
          const label = lang === "zh" ? LABEL_ZH[key] ?? key : key;
          return (
            <div
              key={key}
              data-quote={key}
              className={`rounded-lg border ${isVix ? "p-5 sm:row-span-1 col-span-1 sm:col-span-2 md:col-span-1" : "p-4"}`}
              style={{
                borderColor: isVix ? "var(--tier-current, var(--color-tier-2))" : "var(--color-border)",
                background: "var(--color-bg-surface)",
              }}
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className={`font-medium ${isVix ? "text-base" : "text-sm"}`}>{label}</span>
              </div>
              <div className={`mt-1 font-mono tabular-nums ${isVix ? "text-3xl font-bold" : "text-xl"}`}>
                {q.error ? "—" : fmtPrice(q.last)}
              </div>
              {!q.error && (
                <div className="mt-1 font-mono text-xs tabular-nums text-[color:var(--color-muted)]">
                  {q.change != null && `${fmtSignedNum(q.change)} `}
                  {q.change_pct != null && `(${fmtPct(q.change_pct)})`}
                </div>
              )}
              {q.error && (
                <div className="mt-1 text-xs text-[color:var(--color-muted)]">{q.error}</div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
