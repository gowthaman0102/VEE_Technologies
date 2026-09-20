"use client";

import { MobileNav } from "@/components/mobile-nav";

export function DashboardHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface px-6 py-3.5 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1400px] items-center gap-3">
        <MobileNav />
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.16em] text-muted">Near Real-Time Monitoring</p>
          <h1 className="mt-1 truncate text-base font-semibold text-text">Intelligence Command Center</h1>
        </div>
      </div>
    </header>
  );
}
