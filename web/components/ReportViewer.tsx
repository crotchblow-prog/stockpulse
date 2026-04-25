import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function ReportViewer({ markdown }: { markdown: string }) {
  return (
    <article className="report-prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </article>
  );
}
