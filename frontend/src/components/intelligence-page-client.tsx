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
} from "lucide-react";
import {
  getDashboardIntelligence,
  getDashboardOverview,
} from "@/lib/api";
import type { DashboardOverview, DashboardIntelligenceItem } from "@/lib/api";
import { formatArticleTimestamp, formatLabel, formatRelativeTime } from "@/lib/format";
import { PublisherLogo } from "@/components/publisher-logo";
import { Badge, toneForRisk } from "@/components/ui/badge";
import { focusRing } from "@/components/ui/button-styles";

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
  const [sortOrder, setSortOrder] = useState("Latest first");
  const [page, setPage] = useState(1);
  const [liveStatus, setLiveStatus] = useState<LiveStatus>("live");
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);
  const [featuredArticleId, setFeaturedArticleId] = useState<number | null>(null);

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
  }, [items, search, riskFilter, topicFilter, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paginatedItems = filteredItems.slice((safePage - 1) * pageSize, safePage * pageSize);
  const featuredItem = filteredItems.find((item) => item.article_id === featuredArticleId) ?? filteredItems[0] ?? null;

  const openOriginalArticle = (url: string | null | undefined) => {
    if (!url) return;
    window.location.assign(url);
  };

  const handleFilterChange = (nextSearch?: string, nextRiskFilter?: string, nextTopicFilter?: string, nextSort?: string, nextPageSize?: number) => {
    if (nextSearch !== undefined) setSearch(nextSearch);
    if (nextRiskFilter !== undefined) setRiskFilter(nextRiskFilter);
    if (nextTopicFilter !== undefined) setTopicFilter(nextTopicFilter);
    if (nextSort !== undefined) setSortOrder(nextSort);
    if (nextPageSize !== undefined) setPageSize(nextPageSize);
    setPage(1);
    setFeaturedArticleId(null);
  };

  const openArticleReader = (articleId: number) => {
    const article = items.find((item) => item.article_id === articleId);
    if (article?.url) {
      openOriginalArticle(article.url);
    }
  };

  const metricCards = [
    {
      label: "Total Articles",
      value: overview.total_articles,
      tone: "blue",
      icon: FileText,
      accent: "bg-[#EDF6FF] text-[#3C9CF4]",
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
      accent: "bg-[#FEEDEC] text-[#F26C66]",
    },
    {
      label: "Critical Risk",
      value: overview.critical_risk_items,
      tone: "amber",
      icon: TriangleAlert,
      accent: "bg-[#FFF6E8] text-[#F3B748]",
    },
  ];

  const riskFilters = ["All", "High Risk", "Medium Risk", "Low Risk"];
  const topicFilters = ["All", "Regulatory Action", "Fraud Security", "OpenAI", "Other"];

  return (
    <main className="min-h-screen bg-[#F3F7F8] px-6 py-8 lg:px-8">
      <div className="mx-auto w-full max-w-[1500px]">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-5 border-b border-[#D3E0E5] pb-5">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#0F7A7A]">Near Real-Time Monitoring</p>
            <h1 className="mt-2 text-[44px] font-semibold tracking-[-0.06em] text-[#0F172A] leading-[1.03]">Intelligence Feed</h1>
            <p className="mt-2 max-w-[760px] text-[15px] text-[#586D7B]">Latest fully processed media intelligence with AI triage, deterministic risk scoring, and recommended actions.</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-[#CFEAE4] bg-[#ECFDF5] px-3 py-1.5 text-[13px] font-medium text-[#0D7C5A] shadow-[0_0_0_1px_rgba(16,185,129,0.05)]">
              <span className={`h-2.5 w-2.5 rounded-full ${liveStatus === "live" ? "bg-[#31C48D] animate-pulse" : liveStatus === "updating" ? "bg-[#F2B94B]" : "bg-[#F59E0B]"}`} />
              {liveStatus === "live" ? "Live Monitoring" : liveStatus === "updating" ? "Updating" : "Update delayed"}
            </div>
            <div className="text-[12px] text-[#5B6B75]">{lastUpdatedAt ? `Updated ${formatRelativeTime(lastUpdatedAt)}` : "Updated just now"}</div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metricCards.map(({ label, value, accent, icon: Icon }, index) => (
            <div
              key={label}
              className="group animate-[fadeIn_0.35s_ease-out_forwards] rounded-xl border border-border bg-surface p-4 shadow-[0_1px_2px_rgba(28,23,52,0.06)] transition-colors duration-150 hover:border-border-strong"
              style={{ animationDelay: `${index * 80}ms` }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className={`flex h-11 w-11 items-center justify-center rounded-[12px] ${accent}`}>
                  <Icon className="h-5 w-5" strokeWidth={2.1} />
                </div>
              </div>

              <div className="mt-4">
                <p className="text-[12px] font-medium text-[#64798A]">{label}</p>
                <div className="mt-1 flex items-end justify-between gap-3">
                  <p className="text-[32px] font-semibold leading-none tracking-[-0.05em] text-[#0E1726]">{value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-[12px] border border-[#D9E7EC] bg-white px-3 py-3 shadow-[0_2px_10px_rgba(14,39,58,0.04)]">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <label className="relative block min-w-0 flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              <input
                type="search"
                value={search}
                placeholder="Search articles, publishers, topics..."
                className={`w-full rounded-[10px] border border-[#D7E2EA] bg-[#F9FBFC] py-2.5 pl-9 pr-3 text-[14px] text-[#0F172A] placeholder:text-[#7A8EA0] focus:border-[#97C7E0] focus:outline-none ${focusRing}`}
                onChange={(event) => handleFilterChange(event.target.value, riskFilter, topicFilter, sortOrder, pageSize)}
                aria-label="Search intelligence articles"
              />
            </label>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex flex-wrap items-center gap-2">
                {riskFilters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => handleFilterChange(search, filter, topicFilter, sortOrder, pageSize)}
                    className={`rounded-full border px-3 py-1.5 text-[12px] font-medium transition-colors ${
                      riskFilter === filter
                        ? "border-[#163F3F] bg-[#163F3F] text-white"
                        : "border-[#D9E5EA] bg-[#F8FBFD] text-[#4F6476]"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {topicFilters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => handleFilterChange(search, riskFilter, filter, sortOrder, pageSize)}
                    className={`rounded-full border px-3 py-1.5 text-[12px] font-medium transition-colors ${
                      topicFilter === filter
                        ? "border-[#163F3F] bg-[#163F3F] text-white"
                        : "border-[#D9E5EA] bg-[#F8FBFD] text-[#4F6476]"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <div className="relative">
                <select
                  aria-label="Sort intelligence articles"
                  value={sortOrder}
                  onChange={(event) => handleFilterChange(search, riskFilter, topicFilter, event.target.value, pageSize)}
                  className="appearance-none rounded-[10px] border border-[#D9E5EA] bg-[#F8FBFD] px-3 py-2 pr-8 text-[12px] font-medium text-[#2F4151] focus:border-[#97C7E0] focus:outline-none"
                >
                  <option>Latest first</option>
                  <option>Oldest first</option>
                  <option>Highest risk first</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.1fr_1.6fr]">
          <section className="overflow-hidden rounded-[14px] border border-[#DDE9EE] bg-white shadow-[0_4px_18px_rgba(20,50,70,0.04)]">
            <div className="border-b border-[#E4EDF2] px-4 py-3">
              <h2 className="text-[15px] font-semibold text-[#0F172A]">Featured Intelligence</h2>
            </div>

            {featuredItem ? (
              <div className="space-y-3 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="inline-flex items-center rounded-full bg-[#FDECEC] px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-[#C13A3A]">
                    {formatLabel(featuredItem.risk_level)} {featuredItem.risk_score.toFixed(1)}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {featuredItem.monitoring_topic && (
                      <Badge className="text-[10px] px-2 py-1">{formatLabel(featuredItem.monitoring_topic)}</Badge>
                    )}
                    {featuredItem.event_type && (
                      <Badge className="text-[10px] px-2 py-1">{formatLabel(featuredItem.event_type)}</Badge>
                    )}
                  </div>
                </div>

                <h3 className="max-w-[92%] text-[28px] font-semibold leading-[1.15] tracking-[-0.04em] text-[#0F172A]">
                  {featuredItem.headline || featuredItem.title}
                </h3>

                <p className="max-h-[120px] overflow-hidden text-[15px] leading-7 text-[#52677A]">
                  {featuredItem.summary || featuredItem.executive_summary || "No summary available."}
                </p>

                <div className="flex items-center justify-between gap-3 border-t border-[#EDF3F7] pt-4">
                  <div className="flex items-center gap-3">
                    <PublisherLogo publisherName={featuredItem.publisher_name || featuredItem.source_name || "Nova Cops"} size={42} className="rounded-[10px]" />
                    <div>
                      <div className="text-[12px] font-semibold text-[#0F172A]">{featuredItem.publisher_name || featuredItem.source_name}</div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-[#697F8F]">
                        <time>{featuredItem.published_at ? formatArticleTimestamp(featuredItem.published_at) : "Unknown date"}</time>
                      </div>
                    </div>
                  </div>

                  <div className="text-right text-[11px] text-[#697F8F]">
                    <div className="font-semibold text-[#304861]">Added to Nova Cops</div>
                    <time className="mt-1 block">{formatArticleTimestamp(featuredItem.collected_at)}</time>
                  </div>
                </div>

                <div className="rounded-[12px] border border-[#DDEAF3] bg-[#F4F8FA] p-4">
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#52677A]">Executive Summary</p>
                  <p className="mt-2 text-[14px] leading-6 text-[#21415A]">{featuredItem.executive_summary || "No executive summary available."}</p>
                </div>

                <div className="flex flex-wrap items-center gap-4 border-t border-[#EDF3F7] pt-4 text-[12px] text-[#5D7585]">
                  <div>
                    <div className="font-medium text-[#7A8EA0]">Urgency</div>
                    <div className="mt-1 font-semibold text-[#1E2D3A]">{formatLabel(featuredItem.urgency)}</div>
                  </div>
                  <div>
                    <div className="font-medium text-[#7A8EA0]">Escalation</div>
                    <div className="mt-1 font-semibold text-[#1E2D3A]">{formatLabel(featuredItem.escalation_action)}</div>
                  </div>
                  <div>
                    <div className="font-medium text-[#7A8EA0]">Topic</div>
                    <div className="mt-1 font-semibold text-[#1E2D3A]">{formatLabel(featuredItem.monitoring_topic ?? featuredItem.event_type ?? "General")}</div>
                  </div>
                </div>

                <div className="flex items-center justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => openArticleReader(featuredItem.article_id)}
                    className="inline-flex items-center gap-2 rounded-[10px] border border-[#D9E8F0] bg-white px-3 py-2 text-[13px] font-semibold text-[#0F172A] transition-colors hover:bg-[#F4F8FA]"
                  >
                    View Article <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-[#52677A]">
                <p className="text-[15px] font-medium">No intelligence matches these filters.</p>
                <button type="button" onClick={() => { setSearch(""); setRiskFilter("All"); setTopicFilter("All"); }} className="mt-3 rounded-full border border-[#D9E5EA] bg-[#F8FBFD] px-3 py-1.5 text-[12px] font-medium text-[#21415A]">
                  Clear filters
                </button>
              </div>
            )}
          </section>

          <section className="overflow-hidden rounded-[14px] border border-[#DDE9EE] bg-white shadow-[0_4px_18px_rgba(20,50,70,0.04)]">
            <div className="flex items-center justify-between border-b border-[#E4EDF2] px-4 py-3">
              <h2 className="text-[15px] font-semibold text-[#0F172A]">Latest Articles</h2>
              <div className="flex items-center gap-2 text-[12px] text-[#697F8F]">
                <span>{filteredItems.length} of {items.length}</span>
                <button type="button" className="text-[#204A63] font-medium">View all</button>
              </div>
            </div>

            {error ? (
              <div className="p-6 text-center">
                <p className="text-[15px] font-medium text-[#2E4254]">{error}</p>
                <button type="button" onClick={() => void fetchItems()} className="mt-3 rounded-full border border-[#D9E5EA] bg-[#F8FBFD] px-3 py-1.5 text-[12px] font-medium text-[#21415A]">Retry</button>
              </div>
            ) : paginatedItems.length === 0 ? (
              <div className="p-6 text-center text-[#52677A]">No articles match the current filters.</div>
            ) : (
              <div className="p-2">
                {paginatedItems.map((item, index) => {
                  const tags = [item.monitoring_topic, item.event_type].filter(Boolean).slice(0, 2);
                  return (
                    <div key={item.article_id} className="flex items-start gap-3 border-b border-[#EEF3F6] px-2 py-3 last:border-b-0 hover:bg-[#F7FBFD]">
                      <div className="w-5 pt-2 text-right text-[12px] font-medium text-[#8CA0AF]">{(page - 1) * pageSize + index + 1}</div>
                      <div className="flex shrink-0 pt-1"><PublisherLogo publisherName={item.publisher_name || item.source_name || "Nova Cops"} size={42} className="rounded-[10px]" /></div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="line-clamp-2 text-[14px] font-semibold leading-[1.4] text-[#0F172A]">{item.headline || item.title}</div>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-[#64798A]">
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
                            className="inline-flex shrink-0 items-center justify-center rounded-[8px] border border-[#D9E3EA] bg-white px-2.5 py-1.5 text-[12px] font-medium text-[#1B334A] hover:bg-[#F5F9FB]"
                          >
                            View
                          </button>
                        </div>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] ${toneForRisk(item.risk_level)} ${toneForRisk(item.risk_level).includes("bg-") ? "" : ""}`}>
                            {formatLabel(item.risk_level)} {item.risk_score.toFixed(1)}
                          </span>
                          {tags.map((tag) => (
                            <span key={`${item.article_id}-${tag}`} className="inline-flex items-center rounded-full border border-[#D9E5EA] bg-[#F8FBFD] px-2 py-0.5 text-[10px] font-medium text-[#466278]">
                              {formatLabel(tag ?? "Other")}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}

                <div className="flex flex-col gap-3 border-t border-[#EEF3F6] px-2 pb-2 pt-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-2">
                    <button type="button" aria-label="Previous page" disabled={safePage === 1} onClick={() => setPage((current) => Math.max(1, current - 1))} className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] border border-[#D9E5EA] bg-white text-[#48637A] disabled:cursor-not-allowed disabled:opacity-50">
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    {getPageNumbers(totalPages, page).map((pageNumber, index) =>
                      pageNumber === "ellipsis" ? (
                        <span key={`ellipsis-${index}`} className="px-2 text-[13px] text-[#7B8EA1]">...</span>
                      ) : (
                        <button
                          key={pageNumber}
                          type="button"
                          onClick={() => setPage(pageNumber)}
                          className={`inline-flex h-8 w-8 items-center justify-center rounded-[8px] text-[12px] font-semibold ${
                            page === pageNumber ? "bg-[#163F3F] text-white" : "border border-[#D9E5EA] bg-white text-[#21415A]"
                          }`}
                        >
                          {pageNumber}
                        </button>
                      ),
                    )}
                    <button type="button" aria-label="Next page" disabled={safePage >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] border border-[#D9E5EA] bg-white text-[#48637A] disabled:cursor-not-allowed disabled:opacity-50">
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 text-[12px] text-[#5D7585]">
                    <span>Showing {Math.min((safePage - 1) * pageSize + 1, filteredItems.length)}-{Math.min(safePage * pageSize, filteredItems.length)} of {filteredItems.length}</span>
                    <select
                      aria-label="Select articles per page"
                      value={pageSize}
                      onChange={(event) => handleFilterChange(search, riskFilter, topicFilter, sortOrder, Number(event.target.value))}
                      className="rounded-[8px] border border-[#D9E5EA] bg-[#F8FBFD] px-2 py-1.5 text-[12px] font-medium text-[#21415A]"
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
  );
}
