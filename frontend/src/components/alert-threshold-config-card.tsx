"use client";

import { useState } from "react";
import { ClientConfiguration, updateCompanyConfiguration } from "@/lib/api";

type Props = {
  config: ClientConfiguration;
  onSaved: (newConfig: ClientConfiguration) => void;
};

export function AlertThresholdConfigCard({ config, onSaved }: Props) {
  const [critical, setCritical] = useState(config.risk.critical_threshold);
  const [high, setHigh] = useState(config.risk.high_threshold);
  const [medium, setMedium] = useState(config.risk.medium_threshold);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const handleSave = async () => {
    setStatus("saving");
    try {
      const updated = await updateCompanyConfiguration(config.company_id, {
        risk: {
          critical_threshold: critical,
          high_threshold: high,
          medium_threshold: medium,
        },
      });
      onSaved(updated);
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 3000);
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  return (
    <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)] flex flex-col h-full">
      <div className="flex flex-wrap items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <h2 className="text-[16px] font-semibold text-text">Alert threshold configuration</h2>
        </div>
      </div>

      <div className="p-6 flex-1 flex flex-col justify-between space-y-6">
        <div className="space-y-6">
          <ThresholdSlider label="Critical alert at" value={critical} color="var(--color-critical)" onChange={(v) => setCritical(Math.min(100, Math.max(high + 1, v)))} />
          <ThresholdSlider label="High alert at" value={high} color="#ea580c" onChange={(v) => setHigh(Math.min(100, Math.max(medium + 1, Math.min(critical - 1, v))))} />
          <ThresholdSlider label="Medium alert at" value={medium} color="#eab308" onChange={(v) => setMedium(Math.max(0, Math.min(high - 1, v)))} />
        </div>
        
        <button
          onClick={handleSave}
          disabled={status === "saving" || critical <= high || high <= medium}
          className="w-full mt-4 flex items-center justify-center rounded-[10px] border border-primary bg-surface px-4 py-2 text-[13px] font-semibold text-primary transition-colors hover:bg-primary hover:text-white disabled:opacity-50"
        >
          {status === "saving" ? "Saving..." : status === "saved" ? "Saved!" : status === "error" ? "Save failed" : "Save thresholds"}
        </button>
      </div>
    </section>
  );
}

function ThresholdSlider({ label, value, color, onChange }: { label: string, value: number, color: string, onChange: (v: number) => void }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[13px] font-medium text-text">{label}</span>
        <span className="text-[13px] font-bold text-text">{value}</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, ${color} ${value}%, var(--color-border) ${value}%)`
        }}
      />
    </div>
  );
}
