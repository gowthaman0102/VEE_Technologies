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
  Download,
  FileText,
  FileUp,
  RefreshCcw,
  Sparkles,
  Trash2,
} from "lucide-react";

import {
  deleteReport,
  generateReport,
  getActiveCompany,
  getReportHistory,
  ReportBatchHistoryItem,
  ReportHistoryItem,
} from "@/lib/api";
import { Badge, toneForStatus } from "@/components/ui/badge";
import { focusRing, inputClasses, primaryButton, secondaryButton } from "@/components/ui/button-styles";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { toast } from "@/components/ui/toast";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

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
};

const FORMAT_KEYS = ["pdf", "xlsx", "csv"] as const;

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


export function ReportsPageClient() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [reportType, setReportType] = useState<ReportType>("daily");
  const [timeMode, setTimeMode] = useState<TimeMode>("media");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [history, setHistory] = useState<ReportBatchHistoryItem[]>([]);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingBatch, setPendingBatch] = useState<ReportBatchHistoryItem | null>(null);
  const [historySection, setHistorySection] = useState<"standard" | "search" | "analytics">("standard");

  const loadReports = useCallback(async (resolvedCompanyId: number) => {
    const reports = await getReportHistory(resolvedCompanyId);
    setHistory(reports.items);
  }, []);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("section");
    if (requested === "search" || requested === "analytics") setHistorySection(requested);
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const company = await getActiveCompany();
          setCompanyId(company.id);
          setCompanyName(company.name);
          await loadReports(company.id);
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : "Unable to load reports.");
        } finally {
          setLoading(false);
        }
      })();
    }, 0);
    return () => { window.clearTimeout(timer); };
  }, [loadReports]);

  const visibleHistory = useMemo(
    () => history.filter((batch) => {
      const isSearch = batch.report_type.startsWith("search_");
      const isAnalytics = batch.report_type.startsWith("analytics_");
      return historySection === "search" ? isSearch : historySection === "analytics" ? isAnalytics : !isSearch && !isAnalytics;
    }),
    [history, historySection],
  );

  const historyLabel = useMemo(() => {
    if (!visibleHistory.length) return "0 batches";
    return `${visibleHistory.length} ${visibleHistory.length === 1 ? "batch" : "batches"}`;
  }, [visibleHistory.length]);

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

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (companyId === null) return;

    setError("");
    setSuccessMessage("");

    const payload: {
      company_id: number;
      report_type: ReportType;
      time_mode: TimeMode;
      start_date?: string;
      end_date?: string;
    } = {
      company_id: companyId,
      report_type: reportType,
      time_mode: timeMode,
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
              <p className="text-sm text-muted">Select your report type and time mode. All formats are generated in a single snapshot-consistent batch.</p>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_1fr_220px]">
            <label className="text-sm text-body">
              Report type
              <select
                value={reportType}
                onChange={(event) => {
                  setReportType(event.target.value as ReportType);
                  setError("");
                  setSuccessMessage("");
                }}
                className={`mt-2 ${inputClasses}`}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="custom">Custom</option>
              </select>
            </label>

            <label className="text-sm text-body">
              Time mode
              <select
                value={timeMode}
                onChange={(event) => {
                  setTimeMode(event.target.value as TimeMode);
                }}
                className={`mt-2 ${inputClasses}`}
              >
                <option value="media">Media Period (published_at)</option>
                <option value="ingestion">Ingestion Period (collected_at)</option>
              </select>
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
                Start date
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
                End date
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
                  Custom dates are converted to UTC before report generation.
                </div>
              </div>
            </div>
          )}
        </form>

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
              <div className="mt-3 flex flex-wrap gap-2">
                {(["standard", "search", "analytics"] as const).map((section) => (
                  <button key={section} type="button" onClick={() => setHistorySection(section)} className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${historySection === section ? "bg-primary text-white" : "border border-border bg-surface-raised text-muted"}`}>
                    {section === "standard" ? "Standard reports" : `${section} reports`}
                  </button>
                ))}
              </div>
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
          ) : visibleHistory.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-border bg-surface-raised p-8 text-center">
              <p className="text-base font-medium text-text">No reports generated yet.</p>
              <p className="mt-2 text-sm text-muted">Generate your first report using the controls above.</p>
            </div>
          ) : (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {visibleHistory.map((batch) => {
                const anySuccess = Object.values(batch.formats).some((item) => item.status === "success");
                
                const titleText = `${formatReportType(batch.report_type)} · ${formatCompactDateTime(batch.period_start)} → ${formatCompactDateTime(batch.period_end)}`;

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

                      <Badge tone={toneForStatus(batch.status)}>{formatStatusLabel(batch.status)}</Badge>
                    </div>

                    <div className="mt-4 space-y-2 text-sm text-muted">
                      <p>Batch ID: {batch.batch_id.slice(0, 8)}...</p>
                      {batch.generated_at && (
                        <p>Generated {formatCompactDateTime(batch.generated_at)}</p>
                      )}
                    </div>

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
                          onClick={() => {
                            void removeBatch(batch);
                          }}
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
              })}
            </div>
          )}
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
