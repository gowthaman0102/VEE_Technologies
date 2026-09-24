"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BrainCircuit,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileText,
  Search,
  ShieldAlert,
  TriangleAlert,
  X,
} from "lucide-react";
import {
  getDashboardIntelligence,
  getDashboardOverview,
} from "@/lib/api";
import type { DashboardOverview, DashboardIntelligenceItem } from "@/lib/api";
import { formatArticleTimestamp, formatLabel, formatRelativeTime } from "@/lib/format";
import { PublisherLogo } from "@/components/publisher-logo";
import { Badge, toneForRisk, toneForSentiment } from "@/components/ui/badge";
import { PageAmbient } from "@/components/page-ambient";
import { CosmicPageHero } from "@/components/cosmic-page-hero";
import { focusRing } from "@/components/ui/button-styles";
import { ArticleReaderModal } from "@/components/article-reader-modal";

type Props = {
  initialItems: DashboardIntelligenceItem[];
  initialOverview: DashboardOverview;
};

type LiveStatus = "live" | "updating" | "delayed";

const PAGE_SIZE_OPTIONS = [5, 10, 20] as const;

function getRiskMatchKey(risk: string | null | undefined): string {
  const normalized = (risk ?? "").toLowerCase();
  if (normalized.includes("critical")) return "Critical";
  if (normalized.includes("high")) return "High";
  if (normalized.includes("medium") || normalized.includes("moderate")) return "Medium";
  if (normalized.includes("low")) return "Low";
  return "Other";
}

function matchesTopic(item: DashboardIntelligenceItem, filter: string): boolean {
  const source = [item.monitoring_topic, item.event_type, item.company_name, item.title, item.summary, item.why_it_matters]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  switch (filter) {
    case "High Risk":
      return getRiskMatchKey(item.risk_level) === "High";
    case "Medium Risk":
      return getRiskMatchKey(item.risk_level) === "Medium";
    case "Low Risk":
      return getRiskMatchKey(item.risk_level) === "Low";
    case "Regulatory Action":
      return /regulatory|compliance|legal|oversight|sanction|policy/i.test(source);
    case "Fraud Security":
      return /fraud|security|cyber|breach|phishing|malware|misuse/i.test(source);
    case "OpenAI":
      return /openai/i.test(source);
    case "Other":
      return !/regulatory|compliance|legal|oversight|sanction|policy|fraud|security|cyber|breach|phishing|malware|misuse|openai/i.test(source);
    default:
      return true;
  }
}

function getPageNumbers(totalPages: number, current: number) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);

  const pages = new Set<number>([1, current - 1, current, current + 1, totalPages]);
  const items = Array.from(pages).filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
  const result: Array<number | "ellipsis"> = [];

  for (let i = 0; i < items.length; i += 1) {
    const currentPage = items[i];
    const previous = items[i - 1];
    if (previous !== undefined && currentPage - previous > 1) {
      result.push("ellipsis");
    }
    result.push(currentPage);
  }

  return result;
}

export function IntelligencePageClient({ initialItems, initialOverview }: Props) {
  const [items, setItems] = useState<DashboardIntelligenceItem[]>(initialItems);
  const [overview, setOverview] = useState<DashboardOverview>(initialOverview);
  const [pageSize, setPageSize] = useState<number>(5);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [topicFilter, setTopicFilter] = useState("All");
  const [sentimentFilter, setSentimentFilter] = useState("All");
  const [impactFilter, setImpactFilter] = useState("All");
  const [sortOrder, setSortOrder] = useState("Latest first");
  const [page, setPage] = useState(1);
  const [liveStatus, setLiveStatus] = useState<LiveStatus>("live");
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);
  const [featuredArticleId, setFeaturedArticleId] = useState<number | null>(null);
  const [readerArticleId, setReaderArticleId] = useState<number | null>(null);
  const [viewAllOpen, setViewAllOpen] = useState(false);

  const fetchOverview = async () => {
    const overviewData = await getDashboardOverview();
    setOverview(overviewData);
  };

  const fetchItems = async () => {
    try {
      setLiveStatus("updating");
      const data = await getDashboardIntelligence(200);
      setItems(data.items);
      setLastUpdatedAt(new Date());
      setLiveStatus("live");
      setError(null);
    } catch (caughtError) {
      console.error("Failed to refresh intelligence feed", caughtError);
      setError("Unable to load Intelligence Feed.");
      setLiveStatus("delayed");
    }
  };

  useEffect(() => {
    const interval = window.setInterval(() => {
      void fetchItems();
      void fetchOverview();
    }, 30000);

    return () => window.clearInterval(interval);
  }, []);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    let nextItems = [...items];

    if (query) {
      nextItems = nextItems.filter((item) => {
        const haystack = [
          item.title,
          item.headline,
          item.publisher_name,
          item.source_name,
          item.company_name,
          item.monitoring_topic,
          item.event_type,
          item.summary,
          item.executive_summary,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return haystack.includes(query);
      });
    }

    if (riskFilter !== "All") {
      nextItems = nextItems.filter((item) => getRiskMatchKey(item.risk_level) === riskFilter.replace(" Risk", ""));
    }

    if (sentimentFilter !== "All") {
      nextItems = nextItems.filter(
        (item) => item.sentiment?.toLowerCase() === sentimentFilter.toLowerCase()
      );
    }

    if (topicFilter !== "All") {
      nextItems = nextItems.filter((item) => matchesTopic(item, topicFilter));
    }

    nextItems.sort((a, b) => {
      const aTime = a.published_at ? new Date(a.published_at).getTime() : 0;
      const bTime = b.published_at ? new Date(b.published_at).getTime() : 0;

      if (sortOrder === "Oldest first") {
        return aTime - bTime;
      }
      if (sortOrder === "Highest risk first") {
        return (b.risk_score ?? 0) - (a.risk_score ?? 0);
      }
      return bTime - aTime;
    });

    return nextItems;
  }, [items, search, riskFilter, topicFilter, sentimentFilter, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paginatedItems = filteredItems.slice((safePage - 1) * pageSize, safePage * pageSize);
  const featuredItem = filteredItems.find((item) => item.article_id === featuredArticleId) ?? filteredItems[0] ?? null;

  const openOriginalArticle = (url: string | null | undefined) => {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleFilterChange = (
    nextSearch?: string, 
    nextRiskFilter?: string, 
    nextTopicFilter?: string, 
    nextSentimentFilter?: string, 
    nextSort?: string, 
    nextPageSize?: number
  ) => {
    if (nextSearch !== undefined) setSearch(nextSearch);
    if (nextRiskFilter !== undefined) setRiskFilter(nextRiskFilter);
    if (nextTopicFilter !== undefined) setTopicFilter(nextTopicFilter);
    if (nextSentimentFilter !== undefined) setSentimentFilter(nextSentimentFilter);
    if (nextSort !== undefined) setSortOrder(nextSort);
    if (nextPageSize !== undefined) setPageSize(nextPageSize);
    setPage(1);
    setFeaturedArticleId(null);
  };

  const openArticleReader = (articleId: number) => {
    setReaderArticleId(articleId);
  };

  const metricCards = [
    {
      label: "Total Articles",
      value: overview.total_articles,
      tone: "blue",
      icon: FileText,
      accent: "bg-primary-soft text-primary",
    },
    {
      label: "Processed Intelligence",
      value: overview.processed_articles,
      tone: "violet",
      icon: BrainCircuit,
      accent: "bg-primary-soft text-primary",
    },
    {
      label: "High Risk",
      value: overview.high_risk_items,
      tone: "red",
      icon: ShieldAlert,
      accent: "bg-critical-bg text-critical",
    },
    {
      label: "Critical Risk",
      value: overview.critical_risk_items,
      tone: "amber",
      icon: TriangleAlert,
      accent: "bg-medium-bg text-medium",
    },
  ];

  const riskFilters = ["All", "High Risk", "Medium Risk", "Low Risk"];
  const topicFilters = ["All", "Regulatory Action", "Fraud Security", "OpenAI", "Other"];
  const sentimentFilters = ["All", "Positive", "Neutral", "Negative"];

  return (
    <>
    <main className="relative min-h-screen overflow-hidden bg-canvas px-6 py-8 lg:px-8">
          <PageAmbient kind="intelligence" />
          <div className="relative z-10 mx-auto w-full max-w-[1500px]">
        <div className="mb-4 flex justify-end">
          <div className="page-live-chip" aria-live="polite">
            <span className="page-live-label">LIVE</span>
          </div>
        </div>

        <CosmicPageHero
          variant="intelligence"
          eyebrow="INTELLIGENCE"
          title="Intelligence Feed"
          description="Latest processed media intelligence with AI triage, semantic sentiment, deterministic risk scoring, and business-impact analysis."
          imageSrc="/intelligence-hero.png"
        />

        {/* SECTION 1 - ANALYST TOOLBAR */}
        <div className="mt-6 rounded-[12px] border border-border bg-surface px-4 py-4 shadow-[0_2px_10px_rgba(28,23,52,0.04)]">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <label className="relative block min-w-0 flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <input
                  type="search"
                  value={search}
                  placeholder="Search articles, publishers, topics..."
                  className={`w-full rounded-[10px] border border-border bg-surface-raised py-2.5 pl-9 pr-3 text-[14px] text-text placeholder:text-muted focus:border-primary-border focus:outline-none ${focusRing}`}
                  onChange={(event) => handleFilterChange(event.target.value, riskFilter, topicFilter, sentimentFilter, sortOrder, pageSize)}
                  aria-label="Search intelligence articles"
                />
              </label>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <select
                    aria-label="Sort intelligence articles"
                    value={sortOrder}
                    onChange={(event) => handleFilterChange(search, riskFilter, topicFilter, sentimentFilter, event.target.value, pageSize)}
                    className="appearance-none rounded-[10px] border border-border bg-surface-raised px-3 py-2 pr-8 text-[12px] font-medium text-text-body focus:border-primary-border focus:outline-none"
                  >
                    <option>Latest first</option>
                    <option>Oldest first</option>
                    <option>Highest risk first</option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="text-[12px] font-medium text-muted mt-2 mr-1">Risk:</span>
              <div className="flex flex-wrap items-center gap-2">
                {riskFilters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => handleFilterChange(search, filter, topicFilter, sentimentFilter, sortOrder, pageSize)}
                    className={`rounded-full border px-3 py-1 text-[12px] font-medium transition-colors ${
                      riskFilter === filter
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-surface-raised text-text-body"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-border pt-3">
              <span className="text-[12px] font-medium text-muted mt-2 mr-1">Sentiment:</span>
              <div className="flex flex-wrap items-center gap-2">
                {sentimentFilters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => handleFilterChange(search, riskFilter, topicFilter, filter, sortOrder, pageSize)}
                    className={`rounded-full border px-3 py-1 text-[12px] font-medium transition-colors ${
                      sentimentFilter === filter
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-surface-raised text-text-body"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-border pt-3">
              <span className="text-[12px] font-medium text-muted mt-2 mr-1">Topic/Event:</span>
              <div className="flex flex-wrap items-center gap-2">
                {topicFilters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => handleFilterChange(search, riskFilter, filter, sentimentFilter, sortOrder, pageSize)}
                    className={`rounded-full border px-3 py-1 text-[12px] font-medium transition-colors ${
                      topicFilter === filter
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-surface-raised text-text-body"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.1fr_1.6fr]">
          <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)]">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-[15px] font-semibold text-text">Featured Intelligence</h2>
            </div>

            {featuredItem ? (
              <div className="space-y-3 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="inline-flex items-center rounded-full bg-critical-bg px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-critical">
                    {formatLabel(featuredItem.risk_level)} {featuredItem.risk_score.toFixed(1)}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {featuredItem.sentiment && (
                      <Badge tone={toneForSentiment(featuredItem.sentiment)} className="text-[10px] px-2 py-1">{formatLabel(featuredItem.sentiment)}</Badge>
                    )}
                    {featuredItem.monitoring_topic && (
                      <Badge className="text-[10px] px-2 py-1">{formatLabel(featuredItem.monitoring_topic)}</Badge>
                    )}
                    {featuredItem.event_type && (
                      <Badge className="text-[10px] px-2 py-1">{formatLabel(featuredItem.event_type)}</Badge>
                    )}
                  </div>
                </div>

                <h3 className="max-w-[92%] text-[28px] font-semibold leading-[1.15] tracking-[-0.04em] text-text">
                  {featuredItem.headline || featuredItem.title}
                </h3>

                <p className="max-h-[120px] overflow-hidden text-[15px] leading-7 text-muted">
                  {featuredItem.summary || featuredItem.executive_summary || "No summary available."}
                </p>

                <div className="flex items-center justify-between gap-3 border-t border-border pt-4">
                  <div className="flex items-center gap-3">
                    <PublisherLogo publisherName={featuredItem.publisher_name || featuredItem.source_name || "Nova Cops"} size={42} className="rounded-[10px]" />
                    <div>
                      <div className="text-[12px] font-semibold text-text">{featuredItem.publisher_name || featuredItem.source_name}</div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-muted">
                        <time>{featuredItem.published_at ? formatArticleTimestamp(featuredItem.published_at) : "Unknown date"}</time>
                      </div>
                    </div>
                  </div>

                  <div className="text-right text-[11px] text-muted">
                    <div className="font-semibold text-text-body">Added to Nova Cops</div>
                    <time className="mt-1 block">{formatArticleTimestamp(featuredItem.collected_at)}</time>
                  </div>
                </div>

                <div className="rounded-[12px] border border-border bg-surface-raised p-4">
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted">Executive Summary</p>
                  <p className="mt-2 text-[14px] leading-6 text-text-body">{featuredItem.executive_summary || "No executive summary available."}</p>
                </div>

                <div className="flex flex-wrap items-center gap-4 border-t border-border pt-4 text-[12px] text-muted">
                  <div>
                    <div className="font-medium text-muted">Urgency</div>
                    <div className="mt-1 font-semibold text-text-body">{formatLabel(featuredItem.urgency)}</div>
                  </div>
                  <div>
                    <div className="font-medium text-muted">Escalation</div>
                    <div className="mt-1 font-semibold text-text-body">{formatLabel(featuredItem.escalation_action)}</div>
                  </div>
                  <div>
                    <div className="font-medium text-muted">Topic</div>
                    <div className="mt-1 font-semibold text-text-body">{formatLabel(featuredItem.monitoring_topic ?? featuredItem.event_type ?? "General")}</div>
                  </div>
                </div>

                <div className="flex items-center justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => openArticleReader(featuredItem.article_id)}
                    className="inline-flex items-center gap-2 rounded-[10px] border border-border bg-surface px-3 py-2 text-[13px] font-semibold text-text transition-colors hover:bg-surface-raised"
                  >
                    View Article <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-muted">
                <p className="text-[15px] font-medium">No intelligence matches these filters.</p>
                <button type="button" onClick={() => { setSearch(""); setRiskFilter("All"); setTopicFilter("All"); setSentimentFilter("All"); }} className="mt-3 rounded-full border border-border bg-surface-raised px-3 py-1.5 text-[12px] font-medium text-text-body">
                  Clear filters
                </button>
              </div>
            )}
          </section>

          <section className="overflow-hidden rounded-[14px] border border-border bg-surface shadow-[0_4px_18px_rgba(28,23,52,0.06)]">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="text-[15px] font-semibold text-text">Live Intelligence Queue</h2>
              <button
                type="button"
                onClick={() => setViewAllOpen(true)}
                className="text-[12px] font-medium text-primary hover:underline"
              >
                View full queue
              </button>
            </div>

            {error ? (
              <div className="p-6 text-center">
                <p className="text-[15px] font-medium text-text-body">{error}</p>
                <button type="button" onClick={() => void fetchItems()} className="mt-3 rounded-full border border-border bg-surface-raised px-3 py-1.5 text-[12px] font-medium text-text-body">Retry</button>
              </div>
            ) : paginatedItems.length === 0 ? (
              <div className="p-6 text-center text-muted">No articles match the current filters.</div>
            ) : (
              <div className="p-2">
                {paginatedItems.map((item, index) => {
                  const tags = [item.monitoring_topic, item.event_type].filter(Boolean).slice(0, 2);
                  return (
                    <div key={item.article_id} className="flex items-start gap-3 border-b border-border px-2 py-3 last:border-b-0 hover:bg-surface-raised">
                      <div className="w-5 pt-2 text-right text-[12px] font-medium text-muted">{(page - 1) * pageSize + index + 1}</div>
                      <div className="flex shrink-0 pt-1"><PublisherLogo publisherName={item.publisher_name || item.source_name || "Nova Cops"} size={42} className="rounded-[10px]" /></div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="line-clamp-2 text-[14px] font-semibold leading-[1.4] text-text">{item.headline || item.title}</div>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-muted">
                              <span>{item.publisher_name || item.source_name}</span>
                              <span>·</span>
                              <span>{item.published_at ? formatArticleTimestamp(item.published_at) : "Unknown date"}</span>
                              <span>·</span>
                              <span>Added: {formatArticleTimestamp(item.collected_at)}</span>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => openArticleReader(item.article_id)}
                            className="inline-flex shrink-0 items-center justify-center rounded-[8px] border border-border bg-surface px-2.5 py-1.5 text-[12px] font-medium text-text-body hover:bg-surface-raised"
                          >
                            View
                          </button>
                        </div>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] ${toneForRisk(item.risk_level)} ${toneForRisk(item.risk_level).includes("bg-") ? "" : ""}`}>
                            {formatLabel(item.risk_level)} {item.risk_score.toFixed(1)}
                          </span>
                          {item.sentiment && (
                            <Badge tone={toneForSentiment(item.sentiment)} className="text-[10px] px-2 py-0.5">
                              {formatLabel(item.sentiment)}
                            </Badge>
                          )}
                          {tags.map((tag) => (
                            <span key={`${item.article_id}-${tag}`} className="inline-flex items-center rounded-full border border-border bg-surface-raised px-2 py-0.5 text-[10px] font-medium text-text-body">
                              {formatLabel(tag ?? "Other")}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}

                <div className="flex flex-col gap-3 border-t border-border px-2 pb-2 pt-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-2">
                    <button type="button" aria-label="Previous page" disabled={safePage === 1} onClick={() => setPage((current) => Math.max(1, current - 1))} className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] border border-border bg-surface text-text-body disabled:cursor-not-allowed disabled:opacity-50">
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    {getPageNumbers(totalPages, page).map((pageNumber, index) =>
                      pageNumber === "ellipsis" ? (
                        <span key={`ellipsis-${index}`} className="px-2 text-[13px] text-muted">...</span>
                      ) : (
                        <button
                          key={pageNumber}
                          type="button"
                          onClick={() => setPage(pageNumber)}
                          className={`inline-flex h-8 w-8 items-center justify-center rounded-[8px] text-[12px] font-semibold ${
                            page === pageNumber ? "bg-primary text-white" : "border border-border bg-surface text-text-body"
                          }`}
                        >
                          {pageNumber}
                        </button>
                      ),
                    )}
                    <button type="button" aria-label="Next page" disabled={safePage >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] border border-border bg-surface text-text-body disabled:cursor-not-allowed disabled:opacity-50">
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 text-[12px] text-muted">
                    <span>Showing {Math.min((safePage - 1) * pageSize + 1, filteredItems.length)}-{Math.min(safePage * pageSize, filteredItems.length)} of {filteredItems.length}</span>
                    <select
                      aria-label="Select articles per page"
                      value={pageSize}
                      onChange={(event) => handleFilterChange(search, riskFilter, topicFilter, sentimentFilter, sortOrder, Number(event.target.value))}
                      className="rounded-[8px] border border-border bg-surface-raised px-2 py-1.5 text-[12px] font-medium text-text-body"
                    >
                      {PAGE_SIZE_OPTIONS.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>

    </main>

    {/* Article reader popup */}
    {readerArticleId !== null && (
      <ArticleReaderModal articleId={readerArticleId} onClose={() => setReaderArticleId(null)} />
    )}

    {/* View all articles popup */}
    {viewAllOpen && (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-text/40 p-4 sm:p-6"
        role="presentation"
        onMouseDown={(e) => { if (e.target === e.currentTarget) setViewAllOpen(false); }}
      >
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="view-all-title"
          className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl"
        >
          <header className="flex shrink-0 items-center justify-between gap-4 border-b border-border px-5 py-4 sm:px-6">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-primary">Intelligence Feed</p>
              <h2 id="view-all-title" className="mt-1 text-xl font-bold text-text">
                All Articles
                <span className="ml-2 text-[15px] font-medium text-muted">· {filteredItems.length}</span>
              </h2>
            </div>
            <button
              type="button"
              onClick={() => setViewAllOpen(false)}
              aria-label="Close all articles"
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-raised text-text transition-colors hover:bg-critical-bg hover:border-critical hover:text-critical focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </header>
          <div className="flex-1 overflow-y-auto bg-surface-raised px-4 py-4">
            <div className="space-y-2">
              {filteredItems.map((item, index) => {
                const tags = [item.monitoring_topic, item.event_type].filter(Boolean).slice(0, 2);
                return (
                  <div key={item.article_id} className="flex items-start gap-3 rounded-xl border border-border bg-surface px-3 py-3 hover:bg-surface-raised transition-colors">
                    <div className="w-6 pt-1 text-right text-[12px] font-medium text-muted">{index + 1}</div>
                    <div className="flex shrink-0 pt-0.5">
                      <PublisherLogo publisherName={item.publisher_name || item.source_name || "Nova Cops"} size={38} className="rounded-[8px]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="line-clamp-2 text-[13px] font-semibold leading-[1.4] text-text">{item.headline || item.title}</div>
                          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                            <span>{item.publisher_name || item.source_name}</span>
                            <span>·</span>
                            <span>{item.published_at ? formatArticleTimestamp(item.published_at) : "Unknown date"}</span>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => { setViewAllOpen(false); openArticleReader(item.article_id); }}
                          className="inline-flex shrink-0 items-center justify-center rounded-[8px] border border-border bg-surface px-2.5 py-1.5 text-[12px] font-medium text-text-body hover:bg-surface-raised transition-colors"
                        >
                          View
                        </button>
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] ${toneForRisk(item.risk_level)}`}>
                          {formatLabel(item.risk_level)} {item.risk_score.toFixed(1)}
                        </span>
                        {item.sentiment && (
                          <Badge tone={toneForSentiment(item.sentiment)} className="text-[10px] px-2 py-0.5">
                            {formatLabel(item.sentiment)}
                          </Badge>
                        )}
                        {tags.map((tag) => (
                          <span key={`${item.article_id}-${tag}`} className="inline-flex items-center rounded-full border border-border bg-surface-raised px-2 py-0.5 text-[10px] font-medium text-text-body">
                            {formatLabel(tag ?? "Other")}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </div>
    )}
    </>
  );
}

