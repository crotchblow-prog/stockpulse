import { ImageResponse } from "next/og";
import { readReportJsonByDate } from "@/lib/reports";

export const runtime = "nodejs";
export const alt = "VIX Pulse — daily VIX-tier US-market analysis";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const TIER_HEX: Record<number, string> = {
  0: "#3b82f6",
  1: "#06b6d4",
  2: "#a3a3a3",
  3: "#f59e0b",
  4: "#f97316",
  5: "#ef4444",
};

const TIER_ZH: Record<number, string> = {
  0: "休兵",
  1: "警戒佈局",
  2: "觀察",
  3: "分批進場",
  4: "恐慌承接",
  5: "極端機會",
};

export default async function OGImage({
  params,
}: {
  params: Promise<{ lang: string; date: string }>;
}) {
  const { lang: rawLang, date } = await params;
  const lang = rawLang === "zh" ? "zh" : "en";
  const payload = await readReportJsonByDate(date, lang);

  const tierIdx = payload?.tier?.index ?? 2;
  const tierColor = TIER_HEX[tierIdx] ?? TIER_HEX[2];
  const tierLabel = TIER_ZH[tierIdx] ?? "";
  const vixValue = payload?.vix_value ?? null;
  const holdingsCount = payload ? Object.keys(payload.holdings).length : 0;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: "#0a0a0b",
          padding: 60,
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          color: "#e6e8ee",
          position: "relative",
        }}
      >
        {/* Top: brand + date */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              {/* Tier-ladder logo (Satori works better with divs than inline SVG) */}
              <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 38 }}>
                <div style={{ width: 6, height: 8,  background: "#3b82f6", borderRadius: 1 }} />
                <div style={{ width: 6, height: 14, background: "#06b6d4", borderRadius: 1 }} />
                <div style={{ width: 6, height: 20, background: "#a3a3a3", borderRadius: 1 }} />
                <div style={{ width: 6, height: 26, background: "#f59e0b", borderRadius: 1 }} />
                <div style={{ width: 6, height: 32, background: "#f97316", borderRadius: 1 }} />
                <div style={{ width: 6, height: 38, background: "#ef4444", borderRadius: 1 }} />
              </div>
              <div style={{ fontSize: 36, fontWeight: 700, letterSpacing: 1 }}>VIX Pulse</div>
            </div>
            <div style={{ fontSize: 22, color: "#8a93a6", marginTop: 4 }}>{date}</div>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 24px",
              border: `2px solid ${tierColor}`,
              borderRadius: 8,
              fontSize: 24,
              fontWeight: 600,
              color: tierColor,
            }}
          >
            <span>Tier {tierIdx}</span>
            {tierLabel && <span style={{ color: "#e6e8ee" }}>{tierLabel}</span>}
          </div>
        </div>

        {/* Center: huge VIX */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            flex: 1,
          }}
        >
          <div style={{ fontSize: 28, color: "#8a93a6", marginBottom: 8 }}>VIX</div>
          <div
            style={{
              fontSize: 220,
              fontWeight: 800,
              letterSpacing: -6,
              fontFamily: "ui-monospace, monospace",
              color: "#e6e8ee",
              lineHeight: 1,
            }}
          >
            {vixValue != null ? vixValue.toFixed(2) : "—"}
          </div>
        </div>

        {/* Bottom: counts + zone */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            color: "#8a93a6",
            fontSize: 22,
            borderTop: "1px solid #2a2a30",
            paddingTop: 20,
          }}
        >
          <div style={{ display: "flex" }}>
            {`${holdingsCount} ${holdingsCount === 1 ? "holding" : "holdings"} · Asia/Taipei`}
          </div>
          <div style={{ display: "flex" }}>vixpulse.asia</div>
        </div>
      </div>
    ),
    { ...size }
  );
}
