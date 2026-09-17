"use client";

import {
  TimeRangePreset,
} from "@/lib/time-range";

type TimeRangeSelectorProps = {
  value: TimeRangePreset;
  onChange: (value: TimeRangePreset) => void;
  customStart?: string;
  customEnd?: string;
  onCustomStartChange?: (value: string) => void;
  onCustomEndChange?: (value: string) => void;
};

const presets: {
  value: TimeRangePreset;
  label: string;
}[] = [
  { value: "24h", label: "24h" },
  { value: "7d", label: "7d" },
  { value: "30d", label: "30d" },
  { value: "90d", label: "90d" },
  { value: "custom", label: "Custom" },
];

export function TimeRangeSelector({
  value,
  onChange,
  customStart = "",
  customEnd = "",
  onCustomStartChange,
  onCustomEndChange,
}: TimeRangeSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {presets.map((preset) => {
          const selected = value === preset.value;

          return (
            <button
              key={preset.value}
              type="button"
              onClick={() => onChange(preset.value)}
              className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                selected
                  ? "border-cyan-500 bg-cyan-400 text-slate-950"
                  : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600 hover:text-white"
              }`}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {value === "custom" && (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm text-slate-300">
            Start
            <input
              type="datetime-local"
              value={customStart}
              onChange={(event) =>
                onCustomStartChange?.(
                  event.target.value,
                )
              }
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
            />
          </label>

          <label className="text-sm text-slate-300">
            End
            <input
              type="datetime-local"
              value={customEnd}
              onChange={(event) =>
                onCustomEndChange?.(
                  event.target.value,
                )
              }
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
            />
          </label>
        </div>
      )}
    </div>
  );
}
