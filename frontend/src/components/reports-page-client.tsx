"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  CalendarRange,
  BarChart3,
  Download,
  FileText,
  FileUp,
  Plus,
  RefreshCcw,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";

import {
  deleteReport,
  createReportSchedule,
  deleteReportSchedule,
  generateReport,
  getActiveCompany,
  getReportHistory,
  getReportSchedules,
  getReportSummary,
  ReportBatchHistoryItem,
  ReportSchedule,
  ReportSchedulePayload,
  ReportSummary,
  ReportTemplate,
  updateReportSchedule,
} from "@/lib/api";
import { Badge, toneForStatus } from "@/components/ui/badge";
import { focusRing, inputClasses, primaryButton, secondaryButton } from "@/components/ui/button-styles";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { toast } from "@/components/ui/toast";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";
import { useAutoRefresh } from "@/lib/use-auto-refresh";

type ReportType =
  | "daily"
  | "weekly"
  | "monthly"
  | "custom";

type TimeMode = "media" | "ingestion";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL
  ?? "http://127.0.0.1:8000/api/v1";

const FORMAT_LABELS: Record<string, string> = {
  pdf: "PDF",
  xlsx: "Excel",
  csv: "CSV",
  png: "PNG",
};

const FORMAT_KEYS = ["pdf", "xlsx", "csv", "png"] as const;

function formatDateTime(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatCompactDateTime(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatReportType(value: string) {
  return value.replace(/_/g, " ");
}

function formatStatusLabel(status: string | null | undefined) {
  const safe = (status ?? "").toLowerCase();
  if (safe.includes("pending")) return "Pending";
  if (safe.includes("processing")) return "Processing";
  if (safe.includes("failed") || safe.includes("error")) return "Failed";
  if (safe.includes("success")) return "Success";
  return safe ? safe.charAt(0).toUpperCase() + safe.slice(1) : "Unknown";
}

function percentageChange(previous: number, current: number) {
  if (previous === 0) return current === 0 ? "0.0%" : "—";
  const change = ((current - previous) / previous) * 100;
  return `${change > 0 ? "+" : ""}${change.toFixed(1)}%`;
}


export function ReportsPageClient() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [reportType, setReportType] = useState<ReportType>("daily");
  const [reportTemplate, setReportTemplate] = useState<ReportTemplate>("detailed");
  const [timeMode, setTimeMode] = useState<TimeMode>("media");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [history, setHistory] = useState<ReportBatchHistoryItem[]>([]);
  const [reportSchedules, setReportSchedules] = useState<ReportSchedule[]>([]);
  const [scheduleDraft, setScheduleDraft] = useState<ReportSchedulePayload>({
    name: "",
    report_type: "daily",
    time_mode: "media",
    report_scope: "standard",
    business_impact_category: null,
    report_template: "detailed",
    formats: ["pdf", "xlsx", "csv"],
    run_time_utc: "09:00",
    day_of_week: 1,
    day_of_month: 1,
    custom_period_days: 7,
    is_active: true,
  });
  const [creatingSchedule, setCreatingSchedule] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [savingScheduleId, setSavingScheduleId] = useState<number | null>(null);
  const [deletingScheduleId, setDeletingScheduleId] = useState<number | null>(null);
  const [selectedBatchIds, setSelectedBatchIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<{
    previousBatch: ReportBatchHistoryItem;
    currentBatch: ReportBatchHistoryItem;
    previous: ReportSummary;
    current: ReportSummary;
  } | null>(null);
  const [comparing, setComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingBatch, setPendingBatch] = useState<ReportBatchHistoryItem | null>(null);
  const [activeTab, setActiveTab] = useState<"standard" | "analytics" | "search" | "impact">("standard");

  const loadReports = useCallback(async (resolvedCompanyId: number) => {
    const reports = await getReportHistory(resolvedCompanyId);
    setHistory(reports.items);
  }, []);

  const loadSchedules = useCallback(async (resolvedCompanyId: number) => {
    const response = await getReportSchedules(resolvedCompanyId);
    setReportSchedules(response.items);
  }, []);

  const autoRefreshHistory = useCallback(async () => {
    if (companyId === null) return;
    try {
      await loadReports(companyId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to refresh report history.");
    }
  }, [companyId, loadReports]);

  useAutoRefresh(autoRefreshHistory, { enabled: companyId !== null, intervalMs: 60_000 });

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const company = await getActiveCompany();
          setCompanyId(company.id);
          setCompanyName(company.name);
          await Promise.all([
            loadReports(company.id),
            loadSchedules(company.id).catch((cause) => setError(cause instanceof Error ? cause.message : "Unable to load schedules.")),
          ]);
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : "Unable to load reports.");
        } finally {
          setLoading(false);
        }
      })();
    }, 0);
    return () => { window.clearTimeout(timer); };
  }, [loadReports, loadSchedules]);

  const historyLabel = useMemo(() => {
    if (!history.length) return "0 batches";
    return `${history.length} ${history.length === 1 ? "batch" : "batches"}`;
  }, [history.length]);

  const comparisonMetrics = comparison ? [
    { label: "Articles", previous: comparison.previous.total_articles, current: comparison.current.total_articles },
    { label: "Events", previous: comparison.previous.total_events, current: comparison.current.total_events },
    { label: "High risk", previous: comparison.previous.high_risk_count, current: comparison.current.high_risk_count },
    { label: "Medium risk", previous: comparison.previous.medium_risk_count, current: comparison.current.medium_risk_count },
    { label: "Low risk", previous: comparison.previous.low_risk_count, current: comparison.current.low_risk_count },
    { label: "Positive sentiment", previous: comparison.previous.sentiment_balance.positive, current: comparison.current.sentiment_balance.positive },
    { label: "Neutral sentiment", previous: comparison.previous.sentiment_balance.neutral, current: comparison.current.sentiment_balance.neutral },
    { label: "Negative sentiment", previous: comparison.previous.sentiment_balance.negative, current: comparison.current.sentiment_balance.negative },
  ] : [];

  async function refreshHistory() {
    if (companyId === null) return;
    setError("");
    setRefreshing(true);
    try {
      await loadReports(companyId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to refresh report history.");
    } finally {
      setRefreshing(false);
    }
  }

  async function compareSelectedBatches(nextIds: string[]) {
    setSelectedBatchIds(nextIds);
    setComparison(null);
    setComparisonError("");
    if (nextIds.length !== 2) return;

    const selected = history
      .filter((batch) => nextIds.includes(batch.batch_id))
      .sort((left, right) => new Date(left.period_start).getTime() - new Date(right.period_start).getTime());
    if (selected.length !== 2) return;

    setComparing(true);
    try {
      const [previous, current] = await Promise.all(selected.map((batch) => getReportSummary({
        company_id: batch.company_id,
        start_date: batch.period_start,
        end_date: batch.period_end,
      })));
      setComparison({ previousBatch: selected[0], currentBatch: selected[1], previous, current });
    } catch (cause) {
      setComparisonError(cause instanceof Error ? cause.message : "Unable to compare these report periods.");
    } finally {
      setComparing(false);
    }
  }

  async function createSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (companyId === null) return;
    setError("");
    setCreatingSchedule(true);
    try {
      const created = await createReportSchedule(companyId, {
        ...scheduleDraft,
        name: scheduleDraft.name.trim(),
        business_impact_category: scheduleDraft.report_scope === "business_impact"
          ? scheduleDraft.business_impact_category
          : null,
      });
      setReportSchedules((current) => [created, ...current]);
      setScheduleDraft((current) => ({ ...current, name: "" }));
      setShowScheduleForm(false);
      toast.success("Report schedule created.");
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Unable to create report schedule.";
      setError(message);
      toast.error(message);
    } finally {
      setCreatingSchedule(false);
    }
  }

  async function toggleSchedule(schedule: ReportSchedule) {
    setSavingScheduleId(schedule.id);
    setError("");
    const payload: ReportSchedulePayload = {
      name: schedule.name,
      report_type: schedule.report_type,
      time_mode: schedule.time_mode,
      report_scope: schedule.report_scope,
      business_impact_category: schedule.business_impact_category,
      report_template: schedule.report_template,
      formats: schedule.formats,
      run_time_utc: schedule.run_time_utc,
      day_of_week: schedule.day_of_week,
      day_of_month: schedule.day_of_month,
      custom_period_days: schedule.custom_period_days,
      is_active: !schedule.is_active,
    };
    try {
      const saved = await updateReportSchedule(schedule.id, payload);
      setReportSchedules((current) => current.map((item) => item.id === saved.id ? saved : item));
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Unable to update report schedule.";
      setError(message);
      toast.error(message);
    } finally {
      setSavingScheduleId(null);
    }
  }

  async function removeSchedule(schedule: ReportSchedule) {
    setDeletingScheduleId(schedule.id);
    setError("");
    try {
      await deleteReportSchedule(schedule.id);
      setReportSchedules((current) => current.filter((item) => item.id !== schedule.id));
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Unable to delete report schedule.";
      setError(message);
      toast.error(message);
    } finally {
      setDeletingScheduleId(null);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (companyId === null) return;

    setError("");
    setSuccessMessage("");

    const payload: {
      company_id: number;
      report_type: ReportType;
      time_mode: TimeMode;
      report_scope: "standard";
      report_template: ReportTemplate;
      include_details: boolean;
      start_date?: string;
      end_date?: string;
    } = {
      company_id: companyId,
      report_type: reportType,
      time_mode: timeMode,
      report_scope: "standard",
      report_template: reportTemplate,
      include_details: reportTemplate === "detailed",
    };

    if (reportType === "custom") {
      if (!customStart || !customEnd) {
        setError("Choose both a custom start and end date.");
        return;
      }
      const start = new Date(customStart);
      const end = new Date(customEnd);
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
        setError("Choose a valid custom date range.");
        return;
      }
      if (start >= end) {
        setError("Custom start must be earlier than the end.");
        return;
      }
      payload.start_date = start.toISOString();
      payload.end_date = end.toISOString();
    }

    setGenerating(true);
    try {
      const result = await generateReport(payload);
      await loadReports(companyId);

      const allSuccess = Object.values(result.formats).every((f) => f.status === "success");
      const anyError = Object.values(result.formats).find((f) => f.error);

      if (allSuccess) {
        const message = `Report batch generated successfully (PDF, Excel, CSV). Period: ${formatDateTime(result.period_start)} → ${formatDateTime(result.period_end)}`;
        setSuccessMessage(message);
        toast.success(message);
      } else if (anyError) {
        setError(anyError.error ?? "Report generation failed for one or more formats.");
        toast.error(anyError.error ?? "Report generation failed for one or more formats.");
      } else {
        const message = "Report generation completed.";
        setSuccessMessage(message);
        toast.success(message);
      }
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Unable to generate report.";
      setError(message);
      toast.error(message);
      try {
        await loadReports(companyId);
      } catch {
        // Keep the original generation error.
      }
    } finally {
      setGenerating(false);
    }
  }

  async function removeBatch(batch: ReportBatchHistoryItem) {
    setPendingBatch(batch);
  }

  async function confirmRemoveBatch() {
    if (!pendingBatch) return;
    const batch = pendingBatch;
    setPendingBatch(null);
    setError("");

    try {
      await Promise.all(
        Object.values(batch.formats).map((item) => deleteReport(item.id))
      );
      setHistory((current) => current.filter((record) => record.batch_id !== batch.batch_id));
      setSelectedBatchIds((current) => current.filter((batchId) => batchId !== batch.batch_id));
      setComparison(null);
      const message = `Deleted report batch for ${formatReportType(batch.report_type)} period.`;
      setSuccessMessage(message);
      toast.success(message);
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Unable to delete report batch.";
      setError(message);
      toast.error(message);
    }
  }

  return (
    <main className="relative min-h-[calc(100vh-74px)] overflow-hidden bg-canvas px-4 py-6 sm:px-6 lg:px-8">
      <PageAmbient kind="reports" />
      <div className="relative z-10 mx-auto w-full max-w-[1400px]">
        <CosmicPageHero variant="analytics" eyebrow="REPORTS" imageSrc="/reports-hero.png" title={companyName || "Active Company"} description="Generate executive media-intelligence reports. All formats (PDF, Excel, CSV) are created in a single snapshot-consistent batch." />
        <header className="hidden mb-6 border-b border-border pb-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">REPORTS</p>
              <h1 className="mt-2 text-[38px] font-semibold tracking-[-0.05em] text-text leading-[0.95] sm:text-[46px]">
                {companyName || "OpenAI"}
              </h1>
              <p className="mt-4 max-w-[760px] text-[17px] leading-7 text-muted">
                Generate executive media-intelligence reports. All formats (PDF, Excel, CSV) are created in a single snapshot-consistent batch.
              </p>
            </div>

            <div className="flex items-center justify-center gap-5 xl:justify-end">
              <div className="relative h-[190px] w-[190px] shrink-0">
                <svg viewBox="0 0 190 190" className="h-full w-full" aria-hidden="true">
                  <defs>
                    <linearGradient id="reportPaper" x1="0%" x2="100%" y1="0%" y2="100%">
                      <stop offset="0%" stopColor="var(--color-surface)" />
                      <stop offset="100%" stopColor="var(--color-surface-sunken)" />
                    </linearGradient>
                  </defs>

                  <g opacity="0.72">
                    <rect x="26" y="30" width="98" height="128" rx="12" fill="var(--color-primary-soft)" transform="rotate(-9 75 94)" />
                    <rect x="52" y="18" width="98" height="128" rx="12" fill="var(--color-surface-raised)" transform="rotate(7 101 82)" />
                  </g>

                  <g transform="translate(28 10) rotate(-6 67 95)">
                    <rect x="0" y="0" width="100" height="142" rx="12" fill="url(#reportPaper)" stroke="var(--color-border)" />
                    <rect x="16" y="18" width="68" height="10" rx="4" fill="var(--color-primary-soft)" />
                    <rect x="16" y="34" width="48" height="8" rx="4" fill="var(--color-primary-soft)" />

                    <rect x="16" y="56" width="18" height="48" rx="5" fill="var(--color-primary)" opacity="0.92" />
                    <rect x="38" y="64" width="18" height="40" rx="5" fill="var(--color-primary)" opacity="0.9" />
                    <rect x="60" y="48" width="18" height="56" rx="5" fill="var(--color-primary-soft)" opacity="0.96" />

                    <path d="M18 103 Q32 90 46 97 T72 100 T87 88" fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" />
                    <circle cx="25" cy="95" r="3.5" fill="var(--color-primary)" />
                    <circle cx="48" cy="97" r="3.5" fill="var(--color-primary-hover)" />
                    <circle cx="71" cy="99" r="3.5" fill="var(--color-primary-border)" />
                    <circle cx="86" cy="88" r="3.5" fill="var(--color-primary)" />

                    <rect x="16" y="116" width="40" height="8" rx="4" fill="var(--color-surface-raised)" />
                    <rect x="60" y="116" width="22" height="8" rx="4" fill="var(--color-primary-soft)" />
                  </g>

                  <g transform="translate(76 26) rotate(8 42 74)">
                    <rect x="0" y="0" width="82" height="108" rx="10" fill="var(--color-surface)" stroke="var(--color-border)" />
                    <rect x="12" y="14" width="54" height="8" rx="4" fill="var(--color-surface-raised)" />
                    <rect x="12" y="28" width="36" height="7" rx="4" fill="var(--color-primary-soft)" />

                    <path d="M12 76 L26 68 L38 72 L52 56 L62 60 L70 44" fill="none" stroke="var(--color-primary)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
                    <circle cx="52" cy="56" r="3.5" fill="var(--color-primary)" />

                    <rect x="12" y="84" width="12" height="14" rx="3" fill="var(--color-primary-soft)" />
                    <rect x="28" y="80" width="12" height="18" rx="3" fill="var(--color-primary-border)" />
                    <rect x="44" y="72" width="12" height="26" rx="3" fill="var(--color-primary)" />
                    <rect x="60" y="64" width="12" height="34" rx="3" fill="var(--color-primary-border)" />
                  </g>
                </svg>
              </div>

              <div className="flex max-w-[190px] flex-col items-start text-left">
                <p className="text-[17px] font-medium leading-[1.2] text-text">
                  From global media
                  <br />
                  to actionable insight
                </p>
                <div className="mt-3 h-px w-16 bg-border" />
                <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-primary">
                  FASTER. CLEARER. BRAVER.
                </p>
              </div>
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-5 rounded-xl border border-critical-border bg-critical-bg p-4 text-sm text-critical">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-5 rounded-xl border border-low-border bg-low-bg p-4 text-sm text-low">
            {successMessage}
          </div>
        )}

        <form
          onSubmit={submit}
          className="rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] md:p-6"
        >
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary-border bg-primary-soft text-primary">
              <FileUp className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text">Generate a new report</h2>
              <p className="text-sm text-muted">Choose the dates to cover, how articles are dated, and how much detail to include. PDF, Excel, and CSV files are created together.</p>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_1fr_1fr_220px]">
            <label className="text-sm text-body">
              Date range
              <select
                value={reportType}
                onChange={(event) => {
                  setReportType(event.target.value as ReportType);
                  setError("");
                  setSuccessMessage("");
                }}
                className={`mt-2 ${inputClasses}`}
              >
                <option value="daily">Previous day</option>
                <option value="weekly">Previous week</option>
                <option value="monthly">Previous month</option>
                <option value="custom">Choose dates</option>
              </select>
            </label>

            <label className="text-sm text-body">
              Use date based on
              <select
                value={timeMode}
                onChange={(event) => {
                  setTimeMode(event.target.value as TimeMode);
                }}
                className={`mt-2 ${inputClasses}`}
              >
                <option value="media">When the article was published</option>
                <option value="ingestion">When the article was added</option>
              </select>
            </label>

            <label className="text-sm text-body">
              Report detail
              <select
                value={reportTemplate}
                onChange={(event) => setReportTemplate(event.target.value as ReportTemplate)}
                className={`mt-2 ${inputClasses}`}
              >
                <option value="executive">Brief summary</option>
                <option value="detailed">Full report</option>
                <option value="board_ready">Board summary</option>
              </select>
              {reportTemplate === "board_ready" && (
                <span className="mt-1 block text-xs text-muted">Board summary currently matches Brief summary; charts are not included yet.</span>
              )}
            </label>

            <button
              type="submit"
              disabled={generating || loading || companyId === null}
              className={`${primaryButton} mt-7 h-[46px] w-full xl:mt-0`}
            >
              {generating ? "Generating..." : "Generate report"}
            </button>
          </div>

          {reportType === "custom" && (
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.1fr]">
              <label className="text-sm text-body">
                Start date and time
                <input
                  type="datetime-local"
                  value={customStart}
                  onChange={(event) => {
                    setCustomStart(event.target.value);
                  }}
                  required
                  className={`mt-2 ${inputClasses}`}
                />
              </label>

              <label className="text-sm text-body">
                End date and time
                <input
                  type="datetime-local"
                  value={customEnd}
                  onChange={(event) => {
                    setCustomEnd(event.target.value);
                  }}
                  required
                  className={`mt-2 ${inputClasses}`}
                />
              </label>

              <div className="flex items-end">
                <div className="w-full rounded-xl border border-border bg-surface-raised px-3 py-2.5 text-xs text-muted">
                  Times are adjusted for your local time zone.
                </div>
              </div>
            </div>
          )}
        </form>

        <section className="mt-8 rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] md:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-semibold text-text">Automated scheduling</h3>
              <p className="mt-1 text-sm text-muted">{reportSchedules.length} saved schedules · All times are UTC</p>
            </div>
            <button type="button" onClick={() => setShowScheduleForm((open) => !open)} className={`${secondaryButton} min-h-9 px-3`}>
              {showScheduleForm ? "Cancel" : <><Plus className="h-4 w-4" aria-hidden="true" /> New schedule</>}
            </button>
          </div>

          {reportSchedules.length === 0 ? (
            <p className="mt-4 rounded-lg border border-dashed border-border p-5 text-center text-sm text-muted">No recurring report schedules are configured.</p>
          ) : (
            <ul className="mt-4 divide-y divide-border rounded-lg border border-border">
              {reportSchedules.map((schedule) => (
                <li key={schedule.id} className="flex flex-wrap items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-text">{schedule.name}</p>
                    <p className="mt-1 text-xs capitalize text-muted">{schedule.report_type} · {schedule.report_scope.replace(/_/g, " ")}{schedule.business_impact_category ? ` · ${schedule.business_impact_category.replace(/_/g, " ")}` : ""} · {schedule.formats.map((format) => FORMAT_LABELS[format]).join(", ")}</p>
                    <p className="mt-1 text-xs text-muted">Next run {formatDateTime(schedule.next_run_at)}{schedule.last_run_at ? ` · Last run ${formatDateTime(schedule.last_run_at)}` : ""}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <label className="inline-flex items-center gap-2 text-xs font-medium text-body">
                      <input type="checkbox" checked={schedule.is_active} disabled={savingScheduleId === schedule.id || deletingScheduleId === schedule.id} onChange={() => void toggleSchedule(schedule)} aria-label={`${schedule.is_active ? "Pause" : "Activate"} ${schedule.name}`} className="h-4 w-4 accent-[var(--color-primary)]" />
                      {savingScheduleId === schedule.id ? "Saving..." : schedule.is_active ? "On" : "Off"}
                    </label>
                    <button type="button" onClick={() => void removeSchedule(schedule)} disabled={deletingScheduleId === schedule.id || savingScheduleId === schedule.id} aria-label={`Delete ${schedule.name}`} className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-high-border bg-high-bg text-high disabled:opacity-50">
                      {deletingScheduleId === schedule.id ? <RefreshCcw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> : <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {showScheduleForm && (
            <form onSubmit={createSchedule} className="mt-4 rounded-lg border border-border bg-surface-raised p-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <label className="text-xs font-medium text-body sm:col-span-2">Schedule name
                  <input required maxLength={120} value={scheduleDraft.name} onChange={(event) => setScheduleDraft((current) => ({ ...current, name: event.target.value }))} className={`mt-1.5 ${inputClasses}`} />
                </label>
                <label className="text-xs font-medium text-body">Report period
                  <select value={scheduleDraft.report_type} onChange={(event) => setScheduleDraft((current) => ({ ...current, report_type: event.target.value as ReportSchedulePayload["report_type"] }))} className={`mt-1.5 ${inputClasses}`}>
                    <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="custom">Custom</option>
                  </select>
                </label>
                <label className="text-xs font-medium text-body">Run time (UTC)
                  <input required type="time" value={scheduleDraft.run_time_utc} onChange={(event) => setScheduleDraft((current) => ({ ...current, run_time_utc: event.target.value }))} className={`mt-1.5 ${inputClasses}`} />
                </label>
                {scheduleDraft.report_type === "weekly" && <label className="text-xs font-medium text-body">Run day
                  <select value={scheduleDraft.day_of_week} onChange={(event) => setScheduleDraft((current) => ({ ...current, day_of_week: Number(event.target.value) }))} className={`mt-1.5 ${inputClasses}`}>
                    {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((day, index) => <option key={day} value={index}>{day}</option>)}
                  </select>
                </label>}
                {scheduleDraft.report_type === "monthly" && <label className="text-xs font-medium text-body">Day of month (1-28)
                  <input type="number" min={1} max={28} value={scheduleDraft.day_of_month} onChange={(event) => setScheduleDraft((current) => ({ ...current, day_of_month: Number(event.target.value) }))} className={`mt-1.5 ${inputClasses}`} />
                </label>}
                {scheduleDraft.report_type === "custom" && <label className="text-xs font-medium text-body">Rolling period (days)
                  <input type="number" min={1} max={365} value={scheduleDraft.custom_period_days} onChange={(event) => setScheduleDraft((current) => ({ ...current, custom_period_days: Number(event.target.value) }))} className={`mt-1.5 ${inputClasses}`} />
                </label>}
                <label className="text-xs font-medium text-body">Time mode
                  <select value={scheduleDraft.time_mode} onChange={(event) => setScheduleDraft((current) => ({ ...current, time_mode: event.target.value as ReportSchedulePayload["time_mode"] }))} className={`mt-1.5 ${inputClasses}`}>
                    <option value="media">Media period</option><option value="ingestion">Ingestion period</option>
                  </select>
                </label>
                <label className="text-xs font-medium text-body">Scope
                  <select value={scheduleDraft.report_scope} onChange={(event) => setScheduleDraft((current) => ({ ...current, report_scope: event.target.value as ReportSchedulePayload["report_scope"], business_impact_category: event.target.value === "business_impact" ? current.business_impact_category ?? "cybersecurity" : null }))} className={`mt-1.5 ${inputClasses}`}>
                    <option value="standard">Standard</option><option value="business_impact">Business impact</option>
                  </select>
                </label>
                {scheduleDraft.report_scope === "business_impact" && <label className="text-xs font-medium text-body">Business impact category
                  <select value={scheduleDraft.business_impact_category ?? "cybersecurity"} onChange={(event) => setScheduleDraft((current) => ({ ...current, business_impact_category: event.target.value }))} className={`mt-1.5 ${inputClasses}`}>
                    {["financial", "operational", "legal", "regulatory", "cybersecurity", "reputation", "customer", "product", "market", "competitive"].map((category) => <option key={category} value={category}>{category.replace(/_/g, " ")}</option>)}
                  </select>
                </label>}
                <label className="text-xs font-medium text-body">Template
                  <select value={scheduleDraft.report_template} onChange={(event) => setScheduleDraft((current) => ({ ...current, report_template: event.target.value as ReportTemplate }))} className={`mt-1.5 ${inputClasses}`}>
                    <option value="executive">Executive</option><option value="detailed">Detailed</option><option value="board_ready">Board-ready</option>
                  </select>
                </label>
              </div>
              <fieldset className="mt-4 flex flex-wrap gap-4">
                <legend className="mb-2 text-xs font-medium text-body">Formats</legend>
                {(["pdf", "xlsx", "csv"] as const).map((format) => <label key={format} className="inline-flex items-center gap-2 text-xs text-body"><input type="checkbox" checked={scheduleDraft.formats.includes(format)} onChange={(event) => setScheduleDraft((current) => ({ ...current, formats: event.target.checked ? [...current.formats, format] : current.formats.filter((item) => item !== format) }))} className="h-4 w-4 accent-[var(--color-primary)]" />{FORMAT_LABELS[format]}</label>)}
              </fieldset>
              <button type="submit" disabled={creatingSchedule || !scheduleDraft.name.trim() || scheduleDraft.formats.length === 0} className={`${primaryButton} mt-4 min-h-10 px-4`}>
                {creatingSchedule ? "Saving schedule..." : "Create schedule"}
              </button>
            </form>
          )}
        </section>

        <section className="mt-8 rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] md:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface-raised text-primary">
                  <CalendarRange className="h-4 w-4" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-semibold text-text">Report history</h3>
              </div>
              <p className="mt-2 text-sm text-muted">
                {historyLabel} · Each batch contains PDF, Excel, and CSV
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                void refreshHistory();
              }}
              disabled={loading || companyId === null || refreshing}
              className={`${secondaryButton} min-w-[140px]`}
            >
              {refreshing ? (
                <>
                  <RefreshCcw className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Refreshing...
                </>
              ) : (
                <>
                  <RefreshCcw className="h-4 w-4" aria-hidden="true" />
                  Refresh history
                </>
              )}
            </button>
          </div>

          <section className="mt-5 rounded-lg border border-border bg-surface-raised p-4" aria-labelledby="report-comparison-title">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 id="report-comparison-title" className="text-sm font-semibold text-text">Compare report periods</h4>
                <p className="mt-1 text-xs text-muted">
                  {comparing ? "Loading both report summaries..." : selectedBatchIds.length < 2 ? "Select two batches to compare." : comparison ? `${formatReportType(comparison.previousBatch.report_type)} → ${formatReportType(comparison.currentBatch.report_type)}` : "Comparison unavailable."}
                </p>
              </div>
              <button type="button" onClick={() => void compareSelectedBatches([])} disabled={comparing || selectedBatchIds.length === 0} className={`${secondaryButton} min-h-9 px-3 text-xs`}>Clear selection</button>
            </div>
            {comparisonError && <p role="alert" className="mt-3 text-xs text-critical">{comparisonError}</p>}
            {comparison && (
              <div className="mt-4 overflow-x-auto">
                <p className="mb-2 text-[11px] text-muted">Older period: {formatCompactDateTime(comparison.previousBatch.period_start)} → {formatCompactDateTime(comparison.previousBatch.period_end)} · Newer period: {formatCompactDateTime(comparison.currentBatch.period_start)} → {formatCompactDateTime(comparison.currentBatch.period_end)}</p>
                <table className="w-full min-w-[460px] text-left text-xs">
                  <thead><tr className="border-b border-border text-muted"><th className="py-2 pr-3 font-medium">Metric</th><th className="py-2 pr-3 font-medium">Older</th><th className="py-2 pr-3 font-medium">Newer</th><th className="py-2 font-medium">Change</th></tr></thead>
                  <tbody>{comparisonMetrics.map((metric) => <tr key={metric.label} className="border-b border-border last:border-0"><th className="py-2 pr-3 font-medium text-text">{metric.label}</th><td className="py-2 pr-3 text-body">{metric.previous}</td><td className="py-2 pr-3 text-body">{metric.current}</td><td className="py-2 font-semibold text-primary">{percentageChange(metric.previous, metric.current)}</td></tr>)}</tbody>
                </table>
              </div>
            )}
          </section>

          {loading ? (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="rounded-lg border border-border bg-surface-raised p-4 animate-pulse">
                  <div className="h-4 w-2/3 rounded bg-border" />
                  <div className="mt-3 h-3 w-1/3 rounded bg-border" />
                  <div className="mt-5 h-3 w-full rounded bg-border" />
                  <div className="mt-2 h-3 w-4/5 rounded bg-border" />
                  <div className="mt-5 flex gap-2">
                    <div className="h-9 w-20 rounded-lg bg-border" />
                    <div className="h-9 w-20 rounded-lg bg-border" />
                    <div className="h-9 w-20 rounded-lg bg-border" />
                  </div>
                </div>
              ))}
            </div>
          ) : error && !history.length ? (
            <div className="mt-5 rounded-xl border border-border bg-surface-raised p-6 text-center">
              <p className="text-sm font-medium text-text">Unable to load report history.</p>
              <button
                type="button"
                onClick={() => {
                  void refreshHistory();
                }}
                className={`${secondaryButton} mt-4`}
              >
                Retry
              </button>
            </div>
          ) : history.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-border bg-surface-raised p-8 text-center">
              <p className="text-base font-medium text-text">No reports generated yet.</p>
              <p className="mt-2 text-sm text-muted">Generate your first report using the controls above.</p>
            </div>
          ) : (() => {
            const standardReports = history.filter((b) => !b.report_scope || b.report_scope === "standard");
            const analyticsSnapshots = history.filter((b) => b.report_scope === "analytics_snapshot");
            const searchReports = history.filter((b) => b.report_scope === "search_results" || b.report_scope === "intelligence_export");
            const impactReports = history.filter((b) => b.report_scope === "business_impact");

            const renderBatchCard = (batch: ReportBatchHistoryItem) => {
              const anySuccess = Object.values(batch.formats).some((item) => item.status === "success");
              const categoryLabel = batch.scope_metadata?.category
                ? ` · ${String(batch.scope_metadata.category).replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`
                : "";
              const searchLabel = batch.report_scope === "search_results" || batch.report_scope === "intelligence_export"
                ? " · Search & Intelligence Export"
                : "";
              const snapshotLabel = batch.report_scope === "analytics_snapshot" ? "Analytics Snapshot · " : "";
              const titleText = `${snapshotLabel}${formatReportType(batch.report_type)}${categoryLabel}${searchLabel} · ${formatCompactDateTime(batch.period_start)} → ${formatCompactDateTime(batch.period_end)}`;

              return (
                <article
                  key={batch.batch_id}
                  className="rounded-lg border border-border bg-surface-raised p-4 transition-colors duration-150 hover:border-border-strong hover:shadow-[0_2px_8px_rgba(28,23,52,0.10)]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-surface text-primary">
                          <FileText className="h-4 w-4" aria-hidden="true" />
                        </div>
                        <h4 className="truncate text-[15px] font-semibold text-text">{titleText}</h4>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <label className="inline-flex items-center gap-1.5 text-[11px] text-muted">
                        <input
                          type="checkbox"
                          checked={selectedBatchIds.includes(batch.batch_id)}
                          disabled={comparing || batch.status !== "success" || (selectedBatchIds.length >= 2 && !selectedBatchIds.includes(batch.batch_id))}
                          onChange={(event) => {
                            const next = event.target.checked
                              ? [...selectedBatchIds, batch.batch_id]
                              : selectedBatchIds.filter((id) => id !== batch.batch_id);
                            void compareSelectedBatches(next);
                          }}
                          aria-label={`Select ${formatReportType(batch.report_type)} batch for comparison`}
                          className="h-4 w-4 accent-[var(--color-primary)]"
                        />
                        Compare
                      </label>
                      <Badge tone={toneForStatus(batch.status)}>{formatStatusLabel(batch.status)}</Badge>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2 text-sm text-muted">
                    <p>Batch ID: {batch.batch_id.slice(0, 8)}...</p>
                    {batch.generated_at && (
                      <p>Generated {formatCompactDateTime(batch.generated_at)}</p>
                    )}
                    {batch.report_template && (
                      <p className="capitalize">Template: {batch.report_template.replace(/_/g, " ")}</p>
                    )}
                  </div>

                  {(typeof batch.scope_metadata?.article_ids_count === "number" || typeof batch.scope_metadata?.category === "string") && (
                    <div className="mt-3 flex flex-wrap gap-2">
                       {typeof batch.scope_metadata.article_ids_count === "number" && <span className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs text-body">{batch.scope_metadata.article_ids_count} articles</span>}
                       {typeof batch.scope_metadata.category === "string" && <span className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs text-body">Category: {String(batch.scope_metadata.category).replace(/_/g, " ")}</span>}
                    </div>
                  )}

                  {batch.error && (
                    <div className="mt-4 rounded-lg border border-critical-border bg-critical-bg px-3 py-2 text-sm text-critical">
                      {batch.error}
                    </div>
                  )}

                  <div className="mt-4 border-t border-border pt-3" />

                  <div className="flex flex-wrap items-center gap-2">
                    {FORMAT_KEYS.map((formatKey) => {
                      const item = batch.formats[formatKey];
                      if (!item) return null;

                      const isDownloadable = item.status === "success" && item.filename && item.content_type;
                      const formatLabel = FORMAT_LABELS[formatKey] ?? formatKey.toUpperCase();

                      if (isDownloadable) {
                        return (
                          <a
                            key={formatKey}
                            href={`${API_BASE_URL}/reports/${item.id}/download`}
                            aria-label={`Download ${formatLabel}`}
                            className={`inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-xs font-medium text-body transition-colors hover:border-border-strong hover:text-text ${focusRing}`}
                          >
                            <Download className="h-3.5 w-3.5" aria-hidden="true" />
                            {formatLabel}
                          </a>
                        );
                      }

                      return (
                        <button
                          key={formatKey}
                          type="button"
                          disabled
                          aria-label={`${formatLabel} unavailable`}
                          className="inline-flex cursor-not-allowed items-center gap-2 rounded-lg border border-border bg-surface-muted px-3 py-2 text-xs font-medium text-muted opacity-70"
                        >
                          <Download className="h-3.5 w-3.5" aria-hidden="true" />
                          {formatLabel}
                        </button>
                      );
                    })}

                    <div className="ml-auto">
                      <button
                        type="button"
                        onClick={() => { void removeBatch(batch); }}
                        className="inline-flex items-center gap-2 rounded-lg border border-high-border bg-high-bg px-3 py-2 text-xs font-medium text-high transition-colors hover:bg-high hover:text-white"
                      >
                        <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                        Delete
                      </button>
                    </div>
                  </div>

                  {!anySuccess && !batch.error && (
                    <p className="mt-3 text-xs text-muted">Waiting for report files to become available.</p>
                  )}
                </article>
              );
            };

            const TABS = [
              { id: "standard", label: "Standard Reports", count: standardReports.length, icon: FileText, color: "text-primary bg-primary-soft" },
              { id: "analytics", label: "Analytics Snapshots", count: analyticsSnapshots.length, icon: BarChart3, color: "text-primary bg-primary-soft" },
              { id: "search", label: "Search Exports", count: searchReports.length, icon: Search, color: "text-primary bg-primary-soft" },
              { id: "impact", label: "Business Impact", count: impactReports.length, icon: Sparkles, color: "text-[#2E7D32] bg-[#EEF7EE]" },
            ] as const;

            return (
              <div className="mt-6">
                <div className="flex space-x-1 rounded-xl bg-surface-raised p-1">
                  {TABS.map(tab => {
                    const active = activeTab === tab.id;
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-colors ${active ? "bg-white text-text shadow-sm" : "text-muted hover:bg-white/50 hover:text-text-body"}`}
                      >
                        <div className={`flex h-5 w-5 items-center justify-center rounded-md ${active ? tab.color : "bg-transparent"}`}>
                          <Icon className="h-3.5 w-3.5" />
                        </div>
                        {tab.label}
                        <span className={`ml-1 rounded-full px-2 py-0.5 text-[10px] ${active ? "bg-surface-raised text-text-body" : "bg-surface text-muted"}`}>
                          {tab.count}
                        </span>
                      </button>
                    );
                  })}
                </div>

                <div className="mt-6">
                  {activeTab === "standard" && (
                    standardReports.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border bg-surface-raised p-6 text-center text-sm text-muted">No standard reports yet. Generate one using the form above.</div>
                    ) : (
                      <div className="grid gap-4 md:grid-cols-2">{standardReports.map(renderBatchCard)}</div>
                    )
                  )}

                  {activeTab === "analytics" && (
                    analyticsSnapshots.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border bg-surface-raised p-6 text-center text-sm text-muted">No analytics snapshots yet. Use Download snapshot on the Analytics page to save one here.</div>
                    ) : (
                      <div className="grid gap-4 md:grid-cols-2">{analyticsSnapshots.map(renderBatchCard)}</div>
                    )
                  )}

                  {activeTab === "search" && (
                    searchReports.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border bg-surface-raised p-6 text-center text-sm text-muted">No search result reports yet. Generate one from Search.</div>
                    ) : (
                      <div className="grid gap-4 md:grid-cols-2">{searchReports.map(renderBatchCard)}</div>
                    )
                  )}

                  {activeTab === "impact" && (
                    impactReports.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border bg-surface-raised p-6 text-center text-sm text-muted">No business impact reports yet. Generate one from the Analytics page.</div>
                    ) : (
                      <div className="grid gap-4 md:grid-cols-2">{impactReports.map(renderBatchCard)}</div>
                    )
                  )}
                </div>
              </div>
            );
          })()}
        </section>
      </div>
      <ConfirmDialog
        open={pendingBatch !== null}
        title="Delete report batch"
        description={pendingBatch ? `Delete this report batch? This will permanently remove all formats (PDF, Excel, CSV) for ${formatReportType(pendingBatch.report_type)}.` : undefined}
        confirmLabel="Delete"
        tone="danger"
        onConfirm={confirmRemoveBatch}
        onCancel={() => setPendingBatch(null)}
      />
    </main>
  );
}

