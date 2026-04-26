import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const LOCALES = new Set(["en", "zh"]);

export default async function V2DatedReport({
  params,
}: {
  params: Promise<{ lang: string; date: string }>;
}) {
  const { lang, date } = await params;
  if (!LOCALES.has(lang)) notFound();

  return (
    <div data-tier="2" className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-6 flex items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">VIXPulse v2 — {date}</h1>
        <Badge>preview</Badge>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>M1 foundation</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-[color:var(--color-muted)]">
          Single-date placeholder. Locale: <code className="font-mono">{lang}</code>.
          Date: <code className="font-mono">{date}</code>. Real content lands in M2.
        </CardContent>
      </Card>
    </div>
  );
}
