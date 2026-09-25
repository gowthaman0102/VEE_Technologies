"use client";

import { useEffect, useState } from "react";
import { Check, LoaderCircle, Save, Settings2 } from "lucide-react";
import {
  getCompanyConfiguration,
  updateCompanyConfiguration,
  type ClientConfiguration,
} from "@/lib/api";

const tabs = ["Sources", "Risk", "Alerts", "Reports", "Features"] as const;
type Tab = (typeof tabs)[number];

const reportSections = [
  "executive_summary",
  "kpis",
  "articles",
  "sentiment",
  "risk",
  "business_impact",
  "events",
  "sources",
  "competitors",
  "alerts",
];

const featureLabels: Record<string, string> = {
  sentiment_enabled: "Sentiment",
  risk_enabled: "Risk",
  business_impact_enabled: "Business Impact",
  competitor_detection_enabled: "Competitor Detection",
  event_clustering_enabled: "Event Clustering",
  alerts_enabled: "Alerts",
  reports_enabled: "Reports",
  publisher_country_enabled: "Publisher Country",
};

function splitLines(value: string): string[] {
  return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
}

function joinLines(value: string[]): string {
  return value.join("\n");
}

export function CompanyConfigurationPanel({ companyId }: { companyId: number }) {
  const [config, setConfig] = useState<ClientConfiguration | null>(null);
  const [tab, setTab] = useState<Tab>("Sources");
  const [status, setStatus] = useState<"idle" | "loading" | "saving" | "saved" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getCompanyConfiguration(companyId)
      .then((value) => {
        if (!cancelled) {
          setConfig(value);
          setStatus("idle");
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Unable to load configuration");
          setStatus("error");
        }
      });
    return () => { cancelled = true; };
  }, [companyId]);

  const updateSection = <K extends "sources" | "risk" | "alerts" | "reports" | "features" | "branding">(
    section: K,
    value: ClientConfiguration[K],
  ) => setConfig((current) => current ? { ...current, [section]: value } : current);

  const save = async () => {
    if (!config) return;
    if (!(config.risk.medium_threshold < config.risk.high_threshold && config.risk.high_threshold < config.risk.critical_threshold)) {
      setError("Risk thresholds must satisfy medium < high < critical.");
      setStatus("error");
      return;
    }
    setStatus("saving");
    setError("");
    try {
      const saved = await updateCompanyConfiguration(companyId, {
        sources: config.sources,
        risk: config.risk,
        alerts: config.alerts,
        reports: config.reports,
        features: config.features,
        branding: config.branding,
      });
      setConfig(saved);
      setStatus("saved");
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to save configuration");
      setStatus("error");
    }
  };

  if (status === "error" && !config) {
    return <section className="rounded-xl border border-critical-border bg-critical-bg p-6"><p className="text-sm text-critical">{error || "Unable to load configuration."}</p></section>;
  }

  if (status === "loading" || !config) {
    return <section className="rounded-xl border border-border bg-surface p-6"><p className="flex items-center gap-2 text-sm text-muted"><LoaderCircle size={16} className="animate-spin" /> Loading configuration...</p></section>;
  }

  const inputClass = "mt-1 w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm text-text outline-none focus:border-primary";
  const labelClass = "text-xs font-semibold uppercase tracking-[0.08em] text-muted";

  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
      <div className="flex flex-col gap-4 border-b border-border pb-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3"><Settings2 size={20} className="text-primary" /><div><h2 className="text-lg font-bold text-text">Company Configuration</h2><p className="text-sm text-muted">{config.company_name}</p></div></div>
        <button type="button" onClick={() => void save()} disabled={status === "saving"} className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"><Save size={16} />{status === "saving" ? "Saving..." : status === "saved" ? "Saved" : "Save"}</button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Company configuration sections">
        {tabs.map((item) => <button key={item} type="button" role="tab" aria-selected={tab === item} onClick={() => setTab(item)} className={`rounded-lg px-3 py-2 text-sm font-semibold ${tab === item ? "bg-primary-soft text-primary" : "text-muted hover:bg-surface-raised"}`}>{item}</button>)}
      </div>
      {error && <p className="mt-4 rounded-lg border border-critical-border bg-critical-bg px-3 py-2 text-sm text-critical">{error}</p>}

      {tab === "Sources" && <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="flex items-center gap-2 text-sm font-medium text-text"><input type="checkbox" checked={config.sources.google_news_enabled} onChange={(event) => updateSection("sources", { ...config.sources, google_news_enabled: event.target.checked })} /> Google News</label>
        <label className="flex items-center gap-2 text-sm font-medium text-text"><input type="checkbox" checked={config.sources.newsapi_enabled} onChange={(event) => updateSection("sources", { ...config.sources, newsapi_enabled: event.target.checked })} /> NewsAPI</label>
        <label className="md:col-span-2"><span className={labelClass}>Official RSS sources</span><textarea className={inputClass} rows={3} value={joinLines(config.sources.official_sources)} onChange={(event) => updateSection("sources", { ...config.sources, official_sources: splitLines(event.target.value) })} /></label>
        <label><span className={labelClass}>Preferred sources</span><textarea className={inputClass} rows={3} value={joinLines(config.sources.preferred_sources)} onChange={(event) => updateSection("sources", { ...config.sources, preferred_sources: splitLines(event.target.value) })} /></label>
        <label><span className={labelClass}>Excluded sources</span><textarea className={inputClass} rows={3} value={joinLines(config.sources.excluded_sources)} onChange={(event) => updateSection("sources", { ...config.sources, excluded_sources: splitLines(event.target.value) })} /></label>
      </div>}

      {tab === "Risk" && <div className="mt-5 grid gap-4 sm:grid-cols-3">{(["medium_threshold", "high_threshold", "critical_threshold"] as const).map((key) => <label key={key}><span className={labelClass}>{key.replace("_threshold", "")}</span><input className={inputClass} type="number" min={0} max={100} value={config.risk[key]} onChange={(event) => updateSection("risk", { ...config.risk, [key]: Number(event.target.value) })} /></label>)}</div>}

      {tab === "Alerts" && <div className="mt-5 grid gap-4 md:grid-cols-2"><label className="flex items-center gap-2 text-sm font-medium text-text"><input type="checkbox" checked={config.alerts.enabled} onChange={(event) => updateSection("alerts", { ...config.alerts, enabled: event.target.checked })} /> Alerts enabled</label><label><span className={labelClass}>SLA minutes</span><input className={inputClass} type="number" min={1} value={config.alerts.sla_minutes} onChange={(event) => updateSection("alerts", { ...config.alerts, sla_minutes: Number(event.target.value) })} /></label>{(["minimum_risk_level", "immediate_alert_level"] as const).map((key) => <label key={key}><span className={labelClass}>{key.replaceAll("_", " ")}</span><select className={inputClass} value={config.alerts[key]} onChange={(event) => updateSection("alerts", { ...config.alerts, [key]: event.target.value as ClientConfiguration["alerts"][typeof key] })}><option>low</option><option>medium</option><option>high</option><option>critical</option></select></label>)}</div>}

      {tab === "Reports" && <div className="mt-5 grid gap-4 md:grid-cols-2"><div className="grid gap-2">{reportSections.map((section) => <label key={section} className="flex items-center gap-2 text-sm font-medium text-text"><input type="checkbox" checked={config.reports.enabled_sections.includes(section)} onChange={(event) => updateSection("reports", { ...config.reports, enabled_sections: event.target.checked ? [...config.reports.enabled_sections, section] : config.reports.enabled_sections.filter((item) => item !== section) })} /> {section.replaceAll("_", " ")}</label>)}</div><div className="grid content-start gap-4"><label><span className={labelClass}>Top article limit</span><input className={inputClass} type="number" min={1} value={config.reports.top_article_limit} onChange={(event) => updateSection("reports", { ...config.reports, top_article_limit: Number(event.target.value) })} /></label><label><span className={labelClass}>Report title</span><input className={inputClass} value={config.reports.report_title_template} onChange={(event) => updateSection("reports", { ...config.reports, report_title_template: event.target.value })} /></label></div></div>}

      {tab === "Features" && <div className="mt-5 grid gap-3 sm:grid-cols-2">{Object.entries(config.features).map(([key, enabled]) => <label key={key} className="flex items-center gap-2 text-sm font-medium text-text"><input type="checkbox" checked={enabled} onChange={(event) => updateSection("features", { ...config.features, [key]: event.target.checked })} /> {featureLabels[key] ?? key}</label>)}</div>}

      {status === "saved" && <p className="mt-4 flex items-center gap-2 text-sm font-medium text-low"><Check size={16} /> Configuration saved.</p>}
    </section>
  );
}
