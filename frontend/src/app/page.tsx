import {
  getDashboardOverview,
} from "@/lib/api";


const cards = [
  {
    key: "total_articles",
    label: "Total Articles",
  },
  {
    key: "processed_articles",
    label: "Processed Intelligence",
  },
  {
    key: "total_companies",
    label: "Monitored Companies",
  },
  {
    key: "high_risk_items",
    label: "High Risk",
  },
  {
    key: "critical_risk_items",
    label: "Critical Risk",
  },
  {
    key: "active_alerts",
    label: "Active Alerts",
  },
  {
    key: "overdue_alerts",
    label: "Overdue Alerts",
  },
] as const;


export default async function Home() {
  const overview = await getDashboardOverview();

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Overview
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Media Intelligence Dashboard
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Monitor news volume, AI-processed intelligence,
            risk signals, active alerts, and SLA status.
          </p>
        </div>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <article
              key={card.key}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-sm"
            >
              <p className="text-sm font-medium text-slate-400">
                {card.label}
              </p>

              <p className="mt-4 text-3xl font-semibold text-white">
                {overview[card.key]}
              </p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
