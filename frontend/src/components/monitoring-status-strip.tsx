"use client";

// ── helpers ────────────────────────────────────────────────────────────────

function formatRelativeTime(ts: number | null): string {
  if (ts === null) return "never";
  const diffMs = Date.now() - ts;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  return `${diffHr} hr ago`;
}

// ── Component ───────────────────────────────────────────────────────────────

export function MonitoringStatusStrip({
  totalCompanies,
  lastSyncTimestamp,   // Date.now() value set by parent on each successful refresh
  refreshError,
}: {
  totalCompanies: number;
  lastSyncTimestamp: number | null;
  refreshError: boolean;
}) {
  const companyLabel = `${totalCompanies} ${totalCompanies === 1 ? "company" : "companies"} monitored`;
  const syncLabel = `Last sync ${formatRelativeTime(lastSyncTimestamp)}`;

  return (
    <div
      className={`mt-5 flex items-center justify-between gap-4 rounded-xl border px-5 py-3.5 text-sm font-medium shadow-[0_1px_2px_rgba(28,23,52,0.06)] ${
        refreshError
          ? "border-critical-border bg-critical-bg text-critical"
          : "border-border bg-surface text-text"
      }`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${
            refreshError ? "bg-critical animate-pulse" : "bg-green-500 animate-pulse"
          }`}
          aria-hidden="true"
        />
        <span className="font-semibold">
          {refreshError ? "Monitoring paused — couldn't refresh" : "Monitoring active"}
        </span>
        {!refreshError && (
          <span className="hidden sm:inline text-muted">
            {syncLabel} · {companyLabel} · Risk trend: stable
          </span>
        )}
      </div>
      <span className="shrink-0 text-xs text-muted hidden sm:block">
        {refreshError ? "Showing last good data" : syncLabel}
      </span>
    </div>
  );
}
