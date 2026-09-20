"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useEffect, useState } from "react";
import { X, Activity, BarChart3, FileText, Search, Tags, ArrowRight } from "lucide-react";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import Link from "next/link";

import { ArticleViewButton } from "@/components/article-view-button";
import { ArticleMetadata } from "@/components/article-metadata";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import {
  DashboardArticleItem,
  DashboardArticleMetric,
  DashboardCompanyItem,
  DashboardOverview,
  DashboardIntelligenceItem,
  getDashboardArticles,
  getDashboardCompanies,
  getDashboardOverview,
  getDashboardIntelligence,
  AnalyticsOverview,
  ArticleCategory,
  ReportBatchHistoryItem,
} from "@/lib/api";
import { formatLabel, formatRelativeTime } from "@/lib/format";

import { PublisherLogo } from "./publisher-logo";

type SelectedMetric = DashboardArticleMetric | "companies";

function compactNumber(value: number) {
  return value > 9999 ? `${(value / 1000).toFixed(1)}K` : value.toLocaleString();
}

function SignalPanel({ overview }: { overview: DashboardOverview }) {
  const rows = [
    ["Articles", overview.total_articles],
    ["Processed", overview.processed_articles],
    ["High risk", overview.high_risk_items],
    ["Critical", overview.critical_risk_items],
  ] as const;
  const max = Math.max(...rows.map(([, value]) => value), 1);
  return <section className="overview-panel signal-panel">
    <div className="overview-panel-header"><div><p className="overview-panel-kicker">Current snapshot</p><h2><Activity size={15} /> Signal Matrix</h2></div><span className="overview-live"><i /> Live</span></div>
    <div className="signal-visual" aria-label="Current signal counts by processing state">
      <div className="signal-orbit signal-orbit-one" /><div className="signal-orbit signal-orbit-two" /><div className="signal-core"><span>{compactNumber(overview.total_articles)}</span><small>articles</small></div>
      <span className="signal-node signal-node-one" /><span className="signal-node signal-node-two" /><span className="signal-node signal-node-three" />
    </div>
    <div className="signal-metrics">{rows.slice(0, 3).map(([label, value]) => <div key={label}><strong>{compactNumber(value)}</strong><span>{label}</span><b><i style={{ width: `${Math.max(4, (value / max) * 100)}%` }} /></b></div>)}</div>
  </section>;
}

function TopicsPanel({ categories }: { categories: ArticleCategory[] }) {
  const active = categories.filter((item) => item.is_active).slice(0, 5);
  return <section className="overview-panel topics-panel"><div className="overview-panel-header"><div><p className="overview-panel-kicker">Configured coverage</p><h2><Tags size={15} /> Monitoring Topics</h2></div><Link href="/watchlist" className="panel-link">Manage <ArrowRight size={12} /></Link></div>{active.length ? <div className="topic-list">{active.map((item, index) => <div className="topic-row" key={item.id}><span className="topic-rank">{String(index + 1).padStart(2, "0")}</span><span className="topic-name">{item.name}</span><span className="topic-state">Active</span></div>)}</div> : <EmptyState title="No enabled monitoring topics" description="Add categories in Article Settings." />}</section>;
}

function AnalyticsPanel({ analytics, overview }: { analytics: AnalyticsOverview | null; overview: DashboardOverview }) {
  const risk = analytics?.risk ?? {};
  const values = Object.entries(risk).filter(([, value]) => typeof value === "number");
  const total = values.reduce((sum, [, value]) => sum + value, 0);
  const segments = values.length ? values : [["Processed", overview.processed_articles]] as [string, number][];
  let offset = 0;
  const colors = ["#4d8dff", "#43d4e7", "#f0b34c", "#43ce8c", "#7e66ff"];
  const gradient = segments.map(([, value], index) => { const start = total ? (offset / total) * 360 : 0; offset += value; const end = total ? (offset / total) * 360 : 360; return `${colors[index % colors.length]} ${start}deg ${end}deg`; }).join(", ");
  return <section className="overview-panel analytics-panel"><div className="overview-panel-header"><div><p className="overview-panel-kicker">Last 30 days</p><h2><BarChart3 size={15} /> Analytics Snapshot</h2></div><Link href="/analytics" className="panel-link">View all <ArrowRight size={12} /></Link></div><div className="analytics-value"><strong>{compactNumber(analytics?.total_articles ?? overview.total_articles)}</strong><span>articles in range</span></div><div className="donut-wrap"><div className="overview-donut" style={{ background: `conic-gradient(${gradient})` }}><div><strong>{compactNumber(total || overview.processed_articles)}</strong><span>risk signals</span></div></div><div className="donut-legend">{segments.slice(0, 4).map(([label, value], index) => <div key={label}><i style={{ background: colors[index % colors.length] }} /><span>{formatLabel(label)}</span><b>{value}</b></div>)}</div></div></section>;
}

function ReportsPanel({ reports }: { reports: ReportBatchHistoryItem[] }) {
  return <section className="overview-panel reports-panel"><div className="overview-panel-header"><h2><FileText size={15} /> Reports</h2><Link href="/reports" className="panel-link">View all <ArrowRight size={12} /></Link></div>{reports.length ? <div className="report-list">{reports.slice(0, 4).map((report) => <Link href="/reports" className="report-row" key={report.batch_id}><FileText size={16} /><span><strong>{formatLabel(report.report_type)}</strong><small>{report.generated_at ? formatRelativeTime(new Date(report.generated_at)) : formatLabel(report.status)}</small></span><ArrowRight size={13} /></Link>)}</div> : <EmptyState title="No report batches yet" description="Generated reports will appear here." />}</section>;
}

function QuickSearchPanel() {
  return <section className="overview-panel quick-search-panel"><div className="overview-panel-header"><h2><Search size={15} /> Quick Search</h2><Link href="/search" className="panel-link">Open <ArrowRight size={12} /></Link></div><Link href="/search" className="quick-search-field"><Search size={14} /> Search monitored intelligence...</Link><p>Search by keyword or semantic meaning.</p></section>;
}

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
          <button type="button" onClick={onClose} aria-label="Close detail modal" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border text-muted transition-colors hover:border-border-strong hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"><X size={17} aria-hidden="true" /></button>
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

export function OverviewContent({ 
  initialOverview, 
  initialIntelligence,
  companyName,
  initialAnalytics,
  initialReports,
  initialCategories,
}: { 
  initialOverview: DashboardOverview;
  initialIntelligence: DashboardIntelligenceItem[];
  companyName: string;
  initialAnalytics: AnalyticsOverview | null;
  initialReports: ReportBatchHistoryItem[];
  initialCategories: ArticleCategory[];
}) {
  const [overview, setOverview] = useState<DashboardOverview>(initialOverview);
  const [intelligence, setIntelligence] = useState<DashboardIntelligenceItem[]>(initialIntelligence);
  const [liveStatus, setLiveStatus] = useState<"live" | "updating" | "delayed">("live");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(new Date());

  const [selectedMetric, setSelectedMetric] = useState<SelectedMetric | null>(null);
  const [articles, setArticles] = useState<DashboardArticleItem[]>([]);
  const [companies, setCompanies] = useState<DashboardCompanyItem[]>([]);
  const [detailCount, setDetailCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useAutoRefresh(
    async () => {
      setLiveStatus("updating");
      try {
        const [newOverview, newIntel] = await Promise.all([
          getDashboardOverview(),
          getDashboardIntelligence(6)
        ]);
        setOverview(newOverview);
        setIntelligence(newIntel.items);
        setLiveStatus("live");
        setLastUpdated(new Date());
      } catch {
        setLiveStatus("delayed");
      }
    },
    { intervalMs: 60_000 }
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

  return (
    <div className="flex flex-col">
      <section className="overview-intro">
        <div><p className="overview-intro-kicker">Near Real-Time Monitoring</p><h1>Here&apos;s what&apos;s happening</h1><p>Near real-time intelligence for {companyName || "the active company"} across monitored media.</p></div>
        <div className="overview-intro-status"><span className={`overview-live ${liveStatus === "delayed" ? "delayed" : ""}`}><i /> {liveStatus === "delayed" ? "Update delayed" : liveStatus === "updating" ? "Updating" : "Live"}</span><small>{lastUpdated ? formatRelativeTime(lastUpdated) : "Just now"}</small></div>
      </section>

      <section className="overview-summary-strip" aria-label="Current coverage summary">
        {["Articles", "Processed", "Companies", "High risk", "Critical"].map((label, index) => { const values = [overview.total_articles, overview.processed_articles, overview.total_companies, overview.high_risk_items, overview.critical_risk_items]; return <button type="button" key={label} onClick={() => index === 2 ? openMetric("companies") : index === 3 ? openMetric("high-risk") : index === 4 ? openMetric("critical-risk") : index === 1 ? openMetric("processed") : openMetric("total")}><span>{label}</span><strong>{compactNumber(values[index])}</strong></button>; })}
      </section>

      <section className="overview-command-grid">
        <div className="overview-column overview-column-left"><SignalPanel overview={overview} /><TopicsPanel categories={initialCategories} /></div>
        <section className="overview-panel feed-panel"><div className="overview-panel-header"><div><p className="overview-panel-kicker">Latest processed signals</p><h2><Activity size={15} /> Intelligence Feed</h2></div><Link href="/intelligence" className="panel-link">View all <ArrowRight size={12} /></Link></div>{intelligence.length ? <div className="overview-feed-list">{intelligence.slice(0, 5).map((item) => <div className="overview-feed-row" key={`${item.company_id}-${item.article_id}`}><PublisherLogo publisherName={item.publisher_name} size={36} /><div className="min-w-0 flex-1"><div className="overview-feed-meta">{item.publisher_name} <span>·</span> {formatRelativeTime(new Date(item.published_at ?? item.collected_at))}</div><h3>{item.headline || item.title}</h3><div className="overview-feed-badges"><Badge tone={toneForRisk(item.risk_level)}>{formatLabel(item.risk_level)}</Badge>{item.event_type && <Badge>{formatLabel(item.event_type)}</Badge>}</div></div><ArticleViewButton articleId={item.article_id} sourceUrl={item.url} sourceName={item.source_name} /></div>)}</div> : <EmptyState title="No processed intelligence" description="No recent intelligence is available yet." />}</section>
        <AnalyticsPanel analytics={initialAnalytics} overview={overview} />
        <div className="overview-column overview-column-right"><ReportsPanel reports={initialReports} /><QuickSearchPanel /><section className="overview-panel category-panel"><div className="overview-panel-header"><h2><Tags size={15} /> Categories</h2><Link href="/watchlist" className="panel-link">Manage <ArrowRight size={12} /></Link></div><div className="category-grid">{initialCategories.filter((item) => item.is_active).slice(0, 6).map((item) => <Link href="/watchlist" key={item.id}>{item.name}</Link>)}</div></section></div>
      </section>

      {selectedMetric && (
        <DetailModal 
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
