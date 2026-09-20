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
  Scale,
  ShieldAlert,
  Smile,
  UserRound,
} from "lucide-react";

import {
  AnalyticsOverview,
  getActiveCompany,
  getAnalyticsOverview,
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

const IMPACT_ICONS = [
  BriefcaseBusiness,
  BarChart3,
  Scale,
  Landmark,
  LockKeyhole,
  Heart,
  UserRound,
  BriefcaseBusiness,
  BarChart3,
  ShieldAlert,
];

const IMPACT_COLORS = [
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
  "bg-primary-soft text-primary",
];

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function AnalyticsMetricCard({
  label,
  value,
  icon: Icon,
  iconClass,
}: {
  label: string;
  value: number;
  icon: typeof FileText;
  iconClass: string;
}) {
  return (
    <article className="rounded-[16px] border border-border bg-white px-5 py-4 shadow-[0_5px_18px_rgba(25,59,70,0.05)] transition-shadow hover:shadow-[0_8px_24px_rgba(25,59,70,0.08)]">
      <div className="flex items-center gap-4">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${iconClass}`}>
          <Icon size={23} strokeWidth={2} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-muted">{label}</p>
          <p className="mt-1 text-[29px] font-bold leading-none tracking-tight text-text tabular-nums">{value.toLocaleString()}</p>
        </div>
      </div>
    </article>
  );
}

function SectionHeading({ title, description, action }: { title: string; description: string; action?: string }) {
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
      {action && <button type="button" className="shrink-0 rounded-full border border-border bg-white px-3.5 py-1.5 text-[12px] font-semibold text-body shadow-sm transition-colors hover:bg-surface-raised">{action}</button>}
    </div>
  );
}

export default function AnalyticsPage() {
  const [companyId, setCompanyId] =
    useState<number | null>(null);
  const [companyName, setCompanyName] =
    useState("");

  const [preset, setPreset] =
    useState<TimeRangePreset>("365d");

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

  useEffect(() => {
    async function loadCompany() {
      try {
        const company = await getActiveCompany();
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

        const overview =
          await getAnalyticsOverview(
            companyId,
            range.start,
            range.end,
          );

        setData(overview);
      } catch (cause) {
        setData(null);
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

  return (
    <main className="analytics-page min-h-[calc(100vh-74px)] bg-surface-raised px-5 py-6 sm:px-6 lg:px-8 lg:py-7">
      <div className="mx-auto w-full max-w-[1400px]">
        <header className="flex flex-col justify-between gap-5 border-b border-border pb-5 md:flex-row md:items-end">
          <div className="min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-primary">Analytics</p>
            <h1 className="mt-1.5 text-[28px] font-bold leading-tight tracking-tight text-text">{companyName ? `${companyName} Intelligence Trends` : "Intelligence Trends"}</h1>
            <p className="mt-1.5 text-[13px] text-muted">Explore stored media intelligence across configurable reporting periods.</p>
          </div>
          <div className="shrink-0 rounded-full border border-border bg-white p-1.5 shadow-[0_4px_15px_rgba(25,59,70,0.05)]">
            <TimeRangeSelector
              value={preset}
              onChange={setPreset}
              customStart={customStart}
              customEnd={customEnd}
              onCustomStartChange={setCustomStart}
              onCustomEndChange={setCustomEnd}
            />
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-lg border border-critical-border bg-critical-bg p-4 text-sm text-critical">
            {error}
          </div>
        )}

        {preset === "custom" &&
        (!customStart || !customEnd) ? (
          <EmptyState title="Select a custom time range" description="Choose both a start and end date to load analytics." />
        ) : loading ? (
          <div className="rounded-lg border border-border bg-surface p-10 text-center text-muted">
            Loading analytics...
          </div>
        ) : data === null ? (
          <EmptyState title="No analytics data available." />
        ) : (
          <>
            <section className="grid gap-4 pt-5 sm:grid-cols-2 xl:grid-cols-4">
              <AnalyticsMetricCard label="Articles" value={data.total_articles} icon={FileText} iconClass="bg-primary-soft text-primary" />
              <AnalyticsMetricCard label="Events" value={data.total_events} icon={CalendarDays} iconClass="bg-low-bg text-low" />
              <AnalyticsMetricCard label="Medium risk" value={data.risk.medium_risk_count ?? 0} icon={ShieldAlert} iconClass="bg-medium-bg text-medium" />
              <AnalyticsMetricCard label="Positive sentiment" value={data.sentiment.positive ?? 0} icon={Smile} iconClass="bg-surface-raised text-primary" />
            </section>

            <section className="mt-5 grid items-start gap-5 xl:grid-cols-[1.15fr_0.85fr]">
              <article className="rounded-[17px] border border-border bg-white p-5 shadow-[0_5px_18px_rgba(25,59,70,0.05)] sm:p-6">
                <SectionHeading title="Business impact" description="Distribution of media intelligence by business impact category." action="View all" />
                <div className="mt-5 space-y-2">
                  {Object.entries(data.business_impact).filter(([, value]) => value > 0).length === 0 ? (
                    <p className="rounded-xl bg-surface-raised px-4 py-8 text-center text-sm text-muted">No business-impact data for this period.</p>
                  ) : Object.entries(data.business_impact).filter(([, value]) => value > 0).map(([label, value], index) => {
                    const Icon = IMPACT_ICONS[index % IMPACT_ICONS.length];
                    return (
                      <button key={label} type="button" className="flex w-full items-center gap-3 rounded-xl border border-border bg-surface-raised px-3 py-2 text-left transition-colors hover:border-primary-border hover:bg-surface-raised">
                        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${IMPACT_COLORS[index % IMPACT_COLORS.length]}`}><Icon size={16} strokeWidth={2} aria-hidden="true" /></span>
                        <span className="flex-1 text-[13px] font-medium text-body">{formatLabel(label)}</span>
                        <span className="text-[13px] font-bold tabular-nums text-text">{value.toLocaleString()}</span>
                        <ChevronRight size={16} className="text-muted" aria-hidden="true" />
                      </button>
                    );
                  })}
                </div>
              </article>

              <article className="rounded-[17px] border border-border bg-white p-5 shadow-[0_5px_18px_rgba(25,59,70,0.05)] sm:p-6">
                <SectionHeading title="Competitor mentions" description={`Top organizations mentioned alongside ${companyName || "this company"}.`} action="View all" />
                {data.competitors.length === 0 ? (
                  <div className="mt-5 rounded-xl bg-surface-raised px-4 py-10 text-center text-sm text-muted">No competitor mention data available for the selected period.</div>
                ) : (
                  <div className="mt-5 overflow-hidden rounded-xl border border-border">
                    <div className="grid grid-cols-[1fr_auto] bg-surface-raised px-3 py-2 text-[10px] font-bold uppercase tracking-[0.12em] text-muted"><span>Company</span><span>Mentions</span></div>
                    {data.competitors.map((competitor, index) => {
                      const name = typeof competitor.name === "string" ? competitor.name : "Unknown competitor";
                      const mentions = typeof competitor.mention_count === "number" ? competitor.mention_count : 0;
                      return <div key={`${name}-${index}`} className="grid grid-cols-[1fr_auto] items-center border-t border-border px-3 py-2.5 text-[12px]"><span className="font-medium text-body">{name}</span><span className="font-semibold tabular-nums text-text">{mentions.toLocaleString()}</span></div>;
                    })}
                  </div>
                )}
              </article>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
