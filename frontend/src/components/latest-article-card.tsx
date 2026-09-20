import { ArticleViewButton } from "./article-view-button";

import { formatLabel } from "@/lib/format";
import type { DashboardIntelligenceItem } from "@/lib/api";
import { PublisherLogo } from "./publisher-logo";
import { Bookmark } from "lucide-react";

export function LatestArticleCard({ article }: { article: DashboardIntelligenceItem }) {
  const publishedDate = article.published_at
    ? new Intl.DateTimeFormat(undefined, { 
        day: "numeric", 
        month: "short", 
        year: "numeric", 
        hour: "numeric", 
        minute: "numeric", 
        timeZoneName: "short" 
      }).format(new Date(article.published_at))
    : "Unknown date";

  return (
    <article className="group flex flex-col justify-between rounded-xl border border-border bg-surface p-5 transition-colors duration-150 hover:border-border-strong" style={{ minHeight: "260px" }}>
      <div>
        <div className="flex items-start gap-3">
          <PublisherLogo publisherName={article.publisher_name} size={42} className="rounded-[8px] border border-border shadow-sm" />
          <div className="flex flex-col mt-0.5">
            <span className="text-[12px] font-bold text-text uppercase tracking-wide leading-none">{article.publisher_name}</span>
            <span suppressHydrationWarning className="text-[11px] font-medium text-muted mt-1.5 leading-none">
              {publishedDate}
            </span>
          </div>
        </div>

        <h3 className="mt-4 line-clamp-2 text-[17px] font-bold leading-snug text-text group-hover:text-primary-hover transition-colors">
          {article.risk_level && <span className="text-text">{formatLabel(article.risk_level)} Risk: </span>}
          {article.headline || article.title}
        </h3>
        
        <p className="mt-2 line-clamp-3 text-[13.5px] leading-[1.6] text-muted">
          {article.executive_summary}
        </p>
      </div>

      <div className="mt-5 flex flex-col gap-4">
        <div className="flex flex-wrap gap-1.5">
          {article.risk_level && (
            <span className="inline-flex items-center rounded-full bg-critical-bg px-2.5 py-0.5 text-[11px] font-bold text-critical">
              {formatLabel(article.risk_level)} {article.risk_score !== null ? `· ${article.risk_score}` : ""}
            </span>
          )}
          {article.event_type && (
            <span className="inline-flex items-center rounded-full bg-primary-soft px-2.5 py-0.5 text-[11px] font-bold text-primary">
              {formatLabel(article.event_type)}
            </span>
          )}
          {article.monitoring_topic && (
            <span className="inline-flex items-center rounded-full bg-surface-raised px-2.5 py-0.5 text-[11px] font-semibold text-muted">
              {article.monitoring_topic}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border pt-4">
          <ArticleViewButton
            articleId={article.article_id}
            sourceUrl={article.url}
            sourceName={article.source_name}
          />
          <button 
            type="button" 
            aria-label="Bookmark article"
            className="text-muted hover:text-text transition-colors p-1"
          >
            <Bookmark size={18} strokeWidth={2} />
          </button>
        </div>
      </div>
    </article>
  );
}
