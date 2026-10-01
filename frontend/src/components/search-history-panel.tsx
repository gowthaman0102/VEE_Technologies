"use client";

import { useState } from "react";
import { BookmarkPlus, RotateCcw, X, Trash2, Maximize2 } from "lucide-react";
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
  onDelete,
  onClearHistory,
}: {
  entries: SearchHistoryEntry[];
  canSave: boolean;
  onSave: () => void;
  onRerun: (entry: SearchHistoryEntry) => void;
  onDelete: (id: string) => void;
  onClearHistory: () => void;
}) {
  const [modalOpen, setModalOpen] = useState(false);

  const renderEntryList = (list: SearchHistoryEntry[]) => {
    return (
      <ul className="divide-y divide-border">
        {list.map((entry) => (
          <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0 group">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-text">{entry.query}</p>
              <p className="mt-0.5 text-[11px] capitalize text-muted">
                {entry.mode} A {entry.saved ? "Saved" : "History"} A {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(entry.createdAt)}
              </p>
            </div>
            <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                type="button"
                onClick={() => onRerun(entry)}
                aria-label={`Rerun ${entry.query}`}
                title="Rerun search"
                className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border text-body hover:border-primary-border hover:text-primary transition-colors"
              >
                <RotateCcw size={14} aria-hidden="true" />
              </button>
              <button
                type="button"
                onClick={() => onDelete(entry.id)}
                title="Delete search"
                className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border text-body hover:border-critical-border hover:text-critical transition-colors"
              >
                <X size={14} aria-hidden="true" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <section className="rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-text">Saved searches &amp; history</h2>
        <button
          type="button"
          onClick={onSave}
          disabled={!canSave}
          className="inline-flex items-center gap-1.5 rounded-lg border border-primary-border bg-primary-soft px-2.5 py-1.5 text-xs font-semibold text-primary hover:bg-primary-hover disabled:opacity-50 transition-colors"
        >
          <BookmarkPlus size={14} aria-hidden="true" /> Save current search
        </button>
      </div>
      
      {entries.length === 0 ? (
        <p className="py-5 text-center text-xs text-muted">Your searches will appear here.</p>
      ) : (
        <>
          {renderEntryList(entries.slice(0, 5))}
          {entries.length > 5 && (
            <div className="mt-3 text-center border-t border-border pt-3">
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted hover:text-text transition-colors"
              >
                <Maximize2 size={12} /> View all history ({entries.length})
              </button>
            </div>
          )}
        </>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm sm:p-6" onClick={() => setModalOpen(false)}>
          <div
            className="flex max-h-full w-full max-w-2xl flex-col rounded-2xl bg-surface shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <h2 className="text-lg font-bold text-text">Search History</h2>
                <p className="text-sm text-muted">View and manage all your past and saved searches</p>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted hover:bg-canvas hover:text-text transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5">
              {entries.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted">No history found.</p>
              ) : (
                renderEntryList(entries)
              )}
            </div>
            
            {entries.length > 0 && (
              <div className="border-t border-border bg-canvas/30 px-5 py-4 flex justify-between items-center rounded-b-2xl">
                <p className="text-xs text-muted">Saved searches are preserved when clearing history.</p>
                <button
                  type="button"
                  onClick={onClearHistory}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-critical-border bg-critical-bg px-3 py-1.5 text-xs font-semibold text-critical hover:bg-critical/10 transition-colors"
                >
                  <Trash2 size={14} /> Clear History
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}