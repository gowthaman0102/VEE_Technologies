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
          <PublisherLogo publisherName={article.publisher_name} size={42} className="rounded-[8px] border border-[#DFE9F0] shadow-sm" />
          <div className="flex flex-col mt-0.5">
            <span className="text-[12px] font-bold text-[#0A1730] uppercase tracking-wide leading-none">{article.publisher_name}</span>
            <span suppressHydrationWarning className="text-[11px] font-medium text-[#A0B0C0] mt-1.5 leading-none">
              {publishedDate}
            </span>
          </div>
        </div>

        <h3 className="mt-4 line-clamp-2 text-[17px] font-bold leading-snug text-[#0A1730] group-hover:text-[#3C9CF4] transition-colors">
          {article.risk_level && <span className="text-[#0A1730]">{formatLabel(article.risk_level)} Risk: </span>}
          {article.headline || article.title}
        </h3>
        
        <p className="mt-2 line-clamp-3 text-[13.5px] leading-[1.6] text-[#60718A]">
          {article.executive_summary}
        </p>
      </div>

      <div className="mt-5 flex flex-col gap-4">
        <div className="flex flex-wrap gap-1.5">
          {article.risk_level && (
            <span className="inline-flex items-center rounded-full bg-[#FFF6F6] px-2.5 py-0.5 text-[11px] font-bold text-[#EF4048]">
              {formatLabel(article.risk_level)} {article.risk_score !== null ? `· ${article.risk_score}` : ""}
            </span>
          )}
          {article.event_type && (
            <span className="inline-flex items-center rounded-full bg-[#EEF7FF] px-2.5 py-0.5 text-[11px] font-bold text-[#3C9CF4]">
              {formatLabel(article.event_type)}
            </span>
          )}
          {article.monitoring_topic && (
            <span className="inline-flex items-center rounded-full bg-[#F3F8FC] px-2.5 py-0.5 text-[11px] font-semibold text-[#60718A]">
              {article.monitoring_topic}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-[#DFE9F0] pt-4">
          <ArticleViewButton
            articleId={article.article_id}
            sourceUrl={article.url}
            sourceName={article.source_name}
          />
          <button 
            type="button" 
            aria-label="Bookmark article"
            className="text-[#A0B0C0] hover:text-[#0A1730] transition-colors p-1"
          >
            <Bookmark size={18} strokeWidth={2} />
          </button>
        </div>
      </div>
    </article>
  );
}
