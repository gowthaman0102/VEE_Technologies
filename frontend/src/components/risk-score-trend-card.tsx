"use client";

import { useEffect, useRef, useState } from "react";
import { RiskTrendResponse } from "@/lib/api";

type Props = {
  data: RiskTrendResponse | null;
  range: "7D" | "30D" | "90D";
  onRangeChange: (r: "7D" | "30D" | "90D") => void;
  highThreshold: number;
  error?: boolean;
  isUpdating?: boolean;
};

export function RiskScoreTrendCard({ data, range, onRangeChange, highThreshold, error, isUpdating }: Props) {
  const points = (data?.series ?? []).map((s) => ({
    label: s.period ?? s.bucket ?? null,
    avg: s.average_risk_score,
  }));
  const W = 800;
  const H = 200;
  const PAD_X = 20;
  const PAD_Y = 20;

  const maxRisk = 100;
  const minRisk = 0;
  
  const iW = W - PAD_X * 2;
  const iH = H - PAD_Y * 2;

  const xs = points.map((_, i) => PAD_X + (i / Math.max(1, points.length - 1)) * iW);
  const ys = points.map((p) => PAD_Y + iH - (p.avg / maxRisk) * iH);
  const hasData = xs.length >= 2;

  const linePoints = xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
  const firstX = (xs[0] ?? PAD_X).toFixed(1);
  const lastX = (xs[xs.length - 1] ?? PAD_X).toFixed(1);
  const bottom = (PAD_Y + iH).toFixed(1);
  const areaPoints = `${firstX},${bottom} ${linePoints} ${lastX},${bottom}`;

  const threshY = PAD_Y + iH - (highThreshold / maxRisk) * iH;

  return (
    <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)] relative">
      <div className="flex flex-wrap items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <h2 className="text-[16px] font-semibold text-text">Risk score trend</h2>
          {isUpdating && <span className="text-[12px] font-medium text-muted">Updating...</span>}
          {error && <span className="text-[12px] font-medium text-critical">Failed to load</span>}
        </div>
        <div className="flex items-center gap-1 rounded-[8px] border border-border bg-surface-raised p-1">
          {(["7D", "30D", "90D"] as const).map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={`rounded-[6px] px-3 py-1 text-[12px] font-medium transition-colors ${
                range === r ? "bg-surface text-text shadow-sm" : "text-muted hover:text-text-body"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-[14px] font-semibold text-text">Average risk score - last {range}</h3>
          <p className="text-[12px] text-muted mt-1">Deterministic risk score trend across all monitored intelligence</p>
        </div>

        <div className="relative w-full overflow-hidden" style={{ aspectRatio: "4/1" }}>
          <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-full w-full overflow-visible">
            {/* Background grid */}
            <line x1={PAD_X} y1={PAD_Y} x2={W - PAD_X} y2={PAD_Y} stroke="currentColor" className="text-border" strokeWidth="1" strokeDasharray="4 4" />
            <line x1={PAD_X} y1={PAD_Y + iH / 2} x2={W - PAD_X} y2={PAD_Y + iH / 2} stroke="currentColor" className="text-border" strokeWidth="1" strokeDasharray="4 4" />
            <line x1={PAD_X} y1={bottom} x2={W - PAD_X} y2={bottom} stroke="currentColor" className="text-border" strokeWidth="1" />

            {/* Threshold Line */}
            <line x1={PAD_X} y1={threshY} x2={W - PAD_X} y2={threshY} stroke="var(--color-critical)" strokeWidth="1" opacity="0.6" />
            <text x={W - PAD_X} y={threshY - 6} fill="var(--color-critical)" fontSize="10" fontWeight="600" textAnchor="end" opacity="0.8">
              High-risk threshold ({highThreshold})
            </text>

            {hasData && (
              <>
                <polygon points={areaPoints} fill="var(--color-primary)" opacity="0.1" />
                <polyline points={linePoints} fill="none" stroke="var(--color-primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                {/* Data dots */}
                {xs.map((x, i) => (
                  <circle key={i} cx={x} cy={ys[i]} r="3" fill="var(--color-surface)" stroke="var(--color-primary)" strokeWidth="2" />
                ))}
              </>
            )}
          </svg>
        </div>

        <div className="mt-2 flex items-center justify-between text-[11px] font-medium text-muted px-5">
          <span>{range === "7D" ? "7 days ago" : range === "30D" ? "30 days ago" : "90 days ago"}</span>
          <span>Today</span>
        </div>
      </div>
    </section>
  );
}
