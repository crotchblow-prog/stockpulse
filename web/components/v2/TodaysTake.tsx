import type { Synthesis } from "@/lib/reports";
import type { Locale } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const ACTION_COLOR: Record<string, string> = {
  add: "var(--color-tier-1)",        // cyan — defensive go-ahead
  hold: "var(--color-muted)",        // neutral
  trim: "var(--color-tier-3)",       // amber — caution
  exit: "var(--color-tier-5)",       // alert red
  watch: "var(--color-tier-0)",      // cobalt blue — wait for setup
};

const CONFIDENCE_LABEL: Record<string, string> = {
  low: "low",
  medium: "med",
  high: "high",
};

function extractMarket(synthesis: Synthesis | null | undefined): { read: string | null; devils: string | null } {
  if (!synthesis) return { read: null, devils: null };
  const market = synthesis.market;
  if (typeof market === "string") return { read: market, devils: null };
  if (market && typeof market === "object") {
    return {
      read: typeof market.read === "string" ? market.read : null,
      devils: typeof market.devils_advocate === "string" ? market.devils_advocate : null,
    };
  }
  return { read: null, devils: null };
}

export function TodaysTake({
  synthesis,
  locale,
}: {
  synthesis: Synthesis | null | undefined;
  locale: Locale;
}) {
  const { read, devils } = extractMarket(synthesis);
  const positions = synthesis?.positions ?? [];
  const hasContent = !!(read || devils || positions.length > 0);

  if (!hasContent) {
    return (
      <section data-component="todays-take" className="space-y-3">
        <h2 className="text-lg font-medium">{t(locale, "todays_take")}</h2>
        <p className="text-sm italic text-[color:var(--color-muted)]">
          {t(locale, "synthesis_unavailable")}
        </p>
      </section>
    );
  }

  return (
    <section data-component="todays-take" className="space-y-4">
      <h2 className="text-lg font-medium">{t(locale, "todays_take")}</h2>
      {read && (
        <p className="leading-7 text-sm sm:text-base">
          <span className="font-semibold">{t(locale, "market_read")}</span> {read}
        </p>
      )}
      {devils && (
        <p
          className="leading-7 text-sm sm:text-base text-[color:var(--color-muted)]"
          data-subsection="devils-advocate"
        >
          <span className="font-semibold">{t(locale, "devils_advocate")}</span> {devils}
        </p>
      )}
      {positions.length > 0 && (
        <div data-subsection="position-calls" className="space-y-2">
          <h3 className="text-sm font-semibold tracking-wide uppercase text-[color:var(--color-muted)]">
            {t(locale, "position_calls")}
          </h3>
          <ul className="space-y-2">
            {positions.map((p) => (
              <Card
                key={p.symbol}
                data-position={p.symbol}
                data-action={p.action}
                data-confidence={p.confidence}
              >
                <CardContent className="flex items-start justify-between gap-3 p-4 flex-wrap">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono font-semibold">{p.symbol}</span>
                    <Badge
                      variant="outline"
                      style={{
                        borderColor: ACTION_COLOR[p.action] ?? "var(--color-border)",
                        color: ACTION_COLOR[p.action] ?? "var(--color-fg)",
                      }}
                    >
                      {p.action}
                    </Badge>
                    <span className="text-xs font-mono uppercase text-[color:var(--color-muted)]">
                      {CONFIDENCE_LABEL[p.confidence] ?? p.confidence}
                    </span>
                  </div>
                  {p.rationale && (
                    <p className="text-sm leading-6 basis-full text-[color:var(--color-fg)]">
                      {p.rationale}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
