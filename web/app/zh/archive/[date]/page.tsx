import { notFound } from "next/navigation";
import Link from "next/link";
import { ReportViewer } from "@/components/ReportViewer";
import { readReportByDate } from "@/lib/reports";

export const dynamic = "force-dynamic";

export default async function ZhArchivedReportPage({
  params,
}: {
  params: Promise<{ date: string }>;
}) {
  const { date } = await params;
  const md = await readReportByDate(date, "zh");
  if (!md) notFound();
  return (
    <div>
      <Link
        href="/zh/archive"
        className="text-sm text-[color:var(--color-muted)] hover:text-white"
      >
        ← 返回歷史報告
      </Link>
      <div className="mt-4">
        <ReportViewer markdown={md} />
      </div>
    </div>
  );
}
