"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import { TimeRangeSelector } from "@/components/time-range-selector";
import {
  BriefcaseBusiness,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Clock3,
  FileText,
  Filter,
  Hash,
  Info,
  RotateCcw,
  Search as SearchIcon,
  Shield,
  Smile,
  Tag,
  Waypoints,
  X,
} from "lucide-react";
import { ArticleViewButton } from "@/components/article-view-button";
import { ArticleMetadata } from "@/components/article-metadata";
import {
  getActiveCompany,
  SearchFilters,
  SearchResult,
  searchKeyword,
  searchSemantic,
} from "@/lib/api";
import {
  resolveTimeRange,
  TimeRangePreset,
} from "@/lib/time-range";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { focusRing, inputClasses, primaryButton, secondaryButton } from "@/components/ui/button-styles";

type SearchMode = "keyword" | "semantic";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [mode, setMode] = useState<SearchMode>("keyword");

  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");

  const [timePreset, setTimePreset] =
    useState<TimeRangePreset>("7d");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const [sourceName, setSourceName] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [businessImpact, setBusinessImpact] = useState("");
  const [eventType, setEventType] = useState("");
  const [eventClusterId, setEventClusterId] = useState("");
  const [minimumSimilarity, setMinimumSimilarity] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadCompany() {
      try {
        const company = await getActiveCompany();

        if (!cancelled) {
          setCompanyId(company.id);
          setCompanyName(company.name);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load active company.",
          );
        }
      }
    }

    void loadCompany();

    return () => {
      cancelled = true;
    };
  }, []);

  function buildFilters(): SearchFilters {
    const timeRange = resolveTimeRange(
      timePreset,
      timePreset === "custom"
        ? {
            customStart,
            customEnd,
          }
        : {},
    );

    const filters: SearchFilters = {
      start: timeRange.start,
      end: timeRange.end,
    };

    if (sourceName.trim()) {
      filters.source_name = sourceName.trim();
    }

    if (sentiment.trim()) {
      filters.sentiment = sentiment.trim();
    }

    if (riskLevel.trim()) {
      filters.risk_level = riskLevel.trim();
    }

    if (businessImpact.trim()) {
      filters.business_impact = businessImpact.trim();
    }

    if (eventType.trim()) {
      filters.event_type = eventType.trim();
    }

    if (eventClusterId.trim()) {
      const clusterId = Number(eventClusterId);

      if (
        !Number.isInteger(clusterId)
        || clusterId < 1
      ) {
        throw new Error(
          "Event cluster ID must be a positive integer.",
        );
      }

      filters.event_cluster_id = clusterId;
    }

    return filters;
  }

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!query.trim()) {
      setError("Enter a search query.");
      return;
    }

    if (companyId === null) {
      setError("No active company is available.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const filters = buildFilters();

      let resolvedMinimumSimilarity: number | undefined;

      if (
        mode === "semantic"
        && minimumSimilarity.trim()
      ) {
        resolvedMinimumSimilarity = Number(
          minimumSimilarity,
        );

        if (
          !Number.isFinite(resolvedMinimumSimilarity)
          || resolvedMinimumSimilarity < -1
          || resolvedMinimumSimilarity > 1
        ) {
          throw new Error(
            "Minimum similarity must be between -1 and 1.",
          );
        }
      }

      const data = mode === "keyword"
        ? await searchKeyword(
            companyId,
            query.trim(),
            filters,
            50,
          )
        : await searchSemantic(
            companyId,
            query.trim(),
            filters,
            50,
            resolvedMinimumSimilarity,
          );

      setResults(data.results);
      setSearched(true);
    } catch (cause) {
      setResults([]);
      setSearched(true);
      setError(
        cause instanceof Error
          ? cause.message
          : "Search failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  function clearFilters() {
    setTimePreset("7d");
    setCustomStart("");
    setCustomEnd("");
    setSourceName("");
    setSentiment("");
    setRiskLevel("");
    setBusinessImpact("");
    setEventType("");
    setEventClusterId("");
    setMinimumSimilarity("");
  }

  const activeFilters = [
    sourceName && { label: `Source: ${sourceName}`, clear: () => setSourceName("") },
    sentiment && { label: `Sentiment: ${sentiment}`, clear: () => setSentiment("") },
    riskLevel && { label: `Risk: ${riskLevel}`, clear: () => setRiskLevel("") },
    businessImpact && { label: `Impact: ${businessImpact}`, clear: () => setBusinessImpact("") },
    eventType && { label: `Event: ${eventType}`, clear: () => setEventType("") },
    eventClusterId && { label: `Cluster: ${eventClusterId}`, clear: () => setEventClusterId("") },
    mode === "semantic" && minimumSimilarity && { label: `Similarity: ${minimumSimilarity}`, clear: () => setMinimumSimilarity("") },
    timePreset !== "7d" && { label: `Range: ${timePreset}`, clear: () => { setTimePreset("7d"); setCustomStart(""); setCustomEnd(""); } },
  ].filter(Boolean) as Array<{ label: string; clear: () => void }>;

  const popularSearches = [
    companyName || "OpenAI",
    "regulation",
    "AI safety",
    "policy",
    "data privacy",
    "antitrust",
    "leadership",
  ];

  function dateRangeLabel() {
    if (timePreset === "custom") {
      if (!customStart || !customEnd) return "Choose a custom date range";
      return `${formatSearchDate(customStart)} - ${formatSearchDate(customEnd)}`;
    }

    const range = resolveTimeRange(timePreset);
    return `${formatSearchDate(range.start)} - ${formatSearchDate(range.end)}`;
  }

  function formatSearchDate(value: string) {
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? value
      : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(date);
  }

  return (
    <main className="search-page min-h-[calc(100vh-74px)] bg-canvas px-5 py-6 sm:px-6 lg:px-8 lg:py-7">
      <div className="mx-auto w-full max-w-[1400px]">
        <header className="relative overflow-hidden border-b border-border pb-5">
          <div className="relative z-10 max-w-[620px]">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-primary">SEARCH</p>
            <h1 className="mt-1.5 text-[32px] font-bold leading-tight tracking-[-0.04em] text-text">Article Discovery</h1>
            <p className="mt-2 text-[14px] text-muted">Search for monitored intelligence on {companyName || "your active company"} and the broader media landscape.</p>
          </div>
          <div className="pointer-events-none absolute -right-3 -top-8 h-[180px] w-[470px] text-primary opacity-[0.15]" aria-hidden="true">
            <svg viewBox="0 0 470 180" className="h-full w-full fill-none">
              <path d="M0 138 C56 101 83 104 128 124 S196 151 246 111 S318 28 365 73 S426 116 470 82" stroke="currentColor" strokeWidth="1.2" />
              <path d="M0 157 C57 120 90 124 134 143 S201 169 254 128 S319 48 368 91 S427 136 470 102" stroke="currentColor" strokeWidth="0.75" />
              <path d="M28 96 C82 54 123 52 166 86 S228 138 274 85 S338 18 386 56 S431 89 470 53" stroke="currentColor" strokeWidth="0.7" strokeDasharray="3 5" />
              <circle cx="128" cy="124" r="3.5" fill="currentColor" /><circle cx="246" cy="111" r="3.5" fill="currentColor" />
              <circle cx="365" cy="73" r="3.5" fill="currentColor" /><circle cx="431" cy="105" r="2.5" fill="currentColor" />
            </svg>
          </div>
          <div className="pointer-events-none absolute right-3 top-3 z-10 hidden text-right md:block">
            <p className="text-[12px] leading-5 text-muted">From signal<br />to understanding.</p>
            <div className="ml-auto mt-2 h-px w-7 bg-primary" />
            <p className="mt-2 text-[9px] font-bold uppercase tracking-[0.22em] text-primary">NOVA COPS</p>
          </div>
        </header>

        <form onSubmit={submit} className="mt-5 space-y-4">
          <section className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_8px_24px_rgba(18,32,31,0.06)]">
            <div className="relative flex min-h-[98px] items-center justify-between gap-4 overflow-hidden rounded-t-[16px] bg-primary px-6 py-5 text-white">
              <div className="pointer-events-none absolute inset-0 opacity-20" aria-hidden="true" style={{ background: "linear-gradient(125deg, transparent 56%, rgba(255,255,255,0.18) 56.2%, transparent 74%), linear-gradient(145deg, transparent 68%, rgba(255,255,255,0.09) 68.2%, transparent 82%)" }} />
              <div className="flex items-center gap-3">
                <span className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 text-white"><SearchIcon size={21} aria-hidden="true" /></span>
                <div className="relative"><h2 className="text-[18px] font-bold leading-tight">Search Articles</h2><p className="mt-1 text-[12px] text-white/75">Find relevant content with keyword or semantic search.</p></div>
              </div>
              <div className="relative hidden items-center gap-3 lg:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-white/75"><Waypoints size={18} aria-hidden="true" /></div>
                <div className="text-right uppercase tracking-[0.16em]"><p className="text-[10px] font-bold leading-4 text-white/85">GLOBAL</p><p className="text-[10px] font-bold leading-4 text-white/85">MEDIA INTELLIGENCE</p><p className="mt-1 text-[9px] font-medium tracking-[0.1em] text-white/60">TRUSTED. TIMELY. ACTIONABLE.</p></div>
              </div>
            </div>
            <div className="p-4 sm:p-5">
              <div className="flex flex-col gap-3 lg:flex-row">
              <div className="flex shrink-0 rounded-xl border border-border bg-surface-raised p-1">
                {(["keyword", "semantic"] as SearchMode[]).map((searchMode) => (
                  <button key={searchMode} type="button" onClick={() => setMode(searchMode)} className={`rounded-lg px-4 py-2.5 text-sm font-semibold capitalize transition-colors ${mode === searchMode ? "bg-primary text-white shadow-sm" : "text-body hover:bg-surface hover:text-text"} ${focusRing}`}>
                    {searchMode}
                  </button>
                ))}
              </div>
              <label className="relative min-w-0 flex-1">
                <span className="sr-only">Search article titles and content</span>
                <SearchIcon size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={mode === "keyword" ? "Search article titles and content..." : "Describe the news or topic you want to find..."} className={`min-h-12 pl-11 ${inputClasses}`} />
              </label>
              <button type="submit" disabled={loading || companyId === null} className={`${primaryButton} min-h-12 rounded-xl px-6` }>
                <SearchIcon size={17} aria-hidden="true" />
                {loading ? "Searching..." : "Search"}
              </button>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3">
              <span className="mr-1 text-xs font-semibold text-muted">Popular searches</span>
              {popularSearches.map((suggestion) => <button key={suggestion} type="button" onClick={() => setQuery(suggestion)} className={`${focusRing} rounded-full border border-border bg-surface-raised px-3 py-1.5 text-xs text-body transition-colors hover:border-primary-border hover:bg-primary-soft hover:text-primary`}>{suggestion}</button>)}
              <button type="button" onClick={() => setQuery("")} aria-label="Clear search suggestion" className={`${focusRing} flex h-7 w-7 items-center justify-center rounded-full border border-border bg-surface-raised text-body transition-colors hover:border-primary-border hover:bg-primary-soft hover:text-primary`}>+</button>
              <button type="button" title="Search tips" aria-label="Search tips" className={`${focusRing} ml-auto rounded-full p-1.5 text-muted hover:bg-primary-soft hover:text-primary`}><Info size={15} /></button>
              </div>
            </div>
          </section>

          <section className="rounded-[16px] border border-border bg-surface p-4 shadow-[0_5px_18px_rgba(18,32,31,0.04)] sm:p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft text-primary"><Clock3 size={19} aria-hidden="true" /></span>
                <div><h2 className="text-[16px] font-bold text-text">Time Range</h2><p className="mt-0.5 text-[12px] text-muted">Limit results by article publication time.</p></div>
              </div>
              <button type="button" onClick={clearFilters} className={`${secondaryButton} rounded-xl px-3.5 py-2 text-xs`}><RotateCcw size={15} aria-hidden="true" />Clear filters</button>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
              <TimeRangeSelector value={timePreset} onChange={setTimePreset} customStart={customStart} customEnd={customEnd} onCustomStartChange={setCustomStart} onCustomEndChange={setCustomEnd} />
              <div className="flex items-center gap-3"><div className="flex items-center gap-2 rounded-xl border border-border bg-surface-raised px-3 py-2 text-xs text-body"><CalendarDays size={15} className="text-primary" aria-hidden="true" /><span>{dateRangeLabel()}</span></div><span className="hidden h-7 w-px bg-border sm:block" aria-hidden="true" /></div>
            </div>
          </section>

          <section className="rounded-[16px] border border-border bg-surface p-4 shadow-[0_5px_18px_rgba(18,32,31,0.04)] sm:p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft text-primary"><Filter size={19} aria-hidden="true" /></span><div><h2 className="text-[16px] font-bold text-text">Advanced Filters</h2><p className="mt-0.5 text-[12px] text-muted">Refine your search with additional criteria.</p></div></div>
              <button type="button" onClick={() => setShowAdvancedFilters((visible) => !visible)} aria-expanded={showAdvancedFilters} className={`${secondaryButton} rounded-xl px-3.5 py-2 text-xs`}>
                {showAdvancedFilters ? "Hide filters" : "Show filters"}{showAdvancedFilters ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>
            </div>
            <div className={`grid overflow-hidden transition-[grid-template-rows,opacity,margin] duration-300 ${showAdvancedFilters ? "mt-5 grid-rows-[1fr] opacity-100" : "mt-0 grid-rows-[0fr] opacity-0"}`}>
              <div className="min-h-0 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <FilterInput label="Source" value={sourceName} placeholder="e.g. Reuters" onChange={setSourceName} icon={FileText} />
                <FilterInput label="Sentiment" value={sentiment} placeholder="e.g. negative" onChange={setSentiment} icon={Smile} />
                <FilterInput label="Risk Level" value={riskLevel} placeholder="e.g. high" onChange={setRiskLevel} icon={Shield} />
                <FilterInput label="Business Impact" value={businessImpact} placeholder="e.g. regulatory" onChange={setBusinessImpact} icon={BriefcaseBusiness} />
                <FilterInput label="Event Type" value={eventType} placeholder="e.g. regulatory_action" onChange={setEventType} icon={Tag} />
                <FilterInput label="Event Cluster ID" value={eventClusterId} placeholder="e.g. 7" onChange={setEventClusterId} inputMode="numeric" icon={Waypoints} />
                {mode === "semantic" && <FilterInput label="Minimum Similarity" value={minimumSimilarity} placeholder="Optional, -1 to 1" onChange={setMinimumSimilarity} inputMode="decimal" icon={Hash} />}
              </div>
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-border pt-4" aria-label="Active filters">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Active filters</span>
              {activeFilters.length === 0 && <span className="text-xs text-muted">None</span>}
              {activeFilters.map((filter) => <button key={filter.label} type="button" onClick={filter.clear} className="inline-flex items-center gap-1 rounded-full border border-primary-border bg-primary-soft px-2.5 py-1 text-xs text-primary transition-colors hover:border-primary hover:bg-primary"><span>{filter.label}</span><X size={12} aria-hidden="true" /></button>)}
              {activeFilters.length > 0 && <button type="button" onClick={clearFilters} className={`${secondaryButton} ml-auto rounded-lg px-2.5 py-1.5 text-xs`}><RotateCcw size={13} />Clear all</button>}
            </div>
          </section>
        </form>

        {error && (
          <div className="mt-5 rounded-lg border border-critical-border bg-critical-bg px-4 py-3 text-sm text-critical">
            {error}
          </div>
        )}

        <div className="mt-6 space-y-4">
          {searched && !loading && !error && (
            <p className="text-sm text-muted">
              {results.length} result
              {results.length === 1 ? "" : "s"} found.
            </p>
          )}

          {results.map((result) => (
            <SearchResultCard
              key={result.article_id}
              result={result}
              mode={mode}
            />
          ))}

          {searched
            && !loading
            && !error
            && results.length === 0 && (
              <EmptyState title="No articles matched the current search and filters." />
            )}
        </div>
      </div>
    </main>
  );
}

function FilterInput({
  label,
  value,
  placeholder,
  onChange,
  inputMode,
  icon: Icon,
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  inputMode?: "text" | "numeric" | "decimal";
  icon: typeof FileText;
}) {
  return (
    <label className="text-xs font-semibold text-body">
      {label}
      <span className="relative mt-1.5 block">
        <Icon size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-primary" aria-hidden="true" />
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          inputMode={inputMode}
          className={`h-11 pl-10 ${inputClasses}`}
        />
      </span>
    </label>
  );
}

function SearchResultCard({
  result,
  mode,
}: {
  result: SearchResult;
  mode: SearchMode;
}) {
  return (
    <article className="rounded-xl border border-border bg-surface p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <ArticleMetadata publisherName={result.publisher_name} publishedAt={result.published_at} collectedAt={result.collected_at} compact />
          <p className="mt-3 text-lg font-semibold text-text">{result.title}</p>
        </div>

        <ArticleViewButton
          articleId={result.article_id}
          sourceUrl={result.url}
          sourceName={result.source_name}
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {mode === "semantic"
          && result.similarity !== undefined && (
            <Badge>
              Similarity {result.similarity.toFixed(3)}
            </Badge>
          )}
        <ResultTag
          label="Event"
          value={result.event_type}
        />
        <ResultTag
          label="Sentiment"
          value={result.sentiment}
        />
        <ResultTag
          label="Risk"
          value={
            result.risk_level
              ? result.risk_score !== null
                ? `${result.risk_level} (${result.risk_score})`
                : result.risk_level
              : null
          }
        />
        <ResultTag
          label="Impact"
          value={result.business_impact}
        />
        <ResultTag
          label="Cluster"
          value={
            result.event_cluster_id !== null
              ? String(result.event_cluster_id)
              : null
          }
        />
      </div>
    </article>
  );
}

function ResultTag({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  if (!value) {
    return null;
  }

  return (
    <span className="rounded-full border border-border bg-surface-raised px-3 py-1 text-xs text-body">
      {label}: {value}
    </span>
  );
}
