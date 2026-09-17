import Link from "next/link";

import {
  DashboardAutoRefresh,
} from "@/components/dashboard-auto-refresh";
import {
  getActiveCompany,
  getDashboardIntelligence,
  getDashboardOverview,
  getWatchlistMatches,
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


const quickActions = [
  {
    href: "/search",
    title: "Search Intelligence",
    description:
      "Run keyword or semantic search with advanced filters.",
  },
  {
    href: "/watchlist",
    title: "Watchlist",
    description:
      "Configure monitored signals and review matching articles.",
  },
  {
    href: "/analytics",
    title: "Analytics",
    description:
      "Explore intelligence trends across selectable time ranges.",
  },
  {
    href: "/reports",
    title: "Reports",
    description:
      "Generate and download executive intelligence reports.",
  },
];


export default async function Home() {
  const [
    overview,
    intelligence,
    company,
  ] = await Promise.all([
    getDashboardOverview(),
    getDashboardIntelligence(5),
    getActiveCompany(),
  ]);

  const end = new Date();
  const start = new Date(
    end.getTime() - 7 * 24 * 60 * 60 * 1000,
  );

  const watchlist = await getWatchlistMatches(
    company.id,
    start.toISOString(),
    end.toISOString(),
    5,
  );

  return (
    <main className="px-6 py-8">
      <DashboardAutoRefresh />
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Overview
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Media Intelligence Dashboard
          </h2>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Monitor news volume, AI-processed intelligence,
            risk signals, active alerts, watchlist matches,
            and executive intelligence for {company.name}.
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

        <section className="mt-10 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.16em] text-cyan-400">
                  Latest Intelligence
                </p>

                <h3 className="mt-2 text-xl font-semibold text-white">
                  Executive Signals
                </h3>
              </div>

              <Link
                href="/intelligence"
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-white"
              >
                View all
              </Link>
            </div>

            <div className="mt-5 space-y-4">
              {intelligence.items.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-sm text-slate-400">
                  No processed intelligence is available yet.
                </div>
              ) : (
                intelligence.items.map((item) => (
                  <article
                    key={`${item.company_id}-${item.article_id}`}
                    className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-white hover:text-cyan-300"
                        >
                          {item.headline || item.title}
                        </a>

                        <p className="mt-1 text-xs text-slate-500">
                          {item.company_name} · {item.source_name}
                        </p>
                      </div>

                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                        {item.risk_level} · {item.risk_score}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-slate-300">
                      {item.executive_summary}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs text-cyan-300">
                        {item.event_type}
                      </span>

                      {item.monitoring_topic && (
                        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                          {item.monitoring_topic}
                        </span>
                      )}
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.16em] text-cyan-400">
                  Watchlist
                </p>

                <h3 className="mt-2 text-xl font-semibold text-white">
                  Matches · Last 7 Days
                </h3>
              </div>

              <Link
                href="/watchlist"
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-white"
              >
                Open watchlist
              </Link>
            </div>

            <p className="mt-5 text-4xl font-semibold text-white">
              {watchlist.count}
            </p>

            <p className="mt-1 text-sm text-slate-400">
              active watchlist signal
              {watchlist.count === 1 ? "" : "s"} matched
            </p>

            <div className="mt-5 space-y-3">
              {watchlist.matches.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-400">
                  No watchlist matches in the last 7 days.
                </div>
              ) : (
                watchlist.matches.map((match, index) => (
                  <a
                    key={`${match.watchlist_item_id}-${match.article_id}-${index}`}
                    href={match.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block rounded-xl border border-slate-800 bg-slate-950/60 p-4 hover:border-slate-700"
                  >
                    <p className="font-medium text-white">
                      {match.title}
                    </p>

                    <p className="mt-2 text-xs text-slate-400">
                      {match.item_name} · {match.source_name}
                    </p>
                  </a>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="mt-10">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-cyan-400">
              Intelligence Workspace
            </p>

            <h3 className="mt-2 text-xl font-semibold text-white">
              Quick Actions
            </h3>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {quickActions.map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 transition hover:border-cyan-900 hover:bg-slate-900"
              >
                <p className="font-semibold text-white">
                  {action.title}
                </p>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {action.description}
                </p>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
