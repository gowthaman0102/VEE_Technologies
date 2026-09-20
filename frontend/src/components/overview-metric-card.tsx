"use client";

import { useEffect, useRef, useState } from "react";
const HIGHLIGHT_DURATION_MS = 900;

export function OverviewMetricCard({
  label,
  value,
  icon: Icon,
  iconColorClass = "bg-primary-soft text-primary",
  sparklineColor = "#3E2F82",
  bgClass,
  borderClass,
  valueColorClass,
  trend,
  trendLabel = "LAST 1 HOUR",
  trendColorClass,
  onOpen,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  iconColorClass?: string;
  sparklineColor?: string;
  bgClass?: string;
  borderClass?: string;
  valueColorClass?: string;
  /** e.g. "+42 in 1h" — real live count from last hour */
  trend?: string;
  /** Sub-label under trend number, defaults to "LAST 1 HOUR" */
  trendLabel?: string;
  trendColorClass?: string;
  onOpen?: () => void;
}) {
  const prevValueRef = useRef<string | number | null>(null);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Use the primary violet accent for positive or static movement.
  const resolvedTrendColor = trendColorClass ?? "text-low";

  useEffect(() => {
    if (prevValueRef.current === null) {
      prevValueRef.current = value;
      return;
    }
    if (prevValueRef.current !== value) {
      prevValueRef.current = value;
      if (timerRef.current) clearTimeout(timerRef.current);
      setIsHighlighted(true);
      timerRef.current = setTimeout(() => setIsHighlighted(false), HIGHLIGHT_DURATION_MS);
    }
  }, [value]);

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  const Component = onOpen ? "button" : "div";
  const buttonProps = onOpen
    ? { onClick: onOpen, type: "button" as const, "aria-label": `View details for ${label}` }
    : {};

  return (
    <Component
      {...buttonProps}
      style={{ boxShadow: `0 2px 10px ${sparklineColor}12` }}
      className={[
        "relative flex h-full w-full flex-col justify-between overflow-hidden rounded-xl border text-left transition-colors duration-150",
        bgClass || "bg-surface",
        borderClass || "border-border",
        onOpen
          ? "cursor-pointer hover:border-border-strong hover:shadow-[0_2px_8px_rgba(28,23,52,0.10)]"
          : "",
        isHighlighted
          ? "ring-2 ring-offset-1 ring-primary-border/60"
          : "shadow-[0_1px_2px_rgba(28,23,52,0.06)]",
      ].join(" ")}
    >
      {/* Top row: icon + trend badge */}
      <div className="flex items-start justify-between px-5 pt-5 pb-0">
        {/* Icon block */}
        <div
          className={`flex h-[50px] w-[50px] shrink-0 items-center justify-center rounded-lg p-[10px] ${iconColorClass}`}
        >
          <Icon className="w-full h-full" />
        </div>

        {/* Trend top-right */}
        {trend !== undefined && (
          <div className="flex flex-col items-end mt-0.5">
            <div className={`flex items-center gap-1 text-[13px] font-bold leading-none ${resolvedTrendColor}`}>
              {/* Up arrow */}
              <svg
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <line x1="7" y1="17" x2="17" y2="7" />
                <polyline points="7 7 17 7 17 17" />
              </svg>
              {trend}
            </div>
            <span className="text-[10px] font-medium text-muted uppercase tracking-widest mt-1">
              {trendLabel}
            </span>
          </div>
        )}
      </div>

      {/* Label */}
      <p className="px-5 mt-3 text-[13px] font-semibold text-muted leading-none">{label}</p>

      {/* Big number */}
      <p
        key={String(value)}
        className={[
          "px-5 mt-2 pb-6 text-[38px] font-semibold leading-none tracking-tight tabular-nums",
          valueColorClass || "text-text",
          "transition-transform duration-300 ease-out",
          isHighlighted ? "scale-[1.04] origin-left" : "scale-100",
          "motion-reduce:scale-100 motion-reduce:transition-none",
        ].join(" ")}
      >
        {value}
      </p>

    </Component>
  );
}
