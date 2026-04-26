import type { Tier, Synthesis } from "@/lib/reports";
import type { Locale } from "@/lib/i18n";
import { t } from "@/lib/i18n";

/**
 * Tier Action section — buy_list and sell_list chips. Per Phase 2.5 Commit 9,
 * if a buy-list ticker is also currently held (appears in synthesis.positions),
 * append the action inline (e.g., "TSM (hold)") so the framework view doesn't
 * silently contradict the tactical view.
 */
export function TierAction({
  tier,
  synthesis,
  locale,
}: {
  tier: Tier;
  synthesis: Synthesis | null | undefined;
  locale: Locale;
}) {
  const actions = new Map<string, string>();
  if (synthesis?.positions) {
    for (const p of synthesis.positions) {
      if (typeof p.symbol === "string" && typeof p.action === "string") {
        actions.set(p.symbol, p.action);
      }
    }
  }

  const buyList = tier.buy_list ?? [];
  const sellList = tier.sell_list ?? [];

  return (
    <section data-component="tier-action" data-tier={tier.index} className="space-y-3">
      <h2 className="text-lg font-medium">{t(locale, "tier_action")}</h2>
      <div className="space-y-2">
        <div className="text-sm font-semibold tracking-wide uppercase text-[color:var(--color-muted)]">
          {t(locale, "buy_list")}
        </div>
        {buyList.length === 0 ? (
          <span className="text-sm italic text-[color:var(--color-muted)]">
            {t(locale, "no_buys_at_tier")}
          </span>
        ) : (
          <div className="flex flex-wrap gap-2" data-subsection="buy-list">
            {buyList.map((sym) => {
              const action = actions.get(sym);
              return (
                <span
                  key={sym}
                  data-ticker={sym}
                  data-held={action ? "true" : "false"}
                  className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-sm font-mono"
                  style={{
                    borderColor: "var(--color-border)",
                    background: "var(--color-bg-elevated)",
                  }}
                >
                  <span>{sym}</span>
                  {action && (
                    <span className="text-xs text-[color:var(--color-muted)]">({action})</span>
                  )}
                </span>
              );
            })}
          </div>
        )}
      </div>
      {sellList.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold tracking-wide uppercase text-[color:var(--color-muted)]">
            {t(locale, "sell_list")}
          </div>
          <div className="flex flex-wrap gap-2" data-subsection="sell-list">
            {sellList.map((sym) => (
              <span
                key={sym}
                data-ticker={sym}
                className="inline-flex items-center rounded-md border px-2.5 py-1 text-sm font-mono"
                style={{
                  borderColor: "var(--color-tier-5)",
                  background: "var(--color-bg-elevated)",
                  color: "var(--color-tier-5)",
                }}
              >
                {sym}
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
