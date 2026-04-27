import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n";
import { COMPANY } from "@/lib/company";
import { LegalFooter } from "@/components/v2/LegalFooter";

export const dynamic = "force-static";

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
    title: isZh ? "隱私權政策 — VIX Pulse" : "Privacy Policy — VIX Pulse",
    description: isZh
      ? "VIX Pulse 隱私權政策。"
      : "VIX Pulse privacy policy.",
  };
}

export default async function PrivacyPage({
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
            {isZh ? "隱私權政策" : "Privacy Policy"}
          </h1>
          <p className="mt-2 text-xs text-[color:var(--color-muted)]">
            {isZh
              ? `生效日期：${EFFECTIVE_DATE_ZH}`
              : `Effective: ${EFFECTIVE_DATE_EN}`}
          </p>
        </header>

        <div className="space-y-6 text-sm leading-relaxed text-[color:var(--color-muted)]">
          <section>
            <H2>{`1. ${isZh ? "本政策涵蓋範圍" : "Scope"}`}</H2>
            <p>
              {isZh ? (
                <>
                  本政策說明 {COMPANY.nameZh}（以下簡稱「本公司」、「我們」）如何於
                  vixpulse.asia 及其子網域（以下簡稱「本服務」）收集、使用及保護使用者之個人資料。
                </>
              ) : (
                <>
                  This Privacy Policy explains how {COMPANY.nameEn} (&quot;we&quot;,
                  &quot;us&quot;) collects, uses, and protects personal information on
                  vixpulse.asia and its subdomains (the &quot;Service&quot;).
                </>
              )}
            </p>
          </section>

          <section>
            <H2>{`2. ${isZh ? "我們收集的資料" : "Information we collect"}`}</H2>
            <p className="mb-3">
              {isZh
                ? "目前 VIX Pulse 不提供註冊或登入功能，亦不收取任何付款。我們僅處理以下最低限度之資料："
                : "VIX Pulse currently provides no sign-up or login flow, and processes no payments. We handle only the following minimum data:"}
            </p>
            <ul className="list-disc space-y-2 pl-6">
              <li>
                <strong className="text-[color:var(--color-fg)]">
                  {isZh ? "偏好設定" : "Preferences"}
                </strong>
                —{" "}
                {isZh
                  ? "您所選之語言（英文／中文）儲存於您瀏覽器之 localStorage 中，不會傳送至伺服器。"
                  : "your selected language (English/Chinese) is stored in your browser's localStorage and is not sent to our servers."}
              </li>
              <li>
                <strong className="text-[color:var(--color-fg)]">
                  {isZh ? "伺服器記錄" : "Server logs"}
                </strong>
                —{" "}
                {isZh
                  ? "我們的託管服務供應商 Vercel 會記錄標準存取日誌（IP 位址、User-Agent、時間戳記），用於維護系統安全及偵錯，依其預設政策保留。"
                  : "our hosting provider Vercel records standard access logs (IP address, user agent, timestamps) for security and debugging, retained per its default policy."}
              </li>
              <li>
                <strong className="text-[color:var(--color-fg)]">
                  {isZh ? "帳號資料" : "Account data"}
                </strong>
                —{" "}
                {isZh
                  ? "我們目前不收集任何帳號資料，因本服務尚無註冊機制。"
                  : "we currently do not collect any account data — there is no sign-up."}
              </li>
            </ul>
          </section>

          <section>
            <H2>{`3. ${isZh ? "資料使用目的" : "How we use your information"}`}</H2>
            <ul className="list-disc space-y-1 pl-6">
              <li>{isZh ? "提供本服務並維持其穩定運作。" : "To operate the Service and keep it running reliably."}</li>
              <li>
                {isZh
                  ? "維護服務之安全性並防範濫用。"
                  : "To maintain the security of the Service and prevent abuse."}
              </li>
              <li>
                {isZh
                  ? "履行法律、會計及稅務義務。"
                  : "To comply with legal, accounting, and tax obligations."}
              </li>
            </ul>
            <p className="mt-3">
              {isZh
                ? "我們不會將任何個人資料出售或出租予第三方。我們亦不向使用者寄送行銷郵件。"
                : "We do not sell or rent personal information to any third party, and we do not send marketing emails."}
            </p>
          </section>

          <section>
            <H2>{`4. ${isZh ? "第三方服務提供者" : "Third-party processors"}`}</H2>
            <p>
              {isZh
                ? "為營運本服務，我們僅使用下列外部處理者。各該供應商在其個別政策下處理資料："
                : "To operate the Service we rely on the following external processors. Each handles data under its own policy:"}
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-6">
              <li>
                <strong className="text-[color:var(--color-fg)]">Vercel</strong> —{" "}
                {isZh ? "網站託管及邊緣運算。" : "website hosting and edge compute."}
              </li>
              <li>
                <strong className="text-[color:var(--color-fg)]">GitHub</strong> —{" "}
                {isZh
                  ? "本專案原始碼公開託管於 GitHub。"
                  : "the project source is hosted publicly on GitHub."}
              </li>
            </ul>
          </section>

          <section>
            <H2>{`5. ${isZh ? "資料保留期限" : "Data retention"}`}</H2>
            <p>
              {isZh
                ? "由於本服務不收集帳號資料，我們亦無使用者紀錄可保留。伺服器存取日誌由 Vercel 依其預設政策保留。"
                : "Because we do not collect account data, we have no user records to retain. Server access logs are retained by Vercel under its default policy."}
            </p>
          </section>

          <section>
            <H2>{`6. ${isZh ? "您的權利" : "Your rights"}`}</H2>
            <p>
              {isZh
                ? "依照您所在地區之適用法律（包括但不限於 GDPR、英國 GDPR、加州 CCPA、香港個資條例及台灣個資法），您就您的個人資料享有下列權利："
                : "Subject to applicable law in your region (including but not limited to the GDPR, UK GDPR, California CCPA, Hong Kong PDPO, Taiwan PDPA), you have the following rights over your personal information:"}
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-6">
              <li>{isZh ? "存取及取得副本" : "Access and obtain a copy"}</li>
              <li>{isZh ? "更正不正確之資料" : "Rectify inaccurate data"}</li>
              <li>{isZh ? "請求刪除" : "Request deletion"}</li>
              <li>{isZh ? "反對或限制處理" : "Object to or restrict processing"}</li>
              <li>{isZh ? "撤回先前給予之同意" : "Withdraw consent previously given"}</li>
              <li>
                {isZh ? "向主管機關提出申訴" : "Lodge a complaint with a supervisory authority"}
              </li>
            </ul>
            <p className="mt-3">
              {isZh ? (
                <>
                  行使上述權利請來信{" "}
                  <a
                    href={`mailto:${COMPANY.contactEmail}`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    {COMPANY.contactEmail}
                  </a>
                  ，我們將於 30 日內回覆。
                </>
              ) : (
                <>
                  To exercise any of these rights, please email{" "}
                  <a
                    href={`mailto:${COMPANY.contactEmail}`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    {COMPANY.contactEmail}
                  </a>
                  . We will respond within 30 days.
                </>
              )}
            </p>
          </section>

          <section>
            <H2>{`7. ${isZh ? "資料安全" : "Security"}`}</H2>
            <p>
              {isZh
                ? "我們透過 Vercel 之平台層級控制及業界標準之 TLS 傳輸加密來保護本服務。儘管如此，網際網路傳輸無法保證絕對安全。若發生資料外洩事件，我們將依適用法律通知受影響之使用者及主管機關。"
                : "We protect the Service through Vercel's platform-level controls and industry-standard TLS encryption in transit. No internet transmission is perfectly secure. In the event of a data breach, we will notify affected users and supervisory authorities as required by applicable law."}
            </p>
          </section>

          <section>
            <H2>{`8. ${isZh ? "跨境資料傳輸" : "International data transfers"}`}</H2>
            <p>
              {isZh ? (
                <>
                  本公司設於 {COMPANY.jurisdictionZh}
                  。Vercel 可能於全球邊緣節點儲存及供應本服務之內容，相關內容將適用該等司法管轄區之法律。
                </>
              ) : (
                <>
                  The Service is operated from {COMPANY.jurisdictionEn}. Vercel may store
                  and serve content from edge nodes globally, subject to the laws of
                  those jurisdictions.
                </>
              )}
            </p>
          </section>

          <section>
            <H2>{`9. ${isZh ? "兒童隱私" : "Children"}`}</H2>
            <p>
              {isZh
                ? "本服務不針對 18 歲以下之個人提供。若您未滿 18 歲，請勿使用本服務或向我們提供任何個人資料。"
                : "The Service is not directed at individuals under 18. If you are under 18, please do not use the Service or provide us with any personal information."}
            </p>
          </section>

          <section>
            <H2>{`10. ${isZh ? "政策修訂" : "Changes to this policy"}`}</H2>
            <p>
              {isZh
                ? "我們可能不時修訂本政策。任何重大變更將於本頁面公告，並以電子郵件通知現有訂戶。"
                : "We may update this policy from time to time. Material changes will be posted on this page and, for existing subscribers, notified by email."}
            </p>
          </section>

          <section>
            <H2>{`11. ${isZh ? "聯絡我們" : "Contact"}`}</H2>
            <p>
              {isZh ? (
                <>
                  關於本政策或您個人資料之任何疑問，請寄至{" "}
                  <a
                    href={`mailto:${COMPANY.contactEmail}`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    {COMPANY.contactEmail}
                  </a>
                  ，或參閱{" "}
                  <Link
                    href={`/${lang}/about`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    關於我們
                  </Link>
                  {" "}頁所列之公司地址。
                </>
              ) : (
                <>
                  For any question about this policy or your personal information,
                  please email{" "}
                  <a
                    href={`mailto:${COMPANY.contactEmail}`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    {COMPANY.contactEmail}
                  </a>
                  , or refer to the postal address listed on the{" "}
                  <Link
                    href={`/${lang}/about`}
                    className="underline text-[color:var(--color-accent)]"
                  >
                    About
                  </Link>{" "}
                  page.
                </>
              )}
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
