import { BookmarkPlus, RotateCcw } from "lucide-react";
import { SearchFilters } from "@/lib/api";

export type SearchMode = "keyword" | "semantic";

export type SearchHistoryEntry = {
  id: string;
  query: string;
  mode: SearchMode;
  filters: SearchFilters;
  createdAt: number;
  saved: boolean;
};

export function SearchHistoryPanel({
  entries,
  canSave,
  onSave,
  onRerun,
}: {
  entries: SearchHistoryEntry[];
  canSave: boolean;
  onSave: () => void;
  onRerun: (entry: SearchHistoryEntry) => void;
}) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-text">Saved searches &amp; history</h2>
        <button type="button" onClick={onSave} disabled={!canSave} className="inline-flex items-center gap-1.5 rounded-lg border border-primary-border bg-primary-soft px-2.5 py-1.5 text-xs font-semibold text-primary disabled:opacity-50">
          <BookmarkPlus size={14} aria-hidden="true" /> Save current search
        </button>
      </div>
      {entries.length === 0 ? <p className="py-5 text-center text-xs text-muted">Your searches will appear here.</p> : (
        <ul className="divide-y divide-border">
          {entries.slice(0, 8).map((entry) => <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
            <div className="min-w-0"><p className="truncate text-sm font-semibold text-text">{entry.query}</p>
              <p className="mt-0.5 text-[11px] capitalize text-muted">{entry.mode} · {entry.saved ? "Saved" : "History"} · {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(entry.createdAt)}</p>
            </div>
            <button type="button" onClick={() => onRerun(entry)} aria-label={`Rerun ${entry.query}`} title="Rerun search" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border text-body hover:border-primary-border hover:text-primary"><RotateCcw size={14} aria-hidden="true" /></button>
          </li>)}
        </ul>
      )}
    </section>
  );
}