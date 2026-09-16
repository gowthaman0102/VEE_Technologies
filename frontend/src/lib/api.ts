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

export type KeywordSearchResult = {
  article_id: number;
  title: string;
  source_name: string;
  url: string;
  published_at: string | null;
};

export type KeywordSearchResponse = {
  query: string;
  count: number;
  results: KeywordSearchResult[];
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
