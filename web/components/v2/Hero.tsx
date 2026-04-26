import type { ReportPayload } from "@/lib/reports";
import { fmtPct, fmtSignedNum } from "@/lib/formatters";
import { t } from "@/lib/i18n";

/**
 * Top-of-page hero: tier banner + giant VIX + secondary stats + 1-sentence read.
 *
 * Sets `data-tier={tier.index}` so descendant CSS picks up `--tier-current`
 * from globals.css (the [data-tier="N"] mapping inside [data-v2-root]).
 *
 * Truncates synthesis.market.read to first 2 sentences. Skips rendering
 * the read line if synthesis is missing — the JSON sidecar's synthesis
 * field can be absent (Phase 2 Commit 7's normalization tolerates this).
 */
export function Hero({ payload, lang }: { payload: ReportPayload; lang: "en" | "zh" }) {
  const { tier, vix_value, snapshot, synthesis } = payload;
  const vix = snapshot.VIX;
  const vixChangePct = vix?.change_pct ?? null;

  const marketRead = extractRead(synthesis ?? null);

  return (
    <section
      data-tier={tier.index}
      className="border rounded-lg p-6"
      style={{
        background: "var(--color-bg-surface)",
        borderColor: "var(--tier-current, var(--color-border))",
      }}
    >
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-4">
        <span
          className="text-xs uppercase tracking-wider font-medium"
          style={{ color: "var(--tier-current, var(--color-muted))" }}
        >
          Tier {tier.index}
        </span>
        <span className="text-base font-medium">{t(lang, `tier_action_${tier.index}`)}</span>
        <span className="text-xs text-[color:var(--color-muted)]">
          VIX {fmtSignedNum(tier.vix_range[0], 0)}–{fmtSignedNum(tier.vix_range[1], 1).replace("+", "")}
        </span>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-6xl font-bold leading-none tabular-nums">
            {vix_value.toFixed(2)}
          </div>
          <div className="mt-2 font-mono text-sm text-[color:var(--color-muted)] tabular-nums">
            {vix?.change != null ? `${fmtSignedNum(vix.change)} ` : ""}
            {vixChangePct != null ? `(${fmtPct(vixChangePct)})` : ""}
            {" · "}{lang === "zh" ? "今日 VIX" : "VIX today"}
          </div>
        </div>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-right text-sm">
          <dt className="text-[color:var(--color-muted)]">
            {lang === "zh" ? "現金目標" : "Cash target"}
          </dt>
          <dd className="font-mono tabular-nums">{tier.cash_target_pct}%</dd>
          <dt className="text-[color:var(--color-muted)]">
            {lang === "zh" ? "進場規模" : "Buy size"}
          </dt>
          <dd className="font-mono tabular-nums">{tier.buy_size_pct}%</dd>
        </dl>
      </div>

      {marketRead && (
        <p className="mt-6 leading-7 text-[color:var(--color-fg)] text-sm sm:text-base border-t pt-5"
           style={{ borderColor: "var(--color-border)" }}>
          {marketRead}
        </p>
      )}
    </section>
  );
}

function extractRead(synthesis: ReportPayload["synthesis"] | null | undefined): string | null {
  if (!synthesis) return null;
  const market = synthesis.market;
  let read: string | null = null;
  if (typeof market === "string") {
    read = market;
  } else if (market && typeof market === "object" && "read" in market) {
    read = (market as { read?: string }).read ?? null;
  }
  if (!read) return null;
  return truncateToSentences(read, 2);
}

/**
 * Take the first N sentences of `text`. Splits ONLY at terminator-followed-by-
 * whitespace-followed-by-capital-or-CJK — so decimals like "21.30" and
 * percentages like "+0.16%) signals" don't get treated as sentence boundaries
 * (which produced fragmentary "30) confirms..." reads in earlier versions).
 *
 * Conservative: if no clean break is found, returns the full text unchanged
 * so the page never silently loses data.
 */
function truncateToSentences(text: string, n: number): string {
  const trimmed = text.trim();
  // Lookbehind on terminator (.!?), required whitespace, lookahead on uppercase
  // Latin OR a CJK Unified Ideograph (zh-TW sentences start with CJK).
  const parts = trimmed.split(/(?<=[.!?])\s+(?=[A-Z一-龥])/);
  if (parts.length <= n) return trimmed;
  return parts.slice(0, n).join(" ").trim();
}
