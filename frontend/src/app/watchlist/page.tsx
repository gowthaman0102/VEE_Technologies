import { getWatchlist } from "@/lib/api";

export default async function WatchlistPage() {
  const data = await getWatchlist(1);

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Watchlist
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Monitoring Watchlist
          </h2>
        </div>

        <div className="space-y-4">
          {data.items.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center text-slate-400">
              No watchlist items configured yet.
            </div>
          ) : (
            data.items.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-semibold text-cyan-300">
                    {item.item_type.toUpperCase()}
                  </span>
                  <span className="text-sm text-slate-400">{item.item_name}</span>
                </div>

                <p className="mt-3 text-lg text-white">{item.value}</p>
              </article>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
