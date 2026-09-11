import {
  getDashboardRiskAnalytics,
} from "@/lib/api";


function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}


export default async function RiskPage() {
  const data = await getDashboardRiskAnalytics();

  const cards = [
    {
      label: "Total Assessments",
      value: data.total_assessments,
    },
    {
      label: "Average Risk Score",
      value: data.average_risk_score.toFixed(1),
    },
    {
      label: "Highest Risk Score",
      value: data.highest_risk_score.toFixed(1),
    },
    {
      label: "Human Review",
      value: data.human_review_count,
    },
    {
      label: "Immediate Alerts",
      value: data.immediate_alert_count,
    },
  ];

  const maxRiskCount = Math.max(
    ...data.risk_levels.map(
      (item) => item.count,
    ),
    1,
  );

  const maxEventCount = Math.max(
    ...data.event_types.map(
      (item) => item.count,
    ),
    1,
  );

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Risk Analytics
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Risk Intelligence Overview
          </h2>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Deterministic risk scoring across monitored
            intelligence, including review and alert signals.
          </p>
        </div>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {cards.map((card) => (
            <article
              key={card.label}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
            >
              <p className="text-sm text-slate-400">
                {card.label}
              </p>

              <p className="mt-3 text-3xl font-semibold text-white">
                {card.value}
              </p>
            </article>
          ))}
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="text-lg font-semibold text-white">
              Risk Level Distribution
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Assessment count by deterministic risk level.
            </p>

            <div className="mt-6 space-y-5">
              {data.risk_levels.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No risk assessments available.
                </p>
              ) : (
                data.risk_levels.map((item) => {
                  const width =
                    (item.count / maxRiskCount) *
                    100;

                  return (
                    <div key={item.label}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-300">
                          {formatLabel(item.label)}
                        </span>

                        <span className="text-slate-500">
                          {item.count}
                        </span>
                      </div>

                      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-cyan-400"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="text-lg font-semibold text-white">
              Event Type Distribution
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Intelligence events currently represented in risk scoring.
            </p>

            <div className="mt-6 space-y-5">
              {data.event_types.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No event classifications available.
                </p>
              ) : (
                data.event_types.map((item) => {
                  const width =
                    (item.count / maxEventCount) *
                    100;

                  return (
                    <div key={item.label}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-300">
                          {formatLabel(item.label)}
                        </span>

                        <span className="text-slate-500">
                          {item.count}
                        </span>
                      </div>

                      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-emerald-400"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
