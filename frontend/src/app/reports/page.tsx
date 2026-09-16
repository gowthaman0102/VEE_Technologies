"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  generateReport,
  getActiveCompany,
  getReportHistory,
  ReportHistoryItem,
} from "@/lib/api";

export default function ReportsPage() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [reportType, setReportType] = useState<"daily" | "weekly" | "monthly" | "custom">("weekly");
  const [format, setFormat] = useState<"pdf" | "xlsx" | "csv">("pdf");
  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  async function load() {
    try {
      const company = await getActiveCompany();
      setCompanyId(company.id);
      setCompanyName(company.name);
      const reports = await getReportHistory(company.id);
      setHistory(reports.items);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (companyId === null) return;
    setGenerating(true);
    setError("");
    try {
      await generateReport({ company_id: companyId, report_type: reportType, format });
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to generate report.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Reports</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">{companyName || "Executive Reporting"}</h2>
        </div>
        {error && <p className="mb-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}
        <form onSubmit={submit} className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 md:grid-cols-3">
          <label className="text-sm text-slate-300">Report type<select value={reportType} onChange={(event) => setReportType(event.target.value as typeof reportType)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="custom">Custom</option></select></label>
          <label className="text-sm text-slate-300">Format<select value={format} onChange={(event) => setFormat(event.target.value as typeof format)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"><option value="pdf">PDF</option><option value="xlsx">Excel</option><option value="csv">CSV</option></select></label>
          <button disabled={generating || loading} className="self-end rounded-lg bg-cyan-400 p-3 font-semibold text-slate-950 disabled:opacity-50">{generating ? "Generating..." : "Generate report"}</button>
        </form>
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <h3 className="text-lg font-semibold text-white">Report history</h3>
          {loading ? <p className="mt-4 text-slate-400">Loading reports...</p> : history.length === 0 ? <p className="mt-4 text-slate-400">No reports generated yet.</p> : <div className="mt-4 space-y-3">{history.map((report) => <div key={report.id} className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-4 md:flex-row md:items-center md:justify-between"><div><p className="font-medium text-white">{report.filename}</p><p className="mt-1 text-sm text-slate-400">{report.report_type} · {report.status}</p></div><a href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"}/reports/${report.id}/download`} className="text-sm font-medium text-cyan-400">Download</a></div>)}</div>}
        </section>
      </div>
    </main>
  );
}
