import { LearnPage } from "@/components/learn/LearnPage";

export const dynamic = "force-static";

export const metadata = {
  title: "入門 — VIX Pulse",
  description: "VIX 是什麼、六個 Tier 框架、以及如何讀懂每日報告。",
};

export default function Page() {
  return <LearnPage lang="zh" />;
}
