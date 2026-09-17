"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  generateReport,
  getActiveCompany,
  getReportHistory,
  ReportHistoryItem,
} from "@/lib/api";

type ReportType =
  | "daily"
  | "weekly"
  | "monthly"
  | "custom";

type ReportFormat =
  | "pdf"
  | "xlsx"
  | "csv";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL
  ?? "http://127.0.0.1:8000/api/v1";

function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

function statusClasses(
  status: string,
) {
  const normalized =
    status.toLowerCase();

  if (normalized === "success") {
    return (
      "border-emerald-800 "
      + "bg-emerald-950/40 "
      + "text-emerald-300"
    );
  }

  if (normalized === "failed") {
    return (
      "border-red-800 "
      + "bg-red-950/40 "
      + "text-red-300"
    );
  }

  if (normalized === "processing") {
    return (
      "border-amber-800 "
      + "bg-amber-950/40 "
      + "text-amber-300"
    );
  }

  return (
    "border-slate-700 "
    + "bg-slate-900 "
    + "text-slate-300"
  );
}

export default function ReportsPage() {
  const [companyId, setCompanyId] =
    useState<number | null>(null);

  const [companyName, setCompanyName] =
    useState("");

  const [reportType, setReportType] =
    useState<ReportType>("weekly");

  const [format, setFormat] =
    useState<ReportFormat>("pdf");

  const [customStart, setCustomStart] =
    useState("");

  const [customEnd, setCustomEnd] =
    useState("");

  const [history, setHistory] =
    useState<ReportHistoryItem[]>([]);

  const [error, setError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [generating, setGenerating] =
    useState(false);

  const loadReports = useCallback(
    async (
      resolvedCompanyId: number,
    ) => {
      const reports =
        await getReportHistory(
          resolvedCompanyId,
        );

      setHistory(reports.items);
    },
    [],
  );

  useEffect(() => {
    const timer = window.setTimeout(
      () => {
        void (async () => {
          try {
            const company =
              await getActiveCompany();

            setCompanyId(company.id);
            setCompanyName(company.name);

            await loadReports(company.id);
          } catch (cause) {
            setError(
              cause instanceof Error
                ? cause.message
                : "Unable to load reports.",
            );
          } finally {
            setLoading(false);
          }
        })();
      },
      0,
    );

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadReports]);

  async function refreshHistory() {
    if (companyId === null) {
      return;
    }

    setError("");

    try {
      await loadReports(companyId);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to refresh report history.",
      );
    }
  }

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (companyId === null) {
      return;
    }

    setError("");
    setSuccessMessage("");

    const payload: {
      company_id: number;
      report_type: ReportType;
      format: ReportFormat;
      start_date?: string;
      end_date?: string;
    } = {
      company_id: companyId,
      report_type: reportType,
      format,
    };

    if (reportType === "custom") {
      if (!customStart || !customEnd) {
        setError(
          "Choose both a custom start and end date.",
        );
        return;
      }

      const start =
        new Date(customStart);

      const end =
        new Date(customEnd);

      if (
        Number.isNaN(start.getTime())
        || Number.isNaN(end.getTime())
      ) {
        setError(
          "Choose a valid custom date range.",
        );
        return;
      }

      if (start >= end) {
        setError(
          "Custom start must be earlier than the end.",
        );
        return;
      }

      payload.start_date =
        start.toISOString();

      payload.end_date =
        end.toISOString();
    }

    setGenerating(true);

    try {
      const result =
        await generateReport(payload);

      await loadReports(companyId);

      if (result.status === "success") {
        setSuccessMessage(
          result.filename
            ? `Generated ${result.filename}.`
            : "Report generated successfully.",
        );
      } else {
        setError(
          result.error
            ?? `Report finished with status: ${result.status}.`,
        );
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to generate report.",
      );

      try {
        await loadReports(companyId);
      } catch {
        // Keep the original generation error.
      }
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <p
            className={
              "text-sm font-medium uppercase "
              + "tracking-[0.2em] text-cyan-400"
            }
          >
            Reports
          </p>

          <h2
            className={
              "mt-2 text-3xl font-semibold "
              + "tracking-tight text-white"
            }
          >
            {companyName || "Executive Reporting"}
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Generate executive media-intelligence
            reports and download completed files.
          </p>
        </div>

        {error && (
          <p
            className={
              "mb-5 rounded-xl border border-red-900 "
              + "bg-red-950/30 p-4 text-sm text-red-300"
            }
          >
            {error}
          </p>
        )}

        {successMessage && (
          <p
            className={
              "mb-5 rounded-xl border "
              + "border-emerald-900 "
              + "bg-emerald-950/30 p-4 "
              + "text-sm text-emerald-300"
            }
          >
            {successMessage}
          </p>
        )}

        <form
          onSubmit={submit}
          className={
            "grid gap-4 rounded-2xl border "
            + "border-slate-800 bg-slate-900/70 "
            + "p-6 md:grid-cols-3"
          }
        >
          <label className="text-sm text-slate-300">
            Report type

            <select
              value={reportType}
              onChange={(event) => {
                setReportType(
                  event.target.value as ReportType,
                );
                setError("");
                setSuccessMessage("");
              }}
              className={
                "mt-2 w-full rounded-lg border "
                + "border-slate-700 bg-slate-950 "
                + "p-3 text-white"
              }
            >
              <option value="daily">
                Daily
              </option>

              <option value="weekly">
                Weekly
              </option>

              <option value="monthly">
                Monthly
              </option>

              <option value="custom">
                Custom
              </option>
            </select>
          </label>

          <label className="text-sm text-slate-300">
            Format

            <select
              value={format}
              onChange={(event) => {
                setFormat(
                  event.target.value as ReportFormat,
                );
              }}
              className={
                "mt-2 w-full rounded-lg border "
                + "border-slate-700 bg-slate-950 "
                + "p-3 text-white"
              }
            >
              <option value="pdf">
                PDF
              </option>

              <option value="xlsx">
                Excel
              </option>

              <option value="csv">
                CSV
              </option>
            </select>
          </label>

          <button
            disabled={
              generating
              || loading
              || companyId === null
            }
            className={
              "self-end rounded-lg bg-cyan-400 "
              + "p-3 font-semibold text-slate-950 "
              + "disabled:cursor-not-allowed "
              + "disabled:opacity-50"
            }
          >
            {generating
              ? "Generating..."
              : "Generate report"}
          </button>

          {reportType === "custom" && (
            <>
              <label className="text-sm text-slate-300">
                Start

                <input
                  type="datetime-local"
                  value={customStart}
                  onChange={(event) => {
                    setCustomStart(
                      event.target.value,
                    );
                  }}
                  required
                  className={
                    "mt-2 w-full rounded-lg border "
                    + "border-slate-700 bg-slate-950 "
                    + "p-3 text-white"
                  }
                />
              </label>

              <label className="text-sm text-slate-300">
                End

                <input
                  type="datetime-local"
                  value={customEnd}
                  onChange={(event) => {
                    setCustomEnd(
                      event.target.value,
                    );
                  }}
                  required
                  className={
                    "mt-2 w-full rounded-lg border "
                    + "border-slate-700 bg-slate-950 "
                    + "p-3 text-white"
                  }
                />
              </label>

              <div
                className={
                  "self-end rounded-lg border "
                  + "border-slate-800 bg-slate-950/60 "
                  + "p-3 text-xs text-slate-400"
                }
              >
                Custom dates are converted to UTC
                before report generation.
              </div>
            </>
          )}
        </form>

        <section
          className={
            "mt-8 rounded-2xl border "
            + "border-slate-800 bg-slate-900/70 p-6"
          }
        >
          <div
            className={
              "flex flex-col gap-3 sm:flex-row "
              + "sm:items-center sm:justify-between"
            }
          >
            <div>
              <h3
                className={
                  "text-lg font-semibold text-white"
                }
              >
                Report history
              </h3>

              <p className="mt-1 text-sm text-slate-400">
                {history.length} report
                {history.length === 1 ? "" : "s"}
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                void refreshHistory();
              }}
              disabled={
                loading
                || companyId === null
              }
              className={
                "rounded-lg border border-slate-700 "
                + "px-4 py-2 text-sm font-medium "
                + "text-slate-200 transition "
                + "hover:border-slate-500 "
                + "disabled:opacity-50"
              }
            >
              Refresh history
            </button>
          </div>

          {loading ? (
            <p className="mt-4 text-slate-400">
              Loading reports...
            </p>
          ) : history.length === 0 ? (
            <div
              className={
                "mt-4 rounded-xl border "
                + "border-dashed border-slate-700 "
                + "p-6 text-center"
              }
            >
              <p className="text-slate-300">
                No reports generated yet.
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Generate a report above to create
                the first history entry.
              </p>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {history.map((report) => {
                const downloadable =
                  report.status === "success"
                  && report.filename !== null
                  && report.content_type !== null;

                const displayName =
                  report.filename
                  ?? `${report.report_type} `
                    + `${report.file_format} report`;

                return (
                  <article
                    key={report.id}
                    className={
                      "rounded-xl border "
                      + "border-slate-800 "
                      + "bg-slate-950/60 p-4"
                    }
                  >
                    <div
                      className={
                        "flex flex-col gap-4 "
                        + "lg:flex-row "
                        + "lg:items-start "
                        + "lg:justify-between"
                      }
                    >
                      <div className="min-w-0">
                        <div
                          className={
                            "flex flex-wrap items-center "
                            + "gap-2"
                          }
                        >
                          <p
                            className={
                              "break-all font-medium "
                              + "text-white"
                            }
                          >
                            {displayName}
                          </p>

                          <span
                            className={
                              "rounded-full border "
                              + "px-2.5 py-1 text-xs "
                              + "font-medium capitalize "
                              + statusClasses(
                                report.status,
                              )
                            }
                          >
                            {report.status}
                          </span>
                        </div>

                        <p
                          className={
                            "mt-2 text-sm text-slate-400"
                          }
                        >
                          {report.report_type}
                          {" · "}
                          {report.file_format.toUpperCase()}
                        </p>

                        <p
                          className={
                            "mt-1 text-xs text-slate-500"
                          }
                        >
                          {formatDateTime(
                            report.period_start,
                          )}
                          {" → "}
                          {formatDateTime(
                            report.period_end,
                          )}
                        </p>

                        {report.generated_at && (
                          <p
                            className={
                              "mt-1 text-xs "
                              + "text-slate-500"
                            }
                          >
                            Generated{" "}
                            {formatDateTime(
                              report.generated_at,
                            )}
                          </p>
                        )}

                        {report.error && (
                          <p
                            className={
                              "mt-3 rounded-lg border "
                              + "border-red-900/70 "
                              + "bg-red-950/30 p-3 "
                              + "text-sm text-red-300"
                            }
                          >
                            {report.error}
                          </p>
                        )}
                      </div>

                      {downloadable ? (
                        <a
                          href={
                            `${API_BASE_URL}/reports/`
                            + `${report.id}/download`
                          }
                          className={
                            "shrink-0 rounded-lg "
                            + "bg-cyan-400 px-4 py-2 "
                            + "text-center text-sm "
                            + "font-semibold "
                            + "text-slate-950"
                          }
                        >
                          Download
                        </a>
                      ) : (
                        <span
                          className={
                            "shrink-0 rounded-lg border "
                            + "border-slate-800 px-4 py-2 "
                            + "text-center text-sm "
                            + "text-slate-500"
                          }
                        >
                          Not downloadable
                        </span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
