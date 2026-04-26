import { notFound } from "next/navigation";
import { readReportJsonByDate } from "@/lib/reports";
import { Hero } from "@/components/v2/Hero";
import { WatchList } from "@/components/v2/WatchList";
import { Holdings } from "@/components/v2/Holdings";
import { SnapshotGrid } from "@/components/v2/SnapshotGrid";
import { V2Footer } from "@/components/v2/V2Footer";

const LOCALES = new Set(["en", "zh"]);

export default async function V2LangIndex({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!LOCALES.has(lang)) notFound();
  const language = lang as "en" | "zh";

  const payload = await readReportJsonByDate("latest", language);
  if (!payload) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-[color:var(--color-muted)]">
          {language === "zh"
            ? "尚無報告。每日 cron 將於 22:00 Asia/Taipei 產出。"
            : "No report yet. The daily cron runs at 22:00 Asia/Taipei."}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
      <Hero payload={payload} lang={language} />
      <WatchList holdings={payload.holdings} lang={language} />
      <Holdings holdings={payload.holdings} lang={language} />
      <SnapshotGrid snapshot={payload.snapshot} tierIndex={payload.tier.index} lang={language} />
      <V2Footer date={payload.date} lang={language} />
    </div>
  );
}
