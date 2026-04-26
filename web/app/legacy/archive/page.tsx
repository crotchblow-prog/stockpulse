import Link from "next/link";
import { listArchivedReports } from "@/lib/reports";

export const dynamic = "force-dynamic";

export default async function ArchivePage() {
  const reports = await listArchivedReports();
  return (
    <section>
      <h1 className="text-2xl font-semibold mb-6">Archive</h1>
      {reports.length === 0 ? (
        <p className="text-[color:var(--color-muted)]">No archived reports yet.</p>
      ) : (
        <ul className="space-y-2">
          {reports.map((r) => (
            <li key={r.date}>
              <Link
                href={`/archive/${r.date}`}
                className="block rounded-lg border border-white/10 px-4 py-3 hover:bg-white/5"
              >
                <span className="font-medium">{r.date}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
