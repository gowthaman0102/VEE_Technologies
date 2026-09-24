"use client";

import { useEffect, useRef, useState } from "react";
import { 
  AlertTriangle, BarChart3, ChevronRight, Layers,
  Settings, Eye, Activity, Building2, Globe2, ExternalLink
} from "lucide-react";
import Link from "next/link";
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
import { CoverageGlobe } from "@/components/coverage-globe";

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
  const [showCoverage, setShowCoverage] = useState(false);
  const countryListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showCoverage && countryListRef.current) {
      countryListRef.current.scrollTop = 0;
    }
  }, [showCoverage]);
  
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
          <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
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

            <button
              type="button"
              onClick={() => setShowCoverage(true)}
              className="rounded-xl border border-border bg-surface p-4 text-left shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-primary/40"
              aria-label="Open global company presence"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-low-bg text-low">
                  <Globe2 size={20} aria-hidden="true" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text">Global Company Presence</h2>
                  <p className="text-xs font-medium text-muted">Verified company locations and operating geographies</p>
                </div>
              </div>
              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">Configured geographies</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {overview.company.geographies.length ? overview.company.geographies.map((geography) => (
                  <span key={geography} className="rounded-full bg-low-bg px-2.5 py-1 text-xs font-medium text-text">{geography}</span>
                )) : <span className="text-sm text-muted">No geographies configured</span>}
              </div>
              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">Official presence</p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-xs text-muted">Locations</span><p className="font-bold text-text">{overview.official_location_count}</p></div>
                <div><span className="text-xs text-muted">Countries</span><p className="font-bold text-text">{overview.location_country_count}</p></div>
              </div>
            </button>
          </section>
        )}
      </div>
      {showCoverage && overview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#171238]/55 p-4 backdrop-blur-sm"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowCoverage(false);
          }}
        >
          <section
            className="flex h-[min(760px,calc(100vh-2rem))] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-white/60 bg-surface p-5 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="coverage-dialog-title"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Global company presence</p>
              <h2 id="coverage-dialog-title" className="mt-1 text-xl font-bold text-text">Official locations and operating regions</h2>
              <p className="mt-1 text-sm text-muted">Verified company locations and configured geographies for {overview.company.name}.</p>
              </div>
              <button type="button" onClick={() => setShowCoverage(false)} className="rounded-lg px-3 py-1 text-2xl leading-none text-muted hover:bg-surface-raised" aria-label="Close coverage dialog">×</button>
            </div>

            <div className="mt-5 grid min-h-0 gap-5 lg:h-[clamp(480px,58vh,600px)] lg:grid-cols-[1.15fr_0.85fr]">
              <CoverageGlobe
                markers={overview.headquarters.map((location) => ({
                  label: `${location.label}: ${location.city}, ${location.country}`,
                  latitude: location.latitude,
                  longitude: location.longitude,
                  color: "#a5f3fc",
                  size: 0.55,
                  locationType: location.location_type,
                })).concat(overview.official_locations.flatMap((country) => country.locations
                  .filter((location) => location.location_type !== "headquarters")
                  .map((location) => ({
                    label: `${location.label}: ${location.city}, ${location.country}`,
                    latitude: location.latitude,
                    longitude: location.longitude,
                    color: "#c4b5fd",
                    size: 0.32,
                    locationType: location.location_type,
                  })) ))}
              />

              <div className="flex min-h-0 flex-col">
              <div className="rounded-xl border border-border bg-surface-raised p-3">
                <h3 className="text-sm font-bold uppercase tracking-wide text-muted">Global presence summary</h3>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div><p className="text-lg font-bold text-text">{overview.headquarters[0] ? `${overview.headquarters[0].city}, ${overview.headquarters[0].country}` : "Not configured"}</p><p className="text-[11px] text-muted">Headquarters</p></div>
                  <div><p className="text-lg font-bold text-text">{overview.official_location_count}</p><p className="text-[11px] text-muted">Official locations</p></div>
                  <div><p className="text-lg font-bold text-text">{overview.location_country_count}</p><p className="text-[11px] text-muted">Countries</p></div>
                </div>
                <p className="mt-3 text-xs font-medium text-muted">Only active, verified company locations are shown.</p>
              </div>
              <h3 className="mt-5 text-sm font-bold uppercase tracking-wide text-muted">Official locations</h3>
              <div ref={countryListRef} className="mt-3 min-h-0 space-y-2 overflow-y-auto pr-1 lg:flex-1">
                {overview.official_locations.map((country) => (
                  <div
                    key={country.country}
                    className="rounded-xl border border-border bg-surface-raised px-4 py-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-text">{country.country}</span>
                      <span className="text-xs text-muted">{country.locations.length} location{country.locations.length === 1 ? "" : "s"}</span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {country.locations.map((location) => (
                        <div key={location.id} className="flex items-center justify-between text-xs">
                          <span className="text-text">{location.city}{location.region ? `, ${location.region}` : ""}</span>
                          <span className="text-muted">{location.location_type.replace("_", " ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
