"use client";

import { ArticleMetadata } from "@/components/article-metadata";
import { ArticleViewButton } from "@/components/article-view-button";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { formatLabel } from "@/lib/format";
import type { DashboardIntelligenceItem } from "@/lib/api";

export function IntelligenceFeed({ items }: { items: DashboardIntelligenceItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyState
        title="No intelligence items yet"
        description="Fully processed risk insights will appear here after triage and risk analysis complete."
      />
    );
  }

  return (
    <div className="space-y-5">
      {items.map((item) => (
        <article
          key={`${item.article_id}-${item.company_id}`}
          className="w-full rounded-xl border border-border bg-surface p-6 shadow-[0_1px_2px_rgba(18,32,31,0.04)]"
        >
          <div className="flex flex-col gap-6">
            <div className="flex flex-col-reverse justify-between gap-4 sm:flex-row sm:items-start">
              <div className="flex flex-wrap items-center gap-2 mt-1 sm:mt-0">
                <Badge tone={toneForRisk(item.risk_level)}>
                  {item.risk_level.toUpperCase()} {item.risk_score.toFixed(1)}
                </Badge>
                <Badge>{formatLabel(item.event_type)}</Badge>
                <Badge>{item.company_name}</Badge>
              </div>

              <ArticleViewButton
                articleId={item.article_id}
                sourceUrl={item.url}
                sourceName={item.source_name}
                className="shrink-0 self-start sm:self-auto"
              />
            </div>

            <ArticleMetadata
              publisherName={item.publisher_name}
              publishedAt={item.published_at}
              collectedAt={item.collected_at}
              variant="grid"
            />

            <div>
              <h3 className="text-xl font-semibold leading-7 text-text">
                {item.headline}
              </h3>
              <p className="mt-2 text-sm text-muted">
                Article #{item.article_id}
                {" • "}
                Confidence {(item.confidence * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <section className="rounded-lg border border-border bg-surface-raised p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-primary">
                Executive Summary
              </p>
              <p className="mt-3 text-sm leading-6 text-body">
                {item.executive_summary}
              </p>
            </section>

            <section className="rounded-lg border border-border bg-surface-raised p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-primary">
                Recommended Action
              </p>
              <p className="mt-3 text-sm leading-6 text-body">
                {item.recommended_action}
              </p>
            </section>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-border pt-4 text-xs text-muted">
            <span>
              Urgency:{" "}
              <strong className="font-medium text-body">
                {formatLabel(item.urgency)}
              </strong>
            </span>
            <span>
              Escalation:{" "}
              <strong className="font-medium text-body">
                {formatLabel(item.escalation_action)}
              </strong>
            </span>
            <span>
              Topic:{" "}
              <strong className="font-medium text-body">
                {item.monitoring_topic ?? "General"}
              </strong>
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}
