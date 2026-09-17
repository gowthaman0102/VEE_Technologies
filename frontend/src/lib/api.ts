export type DashboardOverview = {
  total_articles: number;
  processed_articles: number;
  total_companies: number;
  high_risk_items: number;
  critical_risk_items: number;
  active_alerts: number;
  overdue_alerts: number;
};

export type DashboardIntelligenceItem = {
  article_id: number;
  company_id: number;
  company_name: string;

  title: string;
  source_name: string;
  url: string;
  published_at: string | null;

  event_type: string;
  urgency: string;
  confidence: number;

  summary: string;
  why_it_matters: string;

  risk_score: number;
  risk_level: string;
  escalation_action: string;
  monitoring_topic: string | null;

  headline: string;
  executive_summary: string;
  recommended_action: string;
  attention_level: string;

  updated_at: string;
};

export type DashboardIntelligenceResponse = {
  count: number;
  items: DashboardIntelligenceItem[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";

export type ActiveCompany = {
  id: number;
  name: string;
};

export async function getActiveCompany(): Promise<ActiveCompany> {
  const response = await fetch(`${API_BASE_URL}/companies/active`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Active company API failed with status ${response.status}`);
  }
  return response.json();
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/overview`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Dashboard API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function getDashboardIntelligence(
  limit = 20,
): Promise<DashboardIntelligenceResponse> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/intelligence?limit=${limit}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Intelligence API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export type DashboardRiskBucket = {
  label: string;
  count: number;
};

export type DashboardRiskAnalytics = {
  total_assessments: number;
  average_risk_score: number;
  highest_risk_score: number;
  human_review_count: number;
  immediate_alert_count: number;
  risk_levels: DashboardRiskBucket[];
  event_types: DashboardRiskBucket[];
};

export async function getDashboardRiskAnalytics(): Promise<DashboardRiskAnalytics> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/risk-analytics`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Risk analytics API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export type DashboardAlertItem = {
  id: number;
  article_id: number;
  company_id: number;

  alert_type: string;
  severity: string;
  title: string;
  message: string;

  delivery_status: string;
  delivery_channel: string | null;
  retry_count: number;
  last_error: string | null;

  requires_immediate_delivery: boolean;
  sla_due_at: string | null;
  delivered_at: string | null;

  is_overdue: boolean;

  created_at: string;
  updated_at: string;
};

export type DashboardAlertsResponse = {
  total_alerts: number;
  active_alerts: number;
  delivered_alerts: number;
  failed_alerts: number;
  overdue_alerts: number;
  items: DashboardAlertItem[];
};

export async function getDashboardAlerts(
  limit = 50,
): Promise<DashboardAlertsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/alerts?limit=${limit}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Alerts API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export type DashboardMonitoringTopic = {
  topic: string;
  priority: string;
  is_active: boolean;
};

export type DashboardCompanyRelationship = {
  related_company_name: string;
  relationship_type: string;
};

export type DashboardCompanyItem = {
  id: number;
  name: string;
  website: string | null;
  industry: string | null;
  is_active: boolean;

  aliases: string[];
  geographies: string[];
  regulators: string[];
  relationships: DashboardCompanyRelationship[];
  monitoring_topics: DashboardMonitoringTopic[];

  triage_count: number;
  risk_assessment_count: number;
  high_risk_count: number;
  critical_risk_count: number;
  alert_count: number;
};

export type DashboardCompaniesResponse = {
  count: number;
  items: DashboardCompanyItem[];
};

export type WatchlistItem = {
  id: number;
  company_id: number;
  item_type: string;
  item_name: string;
  value: string;
  is_active: boolean;
};

export type WatchlistResponse = {
  count: number;
  items: WatchlistItem[];
};

export type WatchlistMatch = {
  watchlist_item_id: number;
  item_type: string;
  item_name: string;
  value: string;
  article_id: number;
  title: string;
  source_name: string;
  url: string;
  published_at: string | null;
  event_type: string | null;
  monitoring_topic: string | null;
  risk_level: string | null;
  risk_score: number | null;
  business_impact: string | null;
};

export type WatchlistMatchResponse = {
  count: number;
  matches: WatchlistMatch[];
};

export type ReportMetric = {
  label: string;
  value: string | number;
};

export type ReportSummary = {
  company_id: number;
  start_date: string;
  end_date: string;
  total_articles: number;
  total_events: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  sentiment_balance: {
    positive: number;
    neutral: number;
    negative: number;
  };
  metrics: ReportMetric[];
};

export type ReportHistoryItem = {
  id: number;
  company_id: number;
  report_type: string;
  file_format: string;
  filename: string | null;
  content_type: string | null;
  period_start: string;
  period_end: string;
  status: string;
  generated_at: string | null;
  error: string | null;
  created_at: string;
};

export type AnalyticsOverview = {
  company_id: number;
  start: string;
  end: string;
  total_articles: number;
  total_events: number;
  sentiment: Record<string, number>;
  risk: Record<string, number>;
  business_impact: Record<string, number>;
  competitors: Array<{ name: string; mention_count: number }>;
};

export type EventCluster = {
  id: number;
  company_id: number;
  title: string | null;
  representative_article_id: number | null;
  first_published_at: string | null;
  last_published_at: string | null;
  article_count: number;
};

export type EventClusterResponse = {
  count: number;
  items: EventCluster[];
};

export type EventClusterDetail = EventCluster & {
  members: Array<{
    article_id: number;
    title: string;
    source_name: string;
    url: string;
    published_at: string | null;
    similarity: number | null;
  }>;
};

export type SearchFilters = {
  start?: string;
  end?: string;
  source_name?: string;
  sentiment?: string;
  risk_level?: string;
  business_impact?: string;
  event_type?: string;
  event_cluster_id?: number;
};

export type SearchResult = {
  article_id: number;
  title: string;
  source_name: string;
  url: string;
  published_at: string | null;
  event_type: string | null;
  sentiment: string | null;
  risk_level: string | null;
  risk_score: number | null;
  business_impact: string | null;
  event_cluster_id: number | null;
  distance?: number;
  similarity?: number;
};

export type KeywordSearchResult = SearchResult;

export type KeywordSearchResponse = {
  query: string;
  count: number;
  results: KeywordSearchResult[];
};

export type SemanticSearchResponse = {
  query: string;
  count: number;
  results: SearchResult[];
};

export async function getDashboardCompanies(): Promise<DashboardCompaniesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/companies`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Companies API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function getWatchlist(
  companyId: number,
): Promise<WatchlistResponse> {
  const response = await fetch(
    `${API_BASE_URL}/watchlist?company_id=${companyId}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Watchlist API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function getWatchlistMatches(
  companyId: number,
  start: string,
  end: string,
  limit = 100,
): Promise<WatchlistMatchResponse> {
  const params = new URLSearchParams({
    company_id: String(companyId),
    start,
    end,
    limit: String(limit),
  });

  const response = await fetch(
    `${API_BASE_URL}/watchlist/matches?${params}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Watchlist matches API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function getReportSummary(args: {
  company_id: number;
  start_date: string;
  end_date: string;
}): Promise<ReportSummary> {
  const params = new URLSearchParams({
    company_id: String(args.company_id),
    start_date: args.start_date,
    end_date: args.end_date,
  });

  const response = await fetch(
    `${API_BASE_URL}/reports?${params.toString()}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Reports API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function getReportHistory(companyId: number): Promise<{ count: number; items: ReportHistoryItem[] }> {
  const response = await fetch(`${API_BASE_URL}/reports/history?company_id=${companyId}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Report history API failed with status ${response.status}`);
  return response.json();
}

export type GenerateReportResponse = {
  report_id: number;
  status: string;
  filename: string | null;
  content_type: string | null;
  error: string | null;
};

export async function generateReport(args: {
  company_id: number;
  report_type: "daily" | "weekly" | "monthly" | "custom";
  format: "pdf" | "xlsx" | "csv";
  start_date?: string;
  end_date?: string;
}): Promise<GenerateReportResponse> {
  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  if (!response.ok) throw new Error(`Report generation failed with status ${response.status}`);
  return response.json();
}

export async function createWatchlistItem(args: {
  company_id: number;
  item_type: string;
  item_name: string;
  value: string;
}): Promise<WatchlistItem> {
  const response = await fetch(`${API_BASE_URL}/watchlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  if (!response.ok) throw new Error(`Watchlist create failed with status ${response.status}`);
  return response.json();
}

export async function updateWatchlistItem(id: number, values: Partial<WatchlistItem>): Promise<WatchlistItem> {
  const response = await fetch(`${API_BASE_URL}/watchlist/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });
  if (!response.ok) throw new Error(`Watchlist update failed with status ${response.status}`);
  return response.json();
}

export async function deleteWatchlistItem(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/watchlist/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Watchlist delete failed with status ${response.status}`);
}

export async function getAnalyticsOverview(
  companyId: number,
  start: string,
  end: string,
): Promise<AnalyticsOverview> {
  const params = new URLSearchParams({
    company_id: String(companyId),
    start,
    end,
  });
  const response = await fetch(`${API_BASE_URL}/analytics/overview?${params}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Analytics API failed with status ${response.status}`);
  }
  return response.json();
}

export async function getEventClusters(companyId: number): Promise<EventClusterResponse> {
  const response = await fetch(`${API_BASE_URL}/event-clusters?company_id=${companyId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Event cluster API failed with status ${response.status}`);
  }
  return response.json();
}

export async function getEventClusterDetail(companyId: number, clusterId: number): Promise<EventClusterDetail> {
  const response = await fetch(`${API_BASE_URL}/event-clusters/${clusterId}?company_id=${companyId}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Event detail API failed with status ${response.status}`);
  return response.json();
}

function appendSearchFilters(
  params: URLSearchParams,
  filters: SearchFilters,
): void {
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.source_name) params.set("source_name", filters.source_name);
  if (filters.sentiment) params.set("sentiment", filters.sentiment);
  if (filters.risk_level) params.set("risk_level", filters.risk_level);
  if (filters.business_impact) {
    params.set("business_impact", filters.business_impact);
  }
  if (filters.event_type) params.set("event_type", filters.event_type);
  if (filters.event_cluster_id !== undefined) {
    params.set(
      "event_cluster_id",
      String(filters.event_cluster_id),
    );
  }
}

export async function searchKeyword(
  companyId: number,
  query: string,
  filters: SearchFilters = {},
  limit = 50,
): Promise<KeywordSearchResponse> {
  const params = new URLSearchParams({
    company_id: String(companyId),
    q: query,
    limit: String(limit),
  });

  appendSearchFilters(params, filters);

  const response = await fetch(
    `${API_BASE_URL}/search/keyword?${params}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Keyword search API failed with status ${response.status}`,
    );
  }

  return response.json();
}

export async function searchSemantic(
  companyId: number,
  query: string,
  filters: SearchFilters = {},
  limit = 50,
  minimumSimilarity?: number,
): Promise<SemanticSearchResponse> {
  const params = new URLSearchParams({
    company_id: String(companyId),
  });

  appendSearchFilters(params, filters);

  const body: {
    query: string;
    limit: number;
    minimum_similarity?: number;
  } = {
    query,
    limit,
  };

  if (minimumSimilarity !== undefined) {
    body.minimum_similarity = minimumSimilarity;
  }

  const response = await fetch(
    `${API_BASE_URL}/semantic-search?${params}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Semantic search API failed with status ${response.status}`,
    );
  }

  return response.json();
}
