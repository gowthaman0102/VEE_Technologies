"use client";

type CompanyComparisonRow = {
  company_id: number;
  company_name: string;
  avg_risk_score: number;
  critical_events: number;
  trend_delta: number | null;
};

type Props = {
  rows: CompanyComparisonRow[];
  error?: boolean;
  isUpdating?: boolean;
};

export function RiskCompanyComparisonTable({ rows, error, isUpdating }: Props) {
  return (
    <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)]">
      <div className="flex flex-wrap items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <h2 className="text-[16px] font-semibold text-text">Per-company risk comparison</h2>
          {isUpdating && <span className="text-[12px] font-medium text-muted">Updating...</span>}
          {error && <span className="text-[12px] font-medium text-critical">Failed to load</span>}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13px] text-text-body">
          <thead className="border-b border-border bg-surface-raised text-[11px] font-bold uppercase tracking-wider text-muted">
            <tr>
              <th className="px-6 py-3 font-medium">Company</th>
              <th className="px-6 py-3 font-medium">Avg risk score</th>
              <th className="px-6 py-3 font-medium">Critical events</th>
              <th className="px-6 py-3 font-medium text-right">Trend (30d)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border bg-surface">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-6 text-center text-muted">
                  No companies monitored.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.company_id} className="hover:bg-surface-raised transition-colors">
                  <td className="px-6 py-4 font-bold text-text">{row.company_name}</td>
                  <td className="px-6 py-4">{row.avg_risk_score.toFixed(1)}</td>
                  <td className="px-6 py-4">{row.critical_events}</td>
                  <td className="px-6 py-4 text-right font-semibold">
                    {row.trend_delta !== null ? (
                      <span className={row.trend_delta > 0 ? "text-critical" : row.trend_delta < 0 ? "text-low" : "text-muted"}>
                        {row.trend_delta > 0 ? "+" : ""}{row.trend_delta}%
                      </span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="border-t border-border px-6 py-3 text-[11px] text-muted">
        Add more monitored companies to compare risk profiles side by side.
      </div>
    </section>
  );
}
