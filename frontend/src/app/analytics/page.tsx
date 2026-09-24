"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarDays,
  ChevronRight,
  FileText,
  Heart,
  Landmark,
  LockKeyhole,
  Package,
  Scale,
  Search,
  ShieldAlert,
  Smile,
  Sparkles,
  Trophy,
  UserRound,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  AnalyticsOverview,
  DashboardArticleItem,
  getActiveCompany,
  getDashboardArticles,
  getAnalyticsOverview,
  generateReport,
} from "@/lib/api";
import {
  TimeRangeSelector,
} from "@/components/time-range-selector";
import {
  resolveTimeRange,
  TimeRangePreset,
} from "@/lib/time-range";
import {
  useAutoRefresh,
} from "@/lib/use-auto-refresh";
import { EmptyState } from "@/components/ui/empty-state";
import { useCountUp } from "@/hooks/use-count-up";
import { ArticleRow } from "@/components/article-row";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";
import { toast } from "@/components/ui/toast";

const IMPACT_ICONS: LucideIcon[] = [
  BriefcaseBusiness,
  BarChart3,
  Scale,
  Landmark,
  LockKeyhole,
  Heart,
  UserRound,
  Package,
  BarChart3,
  Trophy,
];

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

async function withRetries<T>(operation: () => Promise<T>, attempts = 3) {
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await operation();
    } catch (cause) {
      lastError = cause;
      if (attempt < attempts - 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 350 * (attempt + 1)));
      }
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Unable to load Analytics data.");
}

function AnalyticsMetricCard({
  label,
  value,
  icon: Icon,
  iconClass,
  tintClass,
}: {
  label: string;
  value: number;
  icon: LucideIcon;
  iconClass: string;
  tintClass: string;
}) {
  const animatedValue = useCountUp(value, 650);
  return (
    <article className={`analytics-metric-enter relative overflow-hidden rounded-2xl border border-[rgba(90,72,160,0.12)] bg-gradient-to-br ${tintClass} px-5 py-4 shadow-[0_8px_20px_rgba(65,50,120,0.06)] transition-shadow hover:shadow-[0_10px_24px_rgba(65,50,120,0.1)]`}>
      <div className="relative z-10 flex items-start gap-4">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${iconClass}`}>
          <Icon size={21} strokeWidth={2.1} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-text-body">{label}</p>
          <p className="mt-1 text-[34px] font-extrabold leading-none tracking-tight text-text tabular-nums">{animatedValue.toLocaleString()}</p>
        </div>
      </div>
      <div className="absolute bottom-4 right-4 flex h-12 items-end gap-1 opacity-40" aria-hidden="true">
        {[18, 27, 21, 36, 30, 44, 39].map((height, index) => <span key={index} className="w-1.5 rounded-t-full bg-primary-soft" style={{ height }} />)}
      </div>
    </article>
  );
}

function SectionHeading({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
          <BarChart3 size={20} strokeWidth={2.2} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <h2 className="text-[17px] font-bold leading-tight text-text">{title}</h2>
          <p className="mt-1 text-[12px] leading-5 text-muted">{description}</p>
        </div>
      </div>
    </div>
  );
}

function EmptyCompetitors() {
  return (
    <div className="mt-5 flex min-h-[250px] flex-col items-center justify-center rounded-2xl bg-[#FAF9FF] px-6 text-center">
      <div className="relative flex h-20 w-24 items-center justify-center text-primary-soft">
        <FileText size={56} strokeWidth={1.4} />
        <Search className="absolute right-0 bottom-0 text-primary" size={31} strokeWidth={2.2} />
        <Sparkles className="absolute left-1 top-1 text-primary" size={14} />
      </div>
      <p className="mt-4 max-w-[260px] text-[14px] font-bold leading-5 text-text">No competitor mention data available for the selected period.</p>
      <p className="mt-2 max-w-[280px] text-[12px] leading-5 text-muted">Try selecting a different time range or check back later for new data.</p>
    </div>
  );
}

function ImpactArticlesModal({
  category,
  articles,
  loading,
  onClose,
  onGenerateReport,
  generating,
}: {
  category: string;
  articles: DashboardArticleItem[];
  loading: boolean;
  onClose: () => void;
  onGenerateReport: () => void;
  generating: boolean;
}) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-text/40 p-4 sm:p-6" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="impact-articles-title" className="flex h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_20px_60px_rgba(65,50,120,0.2)]">
        <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-primary">Business Impact</p>
            <h2 id="impact-articles-title" className="mt-1 text-xl font-bold text-text">{formatLabel(category)} articles</h2>
            <p className="mt-1 text-sm text-muted">{loading ? "Loading matching articles..." : `${articles.length} ${articles.length === 1 ? "article" : "articles"}`}</p>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={onGenerateReport} disabled={generating || articles.length === 0} className="inline-flex min-h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-xs font-bold text-white disabled:opacity-50">
              <FileText size={14} aria-hidden="true" /> {generating ? "Generating..." : "Generate report"}
            </button>
            <button type="button" onClick={onClose} aria-label="Close articles" className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"><X size={18} aria-hidden="true" /></button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto bg-surface-raised px-5 py-5 sm:px-6">
          {loading ? <div className="flex h-full items-center justify-center text-sm text-muted">Loading matching articles...</div> : articles.length === 0 ? <EmptyState title="No matching articles found." /> : <div className="space-y-3">{articles.map((article) => <ArticleRow key={article.article_id} article={article} />)}</div>}
        </div>
      </section>
    </div>
  );
}

export default function AnalyticsPage() {
  const [companyId, setCompanyId] =
    useState<number | null>(null);
  const [companyName, setCompanyName] =
    useState("");

  const [preset, setPreset] =
    useState<TimeRangePreset>("7d");

  const [customStart, setCustomStart] =
    useState("");
  const [customEnd, setCustomEnd] =
    useState("");

  const [data, setData] =
    useState<AnalyticsOverview | null>(null);

  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState("");
  const [impactCategory, setImpactCategory] = useState<string | null>(null);
  const [impactArticles, setImpactArticles] = useState<DashboardArticleItem[]>([]);
  const [impactLoading, setImpactLoading] = useState(false);
  const [generatingImpactReport, setGeneratingImpactReport] = useState(false);

  useEffect(() => {
    async function loadCompany() {
      try {
        const company = await withRetries(getActiveCompany);
        setCompanyId(company.id);
        setCompanyName(company.name);
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load active company.",
        );
        setLoading(false);
      }
    }

    void loadCompany();
  }, []);

  const loadAnalytics = useCallback(
    async (showLoading = true) => {
      if (companyId === null) {
        return;
      }

      if (
        preset === "custom"
        && (!customStart || !customEnd)
      ) {
        return;
      }

      if (showLoading) {
        setLoading(true);
      }

      setError("");

      try {
        const range = resolveTimeRange(
          preset,
          preset === "custom"
            ? {
                customStart,
                customEnd,
              }
            : {},
        );

        const overview = await withRetries(() => getAnalyticsOverview(companyId, range.start, range.end));

        setData(overview);
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load analytics.",
        );
      } finally {
        if (showLoading) {
          setLoading(false);
        }
      }
    },
    [
      companyId,
      preset,
      customStart,
      customEnd,
    ],
  );

  useEffect(() => {
    const timer = window.setTimeout(
      () => {
        void loadAnalytics();
      },
      0,
    );

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadAnalytics]);

  const autoRefreshEnabled =
    companyId !== null
    && !(
      preset === "custom"
      && (!customStart || !customEnd)
    );

  useAutoRefresh(
    () => loadAnalytics(false),
    {
      enabled: autoRefreshEnabled,
      intervalMs: 60_000,
    },
  );

  const openImpactArticles = async (category: string) => {
    setImpactCategory(category);
    setImpactArticles([]);
    setImpactLoading(true);
    try {
      const response = await getDashboardArticles("processed");
      const normalizedCategory = category.toLowerCase();
      const startTime = data ? new Date(data.start).getTime() : Number.NEGATIVE_INFINITY;
      const endTime = data ? new Date(data.end).getTime() : Number.POSITIVE_INFINITY;
      setImpactArticles(response.items.filter((article) => {
        const articleTime = new Date(article.published_at ?? article.collected_at).getTime();
        return article.business_impact?.toLowerCase() === normalizedCategory
          && articleTime >= startTime
          && articleTime <= endTime;
      }));
    } finally {
      setImpactLoading(false);
    }
  };

  const generateImpactReport = async () => {
    if (companyId === null || !data || !impactCategory || impactArticles.length === 0) return;
    setGeneratingImpactReport(true);
    try {
      await generateReport({
        company_id: companyId,
        report_type: `analytics_${preset}`,
        report_scope: "analytics",
        report_title: `${formatLabel(impactCategory)} articles - ${preset}`,
        time_mode: "media",
        start_date: data.start,
        end_date: data.end,
        article_ids: impactArticles.map((article) => article.article_id),
      });
      toast.success("Analytics report generated. It is available in Analytics reports.");
      window.location.href = "/reports?section=analytics";
    } catch (cause) {
      toast.error(cause instanceof Error ? cause.message : "Unable to generate analytics report.");
    } finally {
      setGeneratingImpactReport(false);
    }
  };

  return (
    <main className="analytics-page relative min-h-[calc(100vh-74px)] overflow-hidden bg-[radial-gradient(circle_at_70%_8%,rgba(130,100,255,0.09),transparent_34%),linear-gradient(180deg,#FBFBFF_0%,#F6F7FC_100%)] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
      <PageAmbient kind="analytics" />
      <div className="relative z-10 mx-auto w-full max-w-[1440px]">
        <CosmicPageHero variant="analytics" imageSrc="/analytics-hero.png" eyebrow="ANALYTICS" title={companyName ? `${companyName} Intelligence Trends` : "Intelligence Trends"} description="Explore stored media intelligence across configurable reporting periods." />

        <div className="mt-4 flex justify-end">
          <div className="rounded-2xl border border-border bg-surface px-3 py-2 shadow-[0_6px_18px_rgba(27,22,62,0.06)]">
            <TimeRangeSelector value={preset} onChange={setPreset} customStart={customStart} customEnd={customEnd} onCustomStartChange={setCustomStart} onCustomEndChange={setCustomEnd} includeCustom={false} />
          </div>
        </div>

        {error && (
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-critical-border bg-critical-bg p-4 text-sm text-critical">
            <span>{error}</span>
            <button type="button" onClick={() => companyId !== null ? void loadAnalytics() : window.location.reload()} className="rounded-lg border border-critical-border bg-white/60 px-3 py-1.5 text-xs font-bold text-critical transition-colors hover:bg-white">Retry</button>
          </div>
        )}

        {preset === "custom" &&
        (!customStart || !customEnd) ? (
          <EmptyState title="Select a custom time range" description="Choose both a start and end date to load analytics." />
        ) : loading ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((item) => <div key={item} className="h-[126px] animate-pulse rounded-2xl border border-border bg-white/70" />)}
          </div>
        ) : data === null ? (
          <div className="flex min-h-[180px] flex-col items-center justify-center rounded-2xl border border-border bg-white/60 p-6 text-center">
            <p className="text-sm font-semibold text-text">No analytics data available.</p>
            <p className="mt-1 text-xs text-muted">The latest Analytics request could not be completed.</p>
            <button type="button" onClick={() => companyId !== null ? void loadAnalytics() : window.location.reload()} className="mt-4 rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-primary-hover">Try again</button>
          </div>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Analytics summary metrics">
              <AnalyticsMetricCard label="Articles" value={data.total_articles} icon={FileText} iconClass="bg-[#EEE9FF] text-[#4F2DA8]" tintClass="from-white to-[#FBF9FF]" />
              <AnalyticsMetricCard label="Events" value={data.total_events} icon={CalendarDays} iconClass="bg-[#EAF2FF] text-[#3C78F0]" tintClass="from-white to-[#F8FBFF]" />
              <AnalyticsMetricCard label="Medium risk" value={data.risk.medium_risk_count ?? 0} icon={ShieldAlert} iconClass="bg-[#FFF6DD] text-[#C48712]" tintClass="from-white to-[#FFFDF6]" />
              <AnalyticsMetricCard label="Positive sentiment" value={data.sentiment.positive ?? 0} icon={Smile} iconClass="bg-[#E8F8F0] text-[#16A46A]" tintClass="from-white to-[#F7FFFB]" />
            </section>

            <section className="mt-5 grid items-start gap-5 xl:grid-cols-[1.15fr_0.85fr]">
              <article className="analytics-panel-enter rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6">
                <SectionHeading title="Business impact" description="Distribution of media intelligence by business impact category." />
                <div className="mt-5 space-y-1.5">
                  {Object.entries(data.business_impact).filter(([, value]) => value > 0).length === 0 ? (
                    <p className="rounded-xl bg-[#FAF9FF] px-4 py-8 text-center text-sm text-muted">No business-impact data for this period.</p>
                  ) : Object.entries(data.business_impact).filter(([, value]) => value > 0).map(([label, value], index) => {
                    const Icon = IMPACT_ICONS[index % IMPACT_ICONS.length];
                    const totalImpact = Object.values(data.business_impact).reduce((sum, count) => sum + count, 0);
                    const percentage = totalImpact > 0 ? (value / totalImpact) * 100 : 0;
                    return (
                      <div key={label} style={{ animationDelay: `${index * 55}ms` }} className="analytics-row-enter rounded-xl border border-transparent bg-[#FBFAFF] px-3 py-2.5 transition-colors hover:border-[#E9E5F4] hover:bg-white">
                        <div className="flex items-center gap-3">
                          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#EEE9FF] text-primary"><Icon size={16} strokeWidth={2} aria-hidden="true" /></span>
                          <span className="flex-1 text-[13px] font-semibold text-text-body">{formatLabel(label)}</span>
                          <span className="text-[13px] font-bold tabular-nums text-text">{value.toLocaleString()}</span>
                          <button type="button" onClick={() => void openImpactArticles(label)} aria-label={`View ${value} ${formatLabel(label)} articles`} className="rounded-full p-1 text-muted transition-colors hover:bg-primary-soft hover:text-primary"><ChevronRight size={15} aria-hidden="true" /></button>
                        </div>
                        <div className="ml-11 mt-2 flex items-center gap-3"><div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#ECEAF5]"><div className="analytics-impact-bar h-full rounded-full bg-gradient-to-r from-[#9A7AE8] to-[#6B4DE6]" style={{ width: `${percentage}%` }} /></div><span className="w-10 text-right text-[11px] font-semibold text-muted">{percentage.toFixed(1)}%</span></div>
                      </div>
                    );
                  })}
                </div>
              </article>

              <div>
              <article className="analytics-panel-enter rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6" style={{ animationDelay: "120ms" }}>
                <SectionHeading title="Competitor mentions" description={`Top organizations mentioned alongside ${companyName || "this company"}.`} />
                {data.competitors.length === 0 ? (
                  <EmptyCompetitors />
                ) : (
                  <div className="mt-5 overflow-hidden rounded-xl border border-border">
                    <div className="grid grid-cols-[1fr_auto] bg-[#FAF9FF] px-3 py-2 text-[10px] font-bold uppercase tracking-[0.12em] text-muted"><span>Company</span><span>Mentions</span></div>
                    {data.competitors.map((competitor, index) => {
                      const name = typeof competitor.name === "string" ? competitor.name : "Unknown competitor";
                      const mentions = typeof competitor.mention_count === "number" ? competitor.mention_count : 0;
                      return <div key={`${name}-${index}`} className="grid grid-cols-[1fr_auto] items-center border-t border-border px-3 py-3 text-[12px]"><span className="flex items-center gap-2 font-semibold text-body"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-soft text-[10px] font-bold text-primary">{name.slice(0, 2).toUpperCase()}</span>{name}</span><span className="font-semibold tabular-nums text-text">{mentions.toLocaleString()}</span></div>;
                    })}
                  </div>
                )}
              </article>
              </div>
            </section>
          </>
        )}
      </div>
      {impactCategory && <ImpactArticlesModal category={impactCategory} articles={impactArticles} loading={impactLoading} onClose={() => setImpactCategory(null)} onGenerateReport={() => void generateImpactReport()} generating={generatingImpactReport} />}
    </main>
  );
}
