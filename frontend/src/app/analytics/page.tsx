"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

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
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
              Analytics
            </p>

            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
              {companyName
                ? `${companyName} Intelligence Trends`
                : "Intelligence Trends"}
            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Explore stored media intelligence across
              configurable reporting periods.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <TimeRangeSelector
              value={preset}
              onChange={setPreset}
              customStart={customStart}
              customEnd={customEnd}
              onCustomStartChange={
                setCustomStart
              }
              onCustomEndChange={
                setCustomEnd
              }
            />
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {preset === "custom" &&
        (!customStart || !customEnd) ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center">
            <p className="text-lg font-medium text-white">
              Select a custom time range
            </p>

            <p className="mt-2 text-sm text-slate-400">
              Choose both a start and end date
              to load analytics.
            </p>
          </div>
        ) : loading ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-10 text-center text-slate-400">
            Loading analytics...
          </div>
        ) : data === null ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center text-slate-400">
            No analytics data available.
          </div>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                [
                  "Articles",
                  data.total_articles,
                ],
                [
                  "Events",
                  data.total_events,
                ],
                [
                  "High risk",
                  data.risk.high_risk_count ??
                    0,
                ],
                [
                  "Negative sentiment",
                  data.sentiment.negative ?? 0,
                ],
              ].map(([label, value]) => (
                <article
                  key={String(label)}
                  className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
                >
                  <p className="text-sm text-slate-400">
                    {label}
                  </p>

                  <p className="mt-3 text-3xl font-semibold text-white">
                    {value}
                  </p>
                </article>
              ))}
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
                <h3 className="text-lg font-semibold text-white">
                  Business impact
                </h3>

                <div className="mt-4 space-y-3">
                  {Object.entries(
                    data.business_impact,
                  ).length === 0 ? (
                    <p className="text-sm text-slate-500">
                      No business-impact data
                      for this period.
                    </p>
                  ) : (
                    Object.entries(
                      data.business_impact,
                    ).map(
                      ([label, value]) => (
                        <div
                          key={label}
                          className="flex justify-between border-b border-slate-800 py-2 text-sm"
                        >
                          <span className="capitalize text-slate-300">
                            {label.replaceAll(
                              "_",
                              " ",
                            )}
                          </span>

                          <span className="font-semibold text-white">
                            {value}
                          </span>
                        </div>
                      ),
                    )
                  )}
                </div>
              </section>

              <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
                <h3 className="text-lg font-semibold text-white">
                  Competitor mentions
                </h3>

                <div className="mt-4 space-y-3">
                  {data.competitors.length ===
                  0 ? (
                    <p className="text-sm text-slate-500">
                      No configured competitor
                      mentions for this period.
                    </p>
                  ) : (
                    data.competitors.map(
                      (competitor) => (
                        <div
                          key={competitor.name}
                          className="flex justify-between border-b border-slate-800 py-2 text-sm"
                        >
                          <span className="text-slate-300">
                            {competitor.name}
                          </span>

                          <span className="font-semibold text-white">
                            {
                              competitor.mention_count
                            }
                          </span>
                        </div>
                      ),
                    )
                  )}
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
