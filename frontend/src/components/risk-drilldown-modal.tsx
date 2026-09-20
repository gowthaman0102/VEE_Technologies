"use client";

import { useEffect, useState, useRef } from "react";
import { X, Search, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

import { DashboardArticleItem, getRiskDrilldown } from "@/lib/api";
import { ArticleRow } from "@/components/article-row";
import { EmptyState } from "@/components/ui/empty-state";

type RiskDrilldownModalProps = {
  isOpen: boolean;
  metric: string;
  value?: string;
  title: string;
  targetTotal: number;
  onClose: () => void;
};

export function RiskDrilldownModal({
  isOpen,
  metric,
  value,
  title,
  targetTotal,
  onClose,
}: RiskDrilldownModalProps) {
  const [articles, setArticles] = useState<DashboardArticleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  const searchTimeout = useRef<NodeJS.Timeout>(null);

  const PAGE_SIZE = 20;
  const [totalCount, setTotalCount] = useState(targetTotal);
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset page on new search
    }, 300);
    return () => {
      if (searchTimeout.current) clearTimeout(searchTimeout.current);
    };
  }, [search]);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    
    async function fetchDrilldown() {
      setLoading(true);
      setError(null);
      try {
        const response = await getRiskDrilldown(metric, value, page, debouncedSearch);
        if (isMounted) {
          setArticles(response.items);
          setTotalCount(response.total);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load articles.");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchDrilldown();

    return () => { isMounted = false; };
  }, [isOpen, metric, value, page, debouncedSearch]);

  // Handle Escape and outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent background scroll
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 sm:p-6">
      <div 
        className="absolute inset-0 bg-text/40 transition-opacity duration-200" 
        onClick={onClose} 
        aria-hidden="true" 
      />
      
      <section 
        role="dialog" 
        aria-modal="true" 
        aria-labelledby="risk-drilldown-title" 
          className="relative flex h-[85vh] w-full max-w-[1200px] flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_2px_8px_rgba(28,23,52,0.10)] transition-all duration-200 ease-out sm:h-[80vh] scale-100"
      >
        <header className="flex flex-col gap-4 border-b border-border bg-surface px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex-1">
            <h2 id="risk-drilldown-title" className="text-xl font-semibold uppercase tracking-tight text-text">
              {title}
            </h2>
            <p className="mt-1 text-sm text-muted">
              {totalCount} {totalCount === 1 ? "Article" : "Articles"}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative max-w-[300px] flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
              <input 
                type="text" 
                placeholder="Search articles..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-full border border-border bg-background py-2 pl-9 pr-4 text-sm text-body placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <button 
              type="button" 
              onClick={onClose} 
              aria-label="Close modal" 
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border text-muted transition-colors hover:border-border-strong hover:bg-surface-raised hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
          {error ? (
            <div className="flex h-full flex-col items-center justify-center">
              <EmptyState title="Unable to load matching articles." description={error} />
              <button onClick={() => setPage(page)} className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary-hover">Retry</button>
            </div>
          ) : loading ? (
            <div className="flex h-full items-center justify-center">
              <div className="flex flex-col items-center gap-3 text-muted">
                <Loader2 className="animate-spin" size={24} />
                <p className="text-sm">Loading articles...</p>
              </div>
            </div>
          ) : articles.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <EmptyState title="No matching articles found." />
            </div>
          ) : (
            <div className="space-y-4">
              {articles.map((article) => (
                <ArticleRow key={article.article_id} article={article} />
              ))}
            </div>
          )}
        </div>

        {totalCount > PAGE_SIZE && (
          <footer className="flex items-center justify-between border-t border-border bg-surface-raised px-5 py-3 sm:px-6">
            <button 
              type="button"
              disabled={page === 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-body transition-colors hover:bg-surface-hover disabled:pointer-events-none disabled:opacity-50"
            >
              <ChevronLeft size={16} />
              Previous
            </button>
            <p className="text-sm font-medium text-muted">
              {page} / {totalPages}
            </p>
            <button 
              type="button"
              disabled={page === totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-body transition-colors hover:bg-surface-hover disabled:pointer-events-none disabled:opacity-50"
            >
              Next
              <ChevronRight size={16} />
            </button>
          </footer>
        )}
      </section>
    </div>
  );
}
