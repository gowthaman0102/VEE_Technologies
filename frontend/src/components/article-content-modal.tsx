"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { getArticleDetail, ArticleDetail } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { focusRing } from "@/components/ui/button-styles";
import { formatLabel } from "@/lib/format";
import { Badge, toneForRisk } from "@/components/ui/badge";

export function ArticleContentModal({
  articleId,
  onClose,
}: {
  articleId: number;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [article, setArticle] = useState<ArticleDetail | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
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

  const content = article?.cleaned_content || article?.extracted_content || article?.raw_content || article?.description || "No content available for this article.";

  const formattedDate = article?.published_at 
    ? new Date(article.published_at).toLocaleString() 
    : null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-end justify-center bg-text/40 p-0 sm:items-center sm:p-6"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_2px_8px_rgba(28,23,52,0.10)]"
      >
        <div className="flex-1 overflow-y-auto px-5 py-6 sm:px-8">
          {error ? (
            <div className="text-critical">{error}</div>
          ) : loading ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-3/4" />
              <div className="flex gap-2 mb-6">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          ) : (
            <article>
              <h1 className="text-2xl font-bold text-text mb-2">
                {article?.title}
              </h1>
              
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mb-6 text-sm text-muted">
                <span className="font-semibold text-text">{article?.publisher_name}</span>
                {article?.publisher_country_name && article.publisher_country_name.toLowerCase() !== "unknown" && (
                  <span>{article.publisher_country_name}</span>
                )}
                {formattedDate && <span>Published: {formattedDate}</span>}
                {article?.source_name && (
                  <span>Source: {article.source_name}</span>
                )}
              </div>

              <div className="flex flex-wrap gap-2 mb-6">
                {article?.risk_level && (
                  <Badge tone={toneForRisk(article.risk_level)}>
                    {formatLabel(article.risk_level)} {article.risk_score ? `· ${article.risk_score}` : ""}
                  </Badge>
                )}
                {article?.business_impact && (
                  <Badge>{formatLabel(article.business_impact)}</Badge>
                )}
                {article?.sentiment && (
                  <Badge>{formatLabel(article.sentiment)}</Badge>
                )}
              </div>

              <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-body">
                {content}
              </div>
            </article>
          )}
        </div>

        <footer className="shrink-0 flex items-center justify-end gap-3 border-t border-border bg-surface-raised px-5 py-3 sm:px-6">
          <button
            type="button"
            onClick={onClose}
            className={`inline-flex items-center justify-center rounded-[8px] border border-border bg-white px-3.5 py-1.5 text-[13px] font-bold text-text transition-colors duration-150 hover:bg-surface-raised hover:border-primary ${focusRing}`}
          >
            Close
          </button>
          {article?.url && (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#ffffff" }}
              className={`inline-flex items-center justify-center rounded-[8px] bg-primary px-3.5 py-1.5 text-[13px] font-bold transition-colors hover:bg-primary-hover ${focusRing}`}
            >
              View Article
            </a>
          )}
        </footer>
      </section>
    </div>
  );
}
