
import { OverviewContent } from "@/components/overview-content";
import { PageAmbient } from "@/components/page-ambient";
import { getActiveCompany, getDashboardIntelligence, getDashboardOverview } from "@/lib/api";


export default async function Home() {
  const [overview, intelligence, company] = await Promise.all([
    getDashboardOverview(), 
    getDashboardIntelligence(6), 
    getActiveCompany()
  ]);

  return (
    <main className="relative overflow-hidden bg-canvas px-6 py-8 lg:px-8">
          <PageAmbient kind="overview" />
          <div className="relative z-10 mx-auto w-full max-w-[1400px]">
        <OverviewContent 
          initialOverview={overview}
          initialIntelligence={intelligence.items}
          companyName={company.name}
        />
        

      </div>
    </main>
  );
}
