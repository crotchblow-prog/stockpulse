import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { readReportJsonByDate } from "@/lib/reports";
import { loadVixHistory } from "@/lib/vix-history";
import { isLocale, t, type Locale } from "@/lib/i18n";
import { Hero } from "@/components/v2/Hero";
import { TodaysTake } from "@/components/v2/TodaysTake";
import { TierAction } from "@/components/v2/TierAction";
import { UniverseScanner } from "@/components/v2/UniverseScanner";
import { WatchList } from "@/components/v2/WatchList";
import { Holdings } from "@/components/v2/Holdings";
import { SnapshotGrid } from "@/components/v2/SnapshotGrid";
import { V2Footer } from "@/components/v2/V2Footer";
import { LangToggle } from "@/components/v2/LangToggle";
import { VixSparklineLazy } from "@/components/v2/VixSparklineLazy";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string; date: string }>;
}): Promise<Metadata> {
  const { lang, date } = await params;
  if (!isLocale(lang)) return {};
  return {
    alternates: {
      languages: {
        en: `/en/${date}`,
        "zh-Hant": `/zh/${date}`,
      },
    },
  };
}

export default async function V2DatedReport({
  params,
}: {
  params: Promise<{ lang: string; date: string }>;
}) {
  const { lang, date } = await params;
  if (!isLocale(lang)) notFound();
  const language: Locale = lang;

  const payload = await readReportJsonByDate(date, language);
  const history = await loadVixHistory(30, "en");

  if (!payload) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-[color:var(--color-muted)]">
          {t(language, "no_report_for_date", { date })}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
      <header className="flex items-center justify-between gap-3">
        <h1 className="text-base font-semibold tracking-tight font-mono">📊 VIXPulse</h1>
        <LangToggle current={language} pathSuffix={`/${date}`} />
      </header>
      <Hero payload={payload} lang={language} />
      <VixSparklineLazy
        data={history}
        currentTier={payload.tier.index}
        locale={language}
      />
      <TodaysTake synthesis={payload.synthesis} locale={language} />
      <TierAction tier={payload.tier} synthesis={payload.synthesis} locale={language} />
      <UniverseScanner
        universe={payload.regime_universe}
        tierIdx={payload.tier.index}
        tierAction={payload.tier.action}
        locale={language}
      />
      <WatchList holdings={payload.holdings} lang={language} />
      <Holdings holdings={payload.holdings} lang={language} />
      <SnapshotGrid snapshot={payload.snapshot} tierIndex={payload.tier.index} lang={language} />
      <V2Footer date={payload.date} lang={language} />
    </div>
  );
}
