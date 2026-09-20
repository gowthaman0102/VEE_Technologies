"use client";

import { DashboardArticleItem } from "@/lib/api";
import { ArticleMetadata } from "@/components/article-metadata";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { formatLabel } from "@/lib/format";
import { ArticleViewButton } from "@/components/article-view-button";

export function ArticleRow({ article }: { article: DashboardArticleItem }) {
  return (
    <article className="rounded-lg border border-border bg-surface-raised p-4 transition-colors hover:border-border-strong hover:bg-surface-raised-hover">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <ArticleMetadata publisherName={article.publisher_name} publishedAt={article.published_at} collectedAt={article.collected_at} compact />
          <h3 className="mt-3 break-words text-sm font-semibold leading-6 text-text">{article.title}</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {article.risk_level && <Badge tone={toneForRisk(article.risk_level)}>{formatLabel(article.risk_level)}{article.risk_score !== null ? ` · ${article.risk_score}` : ""}</Badge>}
            {article.event_type && <Badge>{formatLabel(article.event_type)}</Badge>}
            {article.business_impact && <Badge>{formatLabel(article.business_impact)}</Badge>}
            {article.sentiment && <Badge>{formatLabel(article.sentiment)}</Badge>}
          </div>
        </div>
        <ArticleViewButton
          articleId={article.article_id}
          sourceUrl={article.url}
          sourceName={article.source_name}
          className="shrink-0 self-start"
        />
      </div>
    </article>
  );
}
