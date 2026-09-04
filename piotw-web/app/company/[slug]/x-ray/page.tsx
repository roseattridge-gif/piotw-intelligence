import { notFound } from "next/navigation";
import { CompanyNav } from "@/components/company-nav";
import { OperationalXRay } from "@/components/operational-xray";
import { getOperationalXRay } from "@/lib/data/operational-xray";

export default async function OperationalXRayPage({params}:{params:Promise<{slug:string}>}){
 const {slug}=await params;const map=await getOperationalXRay(slug);if(!map)notFound();
 return <><CompanyNav slug={slug} active="Operational X-Ray"/><OperationalXRay map={map}/></>;
}
