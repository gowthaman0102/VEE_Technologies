"use client";

import { AnalyticsOverview, EventAnalyticsResponse } from "@/lib/api";

export function OverviewIntelligenceBrief({
  analytics,
  events,
}: {
  analytics: AnalyticsOverview;
  events: EventAnalyticsResponse;
}) {
  const totalArticles = analytics.total_articles;
  const highRisk = (analytics.risk?.high_risk_count ?? 0) + (analytics.risk?.critical_risk_count ?? 0);
  
  const topImpact = Object.entries(analytics.business_impact ?? {}).sort((a, b) => b[1] - a[1])[0];
  const topEvent = events.largest_events?.[0];

  const sentiment = analytics.sentiment ?? {};
  const maxSentiment = Object.entries(sentiment).sort((a, b) => b[1] - a[1])[0];

  return (
    <div className="rounded-xl border border-border bg-surface-raised p-6">
      <h3 className="text-sm font-bold uppercase tracking-wider text-primary mb-3">Today's Intelligence Brief</h3>
      <div className="prose prose-sm text-text-body max-w-none space-y-2">
        <p>
          In the current active period, the system processed <span className="font-semibold text-text">{totalArticles}</span> articles.
          {highRisk > 0 ? (
            <span> There are <span className="font-semibold text-critical">{highRisk}</span> articles flagged as high or critical risk requiring attention.</span>
          ) : (
            <span> There are currently no high or critical risk articles.</span>
          )}
        </p>
        
        {(topEvent || topImpact) && (
          <p>
            {topEvent && (
              <span>The top emerging topic in media coverage is <span className="font-semibold text-text">{topEvent.label}</span>. </span>
            )}
            {topImpact && (
              <span>The primary business impact category identified is <span className="font-semibold text-text">{topImpact[0]}</span>.</span>
            )}
          </p>
        )}

        {maxSentiment && maxSentiment[1] > 0 && (
          <p>
            Overall semantic sentiment towards the monitored company leans <span className="font-semibold text-text">{maxSentiment[0]}</span> with {maxSentiment[1]} articles.
          </p>
        )}
      </div>
    </div>
  );
}
