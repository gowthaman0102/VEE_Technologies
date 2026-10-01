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
  ChevronLeft,
  ChevronRight,
  FileText,
  Heart,
  Landmark,
  LockKeyhole,
  Package,
  Scale,
  ShieldAlert,
  Smile,
  Trophy,
  UserRound,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  AnalyticsOverview,
  ClientConfiguration,
  DashboardArticleItem,
  getActiveCompany,
  getBusinessImpactArticles,
  getAnalyticsOverview,
  generateReport,
  SourceAnalyticsResponse,
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
import { SentimentAndRiskCards } from "@/components/sentiment-risk-cards";
import { PublisherReliabilityTable } from "@/components/publisher-reliability-table";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

const IMPACT_ICONS: Record<string, LucideIcon> = {
  financial: BriefcaseBusiness,
  operational: BarChart3,
  legal: Scale,
  regulatory: Landmark,
  cybersecurity: LockKeyhole,
  reputation: Heart,
  customer: UserRound,
  product: Package,
  market: BarChart3,
  competitive: Trophy,
};

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
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

function ImpactCategoryRow({
  label,
  value,
  totalImpact,
  index,
  onViewArticles,
}: {
  label: string;
  value: number;
  totalImpact: number;
  index: number;
  onViewArticles: () => void;
}) {
  const Icon = IMPACT_ICONS[label] ?? BarChart3;
  const percentage = totalImpact > 0 ? (value / totalImpact) * 100 : 0;

  return (
    <div style={{ animationDelay: `${index * 55}ms` }} className="analytics-row-enter rounded-xl border border-transparent bg-[#FBFAFF] px-3 py-2.5 transition-colors hover:border-[#E9E5F4] hover:bg-white">
      <div className="flex items-center gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#EEE9FF] text-primary"><Icon size={16} strokeWidth={2} aria-hidden="true" /></span>
        <span className="flex-1 text-[13px] font-semibold text-text-body">{formatLabel(label)}</span>
        <span className="text-[13px] font-bold tabular-nums text-text">{value.toLocaleString()}</span>
        <button type="button" onClick={onViewArticles} disabled={value === 0} aria-label={`View ${value} ${formatLabel(label)} articles`} className="rounded-full p-1 text-muted transition-colors hover:bg-primary-soft hover:text-primary disabled:cursor-not-allowed disabled:opacity-35"><ChevronRight size={15} aria-hidden="true" /></button>
      </div>
      <div className="ml-11 mt-2 flex items-center gap-3"><div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#ECEAF5]"><div className="analytics-impact-bar h-full rounded-full bg-gradient-to-r from-[#9A7AE8] to-[#6B4DE6]" style={{ width: `${percentage}%` }} /></div><span className="w-10 text-right text-[11px] font-semibold text-muted">{percentage.toFixed(1)}%</span></div>
    </div>
  );
}

function ImpactCategoriesModal({
  entries,
  onClose,
  onSelect,
}: {
  entries: Array<readonly [string, number]>;
  onClose: () => void;
  onSelect: (category: string) => void;
}) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  const totalImpact = entries.reduce((total, [, value]) => total + value, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-text/40 p-4 sm:p-6" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="impact-categories-title" className="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_20px_60px_rgba(65,50,120,0.2)]">
        <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-primary">Business Impact</p>
            <h2 id="impact-categories-title" className="mt-1 text-xl font-bold text-text">All impact categories</h2>
            <p className="mt-1 text-sm text-muted">{entries.length} categories · {totalImpact.toLocaleString()} article mentions</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close impact categories" className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"><X size={18} aria-hidden="true" /></button>
        </header>
        <div className="flex-1 overflow-y-auto bg-surface-raised px-5 py-5 sm:px-6">
          <div className="space-y-1.5">
            {entries.map(([label, value], index) => (
              <ImpactCategoryRow
                key={label}
                label={label}
                value={value}
                totalImpact={totalImpact}
                index={index}
                onViewArticles={() => onSelect(label)}
              />
            ))}
          </div>
        </div>
        <footer className="flex shrink-0 justify-end border-t border-border bg-surface-raised px-5 py-3 sm:px-6">
          <button type="button" onClick={onClose} className="inline-flex items-center justify-center rounded-[8px] border border-border bg-white px-3.5 py-1.5 text-[13px] font-bold text-text transition-colors hover:bg-surface">Close</button>
        </footer>
      </section>
    </div>
  );
}



function ImpactArticlesModal({
  category,
  articles,
  loading,
  onClose,
  companyId,
  startDate,
  endDate,
  total,
  page,
  onPageChange,
  error,
}: {
  category: string;
  articles: DashboardArticleItem[];
  loading: boolean;
  onClose: () => void;
  companyId: number | null;
  startDate: string;
  endDate: string;
  total: number;
  page: number;
  onPageChange: (page: number) => void;
  error: string;
}) {
  const [reportStatus, setReportStatus] = useState<"idle" | "generating" | "done" | "error">("idle");
  const [reportError, setReportError] = useState("");

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  const handleGenerateReport = async () => {
    if (!companyId) return;
    setReportStatus("generating");
    setReportError("");
    try {
      await generateReport({
        company_id: companyId,
        report_type: "custom",
        report_scope: "business_impact",
        business_impact_category: category,
        start_date: startDate,
        end_date: endDate,
      });
      setReportStatus("done");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Failed to generate report.");
      setReportStatus("error");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-text/40 p-4 sm:p-6" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="impact-articles-title" className="flex h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_20px_60px_rgba(65,50,120,0.2)]">
        <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-primary">Business Impact</p>
            <h2 id="impact-articles-title" className="mt-1 text-xl font-bold text-text">{formatLabel(category)} articles</h2>
            <p className="mt-1 text-sm text-muted">{loading ? "Loading matching articles..." : `${total.toLocaleString()} ${total === 1 ? "article" : "articles"}`}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close articles" className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"><X size={18} aria-hidden="true" /></button>
        </header>
        <div className="flex-1 overflow-y-auto bg-surface-raised px-5 py-5 sm:px-6">
          {loading ? <div className="flex h-full items-center justify-center text-sm text-muted">Loading matching articles...</div> : error ? <div className="flex h-full items-center justify-center text-sm text-critical">{error}</div> : total === 0 ? <EmptyState title="No matching articles found." /> : <div className="space-y-3">{articles.map((article) => <ArticleRow key={article.article_id} article={article} />)}</div>}
        </div>
        <footer className="shrink-0 flex items-center justify-between gap-3 border-t border-border bg-surface-raised px-5 py-3 sm:px-6">
          <div className="text-sm">
            {reportStatus === "done" && (
              <span className="font-semibold text-green-600">✓ Report generated! Check the Reports page.</span>
            )}
            {reportStatus === "error" && (
              <span className="text-critical">{reportError}</span>
            )}
          </div>
          {total > 50 && (
            <div className="flex items-center gap-2 text-xs text-muted">
              <button type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1 || loading} aria-label="Previous page" className="inline-flex h-8 w-8 items-center justify-center rounded border border-border bg-surface disabled:opacity-40"><ChevronLeft size={15} /></button>
              <span>{page} / {Math.ceil(total / 50)}</span>
              <button type="button" onClick={() => onPageChange(page + 1)} disabled={page >= Math.ceil(total / 50) || loading} aria-label="Next page" className="inline-flex h-8 w-8 items-center justify-center rounded border border-border bg-surface disabled:opacity-40"><ChevronRight size={15} /></button>
            </div>
          )}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-[8px] border border-border bg-white px-3.5 py-1.5 text-[13px] font-bold text-text transition-colors hover:bg-surface-raised"
            >
              Close
            </button>
            <button
              type="button"
              onClick={() => void handleGenerateReport()}
              disabled={reportStatus === "generating" || !companyId || articles.length === 0}
              style={{ color: "#ffffff" }}
              className="inline-flex items-center justify-center rounded-[8px] bg-primary px-4 py-1.5 text-[13px] font-bold transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
            >
              {reportStatus === "generating" ? "Generating…" : "Generate Report"}
            </button>
          </div>
        </footer>
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


  const [sources, setSources] = useState<SourceAnalyticsResponse["sources"] | null>(null);
  const [config, setConfig] = useState<ClientConfiguration | null>(null);

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState("");
  const [impactCategory, setImpactCategory] = useState<string | null>(null);
  const [showAllImpacts, setShowAllImpacts] = useState(false);
  const [impactArticles, setImpactArticles] = useState<DashboardArticleItem[]>([]);
  const [impactLoading, setImpactLoading] = useState(false);
  const [impactTotal, setImpactTotal] = useState(0);
  const [impactPage, setImpactPage] = useState(1);
  const [impactError, setImpactError] = useState("");

  useEffect(() => {
    async function loadCompany() {
      try {
        const company = await withRetries(getActiveCompany);
        setCompanyId(company.id);
        setCompanyName(company.name);
        
        // Also fetch company config for reliability scoring
        const { getCompanyConfiguration } = await import("@/lib/api");
        const cfg = await getCompanyConfiguration(company.id);
        setConfig(cfg);
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

        const { getSourceAnalytics } = await import("@/lib/api");

        const [overview, srcRes] = await Promise.all([
          withRetries(() => getAnalyticsOverview(companyId, range.start, range.end)),
          withRetries(() => getSourceAnalytics(range.start, range.end, companyId))
        ]);

        setData(overview);
        setSources(srcRes.sources);
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

  const openImpactArticles = async (category: string, page = 1) => {
    if (companyId === null || data === null) return;
    setImpactCategory(category);
    setImpactPage(page);
    setImpactLoading(true);
    setImpactError("");
    try {
      const response = await getBusinessImpactArticles({
        company_id: companyId,
        category,
        start: data.start,
        end: data.end,
        page,
        page_size: 50,
      });
      setImpactArticles(response.items);
      setImpactTotal(response.total);
    } catch (cause) {
      setImpactArticles([]);
      setImpactTotal(0);
      setImpactError(cause instanceof Error ? cause.message : "Unable to load matching articles.");
    } finally {
      setImpactLoading(false);
    }
  };

  const handleDownload = async () => {
    if (companyId === null) return;
    setExporting(true);
    setExportError("");
    try {
      const range = resolveTimeRange(preset, preset === "custom" ? { customStart, customEnd } : {});
      const element = document.querySelector(".analytics-page") as HTMLElement;
      if (!element) throw new Error("Could not find analytics page element");
      element.setAttribute("data-exporting", "true");
      const html2canvas = (await import("html2canvas-pro")).default;
      const canvas = await html2canvas(element, {
        scale: 2,
        width: element.scrollWidth,
        height: element.scrollHeight,
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight,
        backgroundColor: "#F6F7FC",
        ignoreElements: (candidate) => candidate.getAttribute("role") === "dialog",
      });
      element.removeAttribute("data-exporting");
      const imageData = canvas.toDataURL("image/png");

      const { exportAnalyticsSnapshot } = await import("@/lib/api");
      const saved = await exportAnalyticsSnapshot({
        company_id: companyId,
        start_date: range.start,
        end_date: range.end,
        preset,
        image_data: imageData,
      });
      const downloadLink = document.createElement("a");
      downloadLink.href = imageData;
      downloadLink.download = saved.filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();
    } catch (cause) {
      setExportError(cause instanceof Error ? cause.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const impactEntries = data
    ? [
        ...Object.keys(IMPACT_ICONS),
        ...Object.keys(data.business_impact).filter((label) => !(label in IMPACT_ICONS)),
      ]
        .map((label) => [label, data.business_impact[label] ?? 0] as const)
        .sort(([, a], [, b]) => b - a)
    : [];

  return (
    <main className="analytics-page relative min-h-[calc(100vh-74px)] overflow-hidden bg-[radial-gradient(circle_at_70%_8%,rgba(130,100,255,0.09),transparent_34%),linear-gradient(180deg,#FBFBFF_0%,#F6F7FC_100%)] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
      <PageAmbient kind="analytics" />
      <div className="relative z-10 mx-auto w-full max-w-[1440px]">
        <CosmicPageHero variant="analytics" imageSrc="/analytics-hero.png" eyebrow="ANALYTICS" title={companyName ? `${companyName} Intelligence Trends` : "Intelligence Trends"} description="Explore stored media intelligence across configurable reporting periods." />

        <div className="mt-4 flex flex-wrap items-center justify-end gap-3">
          <div className="rounded-2xl border border-border bg-surface px-3 py-2 shadow-[0_6px_18px_rgba(27,22,62,0.06)]">
            <TimeRangeSelector value={preset} onChange={setPreset} customStart={customStart} customEnd={customEnd} onCustomStartChange={setCustomStart} onCustomEndChange={setCustomEnd} includeCustom />
          </div>
          {exportError && <span className="text-sm text-critical">{exportError}</span>}
          <button 
            type="button" 
            onClick={() => void handleDownload()} 
            disabled={exporting || loading || data === null || (preset === "custom" && (!customStart || !customEnd))}
            className="rounded-[10px] border border-primary px-4 py-2 text-[13px] font-bold text-primary transition-colors hover:bg-primary-soft disabled:opacity-50"
          >
            {exporting ? "Preparing..." : "Download snapshot"}
          </button>
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

            <section className="mt-5 grid min-w-0 items-stretch gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
              <article className="analytics-panel-enter h-full min-w-0 rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6 flex flex-col">
                <SectionHeading title="Business impact" description="Article counts across supported business-impact categories." />
                <div className="mt-5 space-y-1.5 flex-1">
                  {impactEntries
                    .slice(0, 7)
                    .map(([label, value], index) => {
                    const totalImpact = Object.values(data.business_impact).reduce((sum, count) => sum + count, 0);
                    return (
                      <ImpactCategoryRow
                        key={label}
                        label={label}
                        value={value}
                        totalImpact={totalImpact}
                        index={index}
                        onViewArticles={() => void openImpactArticles(label)}
                      />
                    );
                  })}
                </div>
                {impactEntries.length > 7 && (
                  <button
                    type="button"
                    aria-haspopup="dialog"
                    onClick={() => setShowAllImpacts(true)}
                    className="mt-3 inline-flex items-center gap-1.5 self-start text-xs font-semibold text-primary transition-colors hover:text-primary-hover"
                  >
                    Show all {impactEntries.length} categories
                    <ChevronRight size={14} aria-hidden="true" />
                  </button>
                )}
              </article>

              <div className="flex h-full min-w-0 flex-col">
                <SentimentAndRiskCards data={data} />
              </div>
            </section>
            
            <PublisherReliabilityTable sources={sources} config={config} />
          </>
        )}
      </div>
      {showAllImpacts && (
        <ImpactCategoriesModal
          entries={impactEntries}
          onClose={() => setShowAllImpacts(false)}
          onSelect={(category) => {
            setShowAllImpacts(false);
            void openImpactArticles(category);
          }}
        />
      )}
      {impactCategory && (
        <ImpactArticlesModal
          category={impactCategory}
          articles={impactArticles}
          loading={impactLoading}
          onClose={() => setImpactCategory(null)}
          companyId={companyId}
          startDate={data?.start ?? ""}
          endDate={data?.end ?? ""}
          total={impactTotal}
          page={impactPage}
          onPageChange={(page) => void openImpactArticles(impactCategory, page)}
          error={impactError}
        />
      )}
    </main>
  );
}

