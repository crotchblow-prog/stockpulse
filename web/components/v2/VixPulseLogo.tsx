/**
 * VIXPulse logo — six tier-colored bars in ascending height.
 *
 * Variants:
 *  - `currentTier == null` (default): all six bars at full opacity. Used for
 *    favicon, /learn header, OG card, and any context that lacks a "today's tier."
 *  - `currentTier` 0–5: only that bar at full opacity, others dim. Used in the
 *    report-page header so the logo IS today's regime.
 *
 * Tier colors are locked in PROJECT_BRIEF §11 design system:
 *   0 cobalt blue · 1 cyan · 2 neutral gray · 3 amber · 4 orange-red · 5 alert red
 */
const TIERS: { color: string; h: number }[] = [
  { color: "#3b82f6", h: 4 },
  { color: "#06b6d4", h: 7 },
  { color: "#a3a3a3", h: 10 },
  { color: "#f59e0b", h: 13 },
  { color: "#f97316", h: 16 },
  { color: "#ef4444", h: 19 },
];

export function VixPulseLogo({
  currentTier = null,
  size = 24,
  className,
}: {
  currentTier?: number | null;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label="VIXPulse"
    >
      {TIERS.map((t, i) => (
        <rect
          key={i}
          x={i * 4}
          y={24 - t.h}
          width={3}
          height={t.h}
          rx={0.5}
          fill={t.color}
          opacity={currentTier == null ? 1 : i === currentTier ? 1 : 0.25}
        />
      ))}
    </svg>
  );
}
