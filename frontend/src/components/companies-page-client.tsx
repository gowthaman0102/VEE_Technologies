"use client";

import { useEffect, useRef, useState } from "react";
import { 
  Activity, AlertTriangle, BarChart3, Bell, ChevronRight,
  FileText, Skull, X, Layers,
  Settings, Eye
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { ArticleMetadata } from "@/components/article-metadata";
import { ArticleViewButton } from "@/components/article-view-button";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { 
  getDashboardArticles, getDashboardCompanies, getRiskDrilldown, 
  type DashboardArticleItem, type DashboardArticleMetric, 
  type DashboardCompanyItem, type DashboardCompaniesResponse 
} from "@/lib/api";
import { formatLabel } from "@/lib/format";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

type MetricKey = "triage" | "risks" | "high" | "critical" | "alerts";
type MetricTone = "blue" | "amber" | "red" | "critical" | "purple";

const METRIC_CONFIG: Array<{ key: MetricKey; label: string; description: string; tone: MetricTone; icon: LucideIcon }> = [
  { key: "triage", label: "Triage", description: "Items under review", tone: "blue", icon: FileText },
  { key: "risks", label: "Risks", description: "Potential risks identified", tone: "amber", icon: AlertTriangle },
  { key: "high", label: "High", description: "High priority matches", tone: "red", icon: BarChart3 },
  { key: "alerts", label: "Alerts", description: "Total alerts generated", tone: "purple", icon: Bell },
  { key: "critical", label: "Critical", description: "Critical threats detected", tone: "critical", icon: Skull },
];

function AnimatedValue({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef<number | null>(null);

  useEffect(() => {
    const previous = previousValue.current ?? 0;
    previousValue.current = value;
    if (previous === value) {
      setDisplayValue(value);
      return;
    }
    const startedAt = performance.now();
    const duration = 700;
    let frame = 0;
    const update = (now: number) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      // easeOutExpo
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setDisplayValue(Math.round(previous + (value - previous) * ease));
      if (progress < 1) frame = requestAnimationFrame(update);
    };
    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return <>{displayValue}</>;
}

function LiveMetricRing({ config, value, progress, onClick, index }: { config: (typeof METRIC_CONFIG)[number]; value: number; progress: number | null; onClick: () => void; index: number }) {
  const [changed, setChanged] = useState(false);
  const previousValue = useRef(value);

  const baseStyles = {
    blue: { ring: "var(--color-primary)", track: "var(--color-primary-soft)", text: "text-primary" },
    amber: { ring: "var(--color-medium)", track: "var(--color-medium-bg)", text: "text-medium" },
    red: { ring: "var(--color-critical)", track: "var(--color-critical-bg)", text: "text-critical" },
    critical: { ring: "var(--color-muted)", track: "var(--color-surface-sunken)", text: "text-muted" },
    purple: { ring: "var(--color-primary)", track: "var(--color-primary-soft)", text: "text-primary" },
  };

  const isCriticalActive = config.tone === "critical" && value > 0;
  const tone = isCriticalActive 
    ? { ring: "var(--color-high)", track: "var(--color-critical-bg)", text: "text-critical" }
    : baseStyles[config.tone];

  const MetricIcon = config.icon;
  const radius = 72; 
  const strokeWidth = 12;
  const size = 160;
  const circumference = 2 * Math.PI * radius;
  const visualProgress = progress ?? 1;
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setAnimatedProgress(visualProgress));
    return () => cancelAnimationFrame(frame);
  }, [visualProgress]);

  useEffect(() => {
    if (previousValue.current === value) return;
    previousValue.current = value;
    setChanged(true);
    const timeout = window.setTimeout(() => setChanged(false), 650);
    return () => window.clearTimeout(timeout);
  }, [value]);

  return (
    <button 
      type="button" 
      onClick={onClick} 
      aria-label={`${config.label}: ${value}`} 
      className="group relative flex flex-col items-center rounded-xl p-4 text-center transition-colors duration-150 hover:bg-surface-raised animate-[fadeIn_0.5s_ease-out_both] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35"
      style={{ animationDelay: `${80 + index * 50}ms` }}
    >
      <div className="relative h-[120px] w-[120px] lg:h-[120px] lg:w-[120px] xl:h-[128px] xl:w-[128px]">
        <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full -rotate-90 drop-shadow-sm" aria-hidden="true">
          <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={tone.track} strokeWidth={strokeWidth} />
          <circle 
            cx={size/2} cy={size/2} r={radius} fill="none" stroke={tone.ring} 
            strokeLinecap="round" strokeWidth={strokeWidth} 
            strokeDasharray={circumference} 
            strokeDashoffset={circumference * (1 - animatedProgress)}
            className="transition-[stroke-dashoffset] duration-1000 ease-out" 
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 xl:gap-1.5 text-center">
          <MetricIcon size={24} className={tone.text} strokeWidth={2.5} aria-hidden="true" />
          <span className={`text-[32px] font-bold leading-none tracking-tight text-text transition-transform duration-300 xl:text-[36px] ${changed ? 'scale-110 text-primary' : ''}`}>
            <AnimatedValue value={value} />
          </span>
        </div>
      </div>
      
      <div className="mt-3">
        <span className={`text-[12px] font-bold uppercase tracking-[0.08em] ${tone.text}`}>{config.label}</span>
        <p className="mt-1 px-2 text-[12px] leading-tight text-muted">{config.description}</p>
      </div>
    </button>
  );
}

function PriorityTopicCard({ priority, topics, index }: { priority: "high" | "medium" | "low"; topics: string[]; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const visibleTopics = expanded ? topics : topics.slice(0, 5);

  const styles = {
    high: {
      bg: "bg-critical-bg",
      border: "border-critical-border",
      iconBg: "bg-critical-bg",
      iconColor: "text-critical",
      titleColor: "text-critical",
      dot: "bg-critical",
      desc: "High risk and time-sensitive subjects",
      footer: "Highest priority monitoring",
      Icon: AlertTriangle,
      Visual: AlertTriangle,
      visualMotion: "animate-pulse",
    },
    medium: {
      bg: "bg-medium-bg",
      border: "border-medium-border",
      iconBg: "bg-medium-bg",
      iconColor: "text-medium",
      titleColor: "text-medium",
      dot: "bg-medium",
      desc: "Important topics to monitor closely",
      footer: "Active monitoring",
      Icon: BarChart3,
      Visual: BarChart3,
      visualMotion: "animate-[dashboard-rise-in_1.8s_ease-in-out_infinite_alternate]",
    },
    low: {
      bg: "bg-low-bg",
      border: "border-low-border",
      iconBg: "bg-low-bg",
      iconColor: "text-low",
      titleColor: "text-low",
      dot: "bg-low",
      desc: "General awareness and trending topics",
      footer: "Routine monitoring",
      Icon: Eye,
      Visual: Eye,
      visualMotion: "animate-pulse",
    }
  }[priority];

  return (
    <article 
      className={`group companies-topic-card relative flex flex-col overflow-hidden rounded-xl border ${styles.border} ${styles.bg} p-3 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong animate-[fadeIn_0.5s_ease-out_both]`}
      style={{ animationDelay: `${250 + index * 60}ms` }}
    >
      <styles.Visual
        className={`pointer-events-none absolute -bottom-10 -right-10 h-44 w-44 opacity-15 transition-transform duration-700 group-hover:scale-110 ${styles.iconColor} ${styles.visualMotion}`}
        strokeWidth={1.4}
        aria-hidden="true"
      />

      <div className="relative z-10 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${styles.iconBg} ${styles.iconColor}`}>
            <styles.Icon size={20} strokeWidth={2.5} aria-hidden="true" />
          </div>
          <div>
            <h3 className={`text-[15px] font-bold capitalize ${styles.titleColor}`}>{priority} Priority</h3>
            <p className="mt-0.5 text-[11px] font-medium text-muted">{styles.desc}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          aria-label={`${expanded ? "Collapse" : "Show all"} ${priority} priority topics`}
          aria-expanded={expanded}
          className={`flex items-center gap-1 rounded-md px-2 py-1 text-[13px] font-bold ${styles.iconColor} transition-opacity hover:bg-white/40 hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35`}
        >
          {topics.length} {topics.length === 1 ? "Topic" : "Topics"}
          <ChevronRight size={16} aria-hidden="true" className={`transition-transform ${expanded ? "rotate-90" : ""}`} />
        </button>
      </div>

      <ul className="relative z-10 mt-3 flex-1 space-y-1.5">
        {visibleTopics.map((t, i) => (
          <li key={t} className="flex cursor-default items-start gap-2 text-[12px] font-medium text-text transition-colors hover:text-primary animate-[fadeInUp_0.3s_ease-out_both]" style={{ animationDelay: `${(i * 30)}ms` }}>
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${styles.dot}`} aria-hidden="true" />
            {t}
          </li>
        ))}
      </ul>

      <div className="relative z-10 mt-3 flex items-center justify-between border-t border-white/40 pt-3">
        <span className="text-[12px] font-medium text-muted">{styles.footer} · {topics.length} {topics.length === 1 ? "topic" : "topics"}</span>
        {topics.length > 5 && (
          <button 
            type="button" 
            onClick={() => setExpanded(!expanded)} 
            className={`text-[12px] font-bold ${styles.iconColor} hover:opacity-80 transition-opacity`}
          >
            {expanded ? "Show less" : `+${topics.length - 5} more`}
          </button>
        )}
      </div>
    </article>
  );
}

function MetricModal({ metric, articles, loading, onClose }: { metric: MetricKey; articles: DashboardArticleItem[]; loading: boolean; onClose: () => void }) {
  const config = METRIC_CONFIG.find((item) => item.key === metric)!;
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);
  
  const emptyTitle = metric === "critical" ? "No critical threats detected." : metric === "alerts" ? "No alert-linked articles found." : "No matching articles found.";
  
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-text/40 p-0 sm:items-center sm:p-6 transition-opacity animate-[fadeIn_0.2s_ease-out]" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="company-metric-title" className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_2px_8px_rgba(28,23,52,0.10)] animate-[slideUp_0.3s_ease-out]">
        <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Live Intelligence Detail</p>
            <h2 id="company-metric-title" className="mt-1 text-lg font-bold text-text">{config.label}</h2>
            <p className="mt-1 text-sm text-muted">{loading ? "Loading current data..." : `${articles.length} ${articles.length === 1 ? "item" : "items"}`}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close detail modal" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            <X size={17} aria-hidden="true" />
          </button>
        </header>
        <div className="overflow-y-auto px-5 py-5 sm:px-6 bg-surface-raised">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Activity className="animate-spin text-primary mb-3" size={24} />
              <p className="text-sm text-muted">Loading current data...</p>
            </div>
          ) : articles.length === 0 ? (
            <EmptyState title={emptyTitle} />
          ) : (
            <div className="space-y-3">
              {articles.map((article) => (
                <article key={`${article.article_id}-${article.risk_level ?? "article"}`} className="rounded-xl border border-border bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <ArticleMetadata publisherName={article.publisher_name} publishedAt={article.published_at} collectedAt={article.collected_at} compact />
                      <h3 className="mt-3 break-words text-[15px] font-bold leading-relaxed text-text">{article.title}</h3>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {article.risk_level && <Badge tone={toneForRisk(article.risk_level)}>{formatLabel(article.risk_level)}</Badge>}
                        {article.event_type && <Badge>{formatLabel(article.event_type)}</Badge>}
                      </div>
                    </div>
                    <ArticleViewButton articleId={article.article_id} sourceUrl={article.url} sourceName={article.source_name} className="shrink-0 self-start" />
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function groupTopics(company: DashboardCompanyItem) {
  const grouped = { high: [] as string[], medium: [] as string[], low: [] as string[] };
  for (const topic of company.monitoring_topics) {
    const priority = topic.priority.toLowerCase();
    if (priority === "high" || priority === "medium" || priority === "low") grouped[priority].push(topic.topic);
    else grouped.low.push(topic.topic); // fallback
  }
  return grouped;
}

export function CompaniesPageClient({ initialData }: { initialData: DashboardCompaniesResponse }) {
  const [data, setData] = useState(initialData);
  const [liveStatus, setLiveStatus] = useState<"live" | "delayed">("live");
  const [selectedMetric, setSelectedMetric] = useState<MetricKey | null>(null);
  const [articles, setArticles] = useState<DashboardArticleItem[]>([]);
  const [loading, setLoading] = useState(false);
  
  const company = data.items[0];

  useAutoRefresh(async () => {
    try {
      setData(await getDashboardCompanies());
      setLiveStatus("live");
    } catch {
      setLiveStatus("delayed");
    }
  }, { intervalMs: 60_000 });

  if (!company) return <main className="px-6 py-8 lg:px-8"><EmptyState title="No monitored companies found." /></main>;
  
  const topics = groupTopics(company);
  const totalRisks = company.risk_assessment_count;
  const metricValues: Record<MetricKey, number> = { 
    triage: company.triage_count, 
    risks: company.risk_assessment_count, 
    high: company.high_risk_count, 
    critical: company.critical_risk_count, 
    alerts: company.alert_count 
  };

  const openMetric = async (metric: MetricKey) => {
    setSelectedMetric(metric);
    setArticles([]);
    setLoading(true);
    try {
      if (metric === "risks") {
        setArticles((await getRiskDrilldown("total_assessments")).items);
      } else if (metric === "alerts") {
        setArticles((await getRiskDrilldown("immediate_alert")).items);
      } else {
        const apiMetric: DashboardArticleMetric = metric === "triage" ? "processed" : metric === "high" ? "high-risk" : "critical-risk";
        setArticles((await getDashboardArticles(apiMetric)).items);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="companies-page relative min-h-[calc(100vh-74px)] w-full overflow-hidden bg-surface-raised">
          <PageAmbient kind="companies" />
          <div className="relative z-10 mx-auto flex min-h-full w-full max-w-[1600px] flex-col gap-5 px-5 py-5 sm:px-6 lg:px-8">
        <CosmicPageHero
  variant="intelligence"
  imageSrc="/companies-hero.png"
  eyebrow="COMPANIES"
  title="Live Intelligence Overview"
  description={`Real-time analysis from ${company.name} across monitored sources.`}
/>
        {/* Live Intelligence Card */}
        <section className="shrink-0 rounded-[22px] border border-border bg-white p-4 shadow-[0_8px_25px_rgba(20,50,60,0.04)] animate-[fadeIn_0.5s_ease-out_100ms_both] lg:p-4">
          <div className="flex flex-col justify-between gap-3 border-b border-border pb-3 md:flex-row md:items-center">
            <div className="flex items-center gap-5">
              {liveStatus === "live" && (
                <div className="flex items-center gap-2 text-[14px] font-bold text-low">
                  <Activity size={16} strokeWidth={2.5} className="animate-pulse" />
                  Scanning new content...
                </div>
              )}
              <div className={`flex items-center gap-2.5 rounded-full border px-4 py-2 text-[14px] font-bold shadow-sm ${liveStatus === "live" ? "border-low-border bg-low-bg text-low" : "border-medium-border bg-medium-bg text-medium"}`}>
                <span className={`h-2.5 w-2.5 rounded-full ${liveStatus === 'live' ? 'bg-low animate-pulse' : 'bg-medium'}`} />
                {liveStatus === "live" ? "Live" : "Update delayed"}
              </div>
            </div>
          </div>

          <div className="mt-2 grid grid-cols-2 items-start gap-2 md:grid-cols-3 lg:grid-cols-5 lg:gap-3 xl:gap-4">
            {METRIC_CONFIG.map((config, index) => (
              <LiveMetricRing 
                key={config.key} 
                config={config} 
                index={index}
                value={metricValues[config.key]} 
                progress={
                  config.key === "high" || config.key === "critical" 
                    ? (totalRisks > 0 ? metricValues[config.key] / totalRisks : 0) 
                    : null
                } 
                onClick={() => void openMetric(config.key)} 
              />
            ))}
          </div>
        </section>

        {/* Monitoring Topics */}
        <section className="min-h-0 flex-1 animate-[fadeIn_0.5s_ease-out_200ms_both]">
          <div className="flex flex-col justify-between gap-4 border-b border-border pb-4 md:flex-row md:items-end">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-border shadow-sm text-text">
                <Layers size={22} strokeWidth={2.2} />
              </div>
              <div>
                <h2 className="text-[22px] lg:text-[24px] font-bold text-text">
                  Monitoring Topics
                </h2>
                <p className="mt-1.5 text-[15px] font-medium text-muted">AI is monitoring <span className="font-semibold text-text">{company.monitoring_topics.length} topics</span> across global media and online sources</p>
              </div>
            </div>
            
            <div className="flex items-center gap-5">
              <Link href="/watchlist" className="flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-2.5 text-sm font-semibold text-text shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong">
                <Settings size={16} /> Manage Topics
              </Link>
            </div>
          </div>

          <div className="mt-5 grid min-h-0 grid-cols-1 gap-5 lg:grid-cols-3 lg:gap-6 items-start">
            <PriorityTopicCard priority="high" topics={topics.high} index={0} />
            <PriorityTopicCard priority="medium" topics={topics.medium} index={1} />
            <PriorityTopicCard priority="low" topics={topics.low} index={2} />
          </div>
        </section>
      </div>
      
      {selectedMetric && <MetricModal metric={selectedMetric} articles={articles} loading={loading} onClose={() => setSelectedMetric(null)} />}
    </main>
  );
}
