/**
 * Numeric formatters for v2 — keep mono-friendly digit-glyph alignment.
 * All numerics in the UI render via these so signs / decimal places stay
 * consistent across Hero / Holdings / Snapshot.
 */

export function fmtPrice(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  if (Math.abs(v) >= 1000) {
    return v.toLocaleString("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
  return v.toFixed(digits);
}

export function fmtPct(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${(v * 100).toFixed(digits)}%`;
}

export function fmtSignedNum(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(digits)}`;
}

export function fmtRsi(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(0);
}
