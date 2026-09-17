"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  TimeRangeSelector,
} from "@/components/time-range-selector";
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

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Search
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Article Discovery
          </h2>
          {companyName && (
            <p className="mt-2 text-sm text-slate-400">
              Searching monitored intelligence for {companyName}
            </p>
          )}
        </div>

        <form
          onSubmit={submit}
          className="space-y-5"
        >
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex rounded-xl border border-slate-700 bg-slate-900 p-1">
              <button
                type="button"
                onClick={() => setMode("keyword")}
                className={`rounded-lg px-3 py-2 text-sm ${
                  mode === "keyword"
                    ? "bg-cyan-400 text-slate-950"
                    : "text-slate-300"
                }`}
              >
                Keyword
              </button>

              <button
                type="button"
                onClick={() => setMode("semantic")}
                className={`rounded-lg px-3 py-2 text-sm ${
                  mode === "semantic"
                    ? "bg-cyan-400 text-slate-950"
                    : "text-slate-300"
                }`}
              >
                Semantic
              </button>
            </div>

            <input
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              placeholder={
                mode === "keyword"
                  ? "Search article titles and content"
                  : "Describe the news or topic you want to find"
              }
              className="min-h-12 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 text-white outline-none focus:border-cyan-400"
            />

            <button
              type="submit"
              disabled={loading || companyId === null}
              className="min-h-12 rounded-xl bg-cyan-400 px-6 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-white">
                  Time Range
                </h3>
                <p className="mt-1 text-sm text-slate-400">
                  Limit results by article publication time.
                </p>
              </div>

              <button
                type="button"
                onClick={clearFilters}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-white"
              >
                Clear filters
              </button>
            </div>

            <div className="mt-4">
              <TimeRangeSelector
                value={timePreset}
                onChange={setTimePreset}
                customStart={customStart}
                customEnd={customEnd}
                onCustomStartChange={setCustomStart}
                onCustomEndChange={setCustomEnd}
              />
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="font-semibold text-white">
              Advanced Filters
            </h3>

            <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <FilterInput
                label="Source"
                value={sourceName}
                placeholder="e.g. Reuters"
                onChange={setSourceName}
              />

              <FilterInput
                label="Sentiment"
                value={sentiment}
                placeholder="e.g. negative"
                onChange={setSentiment}
              />

              <FilterInput
                label="Risk Level"
                value={riskLevel}
                placeholder="e.g. high"
                onChange={setRiskLevel}
              />

              <FilterInput
                label="Business Impact"
                value={businessImpact}
                placeholder="e.g. regulatory"
                onChange={setBusinessImpact}
              />

              <FilterInput
                label="Event Type"
                value={eventType}
                placeholder="e.g. regulatory_action"
                onChange={setEventType}
              />

              <FilterInput
                label="Event Cluster ID"
                value={eventClusterId}
                placeholder="e.g. 7"
                onChange={setEventClusterId}
                inputMode="numeric"
              />

              {mode === "semantic" && (
                <FilterInput
                  label="Minimum Similarity"
                  value={minimumSimilarity}
                  placeholder="Optional, -1 to 1"
                  onChange={setMinimumSimilarity}
                  inputMode="decimal"
                />
              )}
            </div>
          </section>
        </form>

        {error && (
          <div className="mt-5 rounded-xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="mt-6 space-y-4">
          {searched && !loading && !error && (
            <p className="text-sm text-slate-400">
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
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
                No articles matched the current search and filters.
              </div>
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
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  inputMode?: "text" | "numeric" | "decimal";
}) {
  return (
    <label className="text-sm text-slate-300">
      {label}
      <input
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={placeholder}
        inputMode={inputMode}
        className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
      />
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
    <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="text-lg font-semibold text-white hover:text-cyan-300"
          >
            {result.title}
          </a>

          <p className="mt-2 text-sm text-slate-400">
            {result.source_name}
            {result.published_at
              ? ` · ${new Date(
                  result.published_at,
                ).toLocaleString()}`
              : ""}
          </p>
        </div>

        {mode === "semantic"
          && result.similarity !== undefined && (
            <span className="rounded-full border border-cyan-900 bg-cyan-950/50 px-3 py-1 text-xs font-medium text-cyan-300">
              Similarity {result.similarity.toFixed(3)}
            </span>
          )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
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
    <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
      {label}: {value}
    </span>
  );
}
