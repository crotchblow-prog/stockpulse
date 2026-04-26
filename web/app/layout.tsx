import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://vixpulse.asia"),
  title: "VIXPulse",
  description: "Daily VIX-tier US-market analysis",
  alternates: { canonical: "/" },
  openGraph: {
    title: "VIXPulse",
    description: "Daily VIX-tier US-market analysis",
    url: "https://vixpulse.asia",
    siteName: "VIXPulse",
    locale: "zh_Hant",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "VIXPulse",
    description: "Daily VIX-tier US-market analysis",
  },
};

/**
 * Minimal root after M4 cutover. The chrome (header, footer, brand) lives
 * in each area's own layout: web/app/(default)/layout.tsx for /learn,
 * web/app/[lang]/layout.tsx for the new report pages, web/app/legacy/layout.tsx
 * for the Phase 1 escape hatch. This isolates v2's `[data-v2-root]`
 * from the legacy chrome and lets each area set its own background.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-Hant" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-dvh">{children}</body>
    </html>
  );
}
