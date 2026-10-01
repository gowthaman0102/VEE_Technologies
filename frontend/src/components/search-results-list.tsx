import { useState } from "react";
import { Download } from "lucide-react";
import { ArticleMetadata } from "@/components/article-metadata";
import { ArticleViewButton } from "@/components/article-view-button";
import { Badge, toneForSentiment } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { SearchResult, downloadReport } from "@/lib/api";

export function SearchResultsList({
  results,
  totalCount,
  companyId,
  mode,
  query,
  embedded = false,
}: {
  results: SearchResult[];
  /** Backend total match count (may exceed results.length when capped at 50). */
  totalCount?: number;
  companyId: number | null;
  mode: "keyword" | "semantic";
  query: string;
  embedded?: boolean;
}) {
  const [format, setFormat] = useState<"pdf" | "xlsx" | "csv">("csv");
  const [exporting, setExporting] = useState(false);
  const [message, setMessage] = useState("");

  async function exportResults() {
    if (companyId === null || results.length === 0) return;
    setExporting(true);
    setMessage("");
    try {
      await downloadReport({ company_id: companyId, report_type: "all_history", report_scope: "search_results", article_ids: results.map((result) => result.article_id) }, format);
      setMessage("Export downloaded.");
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }

  const displayTotal = totalCount ?? results.length;
  const isTruncated = totalCount !== undefined && totalCount > results.length;

  return (
    <section className={embedded ? "bg-surface" : "rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5"}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-text">Search results</h2>
          <p className="mt-1 text-xs text-muted">
            {isTruncated
              ? `${results.length} of ${displayTotal} ${mode} matches for "${query}" · showing first ${results.length}`
              : `${displayTotal} ${mode} matches for "${query}"`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="sr-only" htmlFor="search-export-format">Export format</label>
          <select id="search-export-format" value={format} onChange={(event) => setFormat(event.target.value as typeof format)} className="h-9 rounded-lg border border-border bg-surface px-2 text-xs text-text"><option value="csv">CSV</option><option value="xlsx">XLSX</option><option value="pdf">PDF</option></select>
          <button type="button" onClick={() => void exportResults()} disabled={exporting || !results.length || companyId === null} className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-primary-border bg-primary-soft px-3 py-2 text-xs font-semibold text-primary disabled:opacity-50"><Download size={14} aria-hidden="true" />{exporting ? "Exporting..." : "Export results"}</button>
        </div>
      </div>
      {message && <p role="status" className="mb-3 text-xs text-muted">{message}</p>}
      {results.length ? <ul className="divide-y divide-border">
        {results.map((result) => <li key={result.article_id} className="py-4 first:pt-0 last:pb-0"><article className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0"><ArticleMetadata publisherName={result.publisher_name} publishedAt={result.published_at} collectedAt={result.collected_at} compact /><h3 className="mt-2 text-sm font-semibold text-text">{result.title}</h3><p className="mt-1 text-xs text-muted">{result.source_name}</p>
            <div className="mt-3 flex flex-wrap gap-2">{mode === "semantic" && result.similarity !== undefined && <Badge>Similarity {result.similarity.toFixed(3)}</Badge>}{result.sentiment && <Badge tone={toneForSentiment(result.sentiment)}>Sentiment: {result.sentiment}</Badge>}{result.risk_level && <Badge>Risk: {result.risk_level}{result.risk_score !== null ? ` (${result.risk_score})` : ""}</Badge>}</div>
          </div><ArticleViewButton articleId={result.article_id} sourceUrl={result.url} sourceName={result.source_name} />
        </article></li>)}
      </ul> : <EmptyState title="No articles matched the current search and filters." />}
    </section>
  );
}