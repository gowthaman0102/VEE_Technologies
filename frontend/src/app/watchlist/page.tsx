"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  TimeRangeSelector,
} from "@/components/time-range-selector";
import {
  createWatchlistItem,
  deleteWatchlistItem,
  getActiveCompany,
  getWatchlist,
  getWatchlistMatches,
  updateWatchlistItem,
  WatchlistItem,
  WatchlistMatch,
} from "@/lib/api";
import {
  resolveTimeRange,
  TimeRangePreset,
} from "@/lib/time-range";
import {
  useAutoRefresh,
} from "@/lib/use-auto-refresh";

export default function WatchlistPage() {
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState("");

  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [matches, setMatches] = useState<WatchlistMatch[]>([]);

  const [itemType, setItemType] = useState("keyword");
  const [itemName, setItemName] = useState("");
  const [value, setValue] = useState("");

  const [timePreset, setTimePreset] =
    useState<TimeRangePreset>("7d");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [matchesLoading, setMatchesLoading] = useState(false);

  const loadWatchlist = useCallback(
    async (
      resolvedCompanyId: number,
    ) => {
      const data = await getWatchlist(
        resolvedCompanyId,
      );

      setItems(data.items);
    },
    [],
  );

  const loadMatches = useCallback(
    async (
      resolvedCompanyId: number,
      showLoading = true,
    ) => {
      if (showLoading) {
        setMatchesLoading(true);
      }

      try {
        const range = resolveTimeRange(
          timePreset,
          timePreset === "custom"
            ? {
                customStart,
                customEnd,
              }
            : {},
        );

        const data = await getWatchlistMatches(
          resolvedCompanyId,
          range.start,
          range.end,
          100,
        );

        setMatches(data.matches);
      } finally {
        if (showLoading) {
          setMatchesLoading(false);
        }
      }
    },
    [
      timePreset,
      customStart,
      customEnd,
    ],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setLoading(true);
      setError("");

      try {
        const company = await getActiveCompany();

        if (cancelled) {
          return;
        }

        setCompanyId(company.id);
        setCompanyName(company.name);

        const watchlistData = await getWatchlist(
          company.id,
        );

        if (cancelled) {
          return;
        }

        setItems(watchlistData.items);

        const range = resolveTimeRange("7d");

        const matchData = await getWatchlistMatches(
          company.id,
          range.start,
          range.end,
          100,
        );

        if (cancelled) {
          return;
        }

        setMatches(matchData.matches);
      } catch (cause) {
        if (!cancelled) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load watchlist.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  const autoRefreshEnabled =
    companyId !== null
    && !(
      timePreset === "custom"
      && (!customStart || !customEnd)
    );

  useAutoRefresh(
    async () => {
      if (companyId === null) {
        return;
      }

      await Promise.all([
        loadWatchlist(companyId),
        loadMatches(companyId, false),
      ]);
    },
    {
      enabled: autoRefreshEnabled,
      intervalMs: 60_000,
    },
  );

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      companyId === null
      || !itemName.trim()
      || !value.trim()
    ) {
      return;
    }

    setError("");

    try {
      await createWatchlistItem({
        company_id: companyId,
        item_type: itemType,
        item_name: itemName.trim(),
        value: value.trim(),
      });

      setItemName("");
      setValue("");

      await loadWatchlist(companyId);
      await loadMatches(companyId);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create watchlist item.",
      );
    }
  }

  async function toggle(
    item: WatchlistItem,
  ) {
    if (companyId === null) {
      return;
    }

    setError("");

    try {
      await updateWatchlistItem(
        item.id,
        {
          is_active: !item.is_active,
        },
      );

      await loadWatchlist(companyId);
      await loadMatches(companyId);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to update watchlist item.",
      );
    }
  }

  async function remove(
    item: WatchlistItem,
  ) {
    if (companyId === null) {
      return;
    }

    setError("");

    try {
      await deleteWatchlistItem(item.id);

      await loadWatchlist(companyId);
      await loadMatches(companyId);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to delete watchlist item.",
      );
    }
  }

  async function refreshMatches() {
    if (companyId === null) {
      return;
    }

    setError("");

    try {
      await loadMatches(companyId);
    } catch (cause) {
      setMatches([]);
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to load watchlist matches.",
      );
    }
  }

  return (
    <main className="px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
            Watchlist
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            {companyName || "Monitoring Watchlist"}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Configure monitored signals and review matching intelligence.
          </p>
        </div>

        {error && (
          <p className="mb-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">
            {error}
          </p>
        )}

        <form
          onSubmit={submit}
          className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:grid-cols-4"
        >
          <select
            value={itemType}
            onChange={(event) =>
              setItemType(event.target.value)
            }
            className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"
          >
            <option value="keyword">
              Keyword
            </option>
            <option value="topic">
              Topic
            </option>
            <option value="source">
              Source
            </option>
            <option value="risk_category">
              Risk category
            </option>
            <option value="impact_category">
              Impact category
            </option>
          </select>

          <input
            value={itemName}
            onChange={(event) =>
              setItemName(event.target.value)
            }
            placeholder="Item name"
            className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"
          />

          <input
            value={value}
            onChange={(event) =>
              setValue(event.target.value)
            }
            placeholder="Match value"
            className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-white"
          />

          <button
            type="submit"
            disabled={companyId === null}
            className="rounded-lg bg-cyan-400 p-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Add item
          </button>
        </form>

        <section className="mt-6">
          <h3 className="text-xl font-semibold text-white">
            Watchlist Items
          </h3>

          <div className="mt-4 space-y-4">
            {loading ? (
              <p className="text-slate-400">
                Loading watchlist...
              </p>
            ) : items.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-700 p-10 text-center text-slate-400">
                No watchlist items configured yet.
              </div>
            ) : (
              items.map((item) => (
                <article
                  key={item.id}
                  className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 md:flex-row md:items-center md:justify-between"
                >
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-semibold text-cyan-300">
                        {item.item_type.toUpperCase()}
                      </span>

                      <span className={`rounded-full border px-3 py-1 text-xs font-medium ${
                        item.is_active
                          ? "border-emerald-900 bg-emerald-950/30 text-emerald-300"
                          : "border-slate-700 bg-slate-950 text-slate-400"
                      }`}>
                        {item.is_active
                          ? "Active"
                          : "Disabled"}
                      </span>
                    </div>

                    <p className="mt-3 text-lg text-white">
                      {item.item_name}: {item.value}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        void toggle(item)
                      }
                      className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300"
                    >
                      {item.is_active
                        ? "Disable"
                        : "Enable"}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        void remove(item)
                      }
                      className="rounded-lg border border-red-900 px-3 py-2 text-sm text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold text-white">
                Watchlist Matches
              </h3>
              <p className="mt-1 text-sm text-slate-400">
                Articles matching currently active watchlist items.
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                void refreshMatches()
              }
              disabled={
                companyId === null
                || matchesLoading
              }
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {matchesLoading
                ? "Refreshing..."
                : "Refresh matches"}
            </button>
          </div>

          <div className="mt-5">
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

        <div className="mt-6 space-y-4">
          {!loading
            && !matchesLoading
            && matches.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-700 p-10 text-center text-slate-400">
                No watchlist matches were found for the selected time range.
              </div>
            )}

          {matches.map((match, index) => (
            <WatchlistMatchCard
              key={`${match.watchlist_item_id}-${match.article_id}-${index}`}
              match={match}
            />
          ))}
        </div>
      </div>
    </main>
  );
}

function WatchlistMatchCard({
  match,
}: {
  match: WatchlistMatch;
}) {
  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <a
            href={match.url}
            target="_blank"
            rel="noreferrer"
            className="text-lg font-semibold text-white hover:text-cyan-300"
          >
            {match.title}
          </a>

          <p className="mt-2 text-sm text-slate-400">
            {match.source_name}
            {match.published_at
              ? ` · ${new Date(
                  match.published_at,
                ).toLocaleString()}`
              : ""}
          </p>
        </div>

        <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs font-medium text-cyan-300">
          Matched: {match.item_name}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <MatchTag
          label="Type"
          value={match.item_type}
        />
        <MatchTag
          label="Value"
          value={match.value}
        />
        <MatchTag
          label="Event"
          value={match.event_type}
        />
        <MatchTag
          label="Topic"
          value={match.monitoring_topic}
        />
        <MatchTag
          label="Risk"
          value={
            match.risk_level
              ? match.risk_score !== null
                ? `${match.risk_level} (${match.risk_score})`
                : match.risk_level
              : null
          }
        />
        <MatchTag
          label="Impact"
          value={match.business_impact}
        />
      </div>
    </article>
  );
}

function MatchTag({
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
