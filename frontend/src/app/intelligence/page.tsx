import {
  getDashboardIntelligence,
  getDashboardOverview,
} from "@/lib/api";
import { IntelligencePageClient } from "@/components/intelligence-page-client";

export default async function IntelligencePage() {
  const [data, overview] = await Promise.all([
    getDashboardIntelligence(10000),
    getDashboardOverview()
  ]);

  return (
    <IntelligencePageClient 
      initialItems={data.items} 
      initialOverview={overview}
    />
  );
}
