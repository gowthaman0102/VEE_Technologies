import { Heart } from "lucide-react";
import type { AnalyticsOverview } from "@/lib/api";

export function SentimentAndRiskCards({ data }: { data: AnalyticsOverview }) {
  if (!data) return null;

  const totalSentiment = (data.sentiment.positive || 0) + (data.sentiment.neutral || 0) + (data.sentiment.negative || 0);
  const posPct = totalSentiment > 0 ? ((data.sentiment.positive || 0) / totalSentiment) * 100 : 0;
  const neuPct = totalSentiment > 0 ? ((data.sentiment.neutral || 0) / totalSentiment) * 100 : 0;
  const negPct = totalSentiment > 0 ? ((data.sentiment.negative || 0) / totalSentiment) * 100 : 0;

  return (
    <div className="flex h-full min-w-0 flex-col gap-5">
      {/* Sentiment Breakdown - Stacked Bar */}
      <article className="analytics-panel-enter rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6" style={{ animationDelay: "120ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <Heart size={18} className="text-[#e22d6e]" />
          <h3 className="text-[16px] font-semibold text-text">Sentiment Overview</h3>
        </div>
        
        {totalSentiment === 0 ? (
          <p className="rounded-xl bg-[#FAF9FF] px-4 py-8 text-center text-sm text-muted">No sentiment data available.</p>
        ) : (
          <div>
            <div className="h-6 w-full flex rounded-full overflow-hidden mb-4 border border-border">
              <div style={{ width: `${posPct}%` }} className="bg-[#16A46A] transition-all duration-500" title={`Positive: ${data.sentiment.positive}`} />
              <div style={{ width: `${neuPct}%` }} className="bg-[#94a3b8] transition-all duration-500" title={`Neutral: ${data.sentiment.neutral}`} />
              <div style={{ width: `${negPct}%` }} className="bg-critical transition-all duration-500" title={`Negative: ${data.sentiment.negative}`} />
            </div>
            <div className="flex justify-between text-[12px] font-semibold">
              <div className="flex items-center gap-1.5 text-[#16A46A]"><span className="w-2 h-2 rounded-full bg-[#16A46A]" /> {posPct.toFixed(0)}% Positive</div>
              <div className="flex items-center gap-1.5 text-muted"><span className="w-2 h-2 rounded-full bg-[#94a3b8]" /> {neuPct.toFixed(0)}% Neutral</div>
              <div className="flex items-center gap-1.5 text-critical"><span className="w-2 h-2 rounded-full bg-critical" /> {negPct.toFixed(0)}% Negative</div>
            </div>
          </div>
        )}
      </article>

      <RecentAlertsList companyId={data.company_id} />
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";
import { getDashboardIntelligence } from "@/lib/api";
import type { DashboardIntelligenceItem } from "@/lib/api";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import { Clock, ExternalLink } from "lucide-react";

function RecentAlertsList({ companyId }: { companyId: number }) {
  const [items, setItems] = useState<DashboardIntelligenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshError, setRefreshError] = useState(false);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const refreshAlerts = useCallback(async () => {
    try {
      const data = await getDashboardIntelligence(6, companyId, ["critical", "high"]);
      const severeItems = data.items
        .filter((item) => ["critical", "high"].includes(item.risk_level.toLowerCase()))
        .sort((left, right) => {
          const severityDifference = Number(right.risk_level.toLowerCase() === "critical")
            - Number(left.risk_level.toLowerCase() === "critical");
          return severityDifference
            || right.risk_score - left.risk_score
            || new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
        });
      setItems(severeItems);
      setRefreshError(false);
    } catch {
      setRefreshError(true);
    } finally {
      setLoading(false);
      setLastCheckedAt(new Date());
    }
  }, [companyId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshAlerts();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshAlerts]);

  useAutoRefresh(refreshAlerts, { enabled: companyId > 0, intervalMs: 15_000 });

  return (
    <article className="analytics-panel-enter flex min-w-0 flex-1 flex-col rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6" style={{ animationDelay: "180ms" }}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Clock size={18} className="text-[#ea580c]" />
          <h3 className="text-[16px] font-semibold text-text">Live Alerts</h3>
        </div>
        <span className="shrink-0 text-[10px] text-muted" aria-live="polite">
          {refreshError ? "Feed delayed" : lastCheckedAt ? `Checked ${lastCheckedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Connecting..."}
        </span>
      </div>
      
      {loading ? (
        <div className="flex flex-1 flex-col gap-3">
          {[1,2,3].map(i => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : items.length === 0 ? (
        <p className="flex flex-1 items-center justify-center rounded-xl bg-[#FAF9FF] px-4 py-8 text-center text-sm text-muted">
          {refreshError ? "Unable to update the threat feed. Retrying automatically." : "No critical or high-risk articles for this organization."}
        </p>
      ) : (
        <div className="flex min-w-0 flex-1 flex-col gap-3">
          {items.map(item => (
            <div key={`${item.article_id}-${item.company_id}`} className="group flex min-w-0 items-start gap-3 rounded-xl border border-transparent bg-[#FBFAFF] px-3 py-2.5 transition-colors hover:border-[#E9E5F4] hover:bg-white">
              <div className="min-w-0 flex-1">
                <p className="text-[12px] font-semibold text-text truncate">{item.title}</p>
                <div className="mt-1 flex min-w-0 items-center gap-2">
                  <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider
                    ${item.risk_level === 'critical' ? 'bg-red-100 text-red-700' : 
                      item.risk_level === 'high' ? 'bg-orange-100 text-orange-700' : 
                      item.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-700'}`}>
                    {item.risk_level}
                  </span>
                  <span className="min-w-0 truncate text-[10px] text-muted">{item.source_name}</span>
                </div>
              </div>
              {item.url && (
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="p-1.5 rounded-full text-muted opacity-0 group-hover:opacity-100 transition-opacity hover:bg-primary-soft hover:text-primary">
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
