import type { Holding } from "./reports";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

const SEVERITY_ORDER: Record<Severity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};

/**
 * Classify a holding by severity. A holding can match multiple rules; the
 * highest-severity match wins. Returns null when the holding has no
 * watchworthy signal at all (filter out before rendering).
 *
 * Rules per ARIA's M2 brief:
 * - CRITICAL: 'event_play' AND 'earnings_within_3d'
 * - HIGH:     'deep_drawdown'
 *             OR ('underwater' AND vs_avg_cost < -0.20)
 *             OR 'earnings_within_7d'
 * - MEDIUM:   'below_200dma' AND 'below_50dma'
 * - LOW:      'buy_list_member' AND no other watchworthy flags
 */
export function classifySeverity(h: Holding): Severity | null {
  const flags = new Set(h.flags || []);

  if (flags.has("event_play") && flags.has("earnings_within_3d")) {
    return "CRITICAL";
  }

  const isDeepUnderwater =
    flags.has("underwater") && (h.vs_avg_cost ?? 0) < -0.2;
  if (flags.has("deep_drawdown") || isDeepUnderwater || flags.has("earnings_within_7d")) {
    return "HIGH";
  }

  if (flags.has("below_200dma") && flags.has("below_50dma")) {
    return "MEDIUM";
  }

  if (flags.has("buy_list_member")) {
    // No other watchworthy flag — buy_list_member alone is LOW.
    const otherWatchworthy = ["deep_drawdown", "earnings_within_7d", "earnings_within_3d",
      "event_play", "underwater", "below_200dma", "below_50dma"];
    const hasOther = otherWatchworthy.some((f) => flags.has(f));
    if (!hasOther) return "LOW";
  }

  return null;
}

export type ClassifiedHolding = {
  symbol: string;
  severity: Severity;
  holding: Holding;
};

export function classifyAndSort(holdings: Record<string, Holding>): ClassifiedHolding[] {
  const out: ClassifiedHolding[] = [];
  for (const [symbol, holding] of Object.entries(holdings)) {
    const severity = classifySeverity(holding);
    if (severity === null) continue;
    out.push({ symbol, severity, holding });
  }
  out.sort((a, b) => {
    const so = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
    if (so !== 0) return so;
    return a.symbol.localeCompare(b.symbol);
  });
  return out;
}
