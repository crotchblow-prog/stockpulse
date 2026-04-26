import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const LOCALES = new Set(["en", "zh"]);

export default async function V2LangIndex({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!LOCALES.has(lang)) notFound();

  return (
    <div data-tier="2" className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-6 flex items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">VIXPulse v2</h1>
        <Badge>preview</Badge>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>M1 foundation</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-[color:var(--color-muted)]">
          The new app boots. Locale: <code className="font-mono">{lang}</code>. Real
          report content lands in M2 — hero, watch list, holdings, snapshot grid.
        </CardContent>
      </Card>
    </div>
  );
}
