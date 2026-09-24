import { getCompanyOverview, getDashboardCompanies } from "@/lib/api";
import { CompaniesPageClient } from "@/components/companies-page-client";


export default async function CompaniesPage() {
  const data = await getDashboardCompanies();
  const overview = data.items[0]
    ? await getCompanyOverview(data.items[0].id)
    : null;

  return (
    <CompaniesPageClient initialData={data} initialOverview={overview} />
  );
}
