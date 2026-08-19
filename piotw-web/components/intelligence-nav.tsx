import Link from "next/link";

export function IntelligenceNav({ companyId }: { companyId?: string }) {
  return <><nav className="mode-switch observed-switch" aria-label="Data mode"><Link href="/intelligence/brief" aria-current="page">Observed data</Link><Link href="/north-star">North Star demo</Link><Link href="/lab">Real Company Lab</Link><span>Live evidence and explicit unknowns</span></nav><nav className="briefing-nav" aria-label="PIOTW intelligence navigation">
    <Link href="/intelligence/brief">Portfolio brief</Link><Link href="/intelligence">Watchlist</Link><Link href="/intelligence/changes">Recent changes</Link><Link href="/intelligence/compare">Compare</Link>{companyId ? <><Link href={`/intelligence/${companyId}`}>Company</Link><Link href={`/intelligence/${companyId}/brief`}>Evidence brief</Link></> : null}
  </nav></>;
}
