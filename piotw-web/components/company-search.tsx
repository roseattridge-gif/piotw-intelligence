"use client";
import { useRouter } from "next/navigation";
import type { Company } from "@/types/intelligence";
export function CompanySearch({ companies }: { companies: Company[] }) {
  const router=useRouter();
  return <div className="search-control"><label htmlFor="company">Search company intelligence</label><div><select id="company" defaultValue=""><option value="" disabled>Select a company</option>{companies.map(c=><option key={c.id} value={c.slug}>{c.name} {c.ticker?`(${c.ticker})`:""}</option>)}</select><button onClick={()=>{const el=document.querySelector<HTMLSelectElement>("#company");if(el?.value)router.push(`/company/${el.value}`)}}>Open intelligence <span aria-hidden>→</span></button></div><small>Development fixture available</small></div>;
}
