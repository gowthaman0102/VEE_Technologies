import { SearchResult } from "@/lib/api";

export type SearchComparison = {
  keyword: SearchResult[];
  semantic: SearchResult[];
};

export function SearchModeComparison({
  comparison,
  loading,
  disabled,
  onCompare,
}: {
  comparison: SearchComparison | null;
  loading: boolean;
  disabled: boolean;
  onCompare: () => void;
}) {
  const keywordIds = new Set(comparison?.keyword.map((item) => item.article_id) ?? []);
  const semanticIds = new Set(comparison?.semantic.map((item) => item.article_id) ?? []);
  const overlap = [...keywordIds].filter((id) => semanticIds.has(id));
  const keywordOnly = [...keywordIds].filter((id) => !semanticIds.has(id));
  const semanticOnly = [...semanticIds].filter((id) => !keywordIds.has(id));

  return (
    <section className="rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-text">Keyword vs semantic comparison</h2>
        <button type="button" onClick={onCompare} disabled={disabled || loading} className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-body hover:border-primary-border hover:text-primary disabled:opacity-50">{loading ? "Comparing..." : "Compare modes"}</button>
      </div>
      {comparison ? <>
        <div className="grid grid-cols-2 gap-3">
          <Count title="Keyword results" count={comparison.keyword.length} />
          <Count title="Semantic results" count={comparison.semantic.length} />
        </div>
        <div className="mt-3 grid gap-2 text-[11px] sm:grid-cols-3">
          <IdGroup title="Overlap" ids={overlap} /><IdGroup title="Keyword only" ids={keywordOnly} /><IdGroup title="Semantic only" ids={semanticOnly} />
        </div>
      </> : <p className="py-5 text-center text-xs text-muted">Compare both modes for the current query.</p>}
    </section>
  );
}

function Count({ title, count }: { title: string; count: number }) {
  return <div className="rounded-lg border border-border bg-surface-raised p-3"><p className="text-xs font-semibold text-text">{title}</p><p className="mt-1 text-lg font-bold text-primary">{count}</p></div>;
}

function IdGroup({ title, ids }: { title: string; ids: number[] }) {
  return <p className="rounded-lg bg-surface-raised p-2"><span className="font-semibold text-body">{title} ({ids.length})</span><br /><span className="break-words text-muted">{ids.length ? ids.join(", ") : "None"}</span></p>;
}