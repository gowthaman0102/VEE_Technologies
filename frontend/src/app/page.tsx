
import { DashboardAutoRefresh } from "@/components/dashboard-auto-refresh";
import { OverviewContent } from "@/components/overview-content";
import { getActiveCompany, getAnalyticsOverview, getArticleCategories, getDashboardIntelligence, getDashboardOverview, getReportHistory } from "@/lib/api";


export default async function Home() {
  const [overview, intelligence, company] = await Promise.all([
    getDashboardOverview(), 
    getDashboardIntelligence(6), 
    getActiveCompany()
  ]);
  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - 30);
  const [analytics, reports, categories] = await Promise.all([
    getAnalyticsOverview(company.id, start.toISOString(), end.toISOString()).catch(() => null),
    getReportHistory(company.id).catch(() => ({ count: 0, items: [] })),
    getArticleCategories(company.id).catch(() => ({ count: 0, items: [] })),
  ]);

  return (
    <main className="px-6 py-8 lg:px-8">
      <DashboardAutoRefresh />
      <div className="mx-auto w-full max-w-[1400px]">
        <OverviewContent 
          initialOverview={overview}
          initialIntelligence={intelligence.items}
          companyName={company.name}
          initialAnalytics={analytics}
          initialReports={reports.items}
          initialCategories={categories.items}
        />
        

      </div>
    </main>
  );
}
