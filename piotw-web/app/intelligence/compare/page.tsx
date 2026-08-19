import Link from "next/link";
import { IntelligenceNav } from "@/components/intelligence-nav";
import { acceptedObservationCount, healthySourceCount, latestEvidenceDate, profileChanges } from "@/lib/data/intelligence-changes";
import { listCompanyIntelligenceSnapshots } from "@/lib/data/company-intelligence";

const dateOnly = (value: string) => new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
const value = (item: unknown) => item === null || item === undefined ? "Unavailable" : String(item);
export default async function ComparePage({ searchParams }: { searchParams: Promise<{ companies?: string | string[] }> }) {
  const query = await searchParams; const profiles = (await listCompanyIntelligenceSnapshots()).sort((a,b)=>a.display_name.localeCompare(b.display_name));
  const raw = Array.isArray(query.companies) ? query.companies : (query.companies ?? "").split(",");
  const ids = raw.filter(Boolean).slice(0,4); const selected = (ids.length ? profiles.filter((profile)=>ids.includes(profile.company_id)) : profiles.slice(0,2)).slice(0,4);
  const rows = [
    ["Latest evidence date", (p: typeof selected[number]) => dateOnly(latestEvidenceDate(p))],
    ["Source families represented", (p: typeof selected[number]) => new Set(p.source_freshness.map((s)=>String(s.source_family))).size],
    ["Healthy source count", healthySourceCount], ["Accepted development observations", acceptedObservationCount],
    ["Careers snapshots", (p: typeof selected[number]) => p.careers_history?.length ?? 0],
    ["Observed open roles", (p: typeof selected[number]) => p.careers_history?.at(-1)?.open_roles],
    ["New roles", (p: typeof selected[number]) => p.careers_history?.at(-1)?.new_roles],
    ["Persistent roles", (p: typeof selected[number]) => p.careers_history?.at(-1)?.persistent_roles],
    ["Absent once", (p: typeof selected[number]) => p.careers_history?.at(-1)?.absent_once_roles],
    ["Confirmed closures", (p: typeof selected[number]) => p.careers_history?.at(-1)?.confirmed_closed_roles],
    ["Reopened roles", (p: typeof selected[number]) => p.careers_history?.at(-1)?.reopened_roles],
    ["Resolved procurement evidence", () => "Unavailable — no approved supplier identity matches"],
  ] as const;
  return <main className="intelligence-directory compare-page"><IntelligenceNav/><header><p className="eyebrow">Side-by-side factual comparison</p><h1>Compare companies</h1><p>Raw observations only. Fields are not normalized, weighted, ranked or scored.</p></header>
    <form className="compare-selector"><fieldset><legend>Select 2–4 companies</legend>{profiles.map((profile)=><label key={profile.company_id}><input type="checkbox" name="companies" value={profile.company_id} defaultChecked={selected.some((item)=>item.company_id===profile.company_id)}/>{profile.display_name}</label>)}</fieldset><button type="submit">Compare selected companies</button></form>
    <section className="comparison-table"><header><span>Factual attribute</span>{selected.map((profile)=><Link key={profile.company_id} href={`/intelligence/${profile.company_id}`}>{profile.display_name}</Link>)}</header>{rows.map(([label,getter])=><div key={label}><strong>{label}</strong>{selected.map((profile)=><span key={profile.company_id}>{value(getter(profile))}</span>)}</div>)}</section>
    <section className="comparison-observations"><h2>Specific evidence worth inspecting</h2>{selected.map((profile)=><article key={profile.company_id}><header><h3>{profile.display_name}</h3><p>Shown because PIOTW recorded {profileChanges(profile).length} factual changes in the available history.</p></header>{profileChanges(profile).slice(0,3).map((item)=><div key={item.id}><time>{dateOnly(item.date)}</time><p>{item.statement}</p>{item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer">Evidence and source ↗</a> : <Link href={`/intelligence/${profile.company_id}`}>Inspect retained evidence →</Link>}</div>)}</article>)}</section>
    <footer><span>No normalized comparison · no rank · no prediction</span><Link href="/intelligence">← Watchlist</Link></footer></main>;
}
