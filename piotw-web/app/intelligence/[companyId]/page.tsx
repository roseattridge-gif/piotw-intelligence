import { notFound } from "next/navigation";
import { CompanyMonitoringProfile } from "@/components/company-monitoring-profile";
import { getCompanyIntelligenceSnapshot } from "@/lib/data/company-intelligence";
import { selectedPeriod } from "@/lib/data/intelligence-changes";

export default async function IntelligencePage({ params }: { params: Promise<{ companyId: string }> }) {
  const { companyId } = await params;
  const profile = await getCompanyIntelligenceSnapshot(companyId);
  if (!profile) notFound();
  return <CompanyMonitoringProfile profile={profile} period={selectedPeriod(undefined)} />;
}
