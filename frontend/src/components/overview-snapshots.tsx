"use client";

import { formatLabel } from "@/lib/format";
import { toneForRisk, toneForSentiment } from "@/components/ui/badge";

export function RiskSnapshot({ risk }: { risk: Record<string, number> }) {
  const counts = [
    { label: "Critical", count: risk.critical_risk_count ?? 0, tone: toneForRisk("critical") },
    { label: "High", count: risk.high_risk_count ?? 0, tone: toneForRisk("high") },
    { label: "Medium", count: risk.medium_risk_count ?? 0, tone: toneForRisk("medium") },
    { label: "Low", count: risk.low_risk_count ?? 0, tone: toneForRisk("low") },
  ];

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Risk Snapshot</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {counts.map(c => (
          <div key={c.label} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body">{c.label}</span>
            <span className={`inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-bold ${c.tone} ${c.tone.includes("bg-") ? "" : "border"}`}>
              {c.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SentimentSnapshot({ sentiment }: { sentiment: Record<string, number> }) {
  const counts = [
    { label: "Positive", count: sentiment.positive ?? 0, tone: toneForSentiment("positive") },
    { label: "Neutral", count: sentiment.neutral ?? 0, tone: toneForSentiment("neutral") },
    { label: "Negative", count: sentiment.negative ?? 0, tone: toneForSentiment("negative") },
  ];

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Sentiment Snapshot</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-4">
        {counts.map(c => (
          <div key={c.label} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body">{c.label}</span>
            <span className={`inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-bold ${c.tone}`}>
              {c.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function BusinessImpactSnapshot({ impact }: { impact: Record<string, number> }) {
  const sorted = Object.entries(impact)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Business Impact</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {sorted.length > 0 ? sorted.map(([label, count]) => (
          <div key={label} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body truncate mr-2" title={formatLabel(label)}>
              {formatLabel(label)}
            </span>
            <span className="text-sm font-semibold text-text tabular-nums">{count}</span>
          </div>
        )) : (
          <p className="text-sm text-muted text-center italic">No impact data available.</p>
        )}
      </div>
    </div>
  );
}

export function SourceCoverageSnapshot({ sources }: { sources: Array<{ source_name: string; count: number }> }) {
  const sorted = [...sources].sort((a, b) => b.count - a.count).slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Global Media Coverage</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {sorted.length > 0 ? sorted.map((s, i) => (
          <div key={`${s.source_name}-${i}`} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body truncate mr-2">{s.source_name}</span>
            <span className="text-sm font-semibold text-text tabular-nums">{s.count}</span>
          </div>
        )) : (
          <p className="text-sm text-muted text-center italic">No source data available.</p>
        )}
      </div>
    </div>
  );
}

export function EmergingTopicsSnapshot({ events }: { events: Array<{ label: string; count: number }> }) {
  const sorted = [...events].sort((a, b) => b.count - a.count).slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Top Emerging Topics</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {sorted.length > 0 ? sorted.map((e, i) => (
          <div key={`${e.label}-${i}`} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body truncate mr-2">{e.label}</span>
            <span className="text-sm font-semibold text-text tabular-nums">{e.count}</span>
          </div>
        )) : (
          <p className="text-sm text-muted text-center italic">No topics active.</p>
        )}
      </div>
    </div>
  );
}

export function PublisherCountrySnapshot({ countries }: { countries: Array<{ country_name: string; article_count: number }> }) {
  const sorted = [...countries].sort((a, b) => b.article_count - a.article_count).slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-surface p-5 h-full flex flex-col">
      <h3 className="text-[13px] font-bold uppercase tracking-wider text-muted">Publisher Coverage by Country</h3>
      <div className="mt-4 flex-1 flex flex-col justify-center gap-3">
        {sorted.length > 0 ? sorted.map((s, i) => (
          <div key={`${s.country_name}-${i}`} className="flex items-center justify-between">
            <span className="text-sm font-medium text-text-body truncate mr-2">{s.country_name}</span>
            <span className="text-sm font-semibold text-text tabular-nums">{s.article_count}</span>
          </div>
        )) : (
          <p className="text-sm text-muted text-center italic">No country data available.</p>
        )}
      </div>
    </div>
  );
}
