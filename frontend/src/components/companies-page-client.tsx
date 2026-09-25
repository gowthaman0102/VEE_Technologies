"use client";

import { useState } from "react";
import { 
  AlertTriangle, BarChart3, ChevronRight,
  Layers,
  Settings, Eye
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/ui/empty-state";
import { 
  getDashboardCompanies,
  type DashboardCompanyItem, type DashboardCompaniesResponse 
} from "@/lib/api";
import { useAutoRefresh } from "@/lib/use-auto-refresh";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

function PriorityTopicCard({ priority, topics, index }: { priority: "high" | "medium" | "low"; topics: string[]; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const visibleTopics = expanded ? topics : topics.slice(0, 5);

  const styles = {
    high: {
      bg: "bg-critical-bg",
      border: "border-critical-border",
      iconBg: "bg-critical-bg",
      iconColor: "text-critical",
      titleColor: "text-critical",
      dot: "bg-critical",
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
      className={`group companies-topic-card relative flex flex-col overflow-hidden rounded-xl border ${styles.border} ${styles.bg} p-3 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors hover:border-border-strong animate-[fadeIn_0.5s_ease-out_both]`}
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

export function CompaniesPageClient({ initialData }: { initialData: DashboardCompaniesResponse }) {
  const [data, setData] = useState(initialData);
  
  const company = data.items[0];

  useAutoRefresh(async () => {
    try {
      setData(await getDashboardCompanies());
    } catch { }
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

          <div className="mt-5 grid min-h-0 grid-cols-1 gap-5 lg:grid-cols-3 lg:gap-6 items-start">
            <PriorityTopicCard priority="high" topics={topics.high} index={0} />
            <PriorityTopicCard priority="medium" topics={topics.medium} index={1} />
            <PriorityTopicCard priority="low" topics={topics.low} index={2} />
          </div>
        </section>
      </div>
      
    </main>
  );
}
