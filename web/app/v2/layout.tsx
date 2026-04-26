import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "VIXPulse v2 (preview)",
  description: "Phase 3.0 frontend redesign — gated /v2 preview during M1-M3.",
};

export default function V2Layout({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-v2-root
      style={{ background: "var(--color-bg-base)", minHeight: "100dvh" }}
      className="font-sans"
    >
      {children}
    </div>
  );
}
