import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n";
import { COMPANY } from "@/lib/company";
import { LegalFooter } from "@/components/v2/LegalFooter";

export const dynamic = "force-static";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}): Promise<Metadata> {
  const { lang } = await params;
  if (!isLocale(lang)) return {};
  const isZh = lang === "zh";
  return {
    title: isZh ? "關於我們 — VIX Pulse" : "About — VIX Pulse",
    description: isZh
      ? "VIX Pulse 為沙灘紅酒有限公司旗下之資訊軟體產品。"
      : "VIX Pulse is published by Beach & Wne Co.",
  };
}

export default async function AboutPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!isLocale(lang)) notFound();
  const isZh = lang === "zh";

  return (
    <>
      <main className="mx-auto max-w-3xl px-6 py-10 text-[color:var(--color-fg)]">
        <header className="mb-10">
          <h1 className="text-3xl font-bold">{isZh ? "關於我們" : "About Us"}</h1>
          <p className="mt-2 text-[color:var(--color-muted)]">
            {isZh
              ? "VIX Pulse 為沙灘紅酒有限公司旗下之資訊軟體產品，提供以 VIX 為核心之美股決策參考。"
              : "VIX Pulse is a daily VIX-tier US-equity decision-support tool, published by Beach & Wne Co."}
          </p>
        </header>

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-3">
            {isZh ? "業務範圍" : "What we build"}
          </h2>
          <p className="text-sm leading-relaxed text-[color:var(--color-muted)]">
            {isZh
              ? "本公司登記業別為資訊軟體業（I301010）。VIX Pulse 以 VIX 六層級框架（Tier 0–5）為核心，每日從 yfinance 取得市場資料、由 Anthropic Claude 模型彙整觀點，產出免費可公開瀏覽之每日報告。所有軟體輸出皆為資訊性質，並非個人化投資建議，亦非交易買賣之勸誘。"
              : "Our registered business category is Information Software Services (I301010). VIX Pulse applies a six-tier VIX framework (Tier 0–5) to publicly traded US equities. Each day we ingest market data via yfinance, synthesise commentary with Anthropic Claude models, and publish a free daily report. All software output is informational only; it is not personalised investment advice, nor a solicitation to buy or sell."}
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-3">
            {isZh ? "產品與服務" : "Products & Services"}
          </h2>
          <ul className="space-y-3">
            <li
              className="rounded-xl border p-4"
              style={{
                borderColor: "var(--color-border)",
                background: "var(--color-bg-surface)",
              }}
            >
              <div className="font-semibold">
                {isZh ? "免費每日報告" : "Free daily report"}
              </div>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                {isZh
                  ? "於 vixpulse.asia 公開發佈每日 VIX Tier、市場快照、宇宙掃描與隨日綜合觀點，並另提供 /learn 解說頁。目前無任何付費方案。"
                  : "Daily VIX-tier read, market snapshot, universe scanner, and synthesised commentary at vixpulse.asia, plus the /learn explainer. No paid tiers today."}
              </p>
            </li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-3">
            {isZh ? "風險聲明" : "Risk Disclosure"}
          </h2>
          <div
            className="rounded-xl border p-5 text-sm leading-relaxed text-[color:var(--color-muted)]"
            style={{
              borderColor: "color-mix(in srgb, var(--color-danger) 30%, transparent)",
              background: "color-mix(in srgb, var(--color-danger) 5%, transparent)",
            }}
          >
            {isZh
              ? "投資公開上市之美國證券具有風險，可能導致部分或全部本金損失，並不適合所有投資人。VIX Pulse 所發布之所有軟體輸出（包括 VIX 層級判讀、宇宙掃描、綜合觀點及任何衍生指標）皆為資訊性質，並非個人化投資、稅務或法律建議。過去表現不代表未來結果。使用者應在理解相關風險並評估自身財務狀況後，方可進行任何投資決策。"
              : "Investing in publicly traded US securities carries risk and may result in the loss of some or all of your invested capital. It may not be suitable for every investor. All software output published by VIX Pulse — including VIX-tier reads, the universe scanner, synthesised commentary, and any derived indicators — is provided on an informational basis only and does not constitute personalised investment, tax, or legal advice. Past performance is not indicative of future results. You should invest only after you have fully understood the risks involved and assessed your own financial circumstances."}
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-3">
            {isZh ? "公司資訊" : "Company Information"}
          </h2>
          <div
            className="overflow-hidden rounded-xl border"
            style={{
              borderColor: "var(--color-border)",
              background: "var(--color-bg-surface)",
            }}
          >
            <dl
              className="divide-y text-sm"
              style={{ borderColor: "var(--color-border)" }}
            >
              <Row label={isZh ? "公司名稱" : "Legal name"}>
                <span className="font-medium">{isZh ? COMPANY.nameZh : COMPANY.nameEn}</span>
              </Row>
              <Row label={isZh ? "品牌" : "Brand"}>
                <span className="font-medium">VIX Pulse</span>
              </Row>
              <Row label={isZh ? "註冊編號" : "Registration number"}>
                <span className="font-mono">{COMPANY.regNumber}</span>
              </Row>
              <Row label={isZh ? "註冊地" : "Jurisdiction"}>
                {isZh ? COMPANY.jurisdictionZh : COMPANY.jurisdictionEn}
              </Row>
              <Row label={isZh ? "設立日期" : "Incorporated"}>
                {COMPANY.incorporationDate}
              </Row>
              <Row label={isZh ? "註冊地址" : "Registered address"}>
                {isZh ? COMPANY.addressZh : COMPANY.addressEn}
              </Row>
              <Row label={isZh ? "負責人" : "Responsible officer"}>
                {isZh
                  ? `${COMPANY.founderZh} — ${COMPANY.founderTitleZh}`
                  : `${COMPANY.founderEn} — ${COMPANY.founderTitleEn}`}
              </Row>
              <Row label={isZh ? "網站" : "Website"}>
                <a
                  href={COMPANY.websiteUrl}
                  className="underline text-[color:var(--color-accent)]"
                >
                  {COMPANY.websiteUrl}
                </a>
              </Row>
              <Row label={isZh ? "聯絡電郵" : "Contact email"}>
                <a
                  href={`mailto:${COMPANY.contactEmail}`}
                  className="underline text-[color:var(--color-accent)]"
                >
                  {COMPANY.contactEmail}
                </a>
              </Row>
            </dl>
          </div>
        </section>

        <section className="mb-4">
          <h2 className="text-xl font-bold mb-3">
            {isZh ? "聯絡我們" : "Contact"}
          </h2>
          <p className="text-sm text-[color:var(--color-muted)]">
            {isZh ? (
              <>
                一般諮詢、媒體合作及使用者支援請寄至{" "}
                <a
                  href={`mailto:${COMPANY.contactEmail}`}
                  className="underline text-[color:var(--color-accent)]"
                >
                  {COMPANY.contactEmail}
                </a>
                。所有電郵通常在兩個工作日內回覆。
              </>
            ) : (
              <>
                For general inquiries, partnership requests, or user support, please email{" "}
                <a
                  href={`mailto:${COMPANY.contactEmail}`}
                  className="underline text-[color:var(--color-accent)]"
                >
                  {COMPANY.contactEmail}
                </a>
                . We aim to reply within two business days.
              </>
            )}
          </p>
        </section>

        <p
          className="mt-10 border-t pt-4 text-xs text-[color:var(--color-muted)]"
          style={{ borderColor: "var(--color-border)" }}
        >
          {isZh
            ? "本頁最後更新於 2026 年 4 月 27 日。"
            : "Page last updated 27 April 2026."}
        </p>
      </main>
      <LegalFooter lang={lang} />
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-4 px-5 py-3">
      <dt className="w-48 shrink-0 text-[color:var(--color-muted)]">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
