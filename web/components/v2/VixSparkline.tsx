"use client";

import {
  LineChart,
  Line,
  ReferenceArea,
  YAxis,
  XAxis,
  Dot,
  ResponsiveContainer,
} from "recharts";
import type { VixPoint } from "@/lib/vix-history";
import type { Locale } from "@/lib/i18n";
import { t } from "@/lib/i18n";

const TIER_BANDS = [
  { from: 0, to: 15, color: "var(--color-tier-0)" },
  { from: 15, to: 18, color: "var(--color-tier-1)" },
  { from: 18, to: 24.6, color: "var(--color-tier-2)" },
  { from: 24.6, to: 29.5, color: "var(--color-tier-3)" },
  { from: 29.5, to: 35, color: "var(--color-tier-4)" },
  { from: 35, to: 100, color: "var(--color-tier-5)" },
];

export function VixSparkline({
  data,
  currentTier,
  locale,
}: {
  data: VixPoint[];
  currentTier: number;
  locale: Locale;
}) {
  if (data.length === 0) {
    return null;
  }

  const last = data[data.length - 1];
  const high = data.reduce((a, p) => (p.vix > a.vix ? p : a), data[0]);
  const low = data.reduce((a, p) => (p.vix < a.vix ? p : a), data[0]);

  // Y-axis range: snap to a bit beyond min/max so the line doesn't kiss the edges.
  const yMin = Math.max(0, Math.floor(low.vix) - 2);
  const yMax = Math.ceil(high.vix) + 2;

  const tierVar = `var(--color-tier-${currentTier})`;

  return (
    <section
      className="space-y-3"
      data-component="vix-sparkline"
      data-tier={currentTier}
    >
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <h2 className="text-lg font-medium">{t(locale, "vix_history")}</h2>
        <div className="text-xs font-mono text-[color:var(--color-muted)] tabular-nums">
          <span>
            {t(locale, "spark_30d_high")}: {high.vix.toFixed(2)}
          </span>
          <span className="mx-2">·</span>
          <span>
            {t(locale, "spark_30d_low")}: {low.vix.toFixed(2)}
          </span>
          <span className="mx-2">·</span>
          <span>
            {t(locale, "spark_today")}: <span className="font-semibold">{last.vix.toFixed(2)}</span>
          </span>
        </div>
      </div>

      <div
        className="rounded-lg border p-4"
        style={{
          borderColor: "var(--color-border)",
          background: "var(--color-bg-surface)",
          aspectRatio: "16 / 5",
          minHeight: "180px",
        }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 8, right: 16, bottom: 4, left: 4 }}
          >
            {TIER_BANDS.map((band, i) => (
              <ReferenceArea
                key={i}
                y1={band.from}
                y2={band.to}
                fill={band.color}
                fillOpacity={0.05}
                strokeOpacity={0}
              />
            ))}
            <YAxis
              type="number"
              domain={[yMin, yMax]}
              tick={{ fontSize: 10, fill: "var(--color-muted)" }}
              axisLine={false}
              tickLine={false}
              width={32}
            />
            <XAxis dataKey="date" hide />
            <Line
              type="monotone"
              dataKey="vix"
              stroke="var(--color-muted)"
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
            {/* Right-end dot in tier-current color */}
            <Line
              type="monotone"
              dataKey="vix"
              stroke="transparent"
              dot={(props: { cx?: number; cy?: number; index?: number }) => {
                if (props.index !== data.length - 1 || props.cx == null || props.cy == null) {
                  return <g key={`empty-${props.index ?? "x"}`} />;
                }
                return (
                  <Dot
                    key="end-dot"
                    cx={props.cx}
                    cy={props.cy}
                    r={4}
                    fill={tierVar}
                    stroke={tierVar}
                  />
                );
              }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
