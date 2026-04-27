import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n";
import { COMPANY } from "@/lib/company";
import { LegalFooter } from "@/components/v2/LegalFooter";

export const dynamic = "force-static";

const GOVERNING_LAW_EN = "Taiwan (R.O.C.)";
const GOVERNING_LAW_ZH = "中華民國";
const JURISDICTION_COURTS_EN = "Taiwan New Taipei District Court";
const JURISDICTION_COURTS_ZH = "臺灣新北地方法院";
const EFFECTIVE_DATE_EN = "27 April 2026";
const EFFECTIVE_DATE_ZH = "2026 年 4 月 27 日";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}): Promise<Metadata> {
  const { lang } = await params;
  if (!isLocale(lang)) return {};
  const isZh = lang === "zh";
  return {
    title: isZh ? "服務條款 — VIX Pulse" : "Terms of Service — VIX Pulse",
    description: isZh
      ? "VIX Pulse 服務條款。"
      : "VIX Pulse terms of service.",
  };
}

export default async function TermsPage({
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
        <header className="mb-8">
          <h1 className="text-3xl font-bold">
            {isZh ? "服務條款" : "Terms of Service"}
          </h1>
          <p className="mt-2 text-xs text-[color:var(--color-muted)]">
            {isZh
              ? `生效日期：${EFFECTIVE_DATE_ZH}`
              : `Effective: ${EFFECTIVE_DATE_EN}`}
          </p>
        </header>

        <div
          className="mb-8 rounded-xl border p-5 text-sm leading-relaxed text-[color:var(--color-muted)]"
          style={{
            borderColor: "color-mix(in srgb, var(--color-danger) 40%, transparent)",
            background: "color-mix(in srgb, var(--color-danger) 5%, transparent)",
          }}
        >
          <strong className="mb-2 block text-[color:var(--color-danger)]">
            {isZh ? "重要風險聲明" : "Important Risk Disclosure"}
          </strong>
          {isZh
            ? "投資公開上市之美國證券具有風險，可能導致部分或全部本金損失，並不適合所有投資人。VIX Pulse 所發布之所有軟體輸出（包括 VIX 層級判讀、宇宙掃描及綜合觀點）僅屬資訊性質，不構成個人化投資、稅務或法律建議。過去表現不代表未來結果。請於充分理解相關風險並評估自身財務狀況後，自行作出投資決定。"
            : "Investing in publicly traded US securities carries risk and may result in the loss of some or all of your invested capital. It may not be suitable for every investor. All software output published by VIX Pulse — including VIX-tier reads, the universe scanner, and synthesised commentary — is provided on an informational basis only and does not constitute personalised investment, tax, or legal advice. Past performance is not indicative of future results."}
        </div>

        <div className="space-y-6 text-sm leading-relaxed text-[color:var(--color-muted)]">
          <section>
            <H2>{`1. ${isZh ? "條款接受" : "Acceptance"}`}</H2>
            <p>
              {isZh
                ? `使用 vixpulse.asia（「本服務」）即代表您同意受本服務條款（「本條款」）及所引用之所有政策約束。本條款構成您與 ${COMPANY.nameZh}（「本公司」、「我們」）之間之具法律效力契約。若您不同意本條款，請勿使用本服務。`
                : `By accessing vixpulse.asia (the "Service"), you agree to be bound by these Terms of Service (the "Terms") and any policies referenced herein. These Terms constitute a legally binding agreement between you and ${COMPANY.nameEn} ("we", "us"). If you do not agree, do not use the Service.`}
            </p>
          </section>

          <section>
            <H2>{`2. ${isZh ? "資格" : "Eligibility"}`}</H2>
            <p>
              {isZh
                ? "您須年滿 18 歲，且於您所在司法管轄區具完全行為能力並合法取得及使用本服務。您有責任確保您之使用符合您當地法律。"
                : "You must be at least 18 years old and legally able to access and use the Service in your jurisdiction. You are responsible for ensuring that your use of the Service complies with your local laws."}
            </p>
          </section>

          <section>
            <H2>{`3. ${isZh ? "服務內容" : "Services"}`}</H2>
            <p>
              {isZh
                ? "VIX Pulse 為本公司所開發之資訊軟體產品，採 VIX 六層級框架對美國公開上市證券提供每日決策參考報告。"
                : "VIX Pulse is a software product publishing daily VIX-tier US-equity decision-support reports developed by the company."}
            </p>
            <p className="mt-2">
              {isZh
                ? "本服務之所有軟體輸出僅供資訊用途，不構成投資建議或買賣任何金融商品之勸誘。"
                : "All software output is provided for informational purposes only and does not constitute investment advice or a solicitation to buy or sell any financial instrument."}
            </p>
          </section>

          <section>
            <H2>{`4. ${isZh ? "可接受之使用" : "Acceptable Use"}`}</H2>
            <p>{isZh ? "您同意不為下列目的使用本服務：" : "You agree not to:"}</p>
            <ul className="mt-2 list-disc space-y-1 pl-6">
              <li>
                {isZh
                  ? "未經授權存取、擷取或複製本服務之內容、警報或資料。"
                  : "scrape, crawl, or otherwise extract content, alerts, or data from the Service without authorisation;"}
              </li>
              <li>
                {isZh
                  ? "規避任何存取限制。"
                  : "circumvent any access control;"}
              </li>
              <li>
                {isZh
                  ? "在您當地司法管轄區違反任何適用法律之下使用本服務。"
                  : "use the Service in violation of any applicable law in your jurisdiction."}
              </li>
            </ul>
          </section>

          <section>
            <H2>{`5. ${isZh ? "智慧財產權" : "Intellectual Property"}`}</H2>
            <p>
              {isZh
                ? "本服務之所有內容（包括文字、圖表、演算法、商標及使用者介面設計）為本公司或其授權人之財產，受著作權及其他智慧財產法令保護。除依本條款明示授予之有限使用權外，不授予任何其他權利。"
                : "All content on the Service (including text, charts, algorithms, trademarks, and UI design) is the property of the company or its licensors and is protected by copyright and other intellectual-property laws. No rights are granted other than the limited rights of use expressly stated in these Terms."}
            </p>
          </section>

          <section>
            <H2>{`6. ${isZh ? "免責聲明" : "Disclaimer of Warranties"}`}</H2>
            <p>
              {isZh
                ? "本服務以「現狀」及「現有」基礎提供，不附有任何明示或默示之擔保，包括但不限於適售性、特定目的適用性、準確性、可靠性或不侵權等擔保。在法律允許之最大範圍內，本公司不就服務內容之準確性、及時性、完整性，或就基於 VIX 層級框架之輸出所衍生之任何投資結果作任何擔保。"
                : "The Service is provided on an \"as is\" and \"as available\" basis without warranties of any kind, whether express or implied, including warranties of merchantability, fitness for a particular purpose, accuracy, reliability, or non-infringement. To the maximum extent permitted by law we disclaim all warranties regarding the accuracy, timeliness, or completeness of any content, or any investment outcomes derived from publicly traded US securities and VIX-tier framework output."}
            </p>
          </section>

          <section>
            <H2>{`7. ${isZh ? "責任限制" : "Limitation of Liability"}`}</H2>
            <p>
              {isZh
                ? "在法律允許之最大範圍內，本公司、其董事、員工及承包商就任何間接、附帶、衍生性、懲罰性或特殊損害（包括但不限於利潤損失、交易虧損、資料遺失或商譽損失）概不負責，無論該等損害係基於契約、侵權或其他法律依據。本公司對於與本服務相關之全部累計責任，以您於前十二（12）個月內實際向本公司支付之金額為上限。"
                : "To the maximum extent permitted by law, the company, its directors, employees, and contractors shall not be liable for any indirect, incidental, consequential, punitive, or special damages (including but not limited to lost profits, trading losses, loss of data, or loss of goodwill), whether based on contract, tort, or any other legal theory. Our total aggregate liability in connection with the Service is limited to the amount you actually paid us in the preceding twelve (12) months."}
            </p>
          </section>

          <section>
            <H2>{`8. ${isZh ? "使用者賠償責任" : "Indemnification"}`}</H2>
            <p>
              {isZh
                ? "您同意就因您之使用本服務、違反本條款或侵害任何第三方權利所引起之任何索賠、損害、損失、責任、成本及費用（包括合理律師費），對本公司予以賠償並使其免受損害。"
                : "You agree to indemnify and hold harmless the company from and against any claim, damage, loss, liability, cost, or expense (including reasonable legal fees) arising out of your use of the Service, your breach of these Terms, or your violation of any third-party right."}
            </p>
          </section>

          <section>
            <H2>{`9. ${isZh ? "終止" : "Termination"}`}</H2>
            <p>
              {isZh
                ? "若您違反本條款，本公司得隨時暫停或終止您對本服務之存取。您得隨時停止使用本服務。條款中依其性質應於終止後繼續有效之規定（包括第 5、6、7、8、10 條）將繼續有效。"
                : "We may suspend or terminate your access to the Service at any time if you breach these Terms. You may stop using the Service at any time. Sections that by their nature should survive termination (including 5, 6, 7, 8, and 10) will continue in force."}
            </p>
          </section>

          <section>
            <H2>{`10. ${isZh ? "準據法與管轄" : "Governing Law & Jurisdiction"}`}</H2>
            <p>
              {isZh ? (
                <>
                  本條款及任何相關爭議適用 {GOVERNING_LAW_ZH} 之法律，不考慮其法律衝突原則。各方同意將任何爭議提交 {JURISDICTION_COURTS_ZH} 之法院專屬管轄。
                </>
              ) : (
                <>
                  These Terms and any dispute arising out of them are governed by the
                  laws of {GOVERNING_LAW_EN}, without regard to conflict-of-laws
                  principles. The parties submit to the exclusive jurisdiction of the
                  courts of {JURISDICTION_COURTS_EN}.
                </>
              )}
            </p>
          </section>

          <section>
            <H2>{`11. ${isZh ? "條款修訂" : "Changes"}`}</H2>
            <p>
              {isZh
                ? "本公司得不時修訂本條款。重大修訂將於本頁公告，並以電子郵件通知現有訂戶。持續使用本服務即視為接受修訂後之條款。"
                : "We may update these Terms from time to time. Material changes will be posted on this page and, for existing subscribers, notified by email. Continued use of the Service constitutes acceptance of the updated Terms."}
            </p>
          </section>

          <section>
            <H2>{`12. ${isZh ? "聯絡我們" : "Contact"}`}</H2>
            <p>
              {isZh ? "條款相關事宜請寄至 " : "For any question about these Terms, please email "}
              <a
                href={`mailto:${COMPANY.contactEmail}`}
                className="underline text-[color:var(--color-accent)]"
              >
                {COMPANY.contactEmail}
              </a>
              {isZh ? "。公司登記資料請見 " : ". Registration details are on the "}
              <Link
                href={`/${lang}/about`}
                className="underline text-[color:var(--color-accent)]"
              >
                {isZh ? "關於我們" : "About"}
              </Link>{" "}
              {isZh ? "頁面。" : "page."}
            </p>
          </section>
        </div>
      </main>
      <LegalFooter lang={lang} />
    </>
  );
}

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-2 text-lg font-bold text-[color:var(--color-fg)]">{children}</h2>;
}
