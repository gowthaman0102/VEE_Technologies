import type { ReactNode } from "react";

type Tone = "critical" | "high" | "medium" | "low" | "neutral" | "active" | "disabled";

const TONES: Record<Tone, string> = {
  critical: "bg-critical-bg text-critical border-critical-border",
  high: "bg-high-bg text-high border-high-border",
  medium: "bg-medium-bg text-medium border-medium-border",
  low: "bg-low-bg text-low border-low-border",
  neutral: "bg-primary-soft text-primary border-primary-border",
  active: "bg-low-bg text-low border-low-border",
  disabled: "bg-medium-bg text-medium border-medium-border",
};

export function toneForRisk(level?: string | null): Tone {
  const value = (level ?? "").toLowerCase();
  if (value.includes("critical")) return "critical";
  if (value.includes("high")) return "high";
  if (value.includes("medium") || value.includes("moderate")) return "medium";
  if (value.includes("low")) return "low";
  return "neutral";
}

export function toneForStatus(status?: string | null): Tone {
  const value = (status ?? "").toLowerCase();
  if (value.includes("fail") || value.includes("overdue")) return "critical";
  if (value.includes("pending") || value.includes("retry") || value.includes("review")) return "medium";
  if (value.includes("deliver") || value.includes("success") || value.includes("active")) return "low";
  return "neutral";
}

export function Badge({ tone = "neutral", children, className = "" }: { tone?: Tone; children: ReactNode; className?: string }) {
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${TONES[tone]} ${className}`}>{children}</span>;
}
