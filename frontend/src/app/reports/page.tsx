import { getReportSummary } from "@/lib/api";

export default async function ReportsPage() {
  const report = await getReportSummary({ company_id: 1, start_date: "2026-01-01T00:00:00+00:00", end_date: "2026-12-31T23:59:59+00:00" });

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Reports
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Executive Reporting Summary
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">Total articles</p>
            <p className="mt-3 text-3xl font-semibold text-white">{report.total_articles}</p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">Total events</p>
            <p className="mt-3 text-3xl font-semibold text-white">{report.total_events}</p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">High risk</p>
            <p className="mt-3 text-3xl font-semibold text-white">{report.high_risk_count}</p>
          </article>
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">Sentiment</p>
            <p className="mt-3 text-xl font-semibold text-white">
              {report.sentiment_balance.positive} / {report.sentiment_balance.neutral} / {report.sentiment_balance.negative}
            </p>
          </article>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <h3 className="text-lg font-semibold text-white">Metrics</h3>
          <div className="mt-4 space-y-3">
            {report.metrics.map((metric) => (
              <div key={metric.label} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm">
                <span className="text-slate-300">{metric.label}</span>
                <span className="font-semibold text-white">{String(metric.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
