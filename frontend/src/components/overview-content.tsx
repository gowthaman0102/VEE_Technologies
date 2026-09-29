"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import Link from "next/link";

import { ArticleViewButton } from "@/components/article-view-button";
import { ArticleMetadata } from "@/components/article-metadata";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import {
  AnalyticsOverview,
  ArticleTrendPoint,
  DashboardArticleItem,
  DashboardArticleMetric,
  DashboardCompanyItem,
  DashboardOverview,
  DashboardIntelligenceItem,
  EventAnalyticsResponse,
  SourceAnalyticsResponse,
  getDashboardArticles,
  getDashboardCompanies,
  getDashboardOverview,
  getDashboardIntelligence,
  getAnalyticsOverview,
  getArticleTrend,
  getBusinessImpact,
  getSentimentTrend,
  getEventAnalytics,
  getSourceAnalytics,
} from "@/lib/api";
import { formatLabel } from "@/lib/format";

import { OverviewHero } from "./overview-hero";
import { OverviewMetricCard } from "./overview-metric-card";
import { PublisherLogo } from "./publisher-logo";
import { KpiArticleIcon, KpiIntelligenceIcon, KpiCompanyIcon, KpiHighRiskIcon, KpiCriticalRiskIcon } from "./kpi-icons";
import { SignalTrendsSection, SentimentSnapshot } from "./signal-trends-section";
import { TopEventTypesRow } from "./top-event-types-row";
import { MonitoringStatusStrip } from "./monitoring-status-strip";
import { QuickActionsRow } from "./quick-actions-row";
import { ScrollReveal } from "./scroll-reveal";


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
        <div className="min-w-0 flex items-start gap-3">
          <PublisherLogo publisherName={article.publisher_name} size={40} className="mt-1" />
          <div>
            <ArticleMetadata publisherName={article.publisher_name} publishedAt={article.published_at} collectedAt={article.collected_at} compact />
            <h3 className="mt-2 break-words text-sm font-semibold leading-6 text-text">{article.title}</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {article.risk_level && <Badge tone={toneForRisk(article.risk_level)}>{formatLabel(article.risk_level)}{article.risk_score !== null ? ` · ${article.risk_score}` : ""}</Badge>}
              {article.event_type && <Badge>{formatLabel(article.event_type)}</Badge>}
              {article.business_impact && <Badge>{formatLabel(article.business_impact)}</Badge>}
              {article.sentiment && <Badge>{formatLabel(article.sentiment)}</Badge>}
            </div>
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

  // ── Pagination ───────────────────────────────────────────────────
  const PAGE_SIZE = 20;
  const [page, setPage] = useState(1);
  const listRef = useRef<HTMLDivElement>(null);

  const totalPages = isCompanies
    ? Math.max(1, Math.ceil(companies.length / PAGE_SIZE))
    : Math.max(1, Math.ceil(articles.length / PAGE_SIZE));

  const pagedArticles = articles.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const pagedCompanies = companies.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const goToPage = (next: number) => {
    setPage(next);
    listRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  };

  // ── Keyboard ────────────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // ── Rendered item range label ───────────────────────────────────
  const totalItems = isCompanies ? companies.length : articles.length;
  const rangeStart = totalItems === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, totalItems);

  return createPortal(
              <div
                className="fixed inset-0 z-[60] flex items-center justify-center bg-text/40 p-3 sm:p-6"
              >
                <section
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="kpi-detail-title"
                  className="flex h-[80dvh] max-h-[760px] w-full max-w-4xl min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_2px_8px_rgba(28,23,52,0.10)]"
                >
                  {/* ── Header ── */}
                  <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6 shrink-0">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Overview Detail</p>
                      <h2 id="kpi-detail-title" className="mt-1 text-lg font-semibold text-text">{title}</h2>
                      <p className="mt-1 text-sm text-muted">
                        {loading
                          ? "Loading current data..."
                          : totalItems === 0
                            ? "0 items"
                            : `${detailCount.toLocaleString()} ${detailCount === 1 ? "item" : "items"} · showing ${rangeStart}–${rangeEnd}`}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={onClose}
                      aria-label="Close detail modal"
                      className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    >
                      <X size={17} aria-hidden="true" />
                    </button>
                  </header>
                  {/* ── Scrollable body ── */}
                  <div ref={listRef} className="min-h-0 flex-1 overflow-y-auto px-5 py-5 sm:px-6">
                    {error ? (
                      <EmptyState title="Unable to load details" description={error} />
                    ) : loading ? (
                      <div className="space-y-3">
                        {Array.from({ length: 4 }).map((_, i) => (
                          <div key={i} className="rounded-lg border border-border bg-surface p-4">
                            <Skeleton className="h-6 w-1/3 mb-2" />
                            <Skeleton className="h-4 w-1/4" />
                          </div>
                        ))}
                      </div>
                    ) : isCompanies ? (
                      pagedCompanies.length === 0 ? (
                        <EmptyState title="No monitored companies found." />
                      ) : (
                        <div className="space-y-3">
                          {pagedCompanies.map((company) => (
                            <article key={company.id} className="rounded-lg border border-border bg-surface-raised p-4">
                              <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                  <h3 className="font-semibold text-text">{company.name}</h3>
                                  <p className="mt-1 text-sm text-muted">{company.is_active ? "Active monitoring" : "Inactive"}</p>
                                </div>
                                <Badge>{company.monitoring_topics.length} monitoring {company.monitoring_topics.length === 1 ? "category" : "categories"}</Badge>
                              </div>
                              {company.aliases.length > 0 && (
                                <p className="mt-3 text-sm text-body">Aliases: {company.aliases.join(", ")}</p>
                              )}
                            </article>
                          ))}
                        </div>
                      )
                    ) : pagedArticles.length === 0 ? (
                      <EmptyState
                        title={selectedMetric === "critical-risk" ? "No critical-risk articles found." : "No matching articles found."}
                      />
                    ) : (
                      <div className="space-y-3">
                        {pagedArticles.map((article) => (
                          <ArticleRow
                            key={`${article.article_id}-${article.risk_level ?? "article"}`}
                            article={article}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                  {/* ── Pagination footer — only shown when there is more than one page ── */}
                  {!loading && !error && totalPages > 1 && (
                    <footer className="shrink-0 flex items-center justify-between gap-3 border-t border-border bg-surface-raised px-5 py-3 sm:px-6">
                      <p className="text-xs text-muted">
                        Page {page} of {totalPages}
                      </p>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => goToPage(Math.max(1, page - 1))}
                          disabled={page === 1}
                          aria-label="Previous page"
                          className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-surface px-3 text-sm font-medium text-text-body transition-colors hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          <ChevronLeft size={15} aria-hidden="true" />
                          Prev
                        </button>
                        {/* Page number pills — show up to 5 around current */}
                        <div className="hidden sm:flex items-center gap-1">
                          {Array.from({ length: totalPages }, (_, i) => i + 1)
                            .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                            .reduce<(number | "…")[]>((acc, p, idx, arr) => {
                              if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("…");
                              acc.push(p);
                              return acc;
                            }, [])
                            .map((item, idx) =>
                              item === "…" ? (
                                <span key={`ellipsis-${idx}`} className="px-1.5 text-xs text-muted select-none">…</span>
                              ) : (
                                <button
                                  key={item}
                                  type="button"
                                  onClick={() => goToPage(item as number)}
                                  aria-label={`Go to page ${item}`}
                                  aria-current={page === item ? "page" : undefined}
                                  className={`inline-flex h-8 w-8 items-center justify-center rounded-lg text-xs font-semibold transition-colors ${
                                    page === item
                                      ? "bg-primary text-white"
                                      : "border border-border bg-surface text-text-body hover:bg-surface-sunken"
                                  }`}
                                >
                                  {item}
                                </button>
                              )
                            )}
                        </div>
                        <button
                          type="button"
                          onClick={() => goToPage(Math.min(totalPages, page + 1))}
                          disabled={page === totalPages}
                          aria-label="Next page"
                          className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-surface px-3 text-sm font-medium text-text-body transition-colors hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Next
                          <ChevronRight size={15} aria-hidden="true" />
                        </button>
                      </div>
                    </footer>
                  )}
                </section>
              </div>,
              document.body,
            );
}


export function OverviewContent({ 
  initialOverview, 
  initialIntelligence,
  companyName,
  initialAnalyticsOverview,
  initialEventAnalytics,
  initialSourceAnalytics,
  initialTrendPoints,
  initialSentiment,
  initialCategoryDistribution,
  timeWindow,
}: { 
  initialOverview: DashboardOverview;
  initialIntelligence: DashboardIntelligenceItem[];
  companyName: string;
  initialAnalyticsOverview: AnalyticsOverview;
  initialEventAnalytics: EventAnalyticsResponse;
  initialSourceAnalytics: SourceAnalyticsResponse;
  initialTrendPoints: ArticleTrendPoint[];
  initialSentiment: SentimentSnapshot;
  initialCategoryDistribution: Record<string, number>;
  timeWindow: { start: string, end: string };
}) {
  const [overview, setOverview] = useState<DashboardOverview>(initialOverview);
  const [, setIntelligence] = useState<DashboardIntelligenceItem[]>(initialIntelligence);
  const [, setAnalyticsOverview] = useState<AnalyticsOverview>(initialAnalyticsOverview);
  const [, setEventAnalytics] = useState<EventAnalyticsResponse>(initialEventAnalytics);
  const [, setSourceAnalytics] = useState<SourceAnalyticsResponse>(initialSourceAnalytics);

  // ── New widget state ──────────────────────────────────────────────────────
  const [trendPoints, setTrendPoints] = useState<ArticleTrendPoint[]>(initialTrendPoints);
  const [sentiment, setSentiment] = useState<SentimentSnapshot>(initialSentiment);
  const [categoryDistribution, setCategoryDistribution] = useState<Record<string, number>>(initialCategoryDistribution);
  const [lastSyncTimestamp, setLastSyncTimestamp] = useState<number | null>(null);

  // Per-widget error flags — keep last good data visible, show inline indicator
  const [trendError, setTrendError] = useState(false);
  const [sentimentError, setSentimentError] = useState(false);
  const [categoryError, setCategoryError] = useState(false);

  const [liveStatus, setLiveStatus] = useState<"live" | "updating" | "delayed">("live");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const [selectedMetric, setSelectedMetric] = useState<SelectedMetric | null>(null);
  const [articles, setArticles] = useState<DashboardArticleItem[]>([]);
  const [companies, setCompanies] = useState<DashboardCompanyItem[]>([]);
  const [detailCount, setDetailCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Auto-refresh: all 4 new sources + existing KPI data in one Promise.all ─
  useAutoRefresh(
    async () => {
      setLiveStatus("updating");
      // Existing KPI refresh
      const kpiRefresh = Promise.all([
        getDashboardOverview(),
        getDashboardIntelligence(6),
        getAnalyticsOverview(undefined, timeWindow.start, timeWindow.end),
        getEventAnalytics(timeWindow.start, timeWindow.end),
        getSourceAnalytics(timeWindow.start, timeWindow.end),
      ]).then(([newOverview, newIntel, newAnalytics, newEvents, newSources]) => {
        setOverview(newOverview);
        setIntelligence(newIntel.items);
        setAnalyticsOverview(newAnalytics);
        setEventAnalytics(newEvents);
        setSourceAnalytics(newSources);
      }).catch(() => { /* keep last KPI data */ });

      // New widget refreshes — each fails independently
      const trendRefresh = getArticleTrend(timeWindow.start, timeWindow.end, "day")
        .then((pts) => { setTrendPoints(pts); setTrendError(false); })
        .catch(() => setTrendError(true));

      const sentimentRefresh = getSentimentTrend(timeWindow.start, timeWindow.end)
        .then((s) => {
          setSentiment({ positive: s.positive, neutral: s.neutral, negative: s.negative });
          setSentimentError(false);
        })
        .catch(() => setSentimentError(true));

      const categoryRefresh = getBusinessImpact(timeWindow.start, timeWindow.end)
        .then((b) => { setCategoryDistribution(b.category_distribution); setCategoryError(false); })
        .catch(() => setCategoryError(true));

      await Promise.all([kpiRefresh, trendRefresh, sentimentRefresh, categoryRefresh]);

      setLiveStatus("live");
      setLastUpdated(new Date());
      setLastSyncTimestamp(Date.now());
    },
    { intervalMs: 30_000 }
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

  const isRefreshing = liveStatus === "updating";

  return (
    <div className="flex flex-col">
      {/* Hero — always visible, no scroll animation needed */}
      <OverviewHero
        companyName={companyName}
        liveStatus={liveStatus}
        lastUpdated={lastUpdated}
      />

      {/* ── SECTION 1: COVERAGE KPIs ─────────────────────────────────────── */}
      <section className="mt-2">
        <ScrollReveal direction="up" delay={0} duration={500}>
          <h2 className="mb-4 text-base font-semibold text-text">Coverage</h2>
        </ScrollReveal>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {/* Each KPI card slides in with a staggered delay */}
          {[
            <OverviewMetricCard
              key="total"
              label="Total Articles"
              value={overview.total_articles}
              icon={KpiArticleIcon}
              iconColorClass="bg-primary-soft text-primary"
              sparklineColor="var(--color-primary)"
              onOpen={() => openMetric("total")}
            />,
            <OverviewMetricCard
              key="processed"
              label="Processed Intelligence"
              value={overview.processed_articles}
              icon={KpiIntelligenceIcon}
              iconColorClass="bg-primary-soft text-primary"
              sparklineColor="var(--color-primary)"
              onOpen={() => openMetric("processed")}
            />,
            <OverviewMetricCard
              key="companies"
              label="Monitored Companies"
              value={overview.total_companies}
              icon={KpiCompanyIcon}
              iconColorClass="bg-primary-soft text-primary"
              sparklineColor="var(--color-primary)"
              onOpen={() => openMetric("companies")}
            />,
            <OverviewMetricCard
              key="high"
              label="High Risk"
              value={overview.high_risk_items}
              icon={KpiHighRiskIcon}
              iconColorClass="bg-transparent text-critical"
              onOpen={() => openMetric("high-risk")}
            />,
            <OverviewMetricCard
              key="critical"
              label="Critical Risk"
              value={overview.critical_risk_items}
              icon={KpiCriticalRiskIcon}
              iconColorClass="bg-transparent text-medium"
              onOpen={() => openMetric("critical-risk")}
            />,
          ].map((card, i) => (
            <ScrollReveal key={i} direction="up" delay={i * 60} duration={550} threshold={0.05}>
              {card}
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* ── SECTION 2: SIGNAL TRENDS ─────────────────────────────────────── */}
      <ScrollReveal direction="up" delay={0} duration={700} threshold={0.08}>
        <SignalTrendsSection
          trendPoints={trendPoints}
          sentiment={sentiment}
          isRefreshing={isRefreshing}
          trendError={trendError}
          sentimentError={sentimentError}
          lastSyncTimestamp={lastSyncTimestamp}
        />
      </ScrollReveal>

      {/* ── SECTION 3: TOP EVENT TYPES ────────────────────────────────────── */}
      <ScrollReveal direction="up" delay={0} duration={650} threshold={0.1}>
        <TopEventTypesRow
          categoryDistribution={categoryDistribution}
          refreshError={categoryError}
        />
      </ScrollReveal>

      {/* ── SECTION 4: MONITORING STATUS STRIP ───────────────────────────── */}
      <ScrollReveal direction="left" delay={0} duration={600} threshold={0.1}>
        <MonitoringStatusStrip
          totalCompanies={overview.total_companies}
          lastSyncTimestamp={lastSyncTimestamp}
          refreshError={liveStatus === "delayed"}
        />
      </ScrollReveal>

      {/* ── SECTION 5: QUICK ACTIONS ─────────────────────────────────────── */}
      <ScrollReveal direction="up" delay={0} duration={700} threshold={0.08}>
        <QuickActionsRow />
      </ScrollReveal>

      {/* ── Footer note ───────────────────────────────────────────────────── */}
      <ScrollReveal direction="fade" delay={100} duration={800} threshold={0.1}>
        <p className="mt-6 text-xs text-muted">
          Note: &quot;Critical Signals&quot; article list removed from Overview · full feed lives on the{" "}
          <Link href="/intelligence" className="font-semibold text-primary hover:underline">
            Intelligence page
          </Link>
          .
        </p>
      </ScrollReveal>

      {selectedMetric && (
        <DetailModal
          key={selectedMetric}
          selectedMetric={selectedMetric}
          articles={articles}
          companies={companies}
          detailCount={detailCount}
          loading={loading}
          error={error}
          onClose={() => setSelectedMetric(null)}
        />
      )}
    </div>
  );
}
