import { LearnPage } from "@/components/learn/LearnPage";

export const dynamic = "force-static";

export const metadata = {
  title: "Learn — VIX Pulse",
  description: "What VIX is, the 6-tier framework, and how to read the daily report.",
};

export default function Page() {
  return <LearnPage lang="en" />;
}
