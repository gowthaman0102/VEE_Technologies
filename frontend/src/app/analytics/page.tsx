import { getActiveCompany, getAnalyticsOverview } from "@/lib/api";

export default async function AnalyticsPage() {
  const company = await getActiveCompany();
  const end = new Date();
  const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
  const data = await getAnalyticsOverview(
    company.id,
    start.toISOString(),
    end.toISOString(),
  );

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Analytics</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">{company.name} Intelligence Trends</h2>
        </div>
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ["Articles", data.total_articles],
            ["Events", data.total_events],
            ["High risk", data.risk.high_risk_count ?? 0],
            ["Negative sentiment", data.sentiment.negative ?? 0],
          ].map(([label, value]) => (
            <article key={label} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <p className="text-sm text-slate-400">{label}</p>
              <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
            </article>
          ))}
        </section>
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="text-lg font-semibold text-white">Business impact</h3>
            <div className="mt-4 space-y-3">
              {Object.entries(data.business_impact).map(([label, value]) => (
                <div key={label} className="flex justify-between border-b border-slate-800 py-2 text-sm">
                  <span className="capitalize text-slate-300">{label}</span>
                  <span className="font-semibold text-white">{value}</span>
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="text-lg font-semibold text-white">Competitor mentions</h3>
            <div className="mt-4 space-y-3">
              {data.competitors.map((competitor) => (
                <div key={competitor.name} className="flex justify-between border-b border-slate-800 py-2 text-sm">
                  <span className="text-slate-300">{competitor.name}</span>
                  <span className="font-semibold text-white">{competitor.mention_count}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
