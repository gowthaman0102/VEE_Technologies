export function DashboardHeader() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/90 px-6 py-4 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
            Near Real-Time Monitoring
          </p>

          <h1 className="mt-1 text-lg font-semibold text-white">
            Intelligence Command Center
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-900 bg-emerald-950/50 px-3 py-1.5 text-xs font-medium text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Live
          </span>

          <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
            VEE Technologies Monitoring
          </div>
        </div>
      </div>
    </header>
  );
}

