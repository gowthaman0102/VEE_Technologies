"use client";

import { useEffect, useState } from "react";
import { X, ExternalLink } from "lucide-react";
import { ArticleDetail, getArticleDetail } from "@/lib/api";
import { EmptyState } from "./ui/empty-state";
import { formatLabel } from "@/lib/format";
import { Badge, toneForRisk } from "./ui/badge";

export function ArticleReaderModal({
  articleId,
  onClose,
}: {
  articleId: number;
  onClose: () => void;
}) {
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const data = await getArticleDetail(articleId);
        setArticle(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load article");
      } finally {
        setLoading(false);
      }
    };
    fetchArticle();
  }, [articleId]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 sm:p-6" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="reader-title" className="flex h-full max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-[16px] bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-[#DFE9F0] px-6 py-4">
          <div>
            <p className="text-[11px] font-bold tracking-[0.15em] text-[#60718A] uppercase">
              Article Reader
            </p>
          </div>
          <div className="flex items-center gap-2">
            {article?.url && (
              <a href={article.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 rounded-lg border border-[#DFE9F0] px-3 py-1.5 text-sm font-semibold text-[#0A1730] hover:bg-[#F4F9FC] transition-colors">
                Original <ExternalLink size={14} />
              </a>
            )}
            <button type="button" onClick={onClose} aria-label="Close reader" className="flex h-8 w-8 items-center justify-center rounded-full text-[#60718A] hover:bg-[#F4F9FC] hover:text-[#0A1730] transition-colors">
              <X size={20} />
            </button>
          </div>
        </header>
        
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm font-medium text-[#60718A]">Loading intelligence...</p>
            </div>
          )}
          
          {error && (
            <div className="flex h-full items-center justify-center">
              <EmptyState title="Unable to load article" description={error} />
            </div>
          )}
          
          {article && (
            <div className="mx-auto max-w-3xl">
              <div className="mb-6 flex flex-col items-start gap-4">
                <div className="flex flex-wrap gap-2">
                  {article.risk_level && (
                    <Badge tone={toneForRisk(article.risk_level)}>
                      {formatLabel(article.risk_level)} Risk {article.risk_score !== null ? `· ${article.risk_score}` : ""}
                    </Badge>
                  )}
                  {article.event_type && <Badge>{formatLabel(article.event_type)}</Badge>}
                  {article.monitoring_topic && <Badge>{article.monitoring_topic}</Badge>}
                </div>
                <h1 id="reader-title" className="text-2xl font-bold text-[#0A1730] leading-tight sm:text-3xl">
                  {article.title}
                </h1>
                <div className="flex items-center gap-2 text-sm text-[#60718A]">
                  <span className="font-semibold uppercase tracking-wider">{article.publisher_name}</span>
                  <span>·</span>
                  <span suppressHydrationWarning>{article.published_at ? new Intl.DateTimeFormat(undefined, { dateStyle: "long", timeStyle: "short" }).format(new Date(article.published_at)) : "Unknown date"}</span>
                </div>
              </div>
              
              <div className="prose prose-slate max-w-none prose-p:text-[15px] prose-p:leading-relaxed prose-headings:font-bold prose-a:text-[#3C9CF4]">
                {article.executive_summary && (
                  <div className="mb-8 rounded-[12px] bg-[#F4F9FC] p-5 border border-[#DFE9F0]">
                    <h3 className="mb-2 text-sm font-bold text-[#0A1730] uppercase tracking-wide">Executive Summary</h3>
                    <p className="text-[#0A1730]">{article.executive_summary}</p>
                  </div>
                )}
                
                <div className="whitespace-pre-wrap text-[#0A1730]">
                  {article.cleaned_content || article.raw_content || article.description || "No full content available."}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
