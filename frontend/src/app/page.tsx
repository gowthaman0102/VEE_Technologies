
import { DashboardAutoRefresh } from "@/components/dashboard-auto-refresh";
import { OverviewContent } from "@/components/overview-content";
import { getActiveCompany, getDashboardIntelligence, getDashboardOverview } from "@/lib/api";


export default async function Home() {
  const [overview, intelligence, company] = await Promise.all([
    getDashboardOverview(), 
    getDashboardIntelligence(6), 
    getActiveCompany()
  ]);

  return (
    <main className="px-6 py-8 lg:px-8">
      <DashboardAutoRefresh />
      <div className="mx-auto w-full max-w-[1400px]">
        <OverviewContent 
          initialOverview={overview}
          initialIntelligence={intelligence.items}
          companyName={company.name}
        />
        

      </div>
    </main>
  );
}
