"use client";

import { useEffect, useRef, useState } from "react";
import { ArticleTrendPoint } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

export type SentimentSnapshot = {
  positive: number;
  neutral: number;
  negative: number;
};

// ── Constants ─────────────────────────────────────────────────────────────

const DONUT_R = 44;
const DONUT_CIRC = 2 * Math.PI * DONUT_R; // ≈ 276.46

// ── Helpers ────────────────────────────────────────────────────────────────

function shortDayLabel(isoString: string | null): string {
  if (!isoString) return "";
  return new Date(isoString).toLocaleDateString("en-US", { weekday: "short" });
}

function buildCoords(points: ArticleTrendPoint[], W: number, H: number, PAD: number) {
  if (points.length < 2) return { xs: [] as number[], ys: [] as number[] };
  const counts = points.map((p) => p.article_count);
  const maxC = Math.max(...counts, 1);
  const minC = Math.min(...counts);
  const range = maxC - minC || 1;
  const iW = W - PAD * 2;
  const iH = H - PAD * 2;
  const xs = points.map((_, i) => PAD + (i / (points.length - 1)) * iW);
  const ys = points.map((p) => PAD + iH - ((p.article_count - minC) / range) * iH);
  return { xs, ys };
}

// Live "Xs ago" ticker
function useAgoLabel(ts: number | null) {
  const [label, setLabel] = useState("just now");
  useEffect(() => {
    if (ts === null) return;
    const tick = () => {
      const sec = Math.floor((Date.now() - ts) / 1000);
      if (sec < 10) setLabel("just now");
      else if (sec < 60) setLabel(`${sec}s ago`);
      else setLabel(`${Math.floor(sec / 60)}m ago`);
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => clearInterval(id);
  }, [ts]);
  return label;
}

// ── Animated Sparkline ──────────────────────────────────────────────────────

function AnimatedSparkline({
  points,
  refreshError,
  lastSyncTimestamp,
}: {
  points: ArticleTrendPoint[];
  refreshError: boolean;
  lastSyncTimestamp: number | null;
}) {
  const W = 480;
  const H = 110;
  const PAD = 14;
  const { xs, ys } = buildCoords(points, W, H, PAD);
  const hasData = xs.length >= 2;

  const linePoints = xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
  const firstX = (xs[0] ?? PAD).toFixed(1);
  const lastX = (xs[xs.length - 1] ?? PAD).toFixed(1);
  const bottom = (PAD + H - PAD * 2).toFixed(1);
  const areaPoints = `${firstX},${bottom} ${linePoints} ${lastX},${bottom}`;

  // Use animKey to remount SVG on data change → re-triggers CSS animations
  const animKey = points.map((p) => p.article_count).join(",");
  const agoLabel = useAgoLabel(lastSyncTimestamp);

  // CSS-based line draw via strokeDashoffset
  const [dashOffset, setDashOffset] = useState(9999);
  const [dotsVisible, setDotsVisible] = useState<boolean[]>([]);
  const [areaOpacity, setAreaOpacity] = useState(0);
  const polyRef = useRef<SVGPolylineElement>(null);

  useEffect(() => {
    if (!hasData) return;
     
    setTimeout(() => setDashOffset(9999), 0);
    setTimeout(() => setDotsVisible(points.map(() => false)), 0);
    setTimeout(() => setAreaOpacity(0), 0);

    // Measure actual path length after render
    const id = setTimeout(() => {
      const len = polyRef.current?.getTotalLength?.() ?? 600;
      setDashOffset(len);
      // Delay briefly then animate to 0
      requestAnimationFrame(() => {
        setTimeout(() => {
          setDashOffset(0);
          setAreaOpacity(1);
        }, 30);
      });

      // Stagger each dot
      points.forEach((_, i) => {
        setTimeout(() => {
          setDotsVisible((prev) => {
            const next = [...prev];
            next[i] = true;
            return next;
          });
        }, 900 + i * 80);
      });
    }, 30);

    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [animKey]);

  // Pulse ring on latest dot
  const [pulseR, setPulseR] = useState(4);
  const [pulseOp, setPulseOp] = useState(0);
  useEffect(() => {
    if (!hasData) return;
    let forward = true;
    const id = setInterval(() => {
      setPulseR(forward ? 14 : 4);
      setPulseOp(forward ? 0 : 0.6);
      forward = !forward;
    }, 1200);
    return () => clearInterval(id);
  }, [hasData]);

  return (
    <div className="flex-1 min-w-0 rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h3 className="text-sm font-semibold text-text">Article volume · last 7 days</h3>
          <p className="mt-0.5 text-xs text-muted">Daily article intake across all monitored sources</p>
        </div>
        {refreshError ? (
          <span className="shrink-0 rounded-full bg-critical-bg px-2 py-0.5 text-[11px] font-medium text-critical">couldn&apos;t refresh</span>
        ) : (
          <span className="text-[11px] text-muted shrink-0">Updated {agoLabel}</span>
        )}
      </div>

      <div className="mt-1 w-full overflow-hidden">
        {!hasData ? (
          <div className="flex h-[110px] items-center justify-center text-xs text-muted">No article data for this period</div>
        ) : (
          <svg
            key={animKey}
            viewBox={`0 0 ${W} ${H}`}
            className="w-full"
            style={{ height: H }}
            aria-label="Article volume sparkline"
            role="img"
          >
            <defs>
              <linearGradient id="sparkAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.22" />
                <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0" />
              </linearGradient>
              <filter id="dotGlow" x="-100%" y="-100%" width="300%" height="300%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>

            {/* Filled area — CSS opacity transition */}
            <polygon
              points={areaPoints}
              fill="url(#sparkAreaGrad)"
              style={{ opacity: areaOpacity, transition: "opacity 0.8s ease" }}
            />

            {/* Line — CSS stroke-dashoffset transition */}
            <polyline
              ref={polyRef}
              points={linePoints}
              fill="none"
              stroke="var(--color-primary)"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeDasharray={9999}
              strokeDashoffset={dashOffset}
              style={{ transition: "stroke-dashoffset 1.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)" }}
            />

            {/* Staggered dots */}
            {xs.map((x, i) => (
              <circle
                key={i}
                cx={x.toFixed(1)}
                cy={ys[i].toFixed(1)}
                r={dotsVisible[i] ? 4 : 0}
                fill="var(--color-primary)"
                filter="url(#dotGlow)"
                style={{ opacity: dotsVisible[i] ? 1 : 0, transition: "opacity 0.4s ease, r 0.4s ease" }}
              />
            ))}

            {/* Pulse ring on last point */}
            {xs.length > 0 && (
              <circle
                cx={xs[xs.length - 1].toFixed(1)}
                cy={ys[ys.length - 1].toFixed(1)}
                r={pulseR}
                fill="none"
                stroke="var(--color-primary)"
                strokeWidth="1.5"
                style={{ opacity: pulseOp, transition: "r 1.2s ease, opacity 1.2s ease" }}
              />
            )}
          </svg>
        )}
      </div>

      {hasData && (
        <div className="mt-1 flex justify-between px-3">
          {points.map((p, i) => (
            <span key={i} className="text-[10px] text-muted select-none">{shortDayLabel(p.bucket)}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Animated Donut ──────────────────────────────────────────────────────────

// Single circle segment using stroke-dasharray + stroke-dashoffset
function DonutSegment({
  pct,
  color,
  offsetPct,   // cumulative pct of previous segments
  animDelay,
}: {
  pct: number;
  color: string;
  offsetPct: number;
  animDelay: number;
}) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const id = setTimeout(() => setAnimated(true), animDelay);
    return () => clearTimeout(id);
  }, [animDelay, pct]);

  const segLen = (pct / 100) * DONUT_CIRC;
  const gap = DONUT_CIRC - segLen;
  // dashoffset positions the stroke: start at top (-90°) minus cumulative segments
  const dashOffset = DONUT_CIRC / 4 - (offsetPct / 100) * DONUT_CIRC;

  return (
    <circle
      cx="60"
      cy="60"
      r={DONUT_R}
      fill="none"
      stroke={color}
      strokeWidth="14"
      strokeLinecap="butt"
      strokeDasharray={animated ? `${segLen.toFixed(2)} ${gap.toFixed(2)}` : `0 ${DONUT_CIRC.toFixed(2)}`}
      strokeDashoffset={dashOffset}
      style={{
        transition: `stroke-dasharray 0.9s cubic-bezier(0.34, 1.56, 0.64, 1)`,
        transformOrigin: "60px 60px",
        transform: "rotate(0deg)",
      }}
    />
  );
}

function AnimatedDonut({
  sentiment,
  refreshError,
  lastSyncTimestamp,
}: {
  sentiment: SentimentSnapshot;
  refreshError: boolean;
  lastSyncTimestamp: number | null;
}) {
  const total = sentiment.positive + sentiment.neutral + sentiment.negative;
  const pct = (n: number) => (total > 0 ? Math.round((n / total) * 100) : 0);
  const negPct = pct(sentiment.negative);
  const neuPct = pct(sentiment.neutral);
  const posPct = pct(sentiment.positive);

  const segs = [
    { label: "Negative", pct: negPct, color: "var(--color-critical)", offsetPct: 0,                  delay: 80  },
    { label: "Neutral",  pct: neuPct, color: "#6366f1",               offsetPct: negPct,              delay: 350 },
    { label: "Positive", pct: posPct, color: "#22c55e",               offsetPct: negPct + neuPct,     delay: 620 },
  ];

  const dominant = segs.reduce((a, b) => (a.pct >= b.pct ? a : b));
  const animKey = `${negPct}-${neuPct}-${posPct}`;
  const agoLabel = useAgoLabel(lastSyncTimestamp);

  // Count-up for dominant percentage
  const [displayPct, setDisplayPct] = useState(0);
  const rafRef = useRef<number>(0);
  useEffect(() => {
    cancelAnimationFrame(rafRef.current);
    const target = dominant.pct;
    let start: number | null = null;
    const dur = 900;
    const step = (ts: number) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplayPct(Math.round(eased * target));
      if (p < 1) rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [animKey, dominant.pct]);

  return (
    <div className="w-full sm:w-[270px] shrink-0 rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
      <div className="flex items-start justify-between gap-2 mb-1">
        <div>
          <h3 className="text-sm font-semibold text-text">Sentiment snapshot</h3>
          <p className="mt-0.5 text-xs text-muted">Current mix, today</p>
        </div>
        {refreshError ? (
          <span className="shrink-0 rounded-full bg-critical-bg px-2 py-0.5 text-[11px] font-medium text-critical">couldn&apos;t refresh</span>
        ) : (
          <span className="text-[11px] text-muted shrink-0">{agoLabel}</span>
        )}
      </div>

      <div className="mt-3 flex items-center gap-4">
        {/* SVG Donut — pure CSS transitions */}
        <div className="relative shrink-0" style={{ width: 120, height: 120 }}>
          <svg
            key={animKey}
            width="120"
            height="120"
            viewBox="0 0 120 120"
            aria-label="Sentiment donut"
            role="img"
          >
            {/* Grey track */}
            <circle cx="60" cy="60" r={DONUT_R} fill="none" stroke="#e5e7eb" strokeWidth="14" />
            {/* Segments */}
            {total > 0 && segs.map((s) =>
              s.pct > 0 ? (
                <DonutSegment
                  key={`${s.label}-${animKey}`}
                  pct={s.pct}
                  color={s.color}
                  offsetPct={s.offsetPct}
                  animDelay={s.delay}
                />
              ) : null
            )}
          </svg>

          {/* Count-up label in center */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span
              className="text-xl font-bold leading-none tabular-nums"
              style={{ color: dominant.color === "var(--color-critical)" ? "var(--color-critical)" : dominant.color }}
            >
              {displayPct}%
            </span>
            <span className="mt-0.5 text-[10px] font-medium text-muted leading-none">
              {dominant.label.toLowerCase()}
            </span>
          </div>
        </div>

        {/* Legend with animated progress bars */}
        <div className="flex flex-col gap-2.5 flex-1">
          {segs.map(({ label, pct: p, color }) => (
            <div key={label} className="flex flex-col gap-0.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-muted">{label}</span>
                </div>
                <span className="text-xs font-bold text-text tabular-nums">{p}%</span>
              </div>
              <div className="h-1 w-full rounded-full bg-border overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${p}%`,
                    backgroundColor: color,
                    transition: "width 1s cubic-bezier(0.34, 1.56, 0.64, 1)",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Section wrapper ─────────────────────────────────────────────────────────

export function SignalTrendsSection({
  trendPoints,
  sentiment,
  isRefreshing,
  trendError,
  sentimentError,
  lastSyncTimestamp,
}: {
  trendPoints: ArticleTrendPoint[];
  sentiment: SentimentSnapshot;
  isRefreshing: boolean;
  trendError: boolean;
  sentimentError: boolean;
  lastSyncTimestamp: number | null;
}) {
  return (
    <section className="mt-8">
      <div className="mb-4 flex items-center gap-2">
        <h2 className="text-base font-semibold text-text">Signal trends</h2>
        <span
          className={`inline-block h-2 w-2 rounded-full bg-green-500 ${isRefreshing ? "animate-ping" : "animate-pulse"}`}
          aria-label={isRefreshing ? "Refreshing" : "Live"}
        />
        <span className="text-xs text-muted">{isRefreshing ? "Refreshing…" : "Live"}</span>
      </div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch">
        <AnimatedSparkline points={trendPoints} refreshError={trendError} lastSyncTimestamp={lastSyncTimestamp} />
        <AnimatedDonut sentiment={sentiment} refreshError={sentimentError} lastSyncTimestamp={lastSyncTimestamp} />
      </div>
    </section>
  );
}
