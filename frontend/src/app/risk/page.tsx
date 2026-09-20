import { getDashboardRiskAnalytics } from "@/lib/api";
import { RiskDashboardClient } from "@/components/risk-dashboard-client";

export default async function RiskPage() {
  const data = await getDashboardRiskAnalytics();
  return <RiskDashboardClient initialData={data} />;
}
