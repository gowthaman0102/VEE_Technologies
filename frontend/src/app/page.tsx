
import { OverviewContent } from "@/components/overview-content";
import { PageAmbient } from "@/components/page-ambient";
import { 
  getActiveCompany, 
  getDashboardIntelligence, 
  getDashboardOverview,
  getAnalyticsOverview,
  getEventAnalytics,
  getSourceAnalytics
} from "@/lib/api";

export default async function Home() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 7); // Last 7 days

  const endStr = end.toISOString();
  const startStr = start.toISOString();

  const [overview, intelligence, company, analyticsOverview, eventAnalytics, sourceAnalytics] = await Promise.all([
    getDashboardOverview(), 
    getDashboardIntelligence(6), 
    getActiveCompany(),
    getAnalyticsOverview(undefined, startStr, endStr),
    getEventAnalytics(startStr, endStr),
    getSourceAnalytics(startStr, endStr)
  ]);

  return (
    <main className="relative overflow-hidden bg-canvas px-6 py-8 lg:px-8">
      <PageAmbient kind="overview" />
      <div className="relative z-10 mx-auto w-full max-w-[1400px]">
        <OverviewContent 
          initialOverview={overview}
          initialIntelligence={intelligence.items}
          companyName={company.name}
          initialAnalyticsOverview={analyticsOverview}
          initialEventAnalytics={eventAnalytics}
          initialSourceAnalytics={sourceAnalytics}
          timeWindow={{ start: startStr, end: endStr }}
        />
      </div>
    </main>
  );
}
