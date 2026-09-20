"use client";

import { formatRelativeTime } from "@/lib/format";
import { Building2 } from "lucide-react";

type LiveStatus = "live" | "updating" | "delayed";

interface OverviewHeroProps {
  companyName: string;
  liveStatus: LiveStatus;
  lastUpdated: Date | null;
}

export function OverviewHero({ companyName, liveStatus, lastUpdated }: OverviewHeroProps) {
  const updatedLabel = lastUpdated
    ? `Updated ${formatRelativeTime(lastUpdated)}`
    : "Updated just now";

  const dateStr = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    day: "numeric",
    month: "short",
    year: "numeric"
  }).format(new Date());

  return (
    <div 
      className="relative mb-6 flex min-h-[170px] flex-col justify-between overflow-hidden rounded-xl border border-primary-border shadow-[0_1px_2px_rgba(28,23,52,0.06)]"
      style={{ 
        backgroundImage: "url('/hero-globe.png')",
        backgroundSize: "cover",
        backgroundPosition: "center right",
        backgroundRepeat: "no-repeat",
        backgroundColor: "var(--color-sidebar)"
      }}
    >
      {/* Dark gradient overlay on left so text is readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-sidebar/95 via-sidebar/70 to-transparent pointer-events-none z-0" />

      {/* Main Content Area */}
      <div className="relative z-10 flex flex-col justify-between gap-5 p-5 sm:p-6 lg:flex-row lg:items-end">
        <div className="max-w-2xl">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-primary-border">
            Near Real-Time Monitoring
          </p>
          <h1 className="mt-2 text-2xl font-bold leading-tight tracking-tight text-white sm:text-3xl">
            Here&apos;s what&apos;s happening
          </h1>
          <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-sidebar-text">
            Near real-time intelligence for {companyName} across monitored media.
          </p>
          
          <div className="mt-5 flex flex-wrap items-center gap-4">
            <div className="inline-flex items-center gap-1.5 rounded-full border border-low-border bg-low-bg/20 px-2.5 py-1 text-xs font-semibold text-low-bg">
              <span className={`h-1.5 w-1.5 rounded-full bg-low ${liveStatus === "live" ? "animate-pulse motion-reduce:animate-none" : ""}`}></span>
              Live Monitoring
            </div>
            <div className="flex items-center gap-1.5 text-xs text-sidebar-text font-medium">
              <svg className="w-3.5 h-3.5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {updatedLabel}
            </div>
          </div>
        </div>

        <div className="shrink-0 flex flex-col items-start lg:items-end text-left lg:text-right mt-4 lg:mt-0">
          <p suppressHydrationWarning className="text-[13px] text-sidebar-text font-medium mb-1">{dateStr}</p>
          <div className="flex items-center gap-2 mt-1">
            <Building2 size={16} className="text-primary-border" />
            <h3 className="text-[17px] font-bold text-white tracking-wide">{companyName}</h3>
          </div>
          <p className="text-[11px] text-muted mt-1 max-w-[200px] leading-snug">
            Tracking global media<br/>for a safer tomorrow.
          </p>
        </div>
      </div>
    </div>
  );
}
