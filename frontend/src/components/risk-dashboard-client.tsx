"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Bell, ChevronRight, ClipboardList, Gauge, ShieldAlert, Users, Lightbulb, CheckCircle
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { DashboardRiskAnalytics, getDashboardRiskAnalytics } from "@/lib/api";
import { formatLabel } from "@/lib/format";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import { RiskDrilldownModal } from "@/components/risk-drilldown-modal";
import { chartColor } from "@/lib/chart-colors";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

// â”€â”€â”€ Color helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

// Chart colors imported from lib/chart-colors.ts

function riskColor(label: string): string {
  const l = label.toLowerCase();
  if (l.includes("critical")) return "var(--color-critical)";
  if (l.includes("high")) return "var(--color-high)";
  if (l.includes("medium")) return "var(--color-medium)";
  return "var(--color-low)";
}

// â”€â”€â”€ Animated number â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function AnimatedNumber({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(value);
  const prev = useRef<number | null>(null);

  useEffect(() => {
    if (prev.current === null) { prev.current = value; setDisplay(value); return; }
    if (prev.current === value) return;
    const from = prev.current;
    prev.current = value;
    const start = performance.now();
    const dur = 400;
    let id = 0;
    const step = (now: number) => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(2, -10 * p);
      setDisplay(from + (value - from) * eased);
      if (p < 1) id = requestAnimationFrame(step);
      else setDisplay(value);
    };
    id = requestAnimationFrame(step);
    return () => cancelAnimationFrame(id);
  }, [value]);

  return <>{Number(display).toFixed(decimals)}</>;
}

// â”€â”€â”€ KPI Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

type KpiCardConfig = {
  label: string;
  value: number;
  decimals?: number;
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  onClick?: () => void;
  animationDelay?: string;
};

function KpiCard({ label, value, decimals = 0, icon: Icon, iconBg, iconColor, onClick, animationDelay }: KpiCardConfig) {
  const [changed, setChanged] = useState(false);
  const prevValue = useRef<number | null>(null);

  useEffect(() => {
    if (prevValue.current === null) { prevValue.current = value; return; }
    if (prevValue.current === value) return;
    prevValue.current = value;
    setChanged(true);
    const t = setTimeout(() => setChanged(false), 700);
    return () => clearTimeout(t);
  }, [value]);

  const card = (
    <div
      className={`risk-kpi-enter flex items-start gap-4 rounded-xl border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors duration-150 hover:border-border-strong ${changed ? "ring-2 ring-primary-border/60" : "border-border"} ${onClick ? "cursor-pointer" : ""}`}
      style={{ animationDelay }}
    >
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${iconBg}`}>
        <Icon size={20} className={iconColor} strokeWidth={2.2} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-muted leading-tight">{label}</p>
        <p className={`mt-1.5 text-[30px] font-bold leading-none tracking-tight text-text transition-transform duration-300 ${changed ? "scale-105" : "scale-100"}`}>
          <AnimatedNumber value={value} decimals={decimals} />
        </p>
      </div>
      {onClick && <ChevronRight size={16} className="mt-1 shrink-0 text-muted" />}
    </div>
  );

  if (onClick) return <button type="button" onClick={onClick} className="text-left w-full">{card}</button>;
  return card;
}

// â”€â”€â”€ SVG Vertical Bar Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

type RiskLevel = { label: string; count: number };

function collapseEventTypes(data: Array<{ label: string; count: number }>) {
  const sorted = [...data].sort((a, b) => b.count - a.count);
  if (sorted.length <= 4) return sorted;

  const top = sorted.slice(0, 3);
  const remaining = sorted.slice(3).reduce((sum, item) => sum + item.count, 0);
  const existingOther = top.findIndex((item) => item.label.toLowerCase() === "other");
  if (existingOther >= 0) {
    top[existingOther] = { ...top[existingOther], count: top[existingOther].count + remaining };
    return top;
  }

  return [...top, { label: "other", count: remaining }];
}

function RiskBarChart({
  data,
  totalAssessments,
  onBarClick,
}: {
  data: RiskLevel[];
  totalAssessments: number;
  onBarClick: (label: string, count: number) => void;
}) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 80); return () => clearTimeout(t); }, []);

  if (data.length === 0) {
    return <p className="py-10 text-center text-sm text-muted">No risk assessments available.</p>;
  }

  // Ensure High / Medium / Low are present even if zero
  const ORDER = ["critical", "high", "medium", "low"];
  const normalized = ORDER.map(key => {
    const found = data.find(d => d.label.toLowerCase() === key);
    return found ?? { label: key, count: 0 };
  }).filter(d => {
    // Include if backend returned it, or if it's high/medium/low (always show)
    const base = ["high", "medium", "low"];
    return base.includes(d.label.toLowerCase()) || data.some(x => x.label.toLowerCase() === d.label.toLowerCase());
  });

  const maxCount = Math.max(...normalized.map(d => d.count), 1);
  const chartTop = 24;
  const chartH = 184;
  const barW = 56;
  const gap = 48;
  const totalW = normalized.length * (barW + gap) - gap;
  const padLeft = 42;
  const padBottom = 28;

  return (
    <div className="risk-chart-enter">
      <svg
        viewBox={`0 0 ${totalW + padLeft + 16} ${chartH + padBottom + 24}`}
        className="w-full"
        aria-hidden="true"
      >
        {/* Y gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map(frac => {
          const y = chartTop + (1 - frac) * chartH;
          return (
            <g key={frac}>
              <line x1={padLeft} y1={y} x2={totalW + padLeft + 16} y2={y} stroke="var(--border)" strokeWidth={1} />
              <text x={padLeft - 6} y={y + 4} textAnchor="end" fontSize={10} fill="var(--color-muted)">
                {Math.round(frac * maxCount)}
              </text>
            </g>
          );
        })}

        {normalized.map((d, i) => {
          const barH = animated ? Math.max(2, (d.count / maxCount) * chartH) : 2;
          const x = padLeft + i * (barW + gap);
          const y = chartTop + chartH - barH;
          const color = riskColor(d.label);

          return (
            <g key={d.label} className="cursor-pointer" onClick={() => d.count > 0 && onBarClick(d.label, d.count)}>
              {/* Bar */}
              <rect
                x={x} y={y} width={barW} height={barH} rx={6} fill={color}
                style={{ transition: "height 0.8s ease-out, y 0.8s ease-out" }}
                className={d.count > 0 ? "opacity-90 hover:opacity-100" : "opacity-30"}
              />
              {/* Count label above bar â€” always shown clearly above the bar top */}
              <text
                x={x + barW / 2}
                y={d.count === 0
                  ? chartTop + chartH - 26  /* fixed 26px above baseline â€” clear of the axis */
                  : y - 8                   /* always above the bar top */
                }
                textAnchor="middle"
                fontSize={14}
                fontWeight="700"
                fill={d.count === 0 ? "var(--color-muted)" : "var(--color-text)"}
              >
                {d.count}
              </text>
              {/* X label */}
              <text x={x + barW / 2} y={chartTop + chartH + padBottom - 6} textAnchor="middle" fontSize={12} fill="var(--color-muted)" fontWeight="500">
                {formatLabel(d.label)}
              </text>
              {/* Invisible wider hit target */}
              <rect x={x - 4} y={0} width={barW + 8} height={chartH + 32} fill="transparent" />
            </g>
          );
        })}
      </svg>

      {/* Summary row */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {normalized.filter(d => ["high", "medium", "low"].includes(d.label.toLowerCase())).map(d => {
          const pct = totalAssessments > 0 ? ((d.count / totalAssessments) * 100).toFixed(1) : "0.0";
          const color = riskColor(d.label);
          return (
            <button
              key={d.label}
              type="button"
              onClick={() => d.count > 0 && onBarClick(d.label, d.count)}
              className={`flex flex-col items-center rounded-xl border p-3 transition-all hover:shadow-sm ${d.count > 0 ? "cursor-pointer" : "cursor-default opacity-70"}`}
              style={{ borderColor: color + "40", background: color + "0A" }}
            >
              <span className="flex items-center gap-1.5 text-[12px] font-semibold" style={{ color }}>
                <span className="h-2 w-2 rounded-full" style={{ background: color }} />
                {formatLabel(d.label)}
              </span>
              <span className="mt-1 text-[22px] font-bold text-text leading-none">
                <AnimatedNumber value={d.count} />
              </span>
              <span className="text-[12px] font-medium text-muted">{pct}%</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// â”€â”€â”€ Horizontal Event Bars â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function EventBars({
  data,
  onRowClick,
}: {
  data: Array<{ label: string; count: number }>;
  onRowClick: (label: string, count: number) => void;
}) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 120); return () => clearTimeout(t); }, []);

  const sorted = collapseEventTypes(data);
  
  const maxCount = Math.max(...sorted.map(d => d.count), 1);

  if (sorted.length === 0) return <p className="py-8 text-center text-sm text-muted">No event types available.</p>;

  return (
    <div className="risk-chart-enter space-y-2.5">
      {sorted.map((d, i) => {
        const width = animated ? Math.max(2, (d.count / maxCount) * 100) : 0;
        const color = chartColor(i);

        return (
          <button
            key={d.label}
            type="button"
            onClick={() => onRowClick(d.label, d.count)}
            aria-label={`View ${formatLabel(d.label)} articles: ${d.count}`}
            className="group w-full rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-surface-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <div className="flex items-center gap-3">
              <span className="w-[140px] shrink-0 truncate text-[13px] font-medium text-text group-hover:text-primary transition-colors">
                {formatLabel(d.label)}
              </span>
              <div className="flex-1 h-[10px] rounded-full bg-surface-raised overflow-hidden">
                <div
                  className="h-full rounded-full transition-[width] duration-700 ease-out"
                  style={{ width: `${width}%`, backgroundColor: color }}
                />
              </div>
              <span className="w-8 shrink-0 text-right text-[13px] font-bold tabular-nums text-text">{d.count}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

// â”€â”€â”€ SVG Donut Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function DonutChart({
  data,
  onSegmentClick,
}: {
  data: Array<{ label: string; count: number }>;
  onSegmentClick: (label: string, count: number) => void;
}) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 160); return () => clearTimeout(t); }, []);

  const totalEvents = data.reduce((s, d) => s + d.count, 0);
  const sorted = collapseEventTypes(data);

  const R = 80;
  const cx = 100;
  const cy = 100;
  const strokeW = 28;
  const circumference = 2 * Math.PI * R;

  if (totalEvents === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-6">
        <svg viewBox="0 0 200 200" className="h-[180px] w-[180px]">
          <circle cx={cx} cy={cy} r={R} fill="none" stroke="var(--border)" strokeWidth={strokeW} />
          <text x={cx} y={cy - 6} textAnchor="middle" fontSize={22} fontWeight="700" fill="var(--color-text)">0</text>
          <text x={cx} y={cy + 14} textAnchor="middle" fontSize={11} fill="var(--color-muted)">Total Events</text>
        </svg>
        <p className="text-sm text-muted">No events for this period.</p>
      </div>
    );
  }

  // Build arcs using reduce to avoid mutable variable
  const segments = sorted.reduce<Array<{ label: string; count: number; pct: number; dash: number; gap: number; offset: number; color: string }>>(
    (acc, d, i) => {
      const pct = d.count / totalEvents;
      const dash = animated ? pct * circumference : 0;
      const gap = circumference - dash;
      const currentOffset = acc.length > 0 ? acc[acc.length - 1].offset + acc[acc.length - 1].dash : 0;
      return [...acc, { ...d, pct, dash, gap, offset: currentOffset, color: chartColor(i) }];
    },
    []
  );

  return (
    <div>
      <div className="risk-donut-enter flex justify-center">
        <div className="relative">
          <svg viewBox="0 0 200 200" className="h-[190px] w-[190px] -rotate-90">
            {/* Track */}
            <circle cx={cx} cy={cy} r={R} fill="none" stroke="var(--color-border)" strokeWidth={strokeW} />
            {segments.map(s => (
              <circle
                key={s.label}
                cx={cx} cy={cy} r={R}
                fill="none"
                stroke={s.color}
                strokeWidth={strokeW}
                strokeDasharray={`${s.dash} ${circumference - s.dash}`}
                strokeDashoffset={-s.offset}
                strokeLinecap="butt"
                className="cursor-pointer opacity-90 hover:opacity-100 transition-opacity"
                style={{ transition: "stroke-dasharray 0.8s ease-out" }}
                onClick={() => onSegmentClick(s.label, s.count)}
              />
            ))}
          </svg>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[28px] font-bold text-text leading-none">{totalEvents.toLocaleString()}</span>
            <span className="text-[11px] font-medium text-muted mt-1">Total Events</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-1.5">
        {sorted.map((d, i) => {
          const pct = totalEvents > 0 ? ((d.count / totalEvents) * 100).toFixed(1) : "0.0";
          const color = chartColor(i);
          return (
            <button
              key={d.label}
              type="button"
              onClick={() => onSegmentClick(d.label, d.count)}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-surface-raised"
            >
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />
              <span className="truncate text-[12px] text-text font-medium">{formatLabel(d.label)}</span>
              <span className="ml-auto shrink-0 text-[11px] font-semibold text-muted tabular-nums">{d.count} ({pct}%)</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// â”€â”€â”€ Chart Panel Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function ChartCard({
  title,
  subtitle,
  rightContent,
  children,
  className = "",
}: {
  title: string;
  subtitle: string;
  rightContent?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col rounded-xl border border-border bg-surface p-6 shadow-[0_1px_2px_rgba(28,23,52,0.06)] ${className}`}>
      <div className="flex items-start justify-between gap-3 mb-5">
        <div>
          <h3 className="text-[17px] font-bold text-text leading-none">{title}</h3>
          <p className="mt-1.5 text-[13px] text-muted">{subtitle}</p>
        </div>
        {rightContent}
      </div>
      {children}
    </div>
  );
}

// â”€â”€â”€ Utilities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function formatRelative(date: Date): string {
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

// â”€â”€â”€ Modal State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

type ModalState = { isOpen: boolean; metric: string; value?: string; title: string; total: number };

// â”€â”€â”€ Main Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function RiskDashboardClient({ initialData }: { initialData: DashboardRiskAnalytics }) {
  const [data, setData] = useState(initialData);
  const [liveStatus, setLiveStatus] = useState<"live" | "delayed">("live");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [modal, setModal] = useState<ModalState>({ isOpen: false, metric: "", title: "", total: 0 });

  useAutoRefresh(async () => {
    try {
      const fresh = await getDashboardRiskAnalytics();
      setData(fresh);
      setLiveStatus("live");
      setLastUpdated(new Date());
    } catch {
      setLiveStatus("delayed");
    }
  }, { intervalMs: 60_000 });

  const openDrilldown = useCallback((metric: string, title: string, total: number, value?: string) => {
    setModal({ isOpen: true, metric, value, title, total });
  }, []);

  const closeDrilldown = useCallback(() => setModal(prev => ({ ...prev, isOpen: false })), []);

  const total = data.total_assessments;
  const totalEvents = data.event_types.reduce((s, d) => s + d.count, 0);

  // Deterministic insight
  const highLevel = data.risk_levels.find(d => d.label.toLowerCase() === "high");
  const highPct = total > 0 && highLevel ? ((highLevel.count / total) * 100) : 0;
  const topEvent = [...data.event_types].sort((a, b) => b.count - a.count)[0];
  const topEvent2 = [...data.event_types].sort((a, b) => b.count - a.count)[1];

  let insightHeadline = "Current monitored risk remains comparatively limited.";
  let insightBody = "Monitor the feed for developing risk signals.";
  if (data.immediate_alert_count > 0) {
    insightHeadline = "Immediate alert activity requires attention.";
    insightBody = `${data.immediate_alert_count} alert${data.immediate_alert_count > 1 ? "s" : ""} require immediate review.`;
  } else if (highPct >= 60) {
    insightHeadline = "Elevated risk activity requires continued monitoring.";
    const evtParts = [topEvent, topEvent2].filter(Boolean);
    const evtLabel = evtParts.map(e => formatLabel(e!.label)).join(" and ");
    const combinedPct = evtParts.reduce((s, e) => s + (totalEvents > 0 ? e!.count / totalEvents * 100 : 0), 0);
    insightBody = `High-risk events account for ${highPct.toFixed(1)}% of all assessments${evtLabel ? `, with ${evtLabel} representing ${combinedPct.toFixed(1)}% of total event volume.` : "."}`;
  } else if (highPct > 0) {
    insightHeadline = "Moderate risk activity detected across monitored sources.";
    insightBody = `High-risk assessments represent ${highPct.toFixed(1)}% of all assessed intelligence.`;
  }

  const kpis: KpiCardConfig[] = [
    {
      label: "Total Assessments", value: data.total_assessments, icon: ClipboardList, animationDelay: "0ms",
      iconBg: "bg-blue-50", iconColor: "text-blue-500",
      onClick: () => openDrilldown("total_assessments", "All Risk Assessments", data.total_assessments),
    },
    {
      label: "Average Risk Score", value: data.average_risk_score, decimals: 1, icon: Gauge, animationDelay: "70ms",
      iconBg: "bg-amber-50", iconColor: "text-amber-500",
    },
    {
      label: "Highest Risk Score", value: data.highest_risk_score, decimals: 1, icon: ShieldAlert, animationDelay: "140ms",
      iconBg: "bg-red-50", iconColor: "text-red-500",
    },
    {
      label: "Human Review", value: data.human_review_count, icon: Users, animationDelay: "210ms",
      iconBg: "bg-violet-50", iconColor: "text-violet-500",
      onClick: () => openDrilldown("human_review", "Human Review Articles", data.human_review_count),
    },
    {
      label: "Immediate Alerts", value: data.immediate_alert_count, icon: Bell, animationDelay: "280ms",
      iconBg: data.immediate_alert_count > 0 ? "bg-high-bg" : "bg-primary-soft",
      iconColor: data.immediate_alert_count > 0 ? "text-high" : "text-primary",
      onClick: () => openDrilldown("immediate_alert", "Immediate Alert Articles", data.immediate_alert_count),
    },
  ];

  return (
    <main className="relative w-full min-h-screen overflow-hidden bg-surface-raised">
          <PageAmbient kind="risk" />
          <div className="relative z-10 mx-auto w-full max-w-[1600px] px-6 py-7 lg:px-10 space-y-6">

        <div className="mb-4 flex justify-end">
          <div suppressHydrationWarning className="page-live-chip page-live-chip--risk" aria-live="polite">
            <span className="page-live-label">LIVE</span>
          </div>
        </div>

        <CosmicPageHero variant="risk" imageSrc="/risk-analytics-hero.png" eyebrow="RISK ANALYTICS" title="Risk Intelligence Overview" description="Deterministic risk scoring across monitored intelligence, including review and alert signals." />
        {/* â”€â”€ KPI Row â”€â”€â”€ */}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Key performance indicators">
          {kpis.map(kpi => <KpiCard key={kpi.label} {...kpi} />)}
        </section>

        {/* â”€â”€ Analytics Grid â”€â”€â”€ */}
        <section className="grid gap-5 xl:grid-cols-[34fr_38fr_28fr]" aria-label="Risk analytics charts">

          {/* Panel A â€” Risk Level Distribution */}
          <ChartCard
            title="Risk Level Distribution"
            subtitle="Assessment count by deterministic risk level."
            rightContent={
              <span className="rounded-full bg-primary-soft px-3 py-1 text-[12px] font-bold text-primary">
                Total {total.toLocaleString()}
              </span>
            }
          >
            <RiskBarChart
              data={data.risk_levels}
              totalAssessments={total}
              onBarClick={(label, count) => openDrilldown("risk_level", `${formatLabel(label)} Risk Articles`, count, label)}
            />
          </ChartCard>

          {/* Panel B â€” Event Type Distribution */}
          <ChartCard
            title="Event Type Distribution"
            subtitle="Intelligence events currently represented in risk scoring."
          >
            <EventBars
              data={data.event_types}
              onRowClick={(label, count) => openDrilldown("event_type", `${formatLabel(label)} Articles`, count, label)}
            />
          </ChartCard>

          {/* Panel C â€” Event Type Share */}
          <ChartCard
            title="Event Type Share"
            subtitle="Proportion of intelligence events by type."
          >
            <DonutChart
              data={data.event_types}
              onSegmentClick={(label, count) => openDrilldown("event_type", `${formatLabel(label)} Articles`, count, label)}
            />
          </ChartCard>
        </section>

        {/* â”€â”€ Insight Strip â”€â”€â”€ */}
        <section className="flex flex-col gap-4 rounded-xl border border-border bg-surface px-7 py-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)] md:flex-row md:items-center md:justify-between" aria-label="Key insights">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
              <Lightbulb size={20} strokeWidth={2.2} />
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-primary">Key Insights</p>
              <h3 className="mt-0.5 text-[17px] font-bold text-text leading-snug">{insightHeadline}</h3>
              <p className="mt-1 text-[13px] text-muted">{insightBody}</p>
            </div>
          </div>

          <div className={`flex shrink-0 items-center gap-3 rounded-xl border px-5 py-3 ${data.immediate_alert_count > 0 ? "border-critical-border bg-critical-bg" : "border-low-border bg-low-bg"}`}>
            <CheckCircle size={18} className={data.immediate_alert_count > 0 ? "text-critical" : "text-low"} />
            <div>
              <p className={`text-[14px] font-bold ${data.immediate_alert_count > 0 ? "text-critical" : "text-low"}`}>
                {data.immediate_alert_count > 0 ? `${data.immediate_alert_count} Immediate Alert${data.immediate_alert_count > 1 ? "s" : ""}` : "No immediate alerts"}
              </p>
              <p className="text-[12px] font-medium text-muted">
                {data.immediate_alert_count > 0 ? "Items require attention." : "Risk levels are stable."}
              </p>
            </div>
            {data.immediate_alert_count > 0 && (
              <button
                type="button"
                onClick={() => openDrilldown("immediate_alert", "Immediate Alert Articles", data.immediate_alert_count)}
                className="ml-2 flex h-7 w-7 items-center justify-center rounded-full border border-critical-border text-critical hover:bg-surface-raised transition-colors"
              >
                <ChevronRight size={15} />
              </button>
            )}
          </div>
        </section>
      </div>

      <RiskDrilldownModal
        isOpen={modal.isOpen}
        metric={modal.metric}
        value={modal.value}
        title={modal.title}
        targetTotal={modal.total}
        onClose={closeDrilldown}
      />
    </main>
  );
}


