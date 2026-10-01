"use client";

import {
  FormEvent,
  startTransition,
  useEffect,
  useState,
} from "react";

import {
  FileText,
  Filter,
  Info,
  RotateCcw,
  Search as SearchIcon,
  Shield,
  Smile,
  Waypoints,
  X,
} from "lucide-react";
import { SearchAdvancedFilters } from "@/components/search-advanced-filters";
import { SearchHistoryEntry, SearchHistoryPanel } from "@/components/search-history-panel";
import { SearchComparison, SearchModeComparison } from "@/components/search-mode-comparison";
import { SearchResultsList } from "@/components/search-results-list";
import {
  getActiveCompany,
  generateReport,
  getSourceAnalytics,
  SearchFilters,
  SearchResult,
  searchKeyword,
  searchSemantic,
} from "@/lib/api";
import { resolveTimeRange } from "@/lib/time-range";
import { focusRing, inputClasses, primaryButton } from "@/components/ui/button-styles";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";

type SearchMode = "keyword" | "semantic";

export function SearchPageClient() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [resultQuery, setResultQuery] = useState("");
  const [resultFilters, setResultFilters] = useState<SearchFilters>({});
  const [resultMinimumSimilarity, setResultMinimumSimilarity] = useState<number | undefined>();
  const [resultCount, setResultCount] = useState(0);
  const [mode, setMode] = useState<SearchMode>("keyword");
  const [resultMode, setResultMode] = useState<SearchMode>("keyword");
  const [advancedFilters, setAdvancedFilters] = useState<SearchFilters>({});
  const [publishers, setPublishers] = useState<string[]>([]);
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [comparison, setComparison] = useState<SearchComparison | null>(null);
  const [comparing, setComparing] = useState(false);

  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");

  const [sourceName, setSourceName] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [publisherCountry, setPublisherCountry] = useState("");
  const [businessImpact, setBusinessImpact] = useState("");
  const [eventType, setEventType] = useState("");
  const [eventClusterId, setEventClusterId] = useState("");
  const [minimumSimilarity] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resultsOpen, setResultsOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadCompany() {
      try {
        const company = await getActiveCompany();

        if (!cancelled) {
          setCompanyId(company.id);
          setCompanyName(company.name);
          const end = new Date();
          const start = new Date(end);
          start.setUTCFullYear(start.getUTCFullYear() - 1);
          void getSourceAnalytics(start.toISOString(), end.toISOString(), company.id)
            .then((analytics) => {
              if (!cancelled) {
                setPublishers([...new Set(analytics.sources.map((source) => source.source_name))].sort());
              }
            })
            .catch(() => {
              if (!cancelled) setPublishers([]);
            });
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

  useEffect(() => {
    if (companyId === null) return;
    try {
      const stored = window.localStorage.getItem(`search-history:${companyId}`);
      const parsed: unknown = stored ? JSON.parse(stored) : [];
      const entries = Array.isArray(parsed)
        ? parsed.filter((entry): entry is SearchHistoryEntry => (
            typeof entry?.id === "string"
            && typeof entry.query === "string"
            && (entry.mode === "keyword" || entry.mode === "semantic")
            && typeof entry.createdAt === "number"
            && typeof entry.saved === "boolean"
            && typeof entry.filters === "object"
            && entry.filters !== null
          )).slice(0, 20)
        : [];
      startTransition(() => setHistory(entries));
    } catch {
      startTransition(() => setHistory([]));
    }
  }, [companyId]);

  function buildFilters(): SearchFilters {
    const timeRange = resolveTimeRange("7d");

    const filters: SearchFilters = {
      start: advancedFilters.start ?? timeRange.start,
      end: advancedFilters.end ?? timeRange.end,
    };

    if ((advancedFilters.source_name ?? sourceName).trim()) {
      filters.source_name = (advancedFilters.source_name ?? sourceName).trim();
    }

    if ((advancedFilters.sentiment ?? sentiment).trim()) {
      filters.sentiment = (advancedFilters.sentiment ?? sentiment).trim();
    }

    if ((advancedFilters.risk_level ?? riskLevel).trim()) {
      filters.risk_level = (advancedFilters.risk_level ?? riskLevel).trim();
    }
    if (publisherCountry.trim()) {
      filters.publisher_country_code = publisherCountry.trim();
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

  function saveHistoryEntries(entries: SearchHistoryEntry[]) {
    // Prevent duplicates by ID
    const nextMap = new Map<string, SearchHistoryEntry>();
    entries.forEach(e => nextMap.set(e.id, e));
    history.forEach(e => { if (!nextMap.has(e.id)) nextMap.set(e.id, e); });
    
    // Allow more than 20 entries now since we have a view all modal, maybe limit to 100
    const next = Array.from(nextMap.values()).slice(0, 100);
    setHistory(next);
    if (companyId !== null) {
      window.localStorage.setItem(`search-history:${companyId}`, JSON.stringify(next));
    }
  }

  function deleteHistoryEntry(id: string) {
    const next = history.filter(e => e.id !== id);
    setHistory(next);
    if (companyId !== null) {
      window.localStorage.setItem(`search-history:${companyId}`, JSON.stringify(next));
    }
  }

  function clearHistory() {
    const next = history.filter(e => e.saved); // keep only saved
    setHistory(next);
    if (companyId !== null) {
      window.localStorage.setItem(`search-history:${companyId}`, JSON.stringify(next));
    }
  }

  async function runSearch(searchQuery: string, searchMode: SearchMode, filters: SearchFilters) {
    if (!searchQuery.trim()) {
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
      let resolvedMinimumSimilarity: number | undefined;

      if (
        searchMode === "semantic"
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

      const data = searchMode === "keyword"
        ? await searchKeyword(
            companyId,
        searchQuery.trim(),
            filters,
            50,
          )
        : await searchSemantic(
            companyId,
            searchQuery.trim(),
            filters,
            50,
            resolvedMinimumSimilarity,
          );

      setResults(data.results);
      setResultCount(data.count);
      setResultMode(searchMode);
      setResultQuery(searchQuery.trim());
      setResultFilters({ ...filters });
      setResultMinimumSimilarity(resolvedMinimumSimilarity);
      setResultsOpen(true);
      saveHistoryEntries([{
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        query: searchQuery.trim(),
        mode: searchMode,
        filters: { ...filters },
        createdAt: Date.now(),
        saved: false,
      }]);
    } catch (cause) {
      setResults([]);
      setResultsOpen(false);
      setError(
        cause instanceof Error
          ? cause.message
          : "Search failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(query, mode, buildFilters());
  }

  function saveCurrentSearch() {
    if (!query.trim()) return;
    const filters = buildFilters();
    saveHistoryEntries([{
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      query: query.trim(),
      mode,
      filters,
      createdAt: Date.now(),
      saved: true,
    }]);
  }

  function rerunSearch(entry: SearchHistoryEntry) {
    setQuery(entry.query);
    setMode(entry.mode);
    setAdvancedFilters(entry.filters);
    setSourceName(entry.filters.source_name ?? "");
    setSentiment(entry.filters.sentiment ?? "");
    setRiskLevel(entry.filters.risk_level ?? "");
    setPublisherCountry(entry.filters.publisher_country_code ?? "");
    setBusinessImpact(entry.filters.business_impact ?? "");
    setEventType(entry.filters.event_type ?? "");
    setEventClusterId(entry.filters.event_cluster_id === undefined ? "" : String(entry.filters.event_cluster_id));
    void runSearch(entry.query, entry.mode, entry.filters);
  }

  async function compareSearchModes() {
    if (!query.trim() || companyId === null) return;
    const filters = buildFilters();
    setComparing(true);
    setError("");
    try {
      const [keyword, semantic] = await Promise.all([
        searchKeyword(companyId, query.trim(), filters, 50),
        searchSemantic(companyId, query.trim(), filters, 50),
      ]);
      setComparison({ keyword: keyword.results, semantic: semantic.results });
      saveHistoryEntries((["keyword", "semantic"] as SearchMode[]).map((searchMode) => ({
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          query: query.trim(),
          mode: searchMode,
          filters: { ...filters },
          createdAt: Date.now(),
          saved: false,
        })));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Search comparison failed.");
    } finally {
      setComparing(false);
    }
  }

  const popularSearches = [
    companyName || "OpenAI",
    "regulation",
    "AI safety",
    "policy",
    "data privacy",
    "antitrust",
    "leadership",
  ];

  return (
    <main className="search-page relative min-h-[calc(100vh-74px)] overflow-hidden bg-canvas px-5 py-6 sm:px-6 lg:px-8 lg:py-7">
          <PageAmbient kind="search" />
          <div className="relative z-10 mx-auto w-full max-w-[1400px]">
        <CosmicPageHero
  variant="search"
  imageSrc="/search-hero.png"
  eyebrow="SEARCH"
  title="Article Discovery"
  description={`Search for monitored intelligence on ${companyName || "your active company"} and the broader media landscape.`}
/>

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
        </form>

        <div className="mt-4 space-y-4">
          <SearchAdvancedFilters
            filters={buildFilters()}
            publishers={publishers}
            onChange={(next) => {
              setAdvancedFilters(next);
              setSourceName(next.source_name ?? "");
              setSentiment(next.sentiment ?? "");
              setRiskLevel(next.risk_level ?? "");
            }}
          />
          <div className="grid gap-4 xl:grid-cols-2">
            <SearchHistoryPanel
              entries={history}
              canSave={Boolean(query.trim()) && companyId !== null}
              onSave={saveCurrentSearch}
              onRerun={rerunSearch}
              onDelete={deleteHistoryEntry}
              onClearHistory={clearHistory}
            />
            <SearchModeComparison
              comparison={comparison}
              loading={comparing}
              disabled={!query.trim() || companyId === null}
              onCompare={() => void compareSearchModes()}
            />
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-lg border border-critical-border bg-critical-bg px-4 py-3 text-sm text-critical">
            {error}
          </div>
        )}

      </div>
      {resultsOpen && (
        <SearchResultsModal
          results={results}
          totalCount={resultCount}
          companyId={companyId}
          mode={resultMode}
          query={resultQuery}
          filters={resultFilters}
          minimumSimilarity={resultMinimumSimilarity}
          sentiment={sentiment}
          riskLevel={riskLevel}
          publisherCountry={publisherCountry}
          onSentimentChange={setSentiment}
          onRiskLevelChange={setRiskLevel}
          onPublisherCountryChange={setPublisherCountry}
          onClose={() => setResultsOpen(false)}
        />
      )}
    </main>
  );
}

function SearchResultsModal({
  results,
  totalCount,
  companyId,
  mode,
  query,
  filters,
  minimumSimilarity,
  sentiment,
  riskLevel,
  onSentimentChange,
  onRiskLevelChange,
  publisherCountry,
  onPublisherCountryChange,
  onClose,
}: {
  results: SearchResult[];
  totalCount: number;
  companyId: number | null;
  mode: SearchMode;
  query: string;
  filters: SearchFilters;
  minimumSimilarity?: number;
  sentiment: string;
  riskLevel: string;
  publisherCountry: string;
  onSentimentChange: (v: string) => void;
  onRiskLevelChange: (v: string) => void;
  onPublisherCountryChange: (v: string) => void;
  onClose: () => void;
}) {
  const [showFilters, setShowFilters] = useState(false);
  const [reportStatus, setReportStatus] = useState<"idle" | "generating" | "generated" | "error">("idle");

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  // Client-side filter on top of results
  const filtered = results.filter((r) => {
    const sentimentMatch = !sentiment.trim() || (r.sentiment ?? "").toLowerCase().includes(sentiment.trim().toLowerCase());
    const riskMatch = !riskLevel.trim() || (r.risk_level ?? "").toLowerCase().includes(riskLevel.trim().toLowerCase());
    const countryMatch = !publisherCountry.trim() || (r.publisher_country_code ?? "").toLowerCase() === publisherCountry.trim().toLowerCase();
    return sentimentMatch && riskMatch && countryMatch;
  });

  const hasActiveFilters = sentiment.trim() || riskLevel.trim() || publisherCountry.trim();

  async function generateSearchReport() {
    if (companyId === null || filtered.length === 0) return;
    setReportStatus("generating");
    try {
      const reportFilters = { ...filters };
      if (sentiment.trim()) reportFilters.sentiment = sentiment.trim();
      else delete reportFilters.sentiment;
      if (riskLevel.trim()) reportFilters.risk_level = riskLevel.trim();
      else delete reportFilters.risk_level;
      if (publisherCountry.trim()) reportFilters.publisher_country_code = publisherCountry.trim();
      else delete reportFilters.publisher_country_code;

      const orderedArticleIds = filtered.map((r) => r.article_id);

      await generateReport({
        company_id: companyId,
        report_type: "all_history",
        report_scope: "search_results",
        article_ids: orderedArticleIds,
        scope_metadata: {
          query: query.trim(),
          mode: mode,
          filters: reportFilters,
          minimum_similarity: minimumSimilarity,
          displayed_result_count: filtered.length,
          article_count: filtered.length,
          snapshot_at: new Date().toISOString()
        }
      });
      setReportStatus("generated");
    } catch {
      setReportStatus("error");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-text/40 p-4 sm:p-6"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="search-results-title"
        className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl"
      >
        {/* Header */}
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-primary">Search Results</p>
            <h2 id="search-results-title" className="mt-1 text-xl font-bold text-text">
              {filtered.length > 0
                ? `${filtered.length} result${filtered.length === 1 ? "" : "s"} found`
                : "No articles found"}
            </h2>
            {filtered.length > 0 && totalCount > filtered.length && (
              <p className="mt-1 text-xs text-muted">Showing first {filtered.length} of {totalCount} total matches · Generated report will include all {totalCount}.</p>
            )}
            {filtered.length === 0 && <p className="mt-1 text-sm text-muted">No articles matched &quot;{query.trim()}&quot;.</p>}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => void generateSearchReport()}
              disabled={reportStatus === "generating" || filtered.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg border border-primary-border bg-primary-soft px-3 py-2 text-[12px] font-semibold text-primary transition-colors hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <FileText size={14} aria-hidden="true" />
              {reportStatus === "generating" ? "Generating..." : "Generate report"}
            </button>
            <button
              type="button"
              onClick={() => setShowFilters((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-[12px] font-semibold transition-colors ${showFilters ? "border-primary bg-primary-soft text-primary" : "border-border bg-surface-raised text-text hover:border-primary-border hover:text-primary"}`}
            >
              <Filter size={14} aria-hidden="true" />
              Advanced Filters
              {hasActiveFilters && <span className="flex h-2 w-2 rounded-full bg-primary" aria-label="Filters active" />}
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close search results"
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              <X size={19} aria-hidden="true" />
            </button>
          </div>
        </header>
        {reportStatus === "generated" && (
          <p className="border-b border-low-border bg-low-bg px-5 py-2 text-xs font-medium text-low sm:px-6">
            Search report generated. It is available in Reports.
          </p>
        )}
        {reportStatus === "error" && (
          <p className="border-b border-critical-border bg-critical-bg px-5 py-2 text-xs font-medium text-critical sm:px-6">
            Unable to generate the search report.
          </p>
        )}

        {/* Advanced Filters Panel */}
        {showFilters && (
          <div className="shrink-0 border-b border-border bg-surface-raised px-5 py-4 sm:px-6">
            <div className="flex items-center justify-between gap-3 mb-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted">Advanced Filters</p>
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={() => { onSentimentChange(""); onRiskLevelChange(""); onPublisherCountryChange(""); }}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline"
                >
                  <RotateCcw size={11} aria-hidden="true" /> Clear filters
                </button>
              )}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-medium text-muted flex items-center gap-1.5">
                  <Smile size={13} aria-hidden="true" />
                  Sentiment
                </label>
                <select
                  value={sentiment}
                  onChange={(e) => onSentimentChange(e.target.value)}
                  className="rounded-[10px] border border-border bg-surface px-3 py-2 text-[13px] text-text focus:border-primary-border focus:outline-none"
                  aria-label="Filter by sentiment"
                >
                  <option value="">All Sentiments</option>
                  <option value="positive">Positive</option>
                  <option value="neutral">Neutral</option>
                  <option value="negative">Negative</option>
                </select>
              </div>
              <FilterInput label="Risk Level" value={riskLevel} placeholder="e.g. high" onChange={onRiskLevelChange} icon={Shield} />
              <FilterInput label="Publisher Country" value={publisherCountry} placeholder="e.g. US, IN, unknown" onChange={onPublisherCountryChange} icon={Shield} />
            </div>
            {hasActiveFilters && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {sentiment.trim() && (
                  <button type="button" onClick={() => onSentimentChange("")} className="inline-flex items-center gap-1 rounded-full border border-primary-border bg-primary-soft px-2.5 py-1 text-xs text-primary hover:bg-primary hover:text-white transition-colors">
                    Sentiment: {sentiment} <X size={11} aria-hidden="true" />
                  </button>
                )}
                {publisherCountry.trim() && (
                  <button type="button" onClick={() => onPublisherCountryChange("")} className="inline-flex items-center gap-1 rounded-full border border-primary-border bg-primary-soft px-2.5 py-1 text-xs text-primary hover:bg-primary hover:text-white transition-colors">
                    Country: {publisherCountry} <X size={11} aria-hidden="true" />
                  </button>
                )}
                {riskLevel.trim() && (
                  <button type="button" onClick={() => onRiskLevelChange("")} className="inline-flex items-center gap-1 rounded-full border border-primary-border bg-primary-soft px-2.5 py-1 text-xs text-primary hover:bg-primary hover:text-white transition-colors">
                    Risk: {riskLevel} <X size={11} aria-hidden="true" />
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <div className="min-h-0 space-y-4 overflow-y-auto bg-surface-raised p-4 sm:p-6">
          <SearchResultsList
            results={filtered}
            totalCount={totalCount}
            companyId={companyId}
            mode={mode}
            query={query.trim()}
            embedded
          />
        </div>
      </section>
    </div>
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

