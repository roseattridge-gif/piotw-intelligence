import { notFound } from "next/navigation";
import { CompanyHeader } from "@/components/company-header";
import { getCompanyBySlug } from "@/lib/data/companies";
export function generateStaticParams(){return [{slug:"northstar-industrial"},{slug:"travis-perkins"}]}
export default async function Layout({children,params}:{children:React.ReactNode;params:Promise<{slug:string}>}) { const {slug}=await params; const data=await getCompanyBySlug(slug); if(!data&&slug!=="travis-perkins")notFound(); return <div className="company-shell">{data&&<CompanyHeader company={data.company}/>} {children}</div>; }
