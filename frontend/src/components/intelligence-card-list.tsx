"use client";

import { ArticleMetadata } from "@/components/article-metadata";
import { ArticleViewButton } from "@/components/article-view-button";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { formatLabel } from "@/lib/format";
import type { DashboardIntelligenceItem } from "@/lib/api";

export function IntelligenceCardList({ items }: { items: DashboardIntelligenceItem[] }) {
  if (items.length === 0) {

    return <EmptyState title="No processed intelligence" description="No processed intelligence is available yet." />;
  }

  return (
    <div className="mt-5 space-y-4">
      {items.map((item) => (
        <article
          key={`${item.company_id}-${item.article_id}`}
          className="rounded-lg border border-border bg-surface-raised p-4 transition-colors duration-150 hover:border-border-strong"
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0 flex-1">
              <ArticleMetadata
                publisherName={item.publisher_name}
                publishedAt={item.published_at}
                collectedAt={item.collected_at}
                compact
              />
              {item.url ? (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 block break-words text-left text-[15px] font-semibold text-text hover:text-primary hover:underline hover:underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35 focus-visible:ring-offset-2"
                >
                  {item.headline || item.title}
                </a>
              ) : (
                <span className="mt-3 block break-words text-left text-[15px] font-semibold text-text">
                  {item.headline || item.title}
                </span>
              )}
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-body">
                {item.executive_summary}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge tone={toneForRisk(item.risk_level)}>
                  {formatLabel(item.risk_level)} · {item.risk_score}
                </Badge>
                <Badge>{formatLabel(item.event_type)}</Badge>
                {item.monitoring_topic && (
                  <span className="rounded-full border border-border px-2.5 py-1 text-xs text-body">
                    {item.monitoring_topic}
                  </span>
                )}
              </div>
            </div>
            <ArticleViewButton
              articleId={item.article_id}
              sourceUrl={item.url}
              sourceName={item.source_name}
              className="shrink-0 self-start"
            />
          </div>
        </article>
      ))}
    </div>
  );
}
