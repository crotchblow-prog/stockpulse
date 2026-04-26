import { ReportViewer } from "@/components/ReportViewer";
import { readLatestReport } from "@/lib/reports";

export const dynamic = "force-dynamic";

export default async function ZhHomePage() {
  const md = await readLatestReport("zh");
  return <ReportViewer markdown={md} />;
}
