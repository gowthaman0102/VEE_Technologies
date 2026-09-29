import { SearchFilters } from "@/lib/api";
import { inputClasses } from "@/components/ui/button-styles";

export function SearchAdvancedFilters({
  filters,
  publishers,
  onChange,
}: {
  filters: SearchFilters;
  publishers: string[];
  onChange: (filters: SearchFilters) => void;
}) {
  function updateDate(field: "start" | "end", value: string) {
    const next = { ...filters };
    if (value) {
      const time = field === "start" ? "T00:00:00.000Z" : "T23:59:59.999Z";
      next[field] = new Date(`${value}${time}`).toISOString();
    } else {
      delete next[field];
    }
    onChange(next);
  }

  return (
    <section className="rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5">
      <h2 className="mb-3 text-sm font-bold text-text">Advanced filters</h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <label className="text-xs font-medium text-muted">Date from
          <input aria-label="Date from" type="date" value={filters.start?.slice(0, 10) ?? ""} onChange={(event) => updateDate("start", event.target.value)} className={`mt-1.5 ${inputClasses}`} />
        </label>
        <label className="text-xs font-medium text-muted">Date to
          <input aria-label="Date to" type="date" value={filters.end?.slice(0, 10) ?? ""} onChange={(event) => updateDate("end", event.target.value)} className={`mt-1.5 ${inputClasses}`} />
        </label>
        <label className="text-xs font-medium text-muted">Publisher
          <select value={filters.source_name ?? ""} onChange={(event) => onChange({ ...filters, source_name: event.target.value || undefined })} className={`mt-1.5 ${inputClasses}`}>
            <option value="">All publishers</option>
            {publishers.map((publisher) => <option key={publisher} value={publisher}>{publisher}</option>)}
          </select>
        </label>
        <label className="text-xs font-medium text-muted">Risk level
          <select value={filters.risk_level ?? ""} onChange={(event) => onChange({ ...filters, risk_level: event.target.value || undefined })} className={`mt-1.5 ${inputClasses}`}>
            <option value="">All risk levels</option>
            <option value="critical">Critical</option><option value="high">High</option>
            <option value="medium">Medium</option><option value="low">Low</option>
          </select>
        </label>
        <label className="text-xs font-medium text-muted sm:col-span-2 xl:col-span-1">Sentiment
          <select value={filters.sentiment ?? ""} onChange={(event) => onChange({ ...filters, sentiment: event.target.value || undefined })} className={`mt-1.5 ${inputClasses}`}>
            <option value="">All sentiment</option>
            <option value="positive">Positive</option><option value="neutral">Neutral</option><option value="negative">Negative</option>
          </select>
        </label>
      </div>
    </section>
  );
}