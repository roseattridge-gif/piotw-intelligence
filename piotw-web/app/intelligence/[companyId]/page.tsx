import { notFound } from "next/navigation";
import { CompanyMonitoringProfile } from "@/components/company-monitoring-profile";
import { getCompanyIntelligenceSnapshot } from "@/lib/data/company-intelligence";
import { selectedPeriod } from "@/lib/data/intelligence-changes";

export default async function IntelligencePage({ params, searchParams }: { params: Promise<{ companyId: string }>; searchParams: Promise<{ period?: string }> }) {
  const { companyId } = await params;
  const profile = await getCompanyIntelligenceSnapshot(companyId);
  if (!profile) notFound();
  const query = await searchParams;
  return <CompanyMonitoringProfile profile={profile} period={selectedPeriod(query.period)} />;
}
