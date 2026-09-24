"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { useAutoRefresh } from "@/lib/use-auto-refresh";

import { ArticleViewButton } from "@/components/article-view-button";
import { ArticleMetadata } from "@/components/article-metadata";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Section } from "@/components/ui/section";
import { StatCard } from "@/components/ui/stat-card";
import {
  DashboardArticleItem,
  DashboardArticleMetric,
  DashboardCompanyItem,
  DashboardOverview,
  getDashboardArticles,
  getDashboardCompanies,
  getDashboardOverview,
} from "@/lib/api";
import { formatLabel, formatRelativeTime } from "@/lib/format";

type SelectedMetric = DashboardArticleMetric | "companies";

const ARTICLE_METRICS: Record<DashboardArticleMetric, { title: string; description: string }> = {
  total: { title: "All Articles", description: "Every article included in the Overview coverage total." },
  processed: { title: "Processed Intelligence Articles", description: "Articles with completed stored intelligence for active companies." },
  "high-risk": { title: "High Risk Articles", description: "Articles with the current high risk classification." },
  "critical-risk": { title: "Critical Risk Articles", description: "Articles with the current critical risk classification." },
};

function ArticleRow({ article }: { article: DashboardArticleItem }) {
  return (
    <article className="rounded-lg border border-border bg-surface-raised p-4">
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

function DetailModal({
  selectedMetric,
  articles,
  companies,
  detailCount,
  loading,
  error,
  onClose,
}: {
  selectedMetric: SelectedMetric;
  articles: DashboardArticleItem[];
  companies: DashboardCompanyItem[];
  detailCount: number;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  const isCompanies = selectedMetric === "companies";
  const articleConfig = isCompanies ? null : ARTICLE_METRICS[selectedMetric];
  const title = articleConfig?.title ?? "Monitored Companies";
  const count = detailCount;

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-text/40 p-0 sm:items-center sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="kpi-detail-title" className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_2px_8px_rgba(28,23,52,0.10)]">
          <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Overview Detail</p>
            <h2 id="kpi-detail-title" className="mt-1 text-lg font-semibold text-text">{title}</h2>
            <p className="mt-1 text-sm text-muted">{loading ? "Loading current data..." : `${count} ${count === 1 ? "item" : "items"}`}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close detail modal" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"><X size={17} aria-hidden="true" /></button>
        </header>
        <div className="overflow-y-auto px-5 py-5 sm:px-6">
          {error ? <EmptyState title="Unable to load details" description={error} /> : loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="rounded-lg border border-border bg-surface p-4">
                      <Skeleton className="h-6 w-1/3 mb-2" />
                      <Skeleton className="h-4 w-1/4" />
                    </div>
                  ))}
                </div>
              ) : isCompanies ? (
            companies.length === 0 ? <EmptyState title="No monitored companies found." /> : <div className="space-y-3">{companies.map((company) => <article key={company.id} className="rounded-lg border border-border bg-surface-raised p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-text">{company.name}</h3><p className="mt-1 text-sm text-muted">{company.is_active ? "Active monitoring" : "Inactive"}</p></div><Badge>{company.monitoring_topics.length} monitoring {company.monitoring_topics.length === 1 ? "category" : "categories"}</Badge></div>{company.aliases.length > 0 && <p className="mt-3 text-sm text-body">Aliases: {company.aliases.join(", ")}</p>}</article>)}</div>
          ) : articles.length === 0 ? <EmptyState title={selectedMetric === "critical-risk" ? "No critical-risk articles found." : "No matching articles found."} /> : <div className="space-y-3">{articles.map((article) => <ArticleRow key={`${article.article_id}-${article.risk_level ?? "article"}`} article={article} />)}</div>}
        </div>
      </section>
    </div>
  );
}

export function OverviewKpiGrid({ overview: initialOverview }: { overview: DashboardOverview }) {
  const [overview, setOverview] = useState<DashboardOverview>(initialOverview);
  const [liveStatus, setLiveStatus] = useState<"live" | "updating" | "delayed">("live");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const [selectedMetric, setSelectedMetric] = useState<SelectedMetric | null>(null);
  const [articles, setArticles] = useState<DashboardArticleItem[]>([]);
  const [companies, setCompanies] = useState<DashboardCompanyItem[]>([]);
  const [detailCount, setDetailCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Client-side polling so we can observe success/failure
  useAutoRefresh(
    async () => {
      setLiveStatus("updating");
      try {
        const data = await getDashboardOverview();
        setOverview(data);
        setLiveStatus("live");
        setLastUpdated(new Date());
      } catch {
        setLiveStatus("delayed");
      }
    },
    { intervalMs: 60_000 },
  );

  const openMetric = async (metric: SelectedMetric) => {
    setSelectedMetric(metric);
    setLoading(true);
    setError(null);
    setArticles([]);
    setCompanies([]);
    setDetailCount(0);
    try {
      if (metric === "companies") {
        const response = await getDashboardCompanies();
        setCompanies(response.items);
        setDetailCount(response.count);
      } else {
        const response = await getDashboardArticles(metric);
        setArticles(response.items);
        setDetailCount(response.count);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The detail data could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  // Format "Last updated" relative time
  const updatedLabel = lastUpdated
    ? `Updated ${formatRelativeTime(lastUpdated)}`
    : null;

  return <>
    <Section
      title="Coverage"
      action={
        <div className="flex items-center gap-2 text-[11px] text-muted">
          {liveStatus === "live" && updatedLabel && (
            <span className="tabular-nums">{updatedLabel}</span>
          )}
        </div>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total Articles" value={overview.total_articles} isLive liveStatus={liveStatus} onOpen={() => openMetric("total")} actionLabel="View all total articles" />
        <StatCard label="Processed Intelligence" value={overview.processed_articles} isLive liveStatus={liveStatus} onOpen={() => openMetric("processed")} actionLabel="View processed intelligence articles" />
        <StatCard label="Monitored Companies" value={overview.total_companies} onOpen={() => openMetric("companies")} actionLabel="View monitored companies" />
      </div>
    </Section>
    <Section title="Risk Overview" className="mt-8">
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard label="High Risk" value={overview.high_risk_items} tone="high" isLive liveStatus={liveStatus} onOpen={() => openMetric("high-risk")} actionLabel="View all high risk articles" />
        <StatCard label="Critical Risk" value={overview.critical_risk_items} tone="critical" isLive liveStatus={liveStatus} onOpen={() => openMetric("critical-risk")} actionLabel="View all critical risk articles" />
      </div>
    </Section>
    {selectedMetric && <DetailModal selectedMetric={selectedMetric} articles={articles} companies={companies} detailCount={detailCount} loading={loading} error={error} onClose={() => setSelectedMetric(null)} />}
  </>;
}
