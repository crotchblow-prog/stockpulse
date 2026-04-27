import Link from "next/link";
import { t, type Locale } from "@/lib/i18n";
import { COMPANY } from "@/lib/company";

/**
 * Site-wide legal nav footer — © line + four links to /about, /privacy,
 * /terms, mailto:contact. Rendered standalone on the legal pages and
 * embedded in V2Footer + the (learn) layout footer.
 */
export function LegalFooter({ lang }: { lang: Locale }) {
  const year = new Date().getFullYear();
  const company = lang === "zh" ? COMPANY.nameZh : COMPANY.nameEn;
  const brand = t(lang, "footer.copyright_brand");

  return (
    <footer
      className="mx-auto max-w-3xl px-6 py-10 text-xs text-[color:var(--color-muted)] border-t"
      style={{ borderColor: "var(--color-border)" }}
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>© {year} {company} · {brand}</div>
        <nav className="flex flex-wrap gap-x-3 gap-y-1">
          <Link href={`/${lang}/about`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {t(lang, "footer.about")}
          </Link>
          <Link href={`/${lang}/privacy`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {t(lang, "footer.privacy")}
          </Link>
          <Link href={`/${lang}/terms`} className="underline underline-offset-2 hover:text-[color:var(--color-fg)]">
            {t(lang, "footer.terms")}
          </Link>
          <a
            href={`mailto:${COMPANY.contactEmail}`}
            className="underline underline-offset-2 hover:text-[color:var(--color-fg)]"
          >
            {t(lang, "footer.contact")}
          </a>
        </nav>
      </div>
    </footer>
  );
}
