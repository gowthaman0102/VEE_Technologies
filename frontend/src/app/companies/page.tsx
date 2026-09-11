import {
  getDashboardCompanies,
} from "@/lib/api";


function priorityClasses(
  priority: string,
) {
  switch (priority.toLowerCase()) {
    case "high":
      return "border-red-900 bg-red-950/40 text-red-300";

    case "medium":
      return "border-amber-900 bg-amber-950/40 text-amber-300";

    default:
      return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
  }
}


function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}


export default async function CompaniesPage() {
  const data = await getDashboardCompanies();

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Companies
          </p>

          <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-3xl font-semibold tracking-tight text-white">
                Monitored Companies
              </h2>

              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                Company profiles, monitoring priorities,
                regulatory context, and current intelligence
                activity.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                Companies
              </p>

              <p className="mt-1 text-xl font-semibold text-white">
                {data.count}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {data.items.map((company) => (
            <article
              key={company.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
            >
              <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-semibold text-cyan-300">
                      {company.is_active
                        ? "ACTIVE MONITORING"
                        : "INACTIVE"}
                    </span>

                    {company.industry && (
                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                        {company.industry}
                      </span>
                    )}
                  </div>

                  <h3 className="mt-4 text-2xl font-semibold text-white">
                    {company.name}
                  </h3>

                  {company.website && (
                    <a
                      href={company.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-sm text-cyan-400 hover:text-cyan-300"
                    >
                      {company.website}
                    </a>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                  {[
                    {
                      label: "Triage",
                      value: company.triage_count,
                    },
                    {
                      label: "Risks",
                      value: company.risk_assessment_count,
                    },
                    {
                      label: "High",
                      value: company.high_risk_count,
                    },
                    {
                      label: "Critical",
                      value: company.critical_risk_count,
                    },
                    {
                      label: "Alerts",
                      value: company.alert_count,
                    },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3"
                    >
                      <p className="text-xs uppercase tracking-[0.12em] text-slate-500">
                        {item.label}
                      </p>

                      <p className="mt-1 text-xl font-semibold text-white">
                        {item.value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 grid gap-5 xl:grid-cols-2">
                <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-cyan-400">
                    Monitoring Topics
                  </h4>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {company.monitoring_topics.map(
                      (topic) => (
                        <span
                          key={topic.topic}
                          className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${priorityClasses(
                            topic.priority,
                          )}`}
                        >
                          {topic.topic}
                          {" · "}
                          {topic.priority.toUpperCase()}
                        </span>
                      ),
                    )}
                  </div>
                </section>

                <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-emerald-400">
                    Monitoring Context
                  </h4>

                  <div className="mt-4 space-y-4 text-sm">
                    <div>
                      <p className="text-slate-500">
                        Aliases
                      </p>

                      <p className="mt-1 text-slate-300">
                        {company.aliases.length > 0
                          ? company.aliases.join(", ")
                          : "None configured"}
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-500">
                        Geographies
                      </p>

                      <p className="mt-1 text-slate-300">
                        {company.geographies.length > 0
                          ? company.geographies.join(", ")
                          : "None configured"}
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-500">
                        Regulators
                      </p>

                      <p className="mt-1 text-slate-300">
                        {company.regulators.length > 0
                          ? company.regulators.join(", ")
                          : "None configured"}
                      </p>
                    </div>
                  </div>
                </section>
              </div>

              {company.relationships.length > 0 && (
                <section className="mt-5 rounded-xl border border-slate-800 bg-slate-950/60 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-400">
                    Company Relationships
                  </h4>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {company.relationships.map(
                      (relationship) => (
                        <span
                          key={`${relationship.related_company_name}-${relationship.relationship_type}`}
                          className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300"
                        >
                          {relationship.related_company_name}
                          {" · "}
                          {formatLabel(
                            relationship.relationship_type,
                          )}
                        </span>
                      ),
                    )}
                  </div>
                </section>
              )}
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
