import type { AnalyticsOverview } from "@/lib/api";

export function PeriodComparisonStrip({ data }: { data: AnalyticsOverview | null | undefined }) {
  if (!data?.comparison) return null;
  const comp = data.comparison;

  return (
    <section className="mt-5 mb-5 rounded-2xl border border-[rgba(90,72,160,0.12)] bg-white p-5 shadow-[0_8px_20px_rgba(65,50,120,0.06)] sm:p-6 flex flex-col gap-4">
      <h3 className="text-[16px] font-semibold text-text">Period comparison</h3>
      <div className="grid gap-4 sm:grid-cols-3">
        <ComparisonItem 
          label="Articles"
          value={data.total_articles}
          percent={comp.article_volume_change_percent}
        />
        <ComparisonItem 
          label="Avg risk score"
          value={(data.risk.average_risk_score ?? 0).toFixed(1)}
          percent={comp.risk_average_change_percent}
        />
        <ComparisonItem 
          label="Critical events"
          value={data.total_events}
          percent={comp.event_count_change_percent}
        />
      </div>
    </section>
  );
}

function ComparisonItem({ label, value, percent }: { label: string, value: string | number, percent: number | undefined }) {
  const isPositive = percent !== undefined && percent > 0;
  const isNegative = percent !== undefined && percent < 0;
  
  return (
    <div className="flex flex-col border-r last:border-r-0 border-border pr-4">
      <span className="text-[11px] font-bold text-muted">{label}</span>
      <span className="text-2xl font-bold text-text mt-1">{value}</span>
      {percent !== undefined && percent !== null ? (
        <span className={`text-[11px] font-medium mt-1 flex items-center gap-1 ${isPositive ? 'text-green-600' : isNegative ? 'text-critical' : 'text-muted'}`}>
          {isPositive ? '↑' : isNegative ? '↓' : ''} {Math.abs(percent).toFixed(1)}% vs previous period
        </span>
      ) : (
        <span className="text-[11px] font-medium mt-1 text-muted">No prior data</span>
      )}
    </div>
  );
}
