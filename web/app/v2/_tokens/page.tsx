import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const TIERS = [
  { idx: 0, label: "休兵", desc: "rest", vix: "<15", color: "var(--color-tier-0)" },
  { idx: 1, label: "警戒佈局", desc: "cautious", vix: "15–18", color: "var(--color-tier-1)" },
  { idx: 2, label: "觀察", desc: "watch", vix: "18–24.6", color: "var(--color-tier-2)" },
  { idx: 3, label: "分批進場", desc: "scale in", vix: "24.6–29.5", color: "var(--color-tier-3)" },
  { idx: 4, label: "恐慌承接", desc: "catch panic", vix: "29.5–35", color: "var(--color-tier-4)" },
  { idx: 5, label: "極端機會", desc: "extreme", vix: ">35", color: "var(--color-tier-5)" },
];

export default function TokensDemo() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Design tokens</h1>
        <p className="mt-2 text-sm text-[color:var(--color-muted)]">
          Tier color ramp, surfaces, fonts. Used to eyeball M1 tokens before M2 builds on them.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-medium mb-3">Tier ramp</h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {TIERS.map((t) => (
            <div
              key={t.idx}
              data-tier={t.idx}
              className="flex items-center justify-between rounded-lg border p-3"
              style={{ borderColor: t.color }}
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm">Tier {t.idx}</span>
                <span className="text-sm">{t.label}</span>
                <span className="text-xs text-[color:var(--color-muted)]">({t.desc})</span>
              </div>
              <span className="font-mono text-xs text-[color:var(--color-muted)]">VIX {t.vix}</span>
            </div>
          ))}
        </div>
      </section>

      <Separator />

      <section>
        <h2 className="text-lg font-medium mb-3">shadcn primitives</h2>
        <div className="flex flex-wrap items-center gap-3">
          <Button>Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Badge>Badge</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
      </section>

      <Separator />

      <section>
        <h2 className="text-lg font-medium mb-3">Card</h2>
        <Card>
          <CardHeader>
            <CardTitle>Sample card</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <p className="leading-7">
              Prose uses <span className="font-sans">Inter</span>. Numerics use{" "}
              <span className="font-mono">JetBrains Mono — 0123456789</span>.
            </p>
          </CardContent>
        </Card>
      </section>

      <Separator />

      <section>
        <h2 className="text-lg font-medium mb-3">Surfaces</h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <div
            className="rounded-lg border p-4"
            style={{ background: "var(--color-bg-base)", borderColor: "var(--color-border)" }}
          >
            <div className="text-xs text-[color:var(--color-muted)]">--bg-base</div>
            <div className="font-mono text-xs">#0a0a0b</div>
          </div>
          <div
            className="rounded-lg border p-4"
            style={{ background: "var(--color-bg-surface)", borderColor: "var(--color-border)" }}
          >
            <div className="text-xs text-[color:var(--color-muted)]">--bg-surface</div>
            <div className="font-mono text-xs">#111114</div>
          </div>
          <div
            className="rounded-lg border p-4"
            style={{ background: "var(--color-bg-elevated)", borderColor: "var(--color-border)" }}
          >
            <div className="text-xs text-[color:var(--color-muted)]">--bg-elevated</div>
            <div className="font-mono text-xs">#16161a</div>
          </div>
        </div>
      </section>
    </div>
  );
}
