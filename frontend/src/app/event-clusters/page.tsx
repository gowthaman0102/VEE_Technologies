import { getEventClusters } from "@/lib/api";

export default async function EventClustersPage() {
  const data = await getEventClusters(1);

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">Event Clusters</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">Storylines and Events</h2>
        </div>
        <div className="space-y-4">
          {data.items.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-700 p-10 text-center text-slate-400">No event clusters available.</div>
          ) : data.items.map((cluster) => (
            <article key={cluster.id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-white">{cluster.title ?? "Untitled event"}</h3>
                  <p className="mt-2 text-sm text-slate-400">Cluster {cluster.id} · {cluster.article_count} articles</p>
                </div>
                <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-semibold text-cyan-300">TRACKED STORYLINE</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
