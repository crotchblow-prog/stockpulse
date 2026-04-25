import { ReportViewer } from "@/components/ReportViewer";
import { readLatestReport } from "@/lib/reports";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const md = await readLatestReport();
  return <ReportViewer markdown={md} />;
}
