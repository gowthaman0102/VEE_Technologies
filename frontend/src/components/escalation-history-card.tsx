"use client";

import { DashboardIntelligenceItem } from "@/lib/api";
import { formatArticleTimestamp, formatLabel } from "@/lib/format";
import { toneForRisk } from "@/components/ui/badge";
import { Clock } from "lucide-react";

type Props = {
  items: DashboardIntelligenceItem[];
  error?: boolean;
  isUpdating?: boolean;
};

export function EscalationHistoryCard({ items, error, isUpdating }: Props) {
  const escalations = items
    .filter((item) => item.escalation_action === "escalate" || item.escalation_action === "review")
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 10);

  return (
    <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)] flex flex-col h-full">
      <div className="flex flex-wrap items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <h2 className="text-[16px] font-semibold text-text">Escalation history</h2>
          {isUpdating && <span className="text-[12px] font-medium text-muted">Updating...</span>}
          {error && <span className="text-[12px] font-medium text-critical">Failed to load</span>}
        </div>
      </div>

      <div className="p-6 flex-1 overflow-y-auto max-h-[400px]">
        {escalations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted py-10">
            <Clock size={32} className="mb-3 opacity-20" />
            <p className="text-[14px] font-medium">No recent escalations</p>
            <p className="text-[12px] mt-1">Escalated items will appear here</p>
          </div>
        ) : (
          <div className="relative border-l-2 border-border ml-2 space-y-6">
            {escalations.map((item, i) => (
              <div key={`${item.article_id}-${i}`} className="relative pl-6">
                <span className={`absolute -left-[5px] top-1.5 h-2 w-2 rounded-full ring-4 ring-surface bg-${toneForRisk(item.risk_level)}`} />
                <div className="flex items-center gap-2">
                  <span className={`text-[13px] font-bold text-${toneForRisk(item.risk_level)}`}>
                    {formatLabel(item.risk_level)}
                  </span>
                </div>
                <p className="mt-1 text-[13px] font-medium leading-5 text-text-body line-clamp-2">
                  {item.why_it_matters || item.headline || item.title}
                </p>
                <time className="mt-1.5 block text-[11px] text-muted">
                  {formatArticleTimestamp(item.updated_at)}
                </time>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
