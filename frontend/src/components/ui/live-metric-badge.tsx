"use client";


/**
 * LiveMetricBadge – compact professional live indicator.
 * Shows a soft violet dot with a subtle pulse and a "Live" label.
 * Respects prefers-reduced-motion automatically via CSS.
 */
export function LiveMetricBadge({
  status = "live",
}: {
  status?: "live" | "updating" | "delayed";
}) {
  const config = {
    live: {
      dot: "bg-low",
      text: "text-low",
      bg: "bg-low-bg border-low-border",
      label: "Live",
      pulse: "animate-pulse motion-reduce:animate-none",
    },
    updating: {
      dot: "bg-medium",
      text: "text-medium",
      bg: "bg-medium-bg border-medium-border",
      label: "Updating",
      pulse: "animate-pulse motion-reduce:animate-none",
    },
    delayed: {
      dot: "bg-muted",
      text: "text-muted",
      bg: "bg-surface-raised border-border",
      label: "Delayed",
      pulse: "",
    },
  }[status];

  return (
    <span
      role="status"
      aria-label={`${config.label} metric`}
      className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide ${config.bg} ${config.text}`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${config.dot} ${config.pulse}`}
      />
      {config.label}
    </span>
  );
}
