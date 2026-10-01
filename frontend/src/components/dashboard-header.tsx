"use client";

import { MobileNav } from "@/components/mobile-nav";
import { useLiveData, LiveStatus } from "@/components/live-data-provider";

export function DashboardHeader() {
  const { status, serverTime } = useLiveData();

  const statusConfig: Record<LiveStatus, { label: string; color: string }> = {
    live: { label: "Live", color: "bg-emerald-500" },
    processing: { label: "Processing", color: "bg-blue-500" },
    delayed: { label: "Delayed", color: "bg-amber-500" },
    offline: { label: "Offline", color: "bg-rose-500" },
  };

  const currentStatus = statusConfig[status];

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface px-6 py-3.5 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <MobileNav />
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.16em] text-muted">Near Real-Time Monitoring</p>
            <h1 className="mt-1 truncate text-base font-semibold text-text">Intelligence Command Center</h1>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-full border border-border bg-canvas/50 px-3 py-1.5 shadow-sm">
          <div className="relative flex h-2.5 w-2.5 items-center justify-center">
            {(status === "live" || status === "processing") && (
              <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${currentStatus.color}`}></span>
            )}
            <span className={`relative inline-flex h-2 w-2 rounded-full ${currentStatus.color}`}></span>
          </div>
          <span className="text-xs font-medium text-text capitalize">
            {currentStatus.label}
          </span>
        </div>
      </div>
    </header>
  );
}
