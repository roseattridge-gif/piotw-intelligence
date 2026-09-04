import Link from "next/link";
export function CompanyNav({ slug, active }: { slug: string; active: string }) {
  const links = slug==="travis-perkins"?[["Real Company Lab","/lab/travis-perkins"],["Operational X-Ray",`/company/${slug}/x-ray`],["Canonical object","/intelligence/travis-perkins"]]:[["Overview",`/company/${slug}`],["Operational X-Ray",`/company/${slug}/x-ray`],["Evidence",`/company/${slug}/evidence`],["Timeline",`/company/${slug}/timeline`],["Documents",`/company/${slug}/documents`]];
  return <nav className="company-nav" aria-label="Company intelligence"><span>Intelligence file</span><div>{links.map(([label,href],index)=><Link key={label} href={href} aria-current={active===label?"page":undefined}><small>0{index+1}</small>{label}</Link>)}</div></nav>;
}
