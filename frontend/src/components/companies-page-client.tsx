"use client";

import { useState } from "react";
import { 
  AlertTriangle, BarChart3, ChevronRight, Layers,
  Settings, Eye, Activity, Building2, ExternalLink, X
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { EmptyState } from "@/components/ui/empty-state";
import {
  getCompanyOverview,
  getDashboardCompanies,
  type CompanyOverview,
  type DashboardCompanyItem,
  type DashboardCompaniesResponse,
} from "@/lib/api";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";
import { CoverageGlobe, type CoverageMarker } from "@/components/coverage-globe";

function PriorityTopicCard({ priority, topics, index }: { priority: "high" | "medium" | "low"; topics: string[]; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const visibleTopics = expanded ? topics : topics.slice(0, 5);

  const styles = {
    high: {
      bg: "bg-high-bg",
      border: "border-high-border",
      iconBg: "bg-high-bg",
      iconColor: "text-high",
      titleColor: "text-high",
      dot: "bg-high",
      desc: "High risk and time-sensitive subjects",
      footer: "Highest priority monitoring",
      Icon: AlertTriangle,
      Visual: AlertTriangle,
      visualMotion: "animate-pulse",
    },
    medium: {
      bg: "bg-medium-bg",
      border: "border-medium-border",
      iconBg: "bg-medium-bg",
      iconColor: "text-medium",
      titleColor: "text-medium",
      dot: "bg-medium",
      desc: "Important topics to monitor closely",
      footer: "Active monitoring",
      Icon: BarChart3,
      Visual: BarChart3,
      visualMotion: "animate-[dashboard-rise-in_1.8s_ease-in-out_infinite_alternate]",
    },
    low: {
      bg: "bg-low-bg",
      border: "border-low-border",
      iconBg: "bg-low-bg",
      iconColor: "text-low",
      titleColor: "text-low",
      dot: "bg-low",
      desc: "General awareness and trending topics",
      footer: "Routine monitoring",
      Icon: Eye,
      Visual: Eye,
      visualMotion: "animate-pulse",
    }
  }[priority];

  return (
    <article 
      className={`group companies-topic-card relative flex h-full flex-col overflow-hidden rounded-xl border ${styles.border} ${styles.bg} p-3 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong animate-[fadeIn_0.5s_ease-out_both]`}
      style={{ animationDelay: `${250 + index * 60}ms` }}
    >
      <styles.Visual
        className={`pointer-events-none absolute -bottom-10 -right-10 h-44 w-44 opacity-15 transition-transform duration-700 group-hover:scale-110 ${styles.iconColor} ${styles.visualMotion}`}
        strokeWidth={1.4}
        aria-hidden="true"
      />

      <div className="relative z-10 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${styles.iconBg} ${styles.iconColor}`}>
            <styles.Icon size={20} strokeWidth={2.5} aria-hidden="true" />
          </div>
          <div>
            <h3 className={`text-[15px] font-bold capitalize ${styles.titleColor}`}>{priority} Priority</h3>
            <p className="mt-0.5 text-[11px] font-medium text-muted">{styles.desc}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          aria-label={`${expanded ? "Collapse" : "Show all"} ${priority} priority topics`}
          aria-expanded={expanded}
          className={`flex items-center gap-1 rounded-md px-2 py-1 text-[13px] font-bold ${styles.iconColor} transition-opacity hover:bg-white/40 hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35`}
        >
          {topics.length} {topics.length === 1 ? "Topic" : "Topics"}
          <ChevronRight size={16} aria-hidden="true" className={`transition-transform ${expanded ? "rotate-90" : ""}`} />
        </button>
      </div>

      <ul className="relative z-10 mt-3 flex-1 space-y-1.5">
        {visibleTopics.map((t, i) => (
          <li key={t} className="flex cursor-default items-start gap-2 text-[12px] font-medium text-text transition-colors hover:text-primary animate-[fadeInUp_0.3s_ease-out_both]" style={{ animationDelay: `${(i * 30)}ms` }}>
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${styles.dot}`} aria-hidden="true" />
            {t}
          </li>
        ))}
      </ul>

      <div className="relative z-10 mt-3 flex items-center justify-between border-t border-white/40 pt-3">
        <span className="text-[12px] font-medium text-muted">{styles.footer} · {topics.length} {topics.length === 1 ? "topic" : "topics"}</span>
        {topics.length > 5 && (
          <button 
            type="button" 
            onClick={() => setExpanded(!expanded)} 
            className={`text-[12px] font-bold ${styles.iconColor} hover:opacity-80 transition-opacity`}
          >
            {expanded ? "Show less" : `+${topics.length - 5} more`}
          </button>
        )}
      </div>
    </article>
  );
}

function groupTopics(company: DashboardCompanyItem) {
  const grouped = { high: [] as string[], medium: [] as string[], low: [] as string[] };
  for (const topic of company.monitoring_topics) {
    const priority = topic.priority.toLowerCase();
    if (priority === "high" || priority === "medium" || priority === "low") grouped[priority].push(topic.topic);
    else grouped.low.push(topic.topic); // fallback
  }
  return grouped;
}

export function CompaniesPageClient({
  initialData,
  initialOverview,
}: {
  initialData: DashboardCompaniesResponse;
  initialOverview: CompanyOverview | null;
}) {
  const [data, setData] = useState(initialData);
  const [overview, setOverview] = useState(initialOverview);
  const [selectedLocation, setSelectedLocation] = useState<CoverageMarker | null>(null);
  
  
  const company = data.items[0];

  useAutoRefresh(async () => {
    try {
      const nextData = await getDashboardCompanies();
      setData(nextData);
      if (nextData.items[0]) {
        setOverview(await getCompanyOverview(nextData.items[0].id));
      }
    } catch (error) {
      console.error("Failed to refresh companies data", error);
    }
  }, { intervalMs: 60_000 });

  if (!company) return <main className="px-6 py-8 lg:px-8"><EmptyState title="No monitored companies found." /></main>;
  
  const topics = groupTopics(company);

  return (
    <main className="companies-page relative min-h-[calc(100vh-74px)] w-full overflow-hidden bg-surface-raised">
          <PageAmbient kind="companies" />
          <div className="relative z-10 mx-auto flex min-h-full w-full max-w-[1600px] flex-col gap-5 px-5 py-5 sm:px-6 lg:px-8">
        <CosmicPageHero
  variant="intelligence"
  imageSrc="/companies-hero.png"
  eyebrow="COMPANIES"
  title="Live Intelligence Overview"
  description={`Real-time analysis from ${company.name} across monitored sources.`}
/>
        {/* Monitoring Topics */}
        <section className="min-h-0 flex-1 animate-[fadeIn_0.5s_ease-out_200ms_both]">
          <div className="flex flex-col justify-between gap-4 border-b border-border pb-4 md:flex-row md:items-end">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-border shadow-sm text-text">
                <Layers size={22} strokeWidth={2.2} />
              </div>
              <div>
                <h2 className="text-[22px] lg:text-[24px] font-bold text-text">
                  Monitoring Topics
                </h2>
                <p className="mt-1.5 text-[15px] font-medium text-muted">AI is monitoring <span className="font-semibold text-text">{company.monitoring_topics.length} topics</span> across global media and online sources</p>
              </div>
            </div>
            
            <div className="flex items-center gap-5">
              <Link href="/watchlist" className="flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-2.5 text-sm font-semibold text-text shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong">
                <Settings size={16} /> Manage Topics
              </Link>
            </div>
          </div>

          <div className="mt-5 grid min-h-0 grid-cols-1 gap-5 lg:grid-cols-3 lg:gap-6 items-stretch">
            <PriorityTopicCard priority="high" topics={topics.high} index={0} />
            <PriorityTopicCard priority="medium" topics={topics.medium} index={1} />
            <PriorityTopicCard priority="low" topics={topics.low} index={2} />
          </div>
        </section>

        {overview && (
          <>
          <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-border bg-surface p-4 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Building2 size={20} aria-hidden="true" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text">Company Profile Summary</h2>
                  <p className="text-xs font-medium text-muted">Live monitoring configuration</p>
                </div>
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-xs font-medium text-muted">Industry</dt>
                  <dd className="mt-1 font-semibold text-text">{overview.company.industry || "Not configured"}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted">Status</dt>
                  <dd className="mt-1 font-semibold text-text">{overview.company.is_active ? "Active" : "Inactive"}</dd>
                </div>
              </dl>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {overview.company.aliases.map((alias) => (
                  <span key={alias} className="rounded-full bg-surface-raised px-2.5 py-1 font-medium text-muted">{alias}</span>
                ))}
              </div>
              {overview.company.website && (
                <a href={overview.company.website} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">
                  Company website <ExternalLink size={13} aria-hidden="true" />
                </a>
              )}
            </article>

            <article className="rounded-xl border border-border bg-surface p-4 shadow-[0_1px_2px_rgba(28,23,52,0.06)]">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-high-bg text-high">
                  <Activity size={20} aria-hidden="true" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text">Company Health Snapshot</h2>
                  <p className="text-xs font-medium text-muted">Company-scoped live signals</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-xs text-muted">Articles</span><p className="mt-1 font-bold text-text">{overview.health.total_articles}</p></div>
                <div><span className="text-xs text-muted">Active alerts</span><p className="mt-1 font-bold text-text">{overview.health.active_alerts}</p></div>
                <div><span className="text-xs text-muted">High risk</span><p className="mt-1 font-bold text-high">{overview.health.high_risk_count}</p></div>
                <div><span className="text-xs text-muted">Critical risk</span><p className="mt-1 font-bold text-critical">{overview.health.critical_risk_count}</p></div>
              </div>
              <div className="mt-4 border-t border-border pt-3 text-xs font-medium text-muted">
                Sentiment: <span className="text-success">{overview.health.sentiment.positive} positive</span>, {overview.health.sentiment.neutral} neutral, <span className="text-critical">{overview.health.sentiment.negative} negative</span>
              </div>
            </article>

          </section>

          <section className="mt-8 flex w-full flex-col items-center animate-[fadeIn_0.5s_ease-out_300ms_both]">
            <div className="w-full text-center mb-6">
              <h2 className="text-[22px] lg:text-[24px] font-bold text-text">Global Company Presence</h2>
              <p className="mt-1.5 text-[15px] text-muted">Verified company locations and operating geographies</p>
            </div>

            <div className="relative w-full h-[480px] rounded-2xl border border-white/20 bg-[radial-gradient(circle_at_50%_50%,#2d1b69_0%,#150a35_100%)] shadow-2xl flex items-center justify-center">
              {/* Subtle digital grid overlay for cyber theme */}
              <div className="absolute inset-0 z-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDQwIEwgNDAgNDAgTCA0MCAwIiBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-50 rounded-2xl pointer-events-none"></div>

              <CoverageGlobe
                onMarkerClick={(marker) => setSelectedLocation(marker)}
                markers={overview.headquarters.map((location): CoverageMarker => ({
                  label: "OpenAI Headquarters — San Francisco, United States",
                  latitude: location.latitude,
                  longitude: location.longitude,
                  color: "#a5f3fc",
                  size: 0.55,
                  locationType: location.location_type,
                  city: location.city,
                  country: location.country,
                  isHQ: true,
                  imageUrl: overview.company.name === "OpenAI" && location.city === "San Francisco" ? "/images/openai-headquarters.jpg" : undefined
                })).concat(overview.official_locations.flatMap((country) => country.locations
                  .filter((location) => location.location_type !== "headquarters")
                  .map((location): CoverageMarker => ({
                    label: `${location.label}: ${location.city}, ${location.country}`,
                    latitude: location.latitude,
                    longitude: location.longitude,
                    color: "#c4b5fd",
                    size: 0.32,
                    locationType: location.location_type,
                    city: location.city,
                    country: country.country,
                    isHQ: false,
                    imageUrl: undefined
                  })) ))}
              />

            {/* Dynamic Popup Modal */}
              {selectedLocation && (
                <div 
                  className="absolute inset-0 z-50 flex items-center justify-center bg-[#0d091e]/60 backdrop-blur-[2px] animate-[fadeIn_0.2s_ease-out]"
                  onClick={() => setSelectedLocation(null)}
                >
                  <div 
                    className="relative w-[360px] rounded-2xl border border-violet-400/30 bg-[#161033] shadow-[0_20px_50px_rgba(20,10,40,0.8)] animate-[dashboard-rise-in_0.3s_ease-out]"
                    onClick={(e) => e.stopPropagation()}
                    role="dialog"
                    aria-label={`Location details for ${selectedLocation.label}`}
                  >
                    <button 
                      onClick={() => setSelectedLocation(null)}
                      className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white/90 hover:bg-black/90 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-violet-400"
                      aria-label="Close dialog"
                    >
                      <X size={16} />
                    </button>
                    
                    <div className="relative h-[200px] w-full overflow-hidden rounded-t-2xl bg-gradient-to-br from-violet-900/40 to-indigo-900/40 flex items-center justify-center">
                      {selectedLocation.imageUrl ? (
                        <Image 
                          src={selectedLocation.imageUrl} 
                          alt={selectedLocation.label} 
                          fill 
                          sizes="360px"
                          className="object-cover"
                        />
                      ) : (
                        <div className="flex flex-col items-center justify-center text-violet-300/50">
                          <svg className="w-16 h-16 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                          <span className="text-xs tracking-wider uppercase">Facility Image Unavailable</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="p-5 text-center">
                      <h3 className="text-[18px] font-bold text-white tracking-wide">
                        {overview.company.name} {selectedLocation.isHQ ? "Headquarters" : "Office"}
                      </h3>
                      <p className="mt-1.5 text-[14px] font-medium text-white/80">
                        {selectedLocation.city}, {selectedLocation.country}
                      </p>
                      <div className="mt-4 inline-flex rounded-full bg-violet-500/20 px-3 py-1">
                        <p className="text-[11px] font-semibold tracking-wider text-violet-300 uppercase">
                          {selectedLocation.locationType}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Info Strip - Placed below globe in normal document flow */}
            <div className="mt-6 flex w-full max-w-[500px] items-center justify-around rounded-xl border border-white/10 bg-surface/40 px-8 py-4 shadow-sm">
                <div className="flex flex-col items-center">
                  <span className="text-[10px] uppercase tracking-wide text-muted">Headquarters</span>
                  <span className="font-semibold text-text whitespace-nowrap text-sm mt-0.5">{overview.headquarters[0] ? `${overview.headquarters[0].city}, ${overview.headquarters[0].country}` : "Not configured"}</span>
                </div>
                <div className="w-px h-8 bg-white/10"></div>
                <div className="flex flex-col items-center">
                  <span className="text-[10px] uppercase tracking-wide text-muted">Locations</span>
                  <span className="font-semibold text-text whitespace-nowrap text-sm mt-0.5">{overview.official_location_count} <span className="text-muted font-normal">({overview.location_country_count} countries)</span></span>
                </div>
            </div>
          </section>
          </>
        )}
      </div>
    </main>
  );
}
