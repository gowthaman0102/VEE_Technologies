import { getDashboardCompanies, getCompanyOverview } from "@/lib/api";
import { CompaniesPageClient } from "@/components/companies-page-client";


export default async function CompaniesPage() {
  const data = await getDashboardCompanies();
  const firstCompany = data.items[0];
  const overview = firstCompany
    ? await getCompanyOverview(firstCompany.id).catch(() => null)
    : null;

  return (
    <CompaniesPageClient initialData={data} initialOverview={overview} />
  );
}
