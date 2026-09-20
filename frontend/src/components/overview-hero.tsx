"use client";

import { Building2 } from "lucide-react";
import { formatRelativeTime } from "@/lib/format";

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
      className="relative mb-6 flex flex-col justify-between overflow-hidden rounded-xl border border-primary-border shadow-[0_1px_2px_rgba(28,23,52,0.06)]"
      style={{
        minHeight: "225px",
        backgroundColor: "var(--color-sidebar)",
      }}
    >
      {/* ── Animated live background ── */}
      <div
        aria-hidden="true"
        className="hero-bg-anim pointer-events-none absolute inset-0 z-0"
        style={{
          backgroundImage: "url('/hero-globe.png')",
          backgroundSize: "cover",
          backgroundPosition: "center right",
          backgroundRepeat: "no-repeat",
          animation: "hero-pan 14s ease-in-out infinite alternate",
        }}
      />

      {/* A second, softer pass keeps the globe network lines visibly alive. */}
      <div
        aria-hidden="true"
        className="hero-lines-anim pointer-events-none absolute inset-0 z-0"
        style={{
          backgroundImage: "url('/hero-globe.png')",
          backgroundSize: "cover",
          backgroundPosition: "center right",
          backgroundRepeat: "no-repeat",
          opacity: 0.22,
          mixBlendMode: "screen",
          animation: "hero-lines-drift 9s ease-in-out infinite alternate-reverse",
        }}
      />

      {/* Animated connection paths add independent motion to the globe network. */}
      <svg className="hero-network-overlay pointer-events-none absolute inset-y-0 right-0 z-0 h-full w-[68%]" viewBox="0 0 700 300" fill="none" aria-hidden="true">
        <g className="hero-network-paths" stroke="#C5A8FF" strokeWidth="1.5" strokeLinecap="round" opacity="0.7">
          <path d="M84 228C178 152 211 232 300 170S425 53 511 125 605 151 685 61" strokeDasharray="7 13" />
          <path d="M38 113C132 80 177 125 251 91S382 59 448 106 555 239 676 188" strokeDasharray="3 17" />
          <path d="M130 281C205 218 261 250 326 215S439 168 503 206 593 239 665 218" strokeDasharray="2 22" />
        </g>
        <g className="hero-network-nodes" fill="#E5D8FF">
          <circle cx="84" cy="228" r="4" /><circle cx="300" cy="170" r="4" /><circle cx="511" cy="125" r="5" /><circle cx="685" cy="61" r="4" />
          <circle cx="251" cy="91" r="3" /><circle cx="448" cy="106" r="4" /><circle cx="676" cy="188" r="4" />
        </g>
        <g className="hero-network-particles" fill="#FFFFFF">
          <circle cx="176" cy="166" r="2.5" /><circle cx="370" cy="72" r="2" /><circle cx="577" cy="219" r="2.5" /><circle cx="625" cy="102" r="2" />
        </g>
        <g className="hero-network-orbits" stroke="#E5D8FF" strokeWidth="1" opacity="0.45">
          <ellipse cx="522" cy="153" rx="142" ry="42" transform="rotate(-18 522 153)" />
          <ellipse cx="522" cy="153" rx="118" ry="28" transform="rotate(24 522 153)" />
        </g>
      </svg>

      {/* Subtle shimmer overlay on top of the image to give "live" feel */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background:
            "linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.035) 50%, transparent 70%)",
          animation: "hero-shimmer 4s ease-in-out infinite",
        }}
      />

      {/* Dark gradient overlay – left readable, right shows the globe */}
      <div className="absolute inset-0 z-0 pointer-events-none bg-gradient-to-r from-sidebar/96 via-sidebar/72 to-transparent" />

      {/* ── Top row: eyebrow only ── */}
      <div className="relative z-10 flex items-center px-6 pt-6 pb-2">
        <p className="text-[10px] sm:text-[11px] font-bold tracking-[0.15em] text-primary-border uppercase">
          NEAR REAL-TIME MONITORING
        </p>
      </div>

      {/* ── Main content ── */}
      <div className="relative z-10 flex flex-col lg:flex-row lg:items-end justify-between px-6 pb-6 pt-2 gap-6">
        <div className="max-w-2xl">
          <h1 className="text-3xl lg:text-[38px] font-bold tracking-tight text-white leading-tight">
            Intelligence Command Center
          </h1>
          <p className="mt-2 text-[15px] text-sidebar-text max-w-xl leading-relaxed opacity-90">
            Real-time media intelligence, risk signals, and actionable insights for a safer tomorrow.
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <div className="inline-flex items-center gap-1.5 rounded-full border border-low-border bg-low-bg/20 px-2.5 py-1 text-xs font-semibold text-low-bg">
              <span
                className={`h-1.5 w-1.5 rounded-full bg-low ${
                  liveStatus === "live" ? "animate-pulse motion-reduce:animate-none" : ""
                }`}
              />
              Live Monitoring
            </div>
            <div className="flex items-center gap-1.5 text-xs text-sidebar-text font-medium opacity-80">
              <svg className="w-3.5 h-3.5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {updatedLabel}
            </div>
          </div>
        </div>

        <div className="shrink-0 flex flex-col items-start lg:items-end text-left lg:text-right mt-4 lg:mt-0">
          <p suppressHydrationWarning className="text-[13px] text-sidebar-text font-medium mb-1 opacity-80">
            {dateStr}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <Building2 size={16} className="text-primary-border" />
            <h3 className="text-[17px] font-bold text-white tracking-wide">{companyName}</h3>
          </div>
        </div>
      </div>

      {/* Keyframe styles scoped inline */}
      <style>{`
        @keyframes hero-pan {
          0%   { background-position: 78% center; transform: scale(1.00) translate3d(0, 0, 0); }
          50%  { background-position: 91% center; transform: scale(1.05) translate3d(-1%, 1%, 0); }
          100% { background-position: 100% center; transform: scale(1.09) translate3d(0, -1%, 0); }
        }
        @keyframes hero-lines-drift {
          0% { background-position: 100% 48%; transform: translate3d(1%, 0, 0) scale(1.02); opacity: 0.12; }
          50% { background-position: 88% 53%; transform: translate3d(-1%, -1%, 0) scale(1.06); opacity: 0.28; }
          100% { background-position: 76% 47%; transform: translate3d(-2%, 1%, 0) scale(1.1); opacity: 0.16; }
        }
        @keyframes hero-network-drift {
          from { transform: translate3d(2%, 1%, 0); opacity: 0.35; }
          to { transform: translate3d(-3%, -1%, 0); opacity: 0.9; }
        }
        @keyframes hero-network-pulse {
          0%, 100% { opacity: 0.35; transform: scale(0.85); }
          50% { opacity: 1; transform: scale(1.3); }
        }
        .hero-network-paths { animation: hero-network-drift 8s ease-in-out infinite alternate; transform-origin: center; }
        .hero-network-nodes { animation: hero-network-pulse 3.5s ease-in-out infinite; transform-origin: center; }
        .hero-network-particles { animation: hero-network-particles 5s ease-in-out infinite alternate; }
        .hero-network-orbits { animation: hero-network-orbits 12s linear infinite; transform-origin: 522px 153px; }
        @keyframes hero-network-particles {
          from { opacity: 0.2; transform: translate3d(8px, 4px, 0); }
          to { opacity: 1; transform: translate3d(-12px, -7px, 0); }
        }
        @keyframes hero-network-orbits {
          from { transform: rotate(0deg); opacity: 0.2; }
          to { transform: rotate(360deg); opacity: 0.65; }
        }
        @keyframes hero-shimmer {
          0%   { opacity: 0; transform: translateX(-100%); }
          50%  { opacity: 1; }
          100% { opacity: 0; transform: translateX(100%); }
        }
        @media (prefers-reduced-motion: reduce) {
          .hero-bg-anim,
          .hero-lines-anim,
          .hero-network-paths,
          .hero-network-nodes,
          .hero-network-particles,
          .hero-network-orbits { animation: none !important; }
        }
      `}</style>
    </div>
  );
}
