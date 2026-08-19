import { notFound } from "next/navigation";
import { CompanyValueIntelligence } from "@/components/company-value-intelligence";
import { getCompanyIntelligenceV01 } from "@/lib/data/company-intelligence-v01";

export default async function CompanyValuePage({params}:{params:Promise<{companyId:string}>}) {
  const {companyId}=await params;
  const intelligence=await getCompanyIntelligenceV01(companyId);
  if(!intelligence) notFound();
  return <CompanyValueIntelligence intelligence={intelligence}/>;
}
