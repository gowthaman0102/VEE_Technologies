import {
  getDashboardAlerts,
} from "@/lib/api";


function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}


function formatDate(
  value: string | null,
) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(
    new Date(value),
  );
}


function statusClasses(
  status: string,
) {
  switch (status.toLowerCase()) {
    case "delivered":
      return "border-emerald-900 bg-emerald-950/40 text-emerald-300";

    case "failed":
      return "border-red-900 bg-red-950/40 text-red-300";

    default:
      return "border-amber-900 bg-amber-950/40 text-amber-300";
  }
}


export default async function AlertsPage() {
  const data = await getDashboardAlerts(
    50,
  );

  const cards = [
    {
      label: "Total Alerts",
      value: data.total_alerts,
    },
    {
      label: "Active",
      value: data.active_alerts,
    },
    {
      label: "Delivered",
      value: data.delivered_alerts,
    },
    {
      label: "Failed",
      value: data.failed_alerts,
    },
    {
      label: "Overdue",
      value: data.overdue_alerts,
    },
  ];

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Alerts & SLA
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Alert Operations
          </h2>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Monitor alert delivery, retries, failures,
            and SLA deadlines across intelligence events.
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

        <div className="mt-6 space-y-5">
          {data.items.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center">
              <p className="text-lg font-medium text-white">
                No alerts yet
              </p>
            </div>
          ) : (
            data.items.map((alert) => (
              <article
                key={alert.id}
                className={`rounded-2xl border p-6 ${
                  alert.is_overdue
                    ? "border-red-900 bg-red-950/10"
                    : "border-slate-800 bg-slate-900/70"
                }`}
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusClasses(
                          alert.delivery_status,
                        )}`}
                      >
                        {formatLabel(
                          alert.delivery_status,
                        )}
                      </span>

                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                        {formatLabel(
                          alert.alert_type,
                        )}
                      </span>

                      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                        {formatLabel(
                          alert.severity,
                        )}
                      </span>

                      {alert.is_overdue && (
                        <span className="rounded-full border border-red-900 bg-red-950/50 px-3 py-1 text-xs font-semibold text-red-300">
                          SLA OVERDUE
                        </span>
                      )}
                    </div>

                    <h3 className="mt-4 text-xl font-semibold text-white">
                      {alert.title}
                    </h3>

                    <p className="mt-3 max-w-4xl whitespace-pre-line text-sm leading-6 text-slate-400">
                      {alert.message}
                    </p>
                  </div>

                  <div className="shrink-0 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Retries
                    </p>

                    <p className="mt-1 text-xl font-semibold text-white">
                      {alert.retry_count}
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      SLA Due
                    </p>

                    <p className="mt-2 text-sm font-medium text-slate-300">
                      {formatDate(
                        alert.sla_due_at,
                      )}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Delivery Channel
                    </p>

                    <p className="mt-2 text-sm font-medium text-slate-300">
                      {alert.delivery_channel
                        ? formatLabel(
                            alert.delivery_channel,
                          )
                        : "Not attempted"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Delivered At
                    </p>

                    <p className="mt-2 text-sm font-medium text-slate-300">
                      {formatDate(
                        alert.delivered_at,
                      )}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Immediate Delivery
                    </p>

                    <p className="mt-2 text-sm font-medium text-slate-300">
                      {alert.requires_immediate_delivery
                        ? "Required"
                        : "No"}
                    </p>
                  </div>
                </div>

                {alert.last_error && (
                  <div className="mt-4 rounded-xl border border-red-900/60 bg-red-950/20 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.15em] text-red-400">
                      Last Delivery Error
                    </p>

                    <p className="mt-2 text-sm text-red-200">
                      {alert.last_error}
                    </p>
                  </div>
                )}
              </article>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
