"use client";

import { useState } from "react";
import { Search, Sun, Bell } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatRelativeTime } from "@/lib/format";
import { Building2 } from "lucide-react";

type LiveStatus = "live" | "updating" | "delayed";

interface OverviewHeroProps {
  companyName: string;
  liveStatus: LiveStatus;
  lastUpdated: Date | null;
}

export function OverviewHero({ companyName, liveStatus, lastUpdated }: OverviewHeroProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const updatedLabel = lastUpdated
    ? `Updated ${formatRelativeTime(lastUpdated)}`
    : "Updated just now";

  const dateStr = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    day: "numeric",
    month: "short",
    year: "numeric"
  }).format(new Date());

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div 
      className="relative mb-6 flex flex-col justify-between overflow-hidden rounded-xl border border-primary-border shadow-[0_1px_2px_rgba(28,23,52,0.06)]" 
      style={{ 
        minHeight: "225px",
        backgroundImage: "url('/hero-globe.png')",
        backgroundSize: "cover",
        backgroundPosition: "center right",
        backgroundRepeat: "no-repeat",
        backgroundColor: "#2A2059"
      }}
    >
      {/* Dark gradient overlay on left so text is readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#2A2059]/95 via-[#2A2059]/70 to-transparent pointer-events-none z-0" />

      {/* Top Header Row within Hero */}
      <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between p-6 pb-2 w-full">
        <div>
            <p className="text-[10px] sm:text-[11px] font-bold tracking-[0.15em] text-primary-border uppercase mb-1">
            NEAR REAL-TIME MONITORING
          </p>
        </div>

        <div className="flex items-center gap-4 mt-4 sm:mt-0 ml-auto w-full sm:w-auto">
          <form onSubmit={handleSearch} className="relative w-full sm:w-64 lg:w-80 xl:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-sidebar-text" size={16} />
            <input 
              type="text" 
              placeholder="Search articles, companies, topics..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-full border border-white/15 bg-white/10 py-2 pl-9 pr-4 text-sm text-white placeholder-sidebar-text focus:outline-none focus:ring-1 focus:ring-primary-border/50 transition-colors"
            />
          </form>
          
          <div className="hidden lg:flex items-center gap-3 text-sidebar-text">
            <button aria-label="Theme toggle" className="hover:text-white transition-colors p-1"><Sun size={18} /></button>
            <button aria-label="Notifications" className="hover:text-white transition-colors relative p-1">
              <Bell size={18} />
              <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
            </button>
            <button aria-label="User profile" className="ml-1 flex h-7 w-7 items-center justify-center rounded-full bg-primary-soft text-primary font-semibold text-xs">
              N
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="relative z-10 flex flex-col lg:flex-row lg:items-end justify-between p-6 pt-2 h-full gap-6">
        <div className="max-w-2xl">
          <h1 className="text-3xl lg:text-[38px] font-bold tracking-tight text-white leading-tight">
            Intelligence Command Center
          </h1>
          <p className="mt-2 text-[15px] text-[#D3DFE8] max-w-xl leading-relaxed">
            Real-time media intelligence, risk signals, and actionable insights for a safer tomorrow.
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
          <p className="text-[11px] text-[#A0B0C0] mt-1 max-w-[200px] leading-snug">
            Tracking global media<br/>for a safer tomorrow.
          </p>
        </div>
      </div>
    </div>
  );
}
