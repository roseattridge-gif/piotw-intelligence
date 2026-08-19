import { notFound } from "next/navigation";
import { CompanyHeader } from "@/components/company-header";
import { getCompanyBySlug } from "@/lib/data/companies";
export default async function Layout({children,params}:{children:React.ReactNode;params:Promise<{slug:string}>}) { const {slug}=await params; const data=await getCompanyBySlug(slug); if(!data)notFound(); return <div className="company-shell"><CompanyHeader company={data.company}/>{children}</div>; }
