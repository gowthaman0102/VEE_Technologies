"use client";

import { TimeRangePreset } from "@/lib/time-range";
import { inputClasses, focusRing } from "@/components/ui/button-styles";

type TimeRangeSelectorProps = { value: TimeRangePreset; onChange: (value: TimeRangePreset) => void; customStart?: string; customEnd?: string; onCustomStartChange?: (value: string) => void; onCustomEndChange?: (value: string) => void; includeCustom?: boolean };
const presets: { value: TimeRangePreset; label: string }[] = [{ value: "7d", label: "7d" }, { value: "30d", label: "30d" }, { value: "90d", label: "90d" }, { value: "365d", label: "1 Year" }, { value: "custom", label: "Custom" }];

export function TimeRangeSelector({ value, onChange, customStart = "", customEnd = "", onCustomStartChange, onCustomEndChange, includeCustom = true }: TimeRangeSelectorProps) {
  const visiblePresets = includeCustom ? presets : presets.filter((preset) => preset.value !== "custom");
  return <div className="space-y-3"><div className="inline-flex rounded-lg border border-border bg-surface-raised p-1" role="tablist" aria-label="Time range">{visiblePresets.map((preset) => { const selected = value === preset.value; return <button key={preset.value} type="button" role="tab" aria-selected={selected} onClick={() => onChange(preset.value)} className={`${selected ? "rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-sm" : "rounded-md px-3 py-1.5 text-sm font-medium text-muted transition-colors duration-150 hover:text-text"} ${focusRing}`}>{preset.label}</button>; })}</div>{includeCustom && value === "custom" && <div className="grid gap-3 sm:grid-cols-2"><label className="text-xs font-medium text-muted">Start<input type="datetime-local" value={customStart} onChange={(event) => onCustomStartChange?.(event.target.value)} className={`mt-1.5 ${inputClasses}`} /></label><label className="text-xs font-medium text-muted">End<input type="datetime-local" value={customEnd} onChange={(event) => onCustomEndChange?.(event.target.value)} className={`mt-1.5 ${inputClasses}`} /></label></div>}</div>;
}
