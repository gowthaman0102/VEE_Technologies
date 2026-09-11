import {
  getDashboardIntelligence,
} from "@/lib/api";


function formatLabel(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}


function riskClasses(
  riskLevel: string,
) {
  switch (riskLevel.toLowerCase()) {
    case "critical":
      return "border-red-900 bg-red-950/40 text-red-300";

    case "high":
      return "border-orange-900 bg-orange-950/40 text-orange-300";

    case "medium":
      return "border-amber-900 bg-amber-950/40 text-amber-300";

    default:
      return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
  }
}


export default async function IntelligencePage() {
  const data = await getDashboardIntelligence(
    20,
  );

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Intelligence
          </p>

          <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-3xl font-semibold tracking-tight text-white">
                Intelligence Feed
              </h2>

              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                Latest fully processed media intelligence
                with AI triage, deterministic risk scoring,
                and recommended actions.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Intelligence Items
              </p>

              <p className="mt-1 text-xl font-semibold text-white">
                {data.count}
              </p>
            </div>
          </div>
        </div>

        {data.items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center">
            <p className="text-lg font-medium text-white">
              No intelligence items yet
            </p>

            <p className="mt-2 text-sm text-slate-400">
              Fully processed risk insights will appear
              here after triage and risk analysis complete.
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {data.items.map((item) => (
              <article
                key={`${item.article_id}-${item.company_id}`}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${riskClasses(
                          item.risk_level,
                        )}`}
                      >
                        {item.risk_level.toUpperCase()}
                        {" "}
                        {item.risk_score.toFixed(1)}
                      </span>

                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                        {formatLabel(
                          item.event_type,
                        )}
                      </span>

                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-400">
                        {item.company_name}
                      </span>
                    </div>

                    <h3 className="mt-4 text-xl font-semibold leading-7 text-white">
                      {item.headline}
                    </h3>

                    <p className="mt-2 text-sm text-slate-500">
                      {item.source_name}
                      {" • "}
                      Article #{item.article_id}
                    </p>
                  </div>

                  <div className="shrink-0 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Confidence
                    </p>

                    <p className="mt-1 text-lg font-semibold text-white">
                      {(item.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 lg:grid-cols-2">
                  <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.15em] text-cyan-400">
                      Executive Summary
                    </p>

                    <p className="mt-3 text-sm leading-6 text-slate-300">
                      {item.executive_summary}
                    </p>
                  </section>

                  <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-400">
                      Recommended Action
                    </p>

                    <p className="mt-3 text-sm leading-6 text-slate-300">
                      {item.recommended_action}
                    </p>
                  </section>
                </div>

                <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-slate-800 pt-4 text-xs text-slate-500">
                  <span>
                    Urgency:{" "}
                    <strong className="font-medium text-slate-300">
                      {formatLabel(
                        item.urgency,
                      )}
                    </strong>
                  </span>

                  <span>
                    Escalation:{" "}
                    <strong className="font-medium text-slate-300">
                      {formatLabel(
                        item.escalation_action,
                      )}
                    </strong>
                  </span>

                  <span>
                    Topic:{" "}
                    <strong className="font-medium text-slate-300">
                      {item.monitoring_topic ??
                        "General"}
                    </strong>
                  </span>

                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-cyan-400 transition hover:text-cyan-300"
                  >
                    Open source article →
                  </a>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
