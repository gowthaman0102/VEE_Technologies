export const CHART_COLORS = [
  "var(--color-primary)",
  "var(--color-low)",
  "var(--color-medium)",
  "var(--color-high)",
] as const;

export function chartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}
