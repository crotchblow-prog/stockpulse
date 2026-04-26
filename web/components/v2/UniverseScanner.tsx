import type { RegimeUniverseEntry } from "@/lib/reports";
import type { Locale } from "@/lib/i18n";
import { t } from "@/lib/i18n";

/**
 * 📡 Universe Scanner — three sub-region cards (🟢 Add / 🟡 Watch / 🔴 Avoid)
 * mirroring scripts/reporters/markdown_gen._render_universe_scanner.
 *
 * Filter rules + thresholds match Phase 2.5 Commits 6, 6.5, 8, 10, 10.5:
 * - Add filter: high_normal at tier 0-2, defensive at tier 3+. Sample col is normal_weeks.
 * - Watch filter: mean_reverter (single-axis crush > +0.6%). Sample col is crush_event_count.
 * - Avoid filter: crisis_alpha (p25 < -4%). Sample col is spike_event_count.
 * - Empty placeholders show today's gap to the threshold so the tuning conversation is grounded.
 * - Cross-region overlap (Add + Avoid same ticker) decorated in both rows.
 */

type Entry = [string, RegimeUniverseEntry];

function eligible(e: RegimeUniverseEntry, tag: string): boolean {
  if (e.confidence === "low") return false;
  return (e.sensitivity_tags ?? []).includes(tag);
}

function fmtPct1(v: number | null | undefined): string {
  if (v == null) return "—";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}%`;
}

function fmtBeta(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}

function addFilter(tierIdx: number): { tag: string; label: string } {
  if (tierIdx <= 2) return { tag: "high_normal", label: "high_normal" };
  return { tag: "defensive", label: "defensive" };
}

function topNByAbsBeta(entries: Entry[], n = 5): Entry[] {
  return [...entries].sort(([sa, ea], [sb, eb]) => {
    const ba = Math.abs(ea.beta_normal ?? 0);
    const bb = Math.abs(eb.beta_normal ?? 0);
    if (ba !== bb) return bb - ba;
    return sa.localeCompare(sb);
  }).slice(0, n);
}

function topNByCrush(entries: Entry[], n = 5): Entry[] {
  return [...entries].sort(([sa, ea], [sb, eb]) => {
    const va = ea.vix_crush_recovery_pct ?? 0;
    const vb = eb.vix_crush_recovery_pct ?? 0;
    if (va !== vb) return vb - va;
    return sa.localeCompare(sb);
  }).slice(0, n);
}

function topNByAbsP25(entries: Entry[], n = 5): Entry[] {
  return [...entries].sort(([sa, ea], [sb, eb]) => {
    const va = Math.abs(ea.vix_spike_decay_p25_pct ?? 0);
    const vb = Math.abs(eb.vix_spike_decay_p25_pct ?? 0);
    if (va !== vb) return vb - va;
    return sa.localeCompare(sb);
  }).slice(0, n);
}

export function UniverseScanner({
  universe,
  tierIdx,
  tierAction,
  locale,
}: {
  universe: Record<string, RegimeUniverseEntry> | undefined | null;
  tierIdx: number;
  tierAction: string;
  locale: Locale;
}) {
  const universeEntries: Entry[] = universe
    ? Object.entries(universe)
    : [];
  const dataPresent = universeEntries.length > 0;

  const { tag: addTag, label: addLabel } = addFilter(tierIdx);
  const addEligible = universeEntries.filter(([, e]) => eligible(e, addTag));
  const watchEligible = universeEntries.filter(([, e]) => eligible(e, "mean_reverter"));
  const avoidEligible = universeEntries.filter(([, e]) => eligible(e, "crisis_alpha"));

  const addTop = topNByAbsBeta(addEligible);
  const watchTop = topNByCrush(watchEligible);
  const avoidTop = topNByAbsP25(avoidEligible);

  const addSet = new Set(addEligible.map(([s]) => s));
  const avoidSet = new Set(avoidEligible.map(([s]) => s));

  return (
    <section data-component="universe-scanner" className="space-y-3">
      <h2 className="text-lg font-medium">
        {t(locale, "universe_scanner")} — Tier {tierIdx} ({tierAction})
      </h2>
      <p className="text-sm italic text-[color:var(--color-muted)]">
        {t(locale, "scanner_legend")}
      </p>

      {/* 🟢 Add candidates */}
      <SubRegion
        title={t(locale, "add_candidates")}
        filterDesc={`${addLabel}, sample ≥ 8`}
        columns={[
          t(locale, "th_ticker"),
          t(locale, "scanner_th_beta_normal"),
          t(locale, "scanner_th_sample"),
          t(locale, "scanner_th_note"),
        ]}
        emptyMessage={
          dataPresent ? "_no candidates at current thresholds_" : t(locale, "scanner_universe_missing")
        }
        rows={addTop.map(([sym, e]) => ({
          key: sym,
          attrs: { "data-ticker": sym, "data-region": "add" },
          cells: [
            <span key="t" className="font-mono font-semibold">{sym}</span>,
            <span key="b" className="font-mono tabular-nums text-right block">{fmtBeta(e.beta_normal)}</span>,
            <span key="s" className="font-mono tabular-nums text-right block">{e.normal_weeks ?? 0}</span>,
            avoidSet.has(sym) ? (
              <span key="n" className="text-xs">{t(locale, "also_in_avoid")}</span>
            ) : (
              <span key="n" />
            ),
          ],
        }))}
      />

      {/* 🟡 Watch (transition) */}
      <SubRegion
        title={t(locale, "watch_transition")}
        filterDesc="mean_reverter, sample ≥ 8"
        columns={[
          t(locale, "th_ticker"),
          t(locale, "scanner_th_crush"),
          t(locale, "scanner_th_decay"),
          t(locale, "scanner_th_note"),
        ]}
        emptyMessage={
          dataPresent
            ? watchEmptyMessage(universeEntries)
            : t(locale, "scanner_universe_missing")
        }
        rows={watchTop.map(([sym, e]) => ({
          key: sym,
          attrs: { "data-ticker": sym, "data-region": "watch" },
          cells: [
            <span key="t" className="font-mono font-semibold">{sym}</span>,
            <span key="c" className="font-mono tabular-nums text-right block">{fmtPct1(e.vix_crush_recovery_pct)}</span>,
            <span key="d" className="font-mono tabular-nums text-right block">{fmtPct1(e.vix_spike_decay_pct)}</span>,
            <span key="n" />,
          ],
        }))}
      />

      {/* 🔴 Avoid candidates */}
      <SubRegion
        title={t(locale, "avoid_candidates")}
        filterDesc="crisis_alpha, sample ≥ 8"
        columns={[
          t(locale, "th_ticker"),
          t(locale, "scanner_th_decay"),
          t(locale, "scanner_th_sample"),
          t(locale, "scanner_th_note"),
        ]}
        emptyMessage={
          dataPresent
            ? avoidEmptyMessage(universeEntries)
            : t(locale, "scanner_universe_missing")
        }
        rows={avoidTop.map(([sym, e]) => ({
          key: sym,
          attrs: { "data-ticker": sym, "data-region": "avoid" },
          cells: [
            <span key="t" className="font-mono font-semibold">{sym}</span>,
            <span key="d" className="font-mono tabular-nums text-right block">{fmtPct1(e.vix_spike_decay_pct)}</span>,
            <span key="s" className="font-mono tabular-nums text-right block">{e.spike_event_count ?? 0}</span>,
            addSet.has(sym) ? (
              <span key="n" className="text-xs text-[color:var(--color-muted)]">{t(locale, "also_in_add")}</span>
            ) : (
              <span key="n" />
            ),
          ],
        }))}
      />
    </section>
  );
}

function watchEmptyMessage(entries: Entry[]): string {
  const valid = entries.filter(([, e]) => e.confidence !== "low");
  const recoveries = valid
    .map(([, e]) => e.vix_crush_recovery_pct)
    .filter((v): v is number => v != null);
  if (recoveries.length === 0) return "_no candidates fire crush > +0.6%_";
  const best = Math.max(...recoveries);
  return `_no candidates fire crush > +0.6% (best today: ${best >= 0 ? "+" : ""}${best.toFixed(2)}%)_`;
}

function avoidEmptyMessage(entries: Entry[]): string {
  const valid = entries.filter(([, e]) => e.confidence !== "low");
  const p25s = valid
    .map(([, e]) => e.vix_spike_decay_p25_pct)
    .filter((v): v is number => v != null);
  if (p25s.length === 0) return "_no candidates fire p25 decay < -4%_";
  const worst = Math.min(...p25s);
  return `_no candidates fire p25 decay < -4% (worst today: ${worst >= 0 ? "+" : ""}${worst.toFixed(2)}%)_`;
}

function SubRegion({
  title,
  filterDesc,
  columns,
  rows,
  emptyMessage,
}: {
  title: string;
  filterDesc: string;
  columns: string[];
  rows: { key: string; attrs?: Record<string, string>; cells: React.ReactNode[] }[];
  emptyMessage: string;
}) {
  return (
    <div
      className="rounded-lg border overflow-hidden"
      style={{ borderColor: "var(--color-border)", background: "var(--color-bg-surface)" }}
    >
      <div className="px-4 py-3 border-b flex items-baseline gap-2 flex-wrap"
           style={{ borderColor: "var(--color-border)" }}>
        <span className="font-semibold text-sm">{title}</span>
        <span className="text-xs italic text-[color:var(--color-muted)]">_({filterDesc})_</span>
      </div>
      <table className="w-full text-sm tabular-nums">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wider text-[color:var(--color-muted)]"
              style={{ borderColor: "var(--color-border)" }}>
            {columns.map((c, i) => (
              <th key={i} className={`px-4 py-2 font-medium ${i === 0 ? "" : "text-right"}`}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-3 text-xs italic text-[color:var(--color-muted)]">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((r) => (
              <tr
                key={r.key}
                {...(r.attrs ?? {})}
                className="border-b last:border-b-0"
                style={{ borderColor: "var(--color-border)" }}
              >
                {r.cells.map((c, i) => (
                  <td key={i} className="px-4 py-2">
                    {c}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
