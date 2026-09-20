"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import { Card } from "./card";
import { LiveMetricBadge } from "./live-metric-badge";

type Tone = "critical" | "high" | "medium" | "low";
type LiveStatus = "live" | "updating" | "delayed";

const TONE_STYLES: Record<Tone, { border: string; text: string }> = {
  critical: { border: "border-l-critical", text: "text-critical" },
  high:     { border: "border-l-high",     text: "text-high"     },
  medium:   { border: "border-l-medium",   text: "text-medium"   },
  low:      { border: "border-l-low",      text: "text-low"      },
};

// Subtle highlight classes applied when the value changes
const HIGHLIGHT_CLASS = "ring-2 ring-primary-border/60 bg-primary-soft/60";
// Duration must match the timeout below (900ms)
const HIGHLIGHT_DURATION_MS = 900;

export function StatCard({
  label,
  value,
  tone,
  hint,
  isLive = false,
  liveStatus = "live",
  onOpen,
  actionLabel,
}: {
  label: string;
  value: string | number;
  tone?: Tone;
  hint?: string;
  isLive?: boolean;
  liveStatus?: LiveStatus;
  onOpen?: () => void;
  actionLabel?: string;
}) {
  const styles = tone ? TONE_STYLES[tone] : undefined;
  const prevValueRef = useRef<string | number | null>(null);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Skip the very first render — only react to real changes
    if (prevValueRef.current === null) {
      prevValueRef.current = value;
      return;
    }
    if (prevValueRef.current !== value) {
      prevValueRef.current = value;
      // Cancel any pending de-highlight
      if (timerRef.current) clearTimeout(timerRef.current);
      setIsHighlighted(true);
      timerRef.current = setTimeout(() => setIsHighlighted(false), HIGHLIGHT_DURATION_MS);
    }
  }, [value]);

  // Cleanup on unmount
  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  return (
    <Card
      className={[
        styles ? `border-l-[3px] ${styles.border}` : "",
        "transition-all duration-500",
        isHighlighted ? HIGHLIGHT_CLASS : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Header row: label | [live badge] [drilldown arrow] */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-medium text-muted leading-tight">{label}</p>
        <div className="flex shrink-0 items-center gap-1.5">
          {isLive && <LiveMetricBadge status={liveStatus} />}
          {onOpen && (
            <button
              type="button"
              onClick={onOpen}
              aria-label={actionLabel ?? `View ${label.toLowerCase()}`}
              className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-primary-border text-primary transition-colors duration-150 hover:bg-primary-soft hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      {/* Value — animate on change via CSS scale */}
      <p
        key={String(value)}
        className={[
          "mt-3 text-[28px] font-semibold leading-none tabular-nums",
          styles?.text ?? "text-text",
          "transition-transform duration-300 ease-out",
          isHighlighted ? "scale-[1.03]" : "scale-100",
          "motion-reduce:scale-100 motion-reduce:transition-none",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {value}
      </p>

      {hint && <p className="mt-2 text-xs text-muted">{hint}</p>}
    </Card>
  );
}

