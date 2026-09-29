"use client";

// Top 5 event/business-impact types, sorted descending by count.
// Data comes from the category_distribution field of the business-impact API.

const PILL_COLORS = [
  { dot: "var(--color-critical)", bg: "var(--color-critical-bg)", border: "var(--color-critical-border)", text: "var(--color-critical)" },
  { dot: "#f59e0b",              bg: "#fffbeb",                  border: "#fde68a",                      text: "#92400e" },
  { dot: "#22c55e",              bg: "#f0fdf4",                  border: "#bbf7d0",                      text: "#15803d" },
  { dot: "var(--color-primary)", bg: "var(--color-primary-soft)", border: "var(--color-primary-border)", text: "var(--color-primary)" },
  { dot: "#9ca3af",              bg: "#f3f4f6",                  border: "#e5e7eb",                      text: "#374151" },
];

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function TopEventTypesRow({
  categoryDistribution,
  refreshError,
}: {
  categoryDistribution: Record<string, number>;
  refreshError: boolean;
}) {
  // Sort descending and cap at 5
  const sorted = Object.entries(categoryDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <section className="mt-8">
      <h2 className="mb-4 text-base font-semibold text-text">Top event types this week</h2>
      <div className="rounded-xl border border-border bg-surface p-4 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
        {sorted.length === 0 ? (
          <p className="text-sm text-muted">No event data for this period.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {sorted.map(([category, count], i) => {
              const color = PILL_COLORS[i % PILL_COLORS.length];
              return (
                <span
                  key={category}
                  className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold"
                  style={{
                    backgroundColor: color.bg,
                    border: `1px solid ${color.border}`,
                    color: color.text,
                  }}
                >
                  <span
                    className="inline-block h-2 w-2 rounded-full shrink-0"
                    style={{ backgroundColor: color.dot }}
                  />
                  {capitalize(category)}
                  <span className="ml-0.5 font-bold">{count}</span>
                </span>
              );
            })}
            {refreshError && (
              <span className="inline-flex items-center rounded-full bg-critical-bg px-3 py-1.5 text-xs font-medium text-critical">
                couldn&apos;t refresh
              </span>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
