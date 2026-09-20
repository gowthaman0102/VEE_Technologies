import { getDashboardCompanies } from "@/lib/api";
import { CompaniesPageClient } from "@/components/companies-page-client";


export default async function CompaniesPage() {
  const data = await getDashboardCompanies();

  return (
    <CompaniesPageClient initialData={data} />
  );
}
